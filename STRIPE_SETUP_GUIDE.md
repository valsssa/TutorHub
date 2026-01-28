# 🚀 Stripe Setup Guide for EduStream TutorConnect

This guide will help you configure Stripe payments for your tutoring marketplace.

## ✅ What's Already Done

The automated setup has created:

1. ✅ **`.env`** file in project root with Stripe placeholders
2. ✅ **`backend/.env`** file with full configuration
3. ✅ **Updated `docker-compose.yml`** to pass Stripe environment variables
4. ✅ **Setup script** (`setup_stripe.sh`) for validation

## 📋 What You Need to Do

### Step 1: Get Your Stripe API Keys

1. **Sign up for Stripe** (if you haven't already):
   - Go to: https://dashboard.stripe.com/register
   - Complete registration

2. **Get your API keys**:
   - Go to: https://dashboard.stripe.com/apikeys
   - You'll see two keys:
     - **Publishable key** - Starts with `pk_test_...` (for frontend)
     - **Secret key** - Click "Reveal test key" - Starts with `sk_test_...` (for backend)
   - Copy both keys

### Step 2: Set Up Stripe Webhook

1. **Create webhook endpoint**:
   - Go to: https://dashboard.stripe.com/webhooks
   - Click **"Add endpoint"**
   - Enter your endpoint URL: `https://api.valsa.solutions/api/payments/webhook`

2. **Select events to listen to**:
   - Click "Select events"
   - Choose these events:
     - ✅ `checkout.session.completed`
     - ✅ `payment_intent.succeeded`
     - ✅ `payment_intent.payment_failed`
     - ✅ `charge.refunded`
     - ✅ `account.updated` (for Stripe Connect)

3. **Get webhook signing secret**:
   - After creating the endpoint, click on it
   - Click "Reveal" in the "Signing secret" section
   - Copy the secret (starts with `whsec_...`)

### Step 3: (Optional) Set Up Stripe Connect for Tutor Payouts

If you want tutors to receive automatic payouts:

1. **Enable Stripe Connect**:
   - Go to: https://dashboard.stripe.com/settings/connect
   - Enable Connect if not already enabled

2. **Get Connect Client ID**:
   - Go to: https://dashboard.stripe.com/settings/applications
   - Copy your "Client ID" (starts with `ca_...`)

### Step 4: Configure Your Keys

**Option A: Use the automated setup script**

```bash
cd /mnt/c/Users/valsa/Documents/Project1-splitversion
./setup_stripe.sh
```

The script will:
- Validate your current configuration
- Interactively ask for your Stripe keys
- Update both `.env` files automatically
- Verify the key formats

**Option B: Manual configuration**

1. Edit `.env` in project root:
```bash
nano .env
```

2. Replace these lines with your actual keys:
```bash
STRIPE_SECRET_KEY=sk_test_YourActualSecretKeyHere
STRIPE_PUBLISHABLE_KEY=pk_test_YourActualPublishableKeyHere
STRIPE_WEBHOOK_SECRET=whsec_YourActualWebhookSecretHere
STRIPE_CONNECT_CLIENT_ID=ca_YourActualConnectClientIdHere  # Optional
```

3. Save and exit (Ctrl+X, then Y, then Enter)

4. Also update `backend/.env` with the same values

### Step 5: Start Your Application

```bash
# Start all services
docker-compose up -d

# Check if backend started successfully
docker-compose logs backend | grep -i stripe

# You should see: "Stripe configuration loaded successfully"
```

### Step 6: Test Payments

Use Stripe test cards to test payments:

**Successful payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

**Failed payment:**
- Card: `4000 0000 0000 0002`

**3D Secure authentication required:**
- Card: `4000 0025 0000 3155`

More test cards: https://stripe.com/docs/testing

## 🔍 Verify Your Setup

Run the validation script:

```bash
./setup_stripe.sh
```

You should see:
```
✓ Secret Key: Valid (TEST MODE)
✓ Publishable Key: Valid (TEST MODE)
✓ Webhook Secret: Valid
✓ Connect Client ID: Valid
```

## 🎯 Payment Flow

Here's what happens when a student pays:

1. **Student clicks "Pay" on a booking**
   - API endpoint: `POST /api/payments/checkout`
   - Creates Stripe Checkout session
   - Student redirected to Stripe payment page

2. **Student enters card details on Stripe**
   - Stripe processes payment securely
   - No card data touches your server

3. **Payment successful**
   - Stripe sends webhook to: `https://api.valsa.solutions/api/payments/webhook`
   - Backend updates booking status to "CONFIRMED"
   - Payment record created in database

4. **Tutor payout (if Stripe Connect enabled)**
   - Funds automatically transferred to tutor's Stripe account
   - Platform fee deducted (configurable 3-20%)
   - Weekly automatic payouts on Fridays

## 🔐 Security Checklist

- ✅ Never commit `.env` files to git (already in `.gitignore`)
- ✅ Use test keys for development (`sk_test_...`)
- ✅ Use live keys for production (`sk_live_...`)
- ✅ Keep webhook secret secure
- ✅ Verify webhook signatures (already implemented)
- ✅ Use HTTPS for webhook endpoint (required)

## 📊 Monitoring Payments

**Stripe Dashboard:**
- View all payments: https://dashboard.stripe.com/payments
- View webhooks: https://dashboard.stripe.com/webhooks
- View logs: https://dashboard.stripe.com/logs

**Application Logs:**
```bash
# View payment logs
docker-compose logs -f backend | grep payment

# View Stripe API logs
docker-compose logs -f backend | grep stripe
```

## 🐛 Troubleshooting

### Error: "Payment service not configured"

**Cause:** Stripe keys not set or invalid

**Solution:**
```bash
# Check if keys are loaded
docker-compose exec backend env | grep STRIPE

# Restart backend after updating .env
docker-compose restart backend
```

### Error: "Invalid webhook signature"

**Cause:** Webhook secret mismatch

**Solution:**
1. Get fresh webhook secret from Stripe Dashboard
2. Update `STRIPE_WEBHOOK_SECRET` in `.env`
3. Restart: `docker-compose restart backend`

### Error: "Stripe API error"

**Cause:** Invalid API key or network issue

**Solution:**
1. Verify key format (should start with `sk_test_` or `sk_live_`)
2. Check Stripe Dashboard for API status
3. Check application logs: `docker-compose logs backend`

### Webhook not receiving events

**Cause:** Endpoint URL incorrect or not accessible

**Solution:**
1. Verify URL in Stripe Dashboard: `https://api.valsa.solutions/api/payments/webhook`
2. Test webhook: Click "Send test webhook" in Stripe Dashboard
3. Check if API is accessible from internet
4. Check logs: `docker-compose logs backend | grep webhook`

## 🎓 Additional Resources

- **Stripe Documentation**: https://stripe.com/docs
- **Stripe Testing**: https://stripe.com/docs/testing
- **Stripe Connect**: https://stripe.com/docs/connect
- **Webhook Testing**: https://stripe.com/docs/webhooks/test

## 🔄 Going Live (Production)

When ready for production:

1. **Get live API keys**:
   - Switch to live mode in Stripe Dashboard
   - Copy live keys (start with `sk_live_` and `pk_live_`)

2. **Update environment**:
   - Change `ENVIRONMENT=production` in `.env`
   - Replace test keys with live keys
   - Verify webhook endpoint is using HTTPS

3. **Business verification**:
   - Complete Stripe account verification
   - Provide business information
   - Enable Stripe Connect (if using tutor payouts)

4. **Test thoroughly**:
   - Use real card with small amount ($0.50)
   - Verify webhook delivery
   - Test refunds

5. **Monitor**:
   - Set up Stripe alerts
   - Monitor payment logs
   - Track failed payments

---

**Need help?** Check the logs or contact support.

**Ready to go?** Run `./setup_stripe.sh` to get started!
