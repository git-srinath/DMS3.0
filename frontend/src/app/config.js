// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Environment detection
const isDevelopment = process.env.NODE_ENV === 'development' || typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

// Google reCAPTCHA Configuration
// Get a valid site key from https://www.google.com/recaptcha/admin
// You need different keys for development (localhost) and production environments

// reCAPTCHA enable/disable toggle
export const ENABLE_RECAPTCHA = process.env.NEXT_PUBLIC_ENABLE_RECAPTCHA !== 'false';

export const RECAPTCHA_SITE_KEY = ENABLE_RECAPTCHA ? 
  (process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || 
    (isDevelopment ? 
      '6LeYxSUrAAAAAC2sL67J13HUEDP4SKzu5FADsHO-' : // Test key that always passes verification (for development only)
      '6LeYxSUrAAAAAC2sL67J13HUEDP4SKzu5FADsHO-'  // Your production key
    )
  ) : null; 