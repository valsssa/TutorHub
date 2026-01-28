#!/bin/bash

# =============================================================================
# Stripe Setup Script for EduStream TutorConnect
# =============================================================================
# This script helps you configure Stripe payment integration
# It validates your Stripe keys and sets up the environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}==================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}==================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running in project root
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_header "EduStream Stripe Configuration Setup"

# Check if .env files exist
if [ -f ".env" ]; then
    print_success "Found root .env file"
else
    print_warning "Root .env file not found (already created by automation)"
fi

if [ -f "backend/.env" ]; then
    print_success "Found backend/.env file"
else
    print_warning "Backend .env file not found (already created by automation)"
fi

# Function to validate Stripe key format
validate_stripe_key() {
    local key_type=$1
    local key_value=$2

    case $key_type in
        "secret")
            if [[ $key_value =~ ^sk_(test|live)_[A-Za-z0-9]{24,}$ ]]; then
                return 0
            fi
            ;;
        "publishable")
            if [[ $key_value =~ ^pk_(test|live)_[A-Za-z0-9]{24,}$ ]]; then
                return 0
            fi
            ;;
        "webhook")
            if [[ $key_value =~ ^whsec_[A-Za-z0-9]{32,}$ ]]; then
                return 0
            fi
            ;;
        "connect")
            if [[ $key_value =~ ^ca_[A-Za-z0-9]{24,}$ ]]; then
                return 0
            fi
            ;;
    esac
    return 1
}

# Check current Stripe configuration
print_header "Checking Current Stripe Configuration"

STRIPE_SECRET_KEY=$(grep "^STRIPE_SECRET_KEY=" .env 2>/dev/null | cut -d'=' -f2)
STRIPE_PUBLISHABLE_KEY=$(grep "^STRIPE_PUBLISHABLE_KEY=" .env 2>/dev/null | cut -d'=' -f2)
STRIPE_WEBHOOK_SECRET=$(grep "^STRIPE_WEBHOOK_SECRET=" .env 2>/dev/null | cut -d'=' -f2)
STRIPE_CONNECT_CLIENT_ID=$(grep "^STRIPE_CONNECT_CLIENT_ID=" .env 2>/dev/null | cut -d'=' -f2)

# Validate keys
KEYS_VALID=true

if validate_stripe_key "secret" "$STRIPE_SECRET_KEY"; then
    if [[ $STRIPE_SECRET_KEY == *"test"* ]]; then
        print_success "Secret Key: Valid (TEST MODE)"
    else
        print_success "Secret Key: Valid (LIVE MODE)"
    fi
else
    print_error "Secret Key: Invalid or placeholder"
    KEYS_VALID=false
fi

if validate_stripe_key "publishable" "$STRIPE_PUBLISHABLE_KEY"; then
    if [[ $STRIPE_PUBLISHABLE_KEY == *"test"* ]]; then
        print_success "Publishable Key: Valid (TEST MODE)"
    else
        print_success "Publishable Key: Valid (LIVE MODE)"
    fi
else
    print_error "Publishable Key: Invalid or placeholder"
    KEYS_VALID=false
fi

if validate_stripe_key "webhook" "$STRIPE_WEBHOOK_SECRET"; then
    print_success "Webhook Secret: Valid"
else
    print_error "Webhook Secret: Invalid or placeholder"
    KEYS_VALID=false
fi

if validate_stripe_key "connect" "$STRIPE_CONNECT_CLIENT_ID"; then
    print_success "Connect Client ID: Valid"
else
    print_warning "Connect Client ID: Invalid or placeholder (optional for basic payments)"
fi

# Summary
print_header "Configuration Status"

if [ "$KEYS_VALID" = true ]; then
    print_success "All required Stripe keys are configured!"
    print_info "You can now start accepting payments"
    echo ""
    print_info "Next steps:"
    echo "  1. Start your application: docker-compose up -d"
    echo "  2. Test a payment using Stripe test cards"
    echo "  3. Set up webhook endpoint in Stripe Dashboard"
    echo ""
    exit 0
