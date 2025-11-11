# Offline Deployment Setup Guide

This guide will help you set up the Next.js application for deployment in an offline environment where internet access is not available.

## Overview

The application has been configured to use local resources instead of external dependencies like Google Fonts and external images. However, you need to download and place the actual font files manually.

## Required Font Files

### 1. Inter Font Family

Download the Inter font family from: https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip

**Steps:**
1. Download the zip file from the link above
2. Extract the zip file
3. Navigate to the `web` folder in the extracted files
4. Copy the following WOFF2 files to `src/app/fonts/`:
   - `Inter-Regular.woff2`
   - `Inter-Medium.woff2`
   - `Inter-SemiBold.woff2`
   - `Inter-Bold.woff2`

### 2. Dancing Script Font

Download the Dancing Script font from: https://github.com/impallari/DancingScript/tree/master/fonts/webfonts

**Steps:**
1. Navigate to the GitHub repository above
2. Download the following WOFF file to `src/app/fonts/`:
   - `DancingScript-Regular-webfont.woff`

Alternatively, you can download from Google Fonts:
1. Go to https://fonts.google.com/specimen/Dancing+Script
2. Download the font family
3. Convert TTF files to WOFF format (if needed)
4. Place `DancingScript-Regular-webfont.woff` in `src/app/fonts/`

## Font File Locations

After downloading, your `src/app/fonts/` directory should contain:

```
src/app/fonts/
├── fonts.css                           # ✅ Already created
├── GeistVF.woff                        # ✅ Already exists
├── GeistMonoVF.woff                    # ✅ Already exists
├── Inter-Regular.woff2                 # ❌ Need to download
├── Inter-Medium.woff2                  # ❌ Need to download
├── Inter-SemiBold.woff2                # ❌ Need to download
├── Inter-Bold.woff2                    # ❌ Need to download
└── DancingScript-Regular-webfont.woff  # ❌ Need to download
```

## Changes Made for Offline Support

### 1. Layout.js Updates
- ✅ Removed Google Fonts import: `import { Inter } from 'next/font/google'`
- ✅ Removed Google Fonts CDN link from HTML head
- ✅ Added local font configuration using `localFont`
- ✅ Added import for local fonts CSS file

### 2. AboutTabContent.js Updates
- ✅ Removed inline Google Fonts @import for Dancing Script

### 3. Sidebar.js Updates
- ✅ Changed external logo URL to local file: `/ahana-logo.svg`

### 4. Next.js Configuration Updates
- ✅ Added `unoptimized: true` for images
- ✅ Disabled telemetry for offline environments

### 5. Local Assets
- ✅ Downloaded Ahana logo to `public/ahana-logo.svg`
- ✅ Created `src/app/fonts/fonts.css` with local font definitions

## Build Process

After placing all font files, you can build the application:

```bash
npm run build
```

The build should complete without any network timeouts or external resource errors.

## Deployment Steps

1. **Prepare the environment:**
   - Download all required font files as described above
   - Ensure all files are in the correct locations

2. **Build the application:**
   ```bash
   npm install
   npm run build
   ```

3. **Copy to server:**
   - Copy the entire project directory (including `node_modules`, `.next`, etc.)
   - Use SCP or any file transfer method available

4. **Run on server:**
   ```bash
   npm start
   ```

## Verification

To verify that all external dependencies have been removed, you can:

1. **Check for external URLs in the code:**
   ```bash
   grep -r "https://" src/ --exclude-dir=node_modules
   ```

2. **Monitor network requests during build:**
   - The build process should not make any external HTTP requests
   - No Google Fonts or external API calls should occur

## Troubleshooting

### Font Loading Issues
- Ensure font files are in the correct format (WOFF2 for Inter, WOFF for Dancing Script)
- Check that file names match exactly (case-sensitive)
- Verify that `fonts.css` is being imported in `layout.js`

### Build Timeouts
- If you still get timeout errors, check for any remaining external URLs
- Ensure all placeholder font files have been replaced with actual font files

### Missing Fonts Fallback
- The application will fall back to system fonts if custom fonts fail to load
- Check browser developer tools for font loading errors

## Additional Notes

- Inter font files should be in WOFF2 format for optimal performance
- Dancing Script font file should be in WOFF format: `DancingScript-Regular-webfont.woff`
- The application uses font-display: swap for better loading performance
- Local fonts are cached by the browser for subsequent visits
- The setup supports both light and dark themes without external dependencies 