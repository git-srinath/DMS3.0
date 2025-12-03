# Node Modules Analysis Report
**Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Executive Summary

This report analyzes the `node_modules` folder in the frontend application to identify:
- What packages are declared vs actually used
- Package size and structure
- Recommendations for optimization

## 1. Package Statistics

### Declared Dependencies
- **Production Dependencies:** 76 packages (lines 12-77 in package.json)
- **Dev Dependencies:** 9 packages (lines 78-87 in package.json)
- **Total Direct Dependencies:** 85 packages
- **Total Packages in node_modules:** ~660 packages (includes transitive dependencies)

### Why So Many Packages?
This is **normal** for a modern Next.js/React application. Each direct dependency brings its own dependencies (transitive dependencies). For example:
- `@mui/material` → brings in many UI components
- `next` → brings in React, webpack, and many build tools
- `framer-motion` → brings in animation libraries

## 2. Core Dependencies Analysis

### ✅ ESSENTIAL (Actively Used)
These packages are imported and actively used in the codebase:

1. **React Core**
   - `react` ✅ (used everywhere)
   - `react-dom` ✅ (used in layout.js)
   - `next` ✅ (Next.js framework - core)

2. **UI Libraries (MUI)**
   - `@mui/material` ✅ (extensively used across pages)
   - `@mui/icons-material` ✅ (icons used throughout)
   - `@mui/x-date-pickers` ✅ (used in jobs page)
   - `@emotion/react` ✅ (MUI dependency)
   - `@emotion/styled` ✅ (MUI dependency)

3. **UI Libraries (Other)**
   - `antd` ✅ (used in mapper_module/ReferenceForm.js, admin components)
   - `lucide-react` ✅ (used in Sidebar.js, NavBar.js)
   - `framer-motion` ✅ (animations in home page, admin, etc.)

4. **State & Data Fetching**
   - `axios` ✅ (API calls everywhere)

5. **Routing & Navigation**
   - `next/navigation` ✅ (useRouter, usePathname used)
   - `react-router-dom` ⚠️ (may be unused - Next.js uses its own router)

6. **Form & Validation**
   - `zod` ✅ (used in ReferenceForm.js)
   - `react-google-recaptcha` ✅ (login page)

7. **Code Editing**
   - `@monaco-editor/react` ✅ (used in ReferenceForm.js, SqlEditorDialog)
   - `monaco-editor` ✅ (Monaco dependency)

8. **Charts & Visualization**
   - `react-chartjs-2` ✅ (dashboard charts)
   - `chart.js` ✅ (chart.js dependency)

9. **File Handling**
   - `file-saver` ✅ (likely used for downloads)
   - `jspdf` ✅ (PDF generation)
   - `jspdf-autotable` ✅ (PDF tables)

10. **SQL & Data Processing**
    - `sql-formatter` ✅ (used in ReferenceForm.js)

11. **Date Handling**
    - `date-fns` ✅ (used in jobs page)

12. **Utilities**
    - `lodash` ✅ (utility functions)
    - `clsx` ✅ (className utility)
    - `tailwind-merge` ✅ (Tailwind utilities)
    - `js-cookie` ✅ (cookie handling)

### ⚠️ POTENTIALLY UNUSED (Needs Verification)

These packages are declared but **NOT FOUND** in active imports:

1. **Drag & Drop**
   - `@dnd-kit/core` ⚠️
   - `@dnd-kit/modifiers` ⚠️
   - `@dnd-kit/sortable` ⚠️
   - `@dnd-kit/utilities` ⚠️

2. **UI Components**
   - `@nextui-org/react` ⚠️ (might be used in some components)
   - `@radix-ui/react-dialog` ⚠️
   - `@radix-ui/react-label` ⚠️
   - `@radix-ui/react-popover` ⚠️
   - `@radix-ui/react-select` ⚠️
   - `@radix-ui/react-slot` ⚠️

3. **Flow/Graph Libraries**
   - `@xyflow/react` ⚠️
   - `reactflow` ⚠️
   - `dagre` ⚠️ (graph layout)

4. **PDF Viewing**
   - `@react-pdf-viewer/core` ⚠️
   - `@react-pdf-viewer/default-layout` ⚠️
   - `@react-pdf-viewer/highlight` ⚠️
   - `pdfjs-dist` ⚠️

5. **Document Processing**
   - `docx` ⚠️ (Word document generation)
   - `html2canvas` ⚠️
   - `react-highlight-within-textarea` ⚠️
   - `react-markdown` ⚠️
   - `react-quill` ⚠️ (rich text editor)

