# reCAPTCHA Configuration for Environments Without Internet Access

In servers or environments without internet access, Google reCAPTCHA cannot function correctly as it requires communication with Google's servers. This guide explains how to disable reCAPTCHA verification for such environments.

## Disabling reCAPTCHA

1. Create a `.env.local` file in your frontend directory (or edit it if it already exists)
2. Add the following environment variable:

```
# Disable reCAPTCHA verification
NEXT_PUBLIC_ENABLE_RECAPTCHA=false
```

3. Rebuild your Next.js application (or restart the development server if in development mode):

```bash
# For development
npm run dev

# For production build
npm run build
npm run start
```

## How It Works

When `NEXT_PUBLIC_ENABLE_RECAPTCHA` is set to `false`:

- The reCAPTCHA component will not be rendered on the login page
- The login form will not require reCAPTCHA verification to submit
- The login API calls will not include reCAPTCHA tokens

## Re-enabling reCAPTCHA

If your environment later gains internet access and you want to re-enable reCAPTCHA:

1. Edit your `.env.local` file:

```
# Enable reCAPTCHA
NEXT_PUBLIC_ENABLE_RECAPTCHA=true

# Provide a valid site key
NEXT_PUBLIC_RECAPTCHA_SITE_KEY=your_recaptcha_site_key_here
```

2. Rebuild or restart your application

## Sample .env.local File

Here's a complete example of an `.env.local` file:

```
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# reCAPTCHA Configuration
# Enable or disable reCAPTCHA verification (set to 'false' to disable)
NEXT_PUBLIC_ENABLE_RECAPTCHA=false

# Google reCAPTCHA Site Key
# Not needed if NEXT_PUBLIC_ENABLE_RECAPTCHA is set to 'false'
# NEXT_PUBLIC_RECAPTCHA_SITE_KEY=your_recaptcha_site_key_here
``` 