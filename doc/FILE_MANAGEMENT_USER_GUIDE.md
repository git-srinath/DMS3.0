# DMS File Management Utility - User Guide 📁

**Status:** ✅ Production Ready  
**Date:** November 2025  
**Version:** 1.0

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [What Can This Utility Do?](#what-can-this-utility-do)
3. [Supported File Formats](#supported-file-formats)
4. [Getting Started](#getting-started)
5. [How to Use the Utility](#how-to-use-the-utility)
6. [Key Features Explained](#key-features-explained)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 1. Introduction

The **DMS File Management Utility** is a powerful tool that allows you to upload data files and import them into your database tables. Whether you receive daily CSV reports, monthly Excel spreadsheets, or JSON data from external systems, this utility makes it easy to configure and automate your data imports.

---

## 2. What Can This Utility Do?

### Core Capabilities

- **Upload Multiple File Formats**: Support for CSV, Excel, JSON, Parquet, XML, PDF, and Google Sheets
- **Automatic File Detection**: The system automatically recognizes file types and parses them correctly
- **Data Preview**: See a preview of your data before importing to verify everything looks correct
- **Flexible Column Mapping**: Map source columns from your file to target columns in database tables
- **Data Transformations**: Calculate derived values, combine columns, and apply business logic using Python expressions
- **Automatic Table Creation**: The system can create target tables automatically based on your column mappings
- **Three Loading Modes**:
  - **INSERT**: Add new rows to existing tables
  - **TRUNCATE_LOAD**: Clear the table and load fresh data
  - **UPSERT**: Update existing rows or insert new ones based on primary keys
- **Scheduled Processing**: Automate regular imports (daily, weekly, monthly, etc.)
- **Error Handling**: Continue processing even when some rows have errors, with detailed error reporting
- **Complete Audit Trail**: Track who uploaded what, when, and the results of each execution

### Common Use Cases

- **Daily Data Imports**: Automate daily imports from partner systems or external data sources
- **Batch Processing**: Process large historical data files for migrations or bulk updates
- **Regular Data Refreshes**: Keep dimension tables up-to-date with scheduled refreshes
- **Ad-Hoc Uploads**: Import one-time data corrections or urgent updates
- **Data Migration**: Import data from legacy systems in various file formats

---

## 3. Supported File Formats

The utility supports the following file formats:

| Format | Extensions | Key Features |
|--------|-----------|--------------|
| **CSV** | `.csv`, `.tsv`, `.txt` | Automatic delimiter detection, handles quotes and encoding |
| **Excel** | `.xlsx`, `.xls` | Multi-sheet support, preserves data types |
| **JSON** | `.json` | Handles nested structures, array processing |
| **Parquet** | `.parquet`, `.parq` | Efficient for large files, automatic schema detection |
| **XML** | `.xml` | XPath support, nested structure handling |
| **PDF** | `.pdf` | Table extraction from PDF documents |
| **Google Sheets** | `.gsheet` | Direct integration with Google Sheets |

---

## 4. Getting Started

### Accessing the Utility

1. Navigate to the DMS home page
2. Find the **"File Management"** section
3. Click on the **"File Upload"** card to access the utility

### Prerequisites

- Access to the DMS File Management module
- A target database connection configured in DMS
- Files ready for upload in a supported format

---

## 5. How to Use the Utility

### Step 1: Upload a File

1. Click **"New Upload"** or **"Upload File"** button
2. Select a file using one of these methods:
   - **Browse**: Click to open file browser and select your file
   - **Drag and Drop**: Drag a file directly into the upload area
3. The system will automatically:
   - Validate the file
   - Detect the file type
   - Parse the file structure
   - Generate a preview

### Step 2: Review the Preview

After upload, you'll see a preview showing:
- **Column names** detected from your file
- **Sample data** (first 10-200 rows, configurable)
- **File metadata** (size, type, encoding)

**What to check:**
- ✓ Column names are correct
- ✓ Data looks properly formatted
- ✓ No obvious parsing errors
- ✓ Special characters display correctly

### Step 3: Configure Basic Settings

Provide the following information:

**File Information:**
- **File Reference**: A unique identifier (e.g., "CUSTOMER_DAILY_IMPORT")
- **Description**: A clear description of what this upload does
- **File Name**: Automatically populated, but can be edited

**Target Configuration:**
- **Target Connection**: Select the database where data should be loaded
- **Target Schema**: The database schema/namespace
- **Target Table**: The table name where data will be loaded
- **Truncate Flag**: Choose whether to clear the table before loading

**File Options:**
- **Header Rows**: Number of rows to skip at the beginning (if file has metadata)
- **Footer Rows**: Number of rows to skip at the end (if file has summaries)
- **Batch Size**: Number of rows processed per transaction (default: 1000)

### Step 4: Map Columns

For each column you want to import:

1. **Select Source Column**: Choose the column from your file
2. **Specify Target Column**: Enter the target column name in the database
3. **Set Data Type**: Choose the appropriate data type (VARCHAR, INTEGER, DATE, etc.)
4. **Configure Options**:
   - **Primary Key**: Mark if this column is part of the primary key
   - **Required**: Mark if this column must have a value
   - **Default Value**: Specify a default if source data might be missing
   - **Derivation Logic**: Write Python expressions to calculate values

**Example Derivation Logic:**
- Combine columns: `first_name + ' ' + last_name`
- Calculate totals: `quantity * unit_price`
- Conditional logic: `'Premium' if amount > 1000 else 'Standard'`

### Step 5: Save Configuration

1. Review all settings
2. Click **"Save"** to store your configuration
3. The system validates your configuration before saving
4. Once saved, your configuration is ready for execution

### Step 6: Execute or Schedule

**Manual Execution:**
- Click **"Execute"** to run the import immediately
- Monitor progress in real-time
- Review results when complete

**Scheduled Execution:**
1. Configure schedule settings:
   - **Frequency**: Daily, Weekly, Monthly, Half-Yearly, Yearly, or On-Demand
   - **Time**: Specify when the import should run (e.g., "10:30 AM")
   - **Start/End Dates**: Optional validity period
2. The system automatically calculates next run times
3. Scheduled imports run automatically without manual intervention

### Step 7: Monitor Results

After execution, review:

**Execution Summary:**
- Total rows processed
- Rows successfully loaded
- Rows that failed
- Execution status (SUCCESS, FAILED, or PARTIAL)
- Processing duration

**Error Details** (if any):
- View failed rows
- See error codes and messages
- Download error data for analysis
- Filter by error type

**Execution History:**
- View all past executions for this configuration
- Track trends over time
- Identify patterns in failures

---

## 6. Key Features Explained

### Column Mapping

**Direct Mapping**: Map a source column directly to a target column with the same name and data type.

**Transformation Mapping**: Use derivation logic to calculate target values:
- Combine multiple source columns
- Apply mathematical operations
- Use conditional logic
- Call built-in functions

**Default Values**: Specify values to use when source data is missing or null.

### Execution Modes

**INSERT Mode**:
- Adds new rows to the table
- Preserves existing data
- Use for: Incremental data loads, transaction logs

**TRUNCATE_LOAD Mode**:
- Clears the table completely
- Loads fresh data from file
- Use for: Dimension table refreshes, complete data replacements

**UPSERT Mode**:
- Updates existing rows (if primary key matches)
- Inserts new rows (if primary key doesn't exist)
- Use for: Incremental updates, maintaining current state

### Scheduling Options

**Frequency Codes:**
- `DL` - Daily
- `WK` - Weekly (specify day of week)
- `MN` - Monthly (specify day of month)
- `HY` - Half-Yearly
- `YR` - Yearly
- `ID` - On-Demand (manual only)

**Time Parameters:**
- Format: `HH:MM` (24-hour) or `DAY_HH:MM`
- Examples: `10:30`, `MON_10:30`, `01_15:00` (1st of month at 3 PM)

### Error Handling

The system continues processing even when individual rows have errors:
- **Row-Level Errors**: Failed rows are logged but don't stop processing
- **Error Codes**: Standardized codes help identify error types
- **Error Messages**: Detailed explanations of what went wrong
- **Failed Row Data**: Complete row data preserved for analysis

---

## 7. Best Practices

### File Naming

- Use descriptive file references (e.g., "CUSTOMER_DAILY_IMPORT" not "UPLOAD_001")
- Include date/time information for scheduled uploads
- Avoid special characters; use alphanumeric and underscores only
- Follow consistent naming conventions across your organization

### Column Mapping

- **Map all required columns**: Missing required columns cause errors
- **Verify primary keys**: Incorrect primary key definitions cause duplicate errors
- **Test derivation logic**: Test with sample data before production use
- **Choose appropriate data types**: Match data types to actual data

### Performance

- **Optimize batch sizes**: Default 1000 works for most cases; adjust based on row size
- **Keep transformations simple**: Complex logic slows processing
- **Monitor execution times**: Identify slow imports for optimization
- **Schedule during off-peak hours**: Reduce impact on system performance

### Error Management

- **Review error logs regularly**: Identify patterns in data quality issues
- **Fix issues at source**: Address root causes rather than repeatedly handling errors
- **Use appropriate load modes**: Choose INSERT, TRUNCATE_LOAD, or UPSERT based on needs
- **Test with sample data**: Catch configuration issues before full production runs

### Scheduling

- **Set appropriate frequencies**: Match business requirements (daily, weekly, monthly)
- **Use time parameters wisely**: Schedule during off-peak hours
- **Monitor scheduled executions**: Check for late or missing source files
- **Set end dates**: Prevent temporary schedules from running indefinitely

---

## 8. Troubleshooting

### File Upload Issues

**Problem**: File upload fails  
**Solutions**:
- Check file size is within limits
- Verify file format is supported
- Ensure file isn't corrupted
- Try converting file encoding to UTF-8

**Problem**: File preview shows incorrect data  
**Solutions**:
- Check delimiter settings for CSV files
- Verify sheet name for Excel files
- Adjust header/footer row counts
- Check for merged cells or formatting issues

### Column Mapping Issues

**Problem**: Data type errors during execution  
**Solutions**:
- Verify data types match actual data
- Check for text in numeric columns
- Review date format compatibility
- Ensure derivation logic returns correct types

**Problem**: Missing value errors  
**Solutions**:
- Map all required columns
- Set default values for optional columns
- Check source file for missing data
- Verify required field settings

### Execution Issues

**Problem**: Execution fails completely  
**Solutions**:
- Verify target database connection is active
- Check database user permissions
- Ensure target table exists (or allow auto-creation)
- Review error messages for specific issues

**Problem**: Some rows fail but others succeed  
**Solutions**:
- Review error logs for failed rows
- Check for data quality issues in source file
- Verify primary key constraints aren't violated
- Ensure required fields have values

### Performance Issues

**Problem**: Execution is very slow  
**Solutions**:
- Reduce batch size for very wide tables
- Simplify complex transformation logic
- Check database performance (indexes, locks)
- Consider splitting very large files

**Problem**: Memory errors with large files  
**Solutions**:
- Reduce batch size
- Process files in smaller chunks
- Check available system resources
- Contact administrator for system limits

---

## Quick Reference

### Execution Statuses

- **SUCCESS**: All rows processed successfully
- **FAILED**: Critical error prevented completion
- **PARTIAL**: Some rows succeeded, some failed

### Load Modes

- **INSERT**: Add new rows only
- **TRUNCATE_LOAD**: Clear table and load fresh data
- **UPSERT**: Update existing or insert new rows

### Schedule Frequencies

- **DL**: Daily
- **WK**: Weekly
- **MN**: Monthly
- **HY**: Half-Yearly
- **YR**: Yearly
- **ID**: On-Demand

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Production Ready ✅
