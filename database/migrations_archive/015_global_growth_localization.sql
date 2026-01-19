-- ============================================================================
-- Global Growth: Multi-Currency, Language, Localization
-- Design for international scale from day 1
-- ============================================================================

-- ============================================================================
-- Part 1: User Language Preferences
-- ============================================================================

-- Add language and locale preferences to users
ALTER TABLE users
ADD COLUMN IF NOT EXISTS preferred_language CHAR(2) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS detected_language CHAR(2),
ADD COLUMN IF NOT EXISTS locale VARCHAR(10) DEFAULT 'en-US',
ADD COLUMN IF NOT EXISTS detected_locale VARCHAR(10),
ADD COLUMN IF NOT EXISTS locale_detection_confidence NUMERIC(3,2);

COMMENT ON COLUMN users.preferred_language IS
'User-selected language (ISO 639-1): en, es, fr, de, pt, zh, ja, ko, ar, ru, etc.';

COMMENT ON COLUMN users.detected_language IS
'Auto-detected language from browser/IP. Used as fallback if preferred not set.';

COMMENT ON COLUMN users.locale IS
'Full locale code: en-US, es-ES, fr-FR, pt-BR, zh-CN. Determines number/date formats.';

COMMENT ON COLUMN users.locale_detection_confidence IS
'Confidence score (0-1) for auto-detected locale. Higher = more reliable.';

CREATE INDEX IF NOT EXISTS idx_users_language ON users(preferred_language);
CREATE INDEX IF NOT EXISTS idx_users_locale ON users(locale);

-- ============================================================================
-- Part 2: Localized Subject Names
-- ============================================================================

-- Support subject names in multiple languages
CREATE TABLE IF NOT EXISTS subject_localizations (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    language_code CHAR(2) NOT NULL,
    localized_name VARCHAR(100) NOT NULL,
    localized_description TEXT,
    is_machine_translated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_subject_language UNIQUE (subject_id, language_code)
);