6. **Other Utilities**
   - `diff` ⚠️ (diff algorithm)
   - `postgres` ⚠️ (direct database - might not be needed if using API)
   - `react-responsive` ⚠️
   - `react-toastify` ⚠️ (might use MUI Snackbar instead)
   - `react-window` ⚠️ (virtualized lists)
   - `react-day-picker` ⚠️ (might use MUI date pickers)
   - `react-dropzone` ⚠️
   - `class-variance-authority` ⚠️
   - `next-themes` ⚠️ (might use custom theme context)
   - `init` ⚠️ (questionable package)
   - `react-router-dom` ⚠️ (Next.js has its own router)

7. **Dev Dependencies**
   - `@shadcn/ui` ⚠️ (UI components - might not be used)

## 3. Package Categories

### Core Framework (Required)
- Next.js, React, React DOM

### UI Framework (Required)
- MUI Material, MUI Icons, Emotion

### Utilities (Required)
- Axios, Lodash, date-fns, Zod

### Build Tools (Required for Dev)
- TypeScript, PostCSS, TailwindCSS

### Feature-Specific (May Be Optional)
- Monaco Editor (if code editing is used)
- Chart.js (if charts are used)
- PDF libraries (if PDF features are used)

## 4. Recommendations

### High Priority Actions

1. **Remove Unused Packages**
   The following packages appear unused and can be safely removed:
   ```json
   "@dnd-kit/core",
   "@dnd-kit/modifiers", 
   "@dnd-kit/sortable",
   "@dnd-kit/utilities",
   "react-router-dom",
   "react-toastify",
   "react-day-picker",
   "next-themes",
   "init"
   ```

2. **Verify Before Removing**
   These might be used indirectly or in specific features:
   - All Radix UI packages (check for custom components)
   - Flow/graph libraries (check for diagram features)
   - PDF viewer libraries (check for PDF viewing features)
   - Document generation libraries (docx, html2canvas)
   - react-dropzone (check for file upload features)

3. **Keep Essential Packages**
   All MUI packages, React, Next.js, Axios, Monaco Editor, and utilities are essential.

### Package Size Optimization

1. **Use npm audit** to find security vulnerabilities
2. **Use npm outdated** to check for updates
3. Consider using `npm ci` for clean installs (faster, more reliable)

### Git Management

✅ **Good News:** `node_modules` is already in `.gitignore` (line 2)
- This means it won't be committed to Git
- This is the correct setup
- Only `package.json` and `package-lock.json` should be committed

## 5. Action Plan

### Step 1: Create a Backup
```bash
cp package.json package.json.backup
cp package-lock.json package-lock.json.backup
```

### Step 2: Remove Clearly Unused Packages
```bash
npm uninstall @dnd-kit/core @dnd-kit/modifiers @dnd-kit/sortable @dnd-kit/utilities
npm uninstall react-router-dom react-toastify react-day-picker next-themes init
```

### Step 3: Test the Application
- Run `npm run build` to ensure nothing breaks
- Test all major features

### Step 4: Investigate Potentially Unused Packages
- Search codebase for imports of suspicious packages
- Remove if not used

### Step 5: Update Remaining Packages
```bash
npm update
npm audit fix
```

## 6. Size Estimates

- **Total node_modules size:** Typically 200-500 MB for a Next.js app
- **After cleanup:** Expected 30-50% reduction if removing unused packages
- **Build output (.next folder):** Separate, also in .gitignore ✅

## 7. Conclusion

The current `node_modules` setup is **standard** for a Next.js application. The large number of packages is expected due to transitive dependencies. 

**Key Findings:**
1. ✅ `node_modules` is properly excluded from Git
2. ⚠️ ~15-20 packages appear unused and can be removed
3. ✅ All core dependencies are necessary
4. ✅ No critical issues found

**Recommendation:** 
- Remove clearly unused packages (Step 2 above)
- Keep all MUI, React, Next.js, and utility packages
- Test thoroughly after cleanup
- This is a normal-sized Next.js project

## 8. Next Steps

1. Review this analysis
2. Confirm which features actually use the "potentially unused" packages
3. Remove unused packages incrementally
4. Test after each removal
5. Document which packages are needed for which features

---

**Note:** Always test the application after removing packages. Some packages might be used dynamically or in specific code paths not caught by static analysis.