else
    print_error "Stripe is NOT properly configured"
    echo ""
    print_info "To fix this, follow these steps:"
    echo ""
    echo "1. Get your Stripe API keys:"
    echo "   - Go to: https://dashboard.stripe.com/apikeys"
    echo "   - Copy your 'Secret key' (starts with sk_test_ or sk_live_)"
    echo "   - Copy your 'Publishable key' (starts with pk_test_ or pk_live_)"
    echo ""
    echo "2. Set up Stripe webhook:"
    echo "   - Go to: https://dashboard.stripe.com/webhooks"
    echo "   - Click 'Add endpoint'"
    echo "   - URL: https://api.valsa.solutions/api/payments/webhook"
    echo "   - Select events to listen to:"
    echo "     * checkout.session.completed"
    echo "     * payment_intent.succeeded"
    echo "     * payment_intent.payment_failed"
    echo "     * charge.refunded"
    echo "     * account.updated"
    echo "   - Copy the 'Signing secret' (starts with whsec_)"
    echo ""
    echo "3. (Optional) Set up Stripe Connect for tutor payouts:"
    echo "   - Go to: https://dashboard.stripe.com/settings/applications"
    echo "   - Get your Connect 'Client ID' (starts with ca_)"
    echo ""
    echo "4. Update your .env file with the real keys:"
    echo "   - Edit: .env (in project root)"
    echo "   - Replace placeholder values with real Stripe keys"
    echo ""
    echo "5. Run this script again to validate: ./setup_stripe.sh"
    echo ""

    # Interactive mode
    read -p "Would you like to configure Stripe keys now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_header "Interactive Stripe Configuration"

        # Get Secret Key
        echo -n "Enter your Stripe Secret Key (sk_test_... or sk_live_...): "
        read SECRET_KEY_INPUT

        # Get Publishable Key
        echo -n "Enter your Stripe Publishable Key (pk_test_... or pk_live_...): "
        read PUBLISHABLE_KEY_INPUT

        # Get Webhook Secret
        echo -n "Enter your Stripe Webhook Secret (whsec_...): "
        read WEBHOOK_SECRET_INPUT

        # Get Connect Client ID (optional)
        echo -n "Enter your Stripe Connect Client ID (ca_...) [optional, press Enter to skip]: "
        read CONNECT_CLIENT_ID_INPUT

        # Validate inputs
        print_info "Validating keys..."

        VALID=true
        if ! validate_stripe_key "secret" "$SECRET_KEY_INPUT"; then
            print_error "Invalid Secret Key format"
            VALID=false
        fi

        if ! validate_stripe_key "publishable" "$PUBLISHABLE_KEY_INPUT"; then
            print_error "Invalid Publishable Key format"
            VALID=false
        fi

        if ! validate_stripe_key "webhook" "$WEBHOOK_SECRET_INPUT"; then
            print_error "Invalid Webhook Secret format"
            VALID=false
        fi

        if [ "$VALID" = true ]; then
            # Update .env file
            print_info "Updating .env file..."

            sed -i "s|^STRIPE_SECRET_KEY=.*|STRIPE_SECRET_KEY=$SECRET_KEY_INPUT|" .env
            sed -i "s|^STRIPE_PUBLISHABLE_KEY=.*|STRIPE_PUBLISHABLE_KEY=$PUBLISHABLE_KEY_INPUT|" .env
            sed -i "s|^STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET_INPUT|" .env

            if [ -n "$CONNECT_CLIENT_ID_INPUT" ]; then
                sed -i "s|^STRIPE_CONNECT_CLIENT_ID=.*|STRIPE_CONNECT_CLIENT_ID=$CONNECT_CLIENT_ID_INPUT|" .env
            fi

            # Also update backend/.env
            if [ -f "backend/.env" ]; then
                sed -i "s|^STRIPE_SECRET_KEY=.*|STRIPE_SECRET_KEY=$SECRET_KEY_INPUT|" backend/.env
                sed -i "s|^STRIPE_PUBLISHABLE_KEY=.*|STRIPE_PUBLISHABLE_KEY=$PUBLISHABLE_KEY_INPUT|" backend/.env
                sed -i "s|^STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET_INPUT|" backend/.env

                if [ -n "$CONNECT_CLIENT_ID_INPUT" ]; then
                    sed -i "s|^STRIPE_CONNECT_CLIENT_ID=.*|STRIPE_CONNECT_CLIENT_ID=$CONNECT_CLIENT_ID_INPUT|" backend/.env
                fi
            fi

            print_success "Stripe configuration updated successfully!"
            print_info "You can now start your application with: docker-compose up -d"
        else
            print_error "Configuration failed due to invalid keys"
            exit 1
        fi
    else
        print_info "Configuration skipped. Please update .env manually."
        exit 1
    fi
fi
