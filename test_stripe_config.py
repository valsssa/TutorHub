#!/usr/bin/env python3
"""
Stripe Configuration Test Script
Tests if Stripe is properly configured without starting the full application
"""

import os
import sys
import re
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")

def print_header(msg):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def validate_stripe_key_format(key_type, key_value):
    """Validate Stripe key format"""
    if not key_value or key_value == "":
        return False, "Empty key"

    patterns = {
        "secret": r"^sk_(test|live)_[A-Za-z0-9]{24,}$",
        "publishable": r"^pk_(test|live)_[A-Za-z0-9]{24,}$",
        "webhook": r"^whsec_[A-Za-z0-9]{32,}$",
        "connect": r"^ca_[A-Za-z0-9]{24,}$"
    }

    pattern = patterns.get(key_type)
    if not pattern:
        return False, "Unknown key type"

    if re.match(pattern, key_value):
        is_test = "_test_" in key_value if key_type in ["secret", "publishable"] else None
        mode = " (TEST MODE)" if is_test else " (LIVE MODE)" if is_test is False else ""
        return True, f"Valid{mode}"
    else:
        return False, "Invalid format"

def load_env_file(filepath):
    """Load environment variables from .env file"""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

def check_env_file(filepath, file_label):
    """Check a single .env file"""
    print_header(f"Checking {file_label}")

    if not os.path.exists(filepath):
        print_error(f"File not found: {filepath}")
        return False

    print_success(f"File exists: {filepath}")

    env_vars = load_env_file(filepath)

    # Check Stripe keys
    stripe_keys = {
        "STRIPE_SECRET_KEY": "secret",
        "STRIPE_PUBLISHABLE_KEY": "publishable",
        "STRIPE_WEBHOOK_SECRET": "webhook",
        "STRIPE_CONNECT_CLIENT_ID": "connect"
    }

    all_valid = True

    for env_key, key_type in stripe_keys.items():
        key_value = env_vars.get(env_key, "")

        if not key_value:
            print_error(f"{env_key}: Not set")
            all_valid = False
            continue

        # Check if it's a placeholder
        if "YourStripe" in key_value or "your_" in key_value.lower() or "YourActual" in key_value:
            print_warning(f"{env_key}: Placeholder value detected")
            print_info(f"  Current value: {key_value[:30]}...")
            all_valid = False
            continue

        # Validate format
        is_valid, message = validate_stripe_key_format(key_type, key_value)

        if is_valid:
            # Mask the key for security
            masked = f"{key_value[:15]}...{key_value[-4:]}" if len(key_value) > 20 else "***"
            print_success(f"{env_key}: {message}")
            print_info(f"  Value: {masked}")
        else:
            print_error(f"{env_key}: {message}")
            print_info(f"  Current value: {key_value[:30]}...")
            if key_type != "connect":  # Connect is optional
                all_valid = False

    return all_valid

def test_stripe_import():
    """Test if stripe package can be imported"""
    print_header("Testing Stripe Package")

    try:
        import stripe
        print_success(f"Stripe package installed (version: {stripe.__version__})")
        return True
    except ImportError:
        print_error("Stripe package not installed")
        print_info("Install with: pip install stripe==8.0.0")
        return False

def test_stripe_api_connection(api_key):
    """Test actual connection to Stripe API"""
    print_header("Testing Stripe API Connection")

    if not api_key or "YourStripe" in api_key or "your_" in api_key.lower():
        print_warning("Skipping API test - no valid API key configured")
        return False

    try:
        import stripe
        stripe.api_key = api_key

        # Try to retrieve account info
        account = stripe.Account.retrieve()

        print_success("Successfully connected to Stripe API")
        print_info(f"  Account ID: {account.id}")
        print_info(f"  Email: {account.email if hasattr(account, 'email') else 'N/A'}")
        print_info(f"  Charges enabled: {account.charges_enabled}")
        print_info(f"  Payouts enabled: {account.payouts_enabled}")

        return True

    except Exception as e:
        print_error(f"Failed to connect to Stripe API: {str(e)}")
        return False

def main():
    print_header("EduStream Stripe Configuration Test")

    # Get project root
    script_dir = Path(__file__).parent

    # Check root .env
    root_env = script_dir / ".env"
    root_valid = check_env_file(root_env, "Root .env file (Docker Compose)")

    # Check backend .env
    backend_env = script_dir / "backend" / ".env"
    backend_valid = check_env_file(backend_env, "Backend .env file (Application)")

    # Test Stripe package
    package_valid = test_stripe_import()

    # Test API connection if package is available
    api_valid = False
    if package_valid and root_valid:
        env_vars = load_env_file(root_env)
        api_key = env_vars.get("STRIPE_SECRET_KEY", "")
        api_valid = test_stripe_api_connection(api_key)

    # Summary
    print_header("Configuration Summary")

    if root_valid and backend_valid and package_valid:
        print_success("All configuration files are valid!")

        if api_valid:
            print_success("Stripe API connection successful!")
            print_info("\nYou're ready to accept payments! 🎉")
            print_info("\nNext steps:")
            print_info("  1. Start application: docker-compose up -d")
            print_info("  2. Test with Stripe test cards")
            print_info("  3. Set up webhook in Stripe Dashboard")
        else:
            print_warning("\nConfiguration files are valid, but API connection failed")
            print_info("\nPossible reasons:")
            print_info("  - Using placeholder keys (replace with real Stripe keys)")
            print_info("  - Network connectivity issue")
            print_info("  - Invalid API key")
            print_info("\nNext steps:")
            print_info("  1. Get real Stripe keys from https://dashboard.stripe.com/apikeys")
            print_info("  2. Update .env files with real keys")
            print_info("  3. Run this test again")
    else:
        print_error("Configuration is incomplete!")
        print_info("\nTo fix:")
        print_info("  1. Run: ./setup_stripe.sh")
        print_info("  2. Or manually edit .env files")
        print_info("  3. Get Stripe keys from https://dashboard.stripe.com/apikeys")
        print_info("  4. Run this test again")
        sys.exit(1)

if __name__ == "__main__":
    main()