CREATE INDEX IF NOT EXISTS idx_subject_localizations_subject ON subject_localizations(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_localizations_language ON subject_localizations(language_code);

COMMENT ON TABLE subject_localizations IS
'Subject names in multiple languages. Maps to same subject_id.
Example: "Mathematics" (en) = "Mathématiques" (fr) = "Matemáticas" (es)';

-- Insert default English localizations
INSERT INTO subject_localizations (subject_id, language_code, localized_name, localized_description)
SELECT 
    id,
    'en',
    name,
    description
FROM subjects
ON CONFLICT (subject_id, language_code) DO NOTHING;

-- ============================================================================
-- Part 3: Currency Support & Conversion
-- ============================================================================

-- Currency exchange rates table (for display conversion only)
CREATE TABLE IF NOT EXISTS currency_rates (
    id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL,
    to_currency CHAR(3) NOT NULL,
    exchange_rate NUMERIC(12,6) NOT NULL,
    valid_from TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    valid_until TIMESTAMPTZ,
    source VARCHAR(50) DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_currency_pair_date UNIQUE (from_currency, to_currency, valid_from)
);

CREATE INDEX IF NOT EXISTS idx_currency_rates_pair ON currency_rates(from_currency, to_currency, valid_from DESC);
CREATE INDEX IF NOT EXISTS idx_currency_rates_valid ON currency_rates(valid_until) WHERE valid_until IS NOT NULL;

COMMENT ON TABLE currency_rates IS
'Exchange rates for price display conversion (NOT for actual billing).
Actual payments always use tutor native currency.';

-- Insert common currency pairs (base rates, update manually or via API)
INSERT INTO currency_rates (from_currency, to_currency, exchange_rate, valid_from) VALUES
    ('USD', 'EUR', 0.92, CURRENT_TIMESTAMP),
    ('USD', 'GBP', 0.79, CURRENT_TIMESTAMP),
    ('USD', 'CAD', 1.36, CURRENT_TIMESTAMP),
    ('USD', 'AUD', 1.52, CURRENT_TIMESTAMP),
    ('USD', 'JPY', 149.50, CURRENT_TIMESTAMP),
    ('USD', 'BRL', 4.98, CURRENT_TIMESTAMP),
    ('USD', 'INR', 83.12, CURRENT_TIMESTAMP),
    ('EUR', 'USD', 1.09, CURRENT_TIMESTAMP),
    ('EUR', 'GBP', 0.86, CURRENT_TIMESTAMP),
    ('GBP', 'USD', 1.27, CURRENT_TIMESTAMP),
    ('GBP', 'EUR', 1.16, CURRENT_TIMESTAMP)
ON CONFLICT (from_currency, to_currency, valid_from) DO NOTHING;

-- Function to get current exchange rate
CREATE OR REPLACE FUNCTION get_exchange_rate(
    p_from_currency CHAR(3),
    p_to_currency CHAR(3)
)
RETURNS NUMERIC AS $$
DECLARE
    v_rate NUMERIC;
BEGIN
    -- Same currency = 1:1
    IF p_from_currency = p_to_currency THEN
        RETURN 1.0;
    END IF;
    
    -- Get latest valid rate
    SELECT exchange_rate INTO v_rate
    FROM currency_rates
    WHERE from_currency = p_from_currency
      AND to_currency = p_to_currency
      AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
    ORDER BY valid_from DESC
    LIMIT 1;
    
    -- If direct rate not found, try reverse and invert
    IF v_rate IS NULL THEN
        SELECT 1.0 / exchange_rate INTO v_rate
        FROM currency_rates
        WHERE from_currency = p_to_currency
          AND to_currency = p_from_currency
          AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
        ORDER BY valid_from DESC
        LIMIT 1;
    END IF;
    
    RETURN COALESCE(v_rate, 1.0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_exchange_rate IS
'Get current exchange rate between two currencies. Returns 1.0 if not found.';

-- Convert price with formatting
CREATE OR REPLACE FUNCTION convert_price(
    p_amount NUMERIC,
    p_from_currency CHAR(3),
    p_to_currency CHAR(3),
    p_include_symbol BOOLEAN DEFAULT TRUE
)
RETURNS TEXT AS $$
DECLARE
    v_rate NUMERIC;
    v_converted NUMERIC;
    v_symbol TEXT;
BEGIN
    v_rate := get_exchange_rate(p_from_currency, p_to_currency);
    v_converted := ROUND(p_amount * v_rate, 2);
    
    IF p_include_symbol THEN
        -- Add currency symbol
        v_symbol := CASE p_to_currency
            WHEN 'USD' THEN '$'
            WHEN 'EUR' THEN '€'
            WHEN 'GBP' THEN '£'
            WHEN 'JPY' THEN '¥'
            WHEN 'CAD' THEN 'C$'
            WHEN 'AUD' THEN 'A$'
            WHEN 'BRL' THEN 'R$'
            WHEN 'INR' THEN '₹'
            ELSE p_to_currency || ' '
        END;
        
        RETURN v_symbol || v_converted::TEXT;
    ELSE
        RETURN v_converted::TEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 4: Supported Languages & Currencies
-- ============================================================================

-- Available languages (for UI translations)
CREATE TABLE IF NOT EXISTS supported_languages (
    language_code CHAR(2) PRIMARY KEY,
    language_name_en VARCHAR(50) NOT NULL,
    language_name_native VARCHAR(50) NOT NULL,
    is_rtl BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    translation_completeness INTEGER DEFAULT 0 CHECK (translation_completeness BETWEEN 0 AND 100),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

INSERT INTO supported_languages (language_code, language_name_en, language_name_native, is_rtl, translation_completeness) VALUES
    ('en', 'English', 'English', FALSE, 100),
    ('es', 'Spanish', 'Español', FALSE, 100),
    ('fr', 'French', 'Français', FALSE, 100),
    ('de', 'German', 'Deutsch', FALSE, 80),
    ('pt', 'Portuguese', 'Português', FALSE, 80),
    ('it', 'Italian', 'Italiano', FALSE, 60),
    ('zh', 'Chinese', '中文', FALSE, 60),
    ('ja', 'Japanese', '日本語', FALSE, 60),
    ('ko', 'Korean', '한국어', FALSE, 40),
    ('ar', 'Arabic', 'العربية', TRUE, 40),
    ('ru', 'Russian', 'Русский', FALSE, 40),
    ('hi', 'Hindi', 'हिन्दी', FALSE, 20)
ON CONFLICT (language_code) DO NOTHING;

-- Available currencies
CREATE TABLE IF NOT EXISTS supported_currencies (
    currency_code CHAR(3) PRIMARY KEY,
    currency_name VARCHAR(50) NOT NULL,
    currency_symbol VARCHAR(10) NOT NULL,
    decimal_places INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

INSERT INTO supported_currencies (currency_code, currency_name, currency_symbol, decimal_places) VALUES
    ('USD', 'US Dollar', '$', 2),
    ('EUR', 'Euro', '€', 2),
    ('GBP', 'British Pound', '£', 2),
    ('CAD', 'Canadian Dollar', 'C$', 2),
    ('AUD', 'Australian Dollar', 'A$', 2),
    ('JPY', 'Japanese Yen', '¥', 0),
    ('CNY', 'Chinese Yuan', '¥', 2),
    ('BRL', 'Brazilian Real', 'R$', 2),
    ('INR', 'Indian Rupee', '₹', 2),
    ('MXN', 'Mexican Peso', 'Mex$', 2),
    ('KRW', 'South Korean Won', '₩', 0),
    ('RUB', 'Russian Ruble', '₽', 2)
ON CONFLICT (currency_code) DO NOTHING;

-- ============================================================================
-- Part 5: Locale Auto-Detection
-- ============================================================================

-- Function to detect locale from timezone
CREATE OR REPLACE FUNCTION detect_locale_from_timezone(p_timezone VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    RETURN CASE
        -- Americas
        WHEN p_timezone LIKE 'America/New_York' THEN 'en-US'
        WHEN p_timezone LIKE 'America/Chicago' THEN 'en-US'
        WHEN p_timezone LIKE 'America/Denver' THEN 'en-US'
        WHEN p_timezone LIKE 'America/Los_Angeles' THEN 'en-US'
        WHEN p_timezone LIKE 'America/Toronto' THEN 'en-CA'
        WHEN p_timezone LIKE 'America/Vancouver' THEN 'en-CA'
        WHEN p_timezone LIKE 'America/Mexico_City' THEN 'es-MX'
        WHEN p_timezone LIKE 'America/Sao_Paulo' THEN 'pt-BR'
        WHEN p_timezone LIKE 'America/Buenos_Aires' THEN 'es-AR'
        
        -- Europe
        WHEN p_timezone LIKE 'Europe/London' THEN 'en-GB'
        WHEN p_timezone LIKE 'Europe/Paris' THEN 'fr-FR'
        WHEN p_timezone LIKE 'Europe/Berlin' THEN 'de-DE'
        WHEN p_timezone LIKE 'Europe/Madrid' THEN 'es-ES'
        WHEN p_timezone LIKE 'Europe/Rome' THEN 'it-IT'
        WHEN p_timezone LIKE 'Europe/Amsterdam' THEN 'nl-NL'
        WHEN p_timezone LIKE 'Europe/Brussels' THEN 'fr-BE'
        WHEN p_timezone LIKE 'Europe/Zurich' THEN 'de-CH'
        WHEN p_timezone LIKE 'Europe/Vienna' THEN 'de-AT'
        WHEN p_timezone LIKE 'Europe/Moscow' THEN 'ru-RU'
        
        -- Asia
        WHEN p_timezone LIKE 'Asia/Tokyo' THEN 'ja-JP'
        WHEN p_timezone LIKE 'Asia/Seoul' THEN 'ko-KR'
        WHEN p_timezone LIKE 'Asia/Shanghai' THEN 'zh-CN'
        WHEN p_timezone LIKE 'Asia/Hong_Kong' THEN 'zh-HK'
        WHEN p_timezone LIKE 'Asia/Singapore' THEN 'en-SG'
        WHEN p_timezone LIKE 'Asia/Dubai' THEN 'ar-AE'
        WHEN p_timezone LIKE 'Asia/Kolkata' THEN 'en-IN'
        WHEN p_timezone LIKE 'Asia/Bangkok' THEN 'th-TH'
        WHEN p_timezone LIKE 'Asia/Jakarta' THEN 'id-ID'
        
        -- Oceania
        WHEN p_timezone LIKE 'Australia/Sydney' THEN 'en-AU'
        WHEN p_timezone LIKE 'Australia/Melbourne' THEN 'en-AU'
        WHEN p_timezone LIKE 'Pacific/Auckland' THEN 'en-NZ'
        
        -- Default
        ELSE 'en-US'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to suggest currency from locale
CREATE OR REPLACE FUNCTION suggest_currency_from_locale(p_locale VARCHAR)
RETURNS CHAR(3) AS $$
BEGIN
    RETURN CASE
        WHEN p_locale LIKE 'en-US%' THEN 'USD'
        WHEN p_locale LIKE 'en-CA%' THEN 'CAD'
        WHEN p_locale LIKE 'en-GB%' THEN 'GBP'
        WHEN p_locale LIKE 'en-AU%' THEN 'AUD'
        WHEN p_locale LIKE 'en-NZ%' THEN 'NZD'
        WHEN p_locale LIKE 'fr-FR%' THEN 'EUR'
        WHEN p_locale LIKE 'de-DE%' THEN 'EUR'
        WHEN p_locale LIKE 'es-ES%' THEN 'EUR'
        WHEN p_locale LIKE 'it-IT%' THEN 'EUR'
        WHEN p_locale LIKE 'nl-NL%' THEN 'EUR'
        WHEN p_locale LIKE 'pt-BR%' THEN 'BRL'
        WHEN p_locale LIKE 'es-MX%' THEN 'MXN'
        WHEN p_locale LIKE 'ja-JP%' THEN 'JPY'
        WHEN p_locale LIKE 'ko-KR%' THEN 'KRW'
        WHEN p_locale LIKE 'zh-CN%' THEN 'CNY'
        WHEN p_locale LIKE 'ru-RU%' THEN 'RUB'
        WHEN p_locale LIKE 'en-IN%' THEN 'INR'
        ELSE 'USD'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Part 6: Helper Views
-- ============================================================================

-- View for subjects with localized names
CREATE OR REPLACE VIEW subjects_localized AS
SELECT 
    s.id as subject_id,
    s.name as default_name,
    s.description as default_description,
    s.is_active,
    sl.language_code,
    COALESCE(sl.localized_name, s.name) as display_name,
    COALESCE(sl.localized_description, s.description) as display_description
FROM subjects s
LEFT JOIN subject_localizations sl ON s.id = sl.subject_id
WHERE s.is_active = TRUE;

COMMENT ON VIEW subjects_localized IS
'Subjects with localized names. Joins on language_code to get appropriate translation.';

-- View for user preferences summary
CREATE OR REPLACE VIEW user_preferences_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.role,
    u.preferred_language,
    u.locale,
    u.currency,
    u.timezone,
    sl.language_name_en,
    sl.language_name_native,
    sl.is_rtl,
    sc.currency_symbol,
    CASE 
        WHEN u.preferred_language IS NOT NULL THEN 'user_selected'
        WHEN u.detected_language IS NOT NULL THEN 'auto_detected'
        ELSE 'default'
    END as language_source
FROM users u
LEFT JOIN supported_languages sl ON u.preferred_language = sl.language_code
LEFT JOIN supported_currencies sc ON u.currency = sc.currency_code
WHERE u.deleted_at IS NULL;

COMMENT ON VIEW user_preferences_summary IS
'User preferences with language and currency metadata for UI rendering.';

-- ============================================================================
-- Part 7: Common Subject Translations
-- ============================================================================

-- Add Spanish translations
INSERT INTO subject_localizations (subject_id, language_code, localized_name, localized_description) 
SELECT 
    s.id,
    'es',
    CASE s.name
        WHEN 'Mathematics' THEN 'Matemáticas'
        WHEN 'Science' THEN 'Ciencias'
        WHEN 'English' THEN 'Inglés'
        WHEN 'History' THEN 'Historia'
        WHEN 'Computer Science' THEN 'Informática'
        WHEN 'Languages' THEN 'Idiomas'
        WHEN 'Arts' THEN 'Artes'
        WHEN 'Business' THEN 'Negocios'
        ELSE s.name
    END,
    s.description
FROM subjects s
WHERE s.is_active = TRUE
ON CONFLICT (subject_id, language_code) DO NOTHING;

-- Add French translations
INSERT INTO subject_localizations (subject_id, language_code, localized_name, localized_description)
SELECT 
    s.id,
    'fr',
    CASE s.name
        WHEN 'Mathematics' THEN 'Mathématiques'
        WHEN 'Science' THEN 'Sciences'
        WHEN 'English' THEN 'Anglais'
        WHEN 'History' THEN 'Histoire'
        WHEN 'Computer Science' THEN 'Informatique'
        WHEN 'Languages' THEN 'Langues'
        WHEN 'Arts' THEN 'Arts'
        WHEN 'Business' THEN 'Commerce'
        ELSE s.name
    END,
    s.description
FROM subjects s
WHERE s.is_active = TRUE
ON CONFLICT (subject_id, language_code) DO NOTHING;

-- Add German translations
INSERT INTO subject_localizations (subject_id, language_code, localized_name, localized_description)
SELECT 
    s.id,
    'de',
    CASE s.name
        WHEN 'Mathematics' THEN 'Mathematik'
        WHEN 'Science' THEN 'Naturwissenschaften'
        WHEN 'English' THEN 'Englisch'
        WHEN 'History' THEN 'Geschichte'
        WHEN 'Computer Science' THEN 'Informatik'
        WHEN 'Languages' THEN 'Sprachen'
        WHEN 'Arts' THEN 'Kunst'
        WHEN 'Business' THEN 'Wirtschaft'
        ELSE s.name
    END,
    s.description
FROM subjects s
WHERE s.is_active = TRUE
ON CONFLICT (subject_id, language_code) DO NOTHING;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_languages_count INTEGER;
    v_currencies_count INTEGER;
    v_localizations_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_languages_count FROM supported_languages WHERE is_active = TRUE;
    SELECT COUNT(*) INTO v_currencies_count FROM supported_currencies WHERE is_active = TRUE;
    SELECT COUNT(*) INTO v_localizations_count FROM subject_localizations;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 015: Global Growth & Localization ===';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Language Support';
    RAISE NOTICE '  - % languages available', v_languages_count;
    RAISE NOTICE '  - Auto-detection from timezone/browser';
    RAISE NOTICE '  - RTL support for Arabic';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Multi-Currency';
    RAISE NOTICE '  - % currencies supported', v_currencies_count;
    RAISE NOTICE '  - Exchange rate display conversion';
    RAISE NOTICE '  - Currency symbols and formatting';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Localized Subjects';
    RAISE NOTICE '  - % subject translations', v_localizations_count;
    RAISE NOTICE '  - Same subject_id across languages';
    RAISE NOTICE '  - Spanish, French, German included';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Helper Functions';
    RAISE NOTICE '  - get_exchange_rate(from, to)';
    RAISE NOTICE '  - convert_price(amount, from, to)';
    RAISE NOTICE '  - detect_locale_from_timezone()';
    RAISE NOTICE '  - suggest_currency_from_locale()';
    RAISE NOTICE '';
    RAISE NOTICE '🌐 Key: Localize where it matters (pricing, subjects, UI)';
    RAISE NOTICE '📊 Expected: Remove international growth blockers';
END $$;
