# Code Quality & Linting Guide

Complete guide to code quality tools, linters, formatters, and best practices for this project.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Backend Tools](#backend-tools-python)
3. [Frontend Tools](#frontend-tools-typescript)
4. [Pre-commit Hooks](#pre-commit-hooks)
5. [CI/CD Integration](#cicd-integration)
6. [IDE Integration](#ide-integration)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Run All Checks

```bash
# Check mode (no changes)
./scripts/lint-all.sh

# Fix mode (auto-fix issues)
./scripts/lint-all.sh --fix
```

### Backend Only

```bash
# Check mode
./scripts/lint-backend.sh

# Fix mode
./scripts/lint-backend.sh --fix
```

### Frontend Only

```bash
# Check mode
./scripts/lint-frontend.sh

# Fix mode
./scripts/lint-frontend.sh --fix
```

### Pre-commit Hooks Setup

```bash
# Install pre-commit (one-time setup)
pip install pre-commit
pre-commit install

# Pre-commit will now run automatically on git commit

# Run manually on all files
pre-commit run --all-files
```

---

## Backend Tools (Python)

### 1. Ruff - Fast Python Linter & Formatter

**Replaces**: Black, isort, flake8, pyupgrade, flake8-bugbear

**Configuration**: `backend/pyproject.toml`

**What it checks**:
- Code style (PEP 8)
- Import sorting
- Unused imports/variables
- Code complexity
- Python version upgrades
- Bug-prone patterns
- Print statements (should use logging)

**Usage**:

```bash
# Lint check
docker compose exec backend ruff check backend/

# Auto-fix issues
docker compose exec backend ruff check --fix backend/

# Format code (like Black)
docker compose exec backend ruff format backend/

# Check format without changes
docker compose exec backend ruff format --check backend/
```

**Key Rules Enabled**:
- `E` - pycodestyle errors
- `W` - pycodestyle warnings
- `F` - Pyflakes (unused imports, undefined names)
- `I` - isort (import sorting)
- `N` - pep8-naming
- `UP` - pyupgrade (modernize Python syntax)
- `B` - flake8-bugbear (bug-prone patterns)
- `SIM` - flake8-simplify (code simplification)
- `C4` - flake8-comprehensions (better comprehensions)
- `T10` - flake8-debugger (no debugger statements)
- `T20` - flake8-print (no print statements)

**Configuration Example** (`pyproject.toml`):

```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "C4", "T10", "T20"]
ignore = ["E501", "B008"]

[tool.ruff.lint.isort]
known-first-party = ["backend", "core", "modules", "models", "schemas"]
```

### 2. MyPy - Static Type Checker

**Configuration**: `backend/mypy.ini`

**What it checks**:
- Type annotations consistency
- Type errors
- Optional vs None handling
- Generic types
- Return type consistency

**Usage**:

```bash
# Run type check
docker compose exec backend mypy backend/ --config-file mypy.ini

# Generate type coverage report
docker compose exec backend mypy backend/ --html-report mypy-report/
```

**Best Practices**:
- Always add type hints to function signatures
- Use `Optional[Type]` for nullable values
- Use specific types instead of `Any`
- Use `TypedDict` for dictionaries with known keys
- Use generics (`List[str]`, `Dict[str, int]`)

**Example**:

```python
# ✅ Good - Type hints everywhere
def get_user(user_id: int, db: Session) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

# ❌ Bad - No type hints
def get_user(user_id, db):
    return db.query(User).filter(User.id == user_id).first()
```

### 3. Bandit - Security Linter

**Configuration**: `backend/.bandit.yaml`

**What it checks**:
- SQL injection vulnerabilities
- Hardcoded passwords/secrets
- Insecure cryptography
- Shell injection risks
- Insecure SSL/TLS usage
- YAML/XML parsing vulnerabilities
- Unsafe deserialization
- Use of weak random generators

**Usage**:

```bash
# Run security scan
docker compose exec backend bandit -c .bandit.yaml -r backend/

# Generate HTML report
docker compose exec backend bandit -c .bandit.yaml -r backend/ -f html -o bandit-report.html
```

**Common Issues**:

```python
# ❌ Bad - SQL injection risk
query = f"SELECT * FROM users WHERE email = '{email}'"
db.execute(query)

# ✅ Good - Parameterized query
query = db.query(User).filter(User.email == email)

# ❌ Bad - Hardcoded secret
SECRET_KEY = "supersecretkey123"

# ✅ Good - Environment variable
SECRET_KEY = os.getenv("SECRET_KEY")

# ❌ Bad - Insecure random
import random
token = random.randint(1000, 9999)

# ✅ Good - Cryptographically secure
import secrets
token = secrets.token_urlsafe(32)
```

### 4. Safety - Dependency Vulnerability Scanner

**What it checks**:
- Known vulnerabilities in dependencies
- CVE database matches
- Security advisories

**Usage**:

```bash
# Scan dependencies
docker compose exec backend safety check

# JSON output
docker compose exec backend safety check --json

# Check specific file
docker compose exec backend safety check -r requirements.txt
```

**How to Fix Vulnerabilities**:
1. Review the vulnerability details
2. Update to patched version: `pip install package==X.Y.Z`
3. Update `requirements.txt`
4. Rebuild Docker image
5. Re-run tests

### 5. Pytest Coverage

**What it checks**:
- Test coverage percentage
- Uncovered lines
- Missing test cases

**Usage**:

```bash
# Run tests with coverage
docker compose exec backend pytest --cov=backend --cov-report=html --cov-report=term

# View HTML report
open backend/htmlcov/index.html
```

**Coverage Goals**:
- Overall: ≥80%
- Critical modules (auth, payments): ≥90%
- Utils/helpers: ≥70%

---

## Frontend Tools (TypeScript)

### 1. ESLint - JavaScript/TypeScript Linter

**Configuration**: `frontend/.eslintrc.json` and `frontend/eslint.config.mjs`

**What it checks**:
- TypeScript errors
- React best practices
- Next.js best practices
- Unused variables
- Missing dependencies in useEffect
- Accessibility issues
- Performance anti-patterns

**Usage**:

```bash
# Lint check
docker compose exec frontend npm run lint

# Auto-fix issues
docker compose exec frontend npm run lint:fix

# Lint specific file
docker compose exec frontend npx eslint app/page.tsx
```

**Key Rules**:
- React Hooks rules (exhaustive-deps)
- Next.js optimizations (no-img-element)
- TypeScript strict mode
- Accessibility (jsx-a11y)
- Import sorting

**Common Issues**:

```typescript
// ❌ Bad - Missing dependency in useEffect
useEffect(() => {
  fetchData(userId);
}, []); // userId is missing

// ✅ Good - All dependencies included
useEffect(() => {
  fetchData(userId);
}, [userId]);

// ❌ Bad - Unescaped entities
<p>Don't use plain quotes</p>

// ✅ Good - Escaped entities
<p>Don&apos;t use plain quotes</p>

// ❌ Bad - Using <img> instead of Next.js Image
<img src="/logo.png" alt="Logo" />

// ✅ Good - Using Next.js Image component
<Image src="/logo.png" alt="Logo" width={100} height={100} />
```

### 2. Prettier - Code Formatter

**Configuration**: `frontend/.prettierrc.json`

**What it formats**:
- JavaScript/TypeScript
- JSX/TSX
- CSS/SCSS
- JSON
- Markdown

**Usage**:

```bash
# Check formatting
docker compose exec frontend npm run format:check

# Auto-format
docker compose exec frontend npm run format:fix

# Format specific file
docker compose exec frontend npx prettier --write app/page.tsx
```

**Configuration** (`.prettierrc.json`):

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

**Before/After**:

```typescript
// Before
const user={name:"John",email:"john@example.com",role:"admin"}

// After (Prettier formatted)
const user = {
  name: 'John',
  email: 'john@example.com',
  role: 'admin',
};
```

### 3. TypeScript Compiler (tsc)

**Configuration**: `frontend/tsconfig.json`

**What it checks**:
- Type errors
- Unused variables
- Implicit any types
- Strict null checks
- Module resolution

**Usage**:

```bash
# Type check
docker compose exec frontend npm run type-check

# Type check tests
docker compose exec frontend npm run type-check:tests

# Watch mode
docker compose exec frontend npx tsc --noEmit --watch
```

**Strict Mode Settings** (`tsconfig.json`):

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

---

## Pre-commit Hooks

Pre-commit hooks run automatically before each commit, ensuring code quality.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Update hook versions
pre-commit autoupdate
```

### What Runs on Commit?

**Automatic Checks**:
1. ✅ Trailing whitespace removal
2. ✅ End-of-file fixing
3. ✅ YAML/JSON/TOML syntax check
4. ✅ Large files detection (>1MB)
5. ✅ Merge conflict markers detection
6. ✅ Private key detection
7. ✅ **Ruff** - Python linting & formatting
8. ✅ **MyPy** - Type checking
9. ✅ **Bandit** - Security scanning
10. ✅ **ESLint** - Frontend linting
11. ✅ **Prettier** - Frontend formatting
12. ✅ **TypeScript** - Type checking
13. ✅ **Secrets detection** - No committed secrets

### Manual Run

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run prettier --all-files

# Skip hooks (emergency only)
git commit --no-verify -m "commit message"
```

### Skipping Specific Hooks

```bash
# Skip all hooks
SKIP= git commit -m "message"

# Skip specific hooks
SKIP=mypy,eslint git commit -m "message"
```

**⚠️ WARNING**: Only skip hooks when absolutely necessary (hotfixes). Always fix issues instead.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      - name: Run Ruff
        run: ruff check backend/
      - name: Run MyPy
        run: mypy backend/ --config-file backend/mypy.ini
      - name: Run Bandit
        run: bandit -c backend/.bandit.yaml -r backend/

  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run ESLint
        run: cd frontend && npm run lint
      - name: Run Prettier
        run: cd frontend && npm run format:check
      - name: Run TypeScript
        run: cd frontend && npm run type-check
```

---

## IDE Integration

### Visual Studio Code

**Extensions to Install**:
- Python (Microsoft)
- Pylance
- Ruff
- ESLint
- Prettier
- TypeScript and JavaScript Language Features

**Settings** (`.vscode/settings.json`):

```json
{
  // Python
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "ruff.enable": true,
  "ruff.organizeImports": true,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll": true
    }
  },

  // TypeScript/JavaScript
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "eslint.format.enable": true,

  // General
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

### PyCharm / IntelliJ IDEA

**Settings**:
1. **File → Settings → Tools → Python Integrated Tools**
   - Set Ruff as linter
2. **File → Settings → Editor → Code Style → Python**
   - Line length: 120
3. **File → Settings → Editor → Inspections**
   - Enable all Python inspections

### Vim/Neovim

**Plugins**:
- ALE (Asynchronous Lint Engine)
- coc.nvim (Conquer of Completion)

**Configuration** (`.vimrc`):

```vim
" ALE configuration
let g:ale_linters = {
\   'python': ['ruff', 'mypy', 'bandit'],
\   'typescript': ['eslint', 'tsserver'],
\}

let g:ale_fixers = {
\   'python': ['ruff_format'],
\   'typescript': ['prettier', 'eslint'],
\}

let g:ale_fix_on_save = 1
```

---

## Troubleshooting

### Ruff Issues

**Problem**: Ruff command not found
```bash
# Solution: Install ruff
pip install ruff

# Or use Docker
docker compose exec backend ruff check backend/
```

**Problem**: Import order conflicts
```bash
# Solution: Auto-fix imports
ruff check --select I --fix backend/
```

### MyPy Issues

**Problem**: Missing type stubs
```bash
# Solution: Install type stubs
pip install types-requests types-redis sqlalchemy-stubs
```

**Problem**: Too many errors
```bash
# Solution: Start with less strict settings
# Edit mypy.ini and comment out strict checks temporarily
```

### ESLint Issues

**Problem**: ESLint not finding config
```bash
# Solution: Clear cache
rm -rf frontend/.eslintcache
npm run lint
```

**Problem**: Conflicting rules with Prettier
```bash
# Solution: Install eslint-config-prettier
npm install --save-dev eslint-config-prettier
```

### Pre-commit Issues

**Problem**: Pre-commit hook failing
```bash
# Solution: Update hooks
pre-commit clean
pre-commit install --install-hooks
pre-commit run --all-files
```

**Problem**: Slow pre-commit
```bash
# Solution: Skip slow hooks temporarily
SKIP=mypy git commit -m "message"
```

---

## Summary

### Checklist Before Commit

- [ ] Run `./scripts/lint-all.sh --fix`
- [ ] Fix all linting errors
- [ ] Run tests: `docker compose -f docker-compose.test.yml up`
- [ ] Check test coverage: `pytest --cov`
- [ ] Review git diff: `git diff --cached`
- [ ] Write clear commit message (Conventional Commits)
- [ ] Commit (pre-commit hooks will run automatically)

### Quality Standards

- **Code Style**: Enforced by Ruff/Prettier
- **Type Safety**: 100% type hint coverage (Python), strict TypeScript
- **Security**: No Bandit/Safety warnings
- **Test Coverage**: ≥80% overall, ≥90% critical modules
- **Documentation**: All public APIs documented
- **Performance**: No performance anti-patterns

---

## Additional Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [ESLint Rules](https://eslint.org/docs/rules/)
- [Prettier Options](https://prettier.io/docs/en/options.html)
- [Pre-commit Framework](https://pre-commit.com/)
- [Bandit Documentation](https://bandit.readthedocs.io/)

---

**Last Updated**: 2026-01-28
