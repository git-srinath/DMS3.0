# DMS Report Utility - User Guide

**Version:** 1.0  
**Date:** December 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Creating Reports](#creating-reports)
4. [Configuring Report Fields](#configuring-report-fields)
5. [Setting Up Report Layouts](#setting-up-report-layouts)
6. [Generating Reports](#generating-reports)
7. [Scheduling Reports](#scheduling-reports)
8. [Viewing Report History](#viewing-report-history)
9. [Output Formats](#output-formats)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## 1. Introduction

The DMS Report Utility is a powerful tool that allows you to create, manage, and generate business reports from your database. With this utility, you can:

- Create reports from SQL queries stored in the Manage SQL module or enter custom queries
- Configure which columns appear in your reports and how they're formatted
- Apply formulas to calculate derived values
- Generate reports in multiple formats (CSV, Excel, PDF, JSON, XML, Parquet)
- Schedule reports to run automatically
- Track execution history and download past reports

This guide will walk you through using the Report Utility to create and manage your reports effectively.

---

## 2. Getting Started

### Accessing the Report Utility

1. Log in to the DMS application
2. Navigate to the **Reports** module from the main navigation menu
3. You'll see a list of all available reports in your system

### Understanding the Interface

The Reports module consists of three main areas:

- **Reports List**: View and manage all report definitions
- **Report Configuration**: Create and edit report settings
- **Report Runs**: View execution history and download generated reports

---

## 3. Creating Reports

### Step 1: Basic Information

When creating a new report, start by providing basic information:

1. Click **"New Report"** or **"Create Report"** button
2. Enter a **Report Name** - Choose a descriptive name that clearly indicates the report's purpose (e.g., "Daily Sales Summary" or "Monthly Customer Activity")
3. Enter a **Description** - Provide context about what the report contains, who it's for, and any special considerations
4. Set the **Status** - Choose "Active" to make the report available for execution, or "Inactive" to temporarily disable it

### Step 2: Selecting a Data Source

You can create reports from two types of data sources:

#### Option A: Using Managed SQL Queries

1. Select **"Managed SQL Query"** as the data source type
2. Choose a query from the **Manage SQL** module dropdown
3. The system automatically retrieves the SQL query, database connection, and available columns
4. This approach is recommended for reports that use shared, standardized queries

**Benefits of Managed SQL:**
- Changes to the query automatically update all reports using it
- Ensures consistency across multiple reports
- Centralized query management

#### Option B: Using Ad-Hoc SQL Queries

1. Select **"Ad-Hoc SQL Query"** as the data source type
2. Enter your SQL query directly in the query editor
3. Select the **Database Connection** from the dropdown
4. The system validates your query syntax before saving

**When to Use Ad-Hoc SQL:**
- One-time reports
- Highly customized queries specific to a single report
- Quick exploratory reports

### Step 3: Database Connection

Select the database connection that contains the data you want to report on. The system will use this connection to execute your SQL query.

### Step 4: Preview Your Query

Before configuring fields, use the **Preview** button to:
- Verify your query returns the expected data
- See available columns
- Check data quality
- Validate query results

The preview shows a limited number of rows (typically 100) to help you validate your configuration quickly.

---

## 4. Configuring Report Fields

After selecting your data source, configure which columns appear in your report and how they're presented.

### Mapping Source Columns to Report Fields

1. The system automatically detects available columns from your SQL query
2. For each column you want in your report:
   - Select the **Source Column** from the dropdown
   - Enter a **Field Name** - Use user-friendly names (e.g., "Customer ID" instead of "CUST_ID")
   - Enter a **Field Description** - Explain what the field represents
   - Select the **Data Type** (text, number, date, boolean)

### Using Formulas

You can create calculated fields using formulas:

1. Select **"Use Formula"** for a field
2. Enter your formula expression, such as:
   - `quantity * unit_price` - Calculate total amount
   - `CONCAT(first_name, ' ', last_name)` - Combine text fields
   - `CASE WHEN status = 'A' THEN 'Active' ELSE 'Inactive' END` - Conditional logic

**Formula Tips:**
- Reference other fields by their source column names
- Use standard mathematical operators (+, -, *, /)
- Test formulas with sample data before saving
- Keep formulas simple for better performance

### Field Ordering

Arrange fields in the order you want them to appear in the report. Use the up/down arrows or drag-and-drop to reorder fields.

---

## 5. Setting Up Report Layouts

### Grouping Data

Organize your report data into logical groups:

1. Select fields to use for grouping
2. Set the **Group By** option for each grouping field
3. Reports will be organized hierarchically by your grouping fields

**Example:** Group a sales report by Region, then by Product Category

### Sorting Data

Control the order of rows in your report:

1. Select fields to sort by
2. Set the **Sort Order** (Ascending or Descending)
3. Set the **Sort Sequence** to determine priority when multiple sort fields are used

**Example:** Sort by Date (descending), then by Customer Name (ascending)

### Panel Types

Choose how fields are displayed:

- **Detail Panels**: Show individual transaction rows
- **Summary Panels**: Show aggregated data (totals, averages, counts)

You can combine both panel types in a single report to show both detailed and summary information.

---

## 6. Generating Reports

### Output Format Selection

Before generating a report, select your desired output format:

- **CSV**: Best for data exchange and importing into other systems
- **Excel (XLSX)**: Ideal for spreadsheet analysis and formatting
- **PDF**: Professional documents for distribution and printing
- **JSON**: Structured data for API integration
- **XML**: Structured data for enterprise systems
- **Parquet**: Optimized format for large datasets and analytics

You can configure a report to support multiple formats and choose the format when generating.

### Manual Execution

To generate a report immediately:

1. Navigate to the **Reports** list
2. Find the report you want to generate
3. Click **"Execute"** or **"Generate"**
4. Select your desired output format
5. Click **"Generate Report"**
6. The report will be generated and made available for download

### Preview Before Generating

Always use the **Preview** function before generating large reports:

1. Click **"Preview"** on any report
2. Review the sample data (limited rows)
3. Verify field mappings and formulas are working correctly
4. Check that data looks as expected
5. Generate the full report once satisfied

---

## 7. Scheduling Reports

Automate report generation by setting up schedules.

### Creating a Schedule

1. Open the report you want to schedule
2. Navigate to the **Scheduling** section
3. Click **"Add Schedule"**
4. Configure the following:

#### Frequency Options

- **Daily**: Report runs every day at a specified time
- **Weekly**: Report runs on specific days of the week (e.g., every Monday)
- **Monthly**: Report runs on specific days of the month (e.g., 1st of each month)
- **Half-Yearly**: Report runs twice per year
- **Yearly**: Report runs once per year
- **On-Demand**: Report only runs when manually triggered

#### Time Settings

- Set the **Time** when the report should execute (e.g., 10:30 AM)
- For weekly schedules, specify the day (e.g., MON_10:30 for Mondays at 10:30 AM)

#### Schedule Validity

- **Start Date**: When the schedule should begin
- **End Date**: When the schedule should stop (optional, for temporary schedules)

### Managing Schedules

- **Active**: Schedule is running and will execute reports automatically
- **Paused**: Schedule is temporarily disabled but configuration is preserved
- **Multiple Schedules**: You can create multiple schedules for the same report with different frequencies

### Delivery Options

Configure how scheduled reports are delivered:

#### Email Delivery

1. Enable **Email Delivery**
2. Enter recipient email addresses (multiple recipients supported)
3. Customize email subject and body
4. Reports will be attached to emails when generated

#### File System Delivery

1. Enable **File System Delivery**
2. Specify the file path or directory where reports should be saved
3. The system will create directories as needed
4. Useful for integration with document management systems or shared drives

#### Download Delivery

1. Reports are automatically available in the **Report Runs** interface
2. Recipients can download reports from the web interface
3. No additional configuration needed

---

## 8. Viewing Report History

### Report Runs Interface

The **Report Runs** interface provides a complete history of all report executions:

1. Navigate to **"Report Runs"** from the main menu
2. View a chronological list of all report executions
3. Each entry shows:
   - Report name
   - Execution timestamp
   - Status (Success, Failed, Running)
   - Number of rows generated
   - Output format
   - Delivery status

### Filtering and Searching

Use filters to find specific executions:

- Filter by **Report Name**
- Filter by **Status** (Success, Failed, Running)
- Filter by **Date Range**
- Filter by **Output Format**
- Search by keywords

### Viewing Execution Details

Click on any execution to see detailed information:

- Exact SQL query that was executed
- Parameters used (if any)
- Output files generated
- File locations
- Error messages (if execution failed)
- Execution duration

### Downloading Past Reports

1. Find the execution you want in the **Report Runs** list
2. Click **"Download"** next to the execution
3. Select the output format you want to download
4. The file will be downloaded to your computer

**Note:** Download availability depends on file retention policies. Contact your administrator if files are no longer available.

---

## 9. Output Formats

Understanding output formats helps you choose the right format for your needs.

### CSV Format

**Best for:**
- Data exchange between systems
- Importing into spreadsheet applications
- Simple data processing

**Characteristics:**
- Universal compatibility
- Plain text format
- No formatting or styling
- Small file sizes

### Excel Format (XLSX)

**Best for:**
- Spreadsheet analysis
- Manual data manipulation
- Sharing with business users
- Charts and pivot tables (when opened in Excel)

**Characteristics:**
- Preserves data types (numbers, dates)
- Professional appearance
- Compatible with Microsoft Excel and Google Sheets
- Supports formatting

### PDF Format

**Best for:**
- Document distribution
- Archiving and printing
- Professional presentations
- Compliance documentation

**Characteristics:**
- Professional formatting
- Page breaks for large reports
- Headers and footers
- Read-only format

### JSON Format

**Best for:**
- API integration
- Web application consumption
- Programmatic data processing
- Modern data exchange

**Characteristics:**
- Structured data format
- Includes metadata
- Machine-readable
- Lightweight

### XML Format

**Best for:**
- Enterprise system integration
- Legacy system compatibility
- Structured data exchange
- Data validation

**Characteristics:**
- Hierarchical structure
- Well-formed and validated
- Supports attributes and namespaces
- Standard format

### Parquet Format

**Best for:**
- Large datasets
- Analytics and data processing
- Data lake ingestion
- Big data platforms

**Characteristics:**
- Columnar storage (efficient)
- Compressed format
- Optimized for analytics
- Requires specialized tools to view

---

## 10. Best Practices

### Report Naming

- Use descriptive, meaningful names (e.g., "Daily Sales Summary" not "Report_001")
- Include frequency in names for scheduled reports (e.g., "Monthly Revenue Report")
- Avoid special characters
- Follow consistent naming conventions across your organization

### SQL Query Management

- Use **Managed SQL** queries for reports that share data sources
- This ensures consistency and makes updates easier
- Convert frequently used ad-hoc queries to managed SQL for better maintenance
- Optimize queries with appropriate WHERE clauses and filters

### Field Configuration

- Use user-friendly field names that business users will understand
- Provide clear descriptions for each field
- Test formulas thoroughly with sample data before production use
- Keep formulas simple for better performance

### Output Format Selection

- Choose formats based on how reports will be used:
  - **CSV** for data exchange
  - **Excel** for analysis
  - **PDF** for distribution
  - **JSON/XML** for integration
- Configure multiple formats if reports serve different purposes

### Scheduling

- Schedule reports during off-peak hours when possible
- Set appropriate frequencies that match business needs
- Use start and end dates for temporary schedules
- Monitor scheduled executions regularly

### Performance

- Use **Preview** before generating large reports
- Set appropriate preview row limits (default is 100 rows)
- For very large reports, consider using asynchronous execution
- Add filters to SQL queries to limit data when possible

---

## 11. Troubleshooting

### Report Execution Fails

**Check the execution history:**
1. Go to **Report Runs**
2. Find the failed execution
3. Review the error message
4. Common issues:
   - Database connection problems
   - SQL syntax errors
   - Missing tables or columns

**Solutions:**
- Verify database connection is active
- Check SQL query syntax for your database type
- Ensure all referenced tables and columns exist

### SQL Query Errors

**Symptoms:** Reports fail with SQL-related error messages

**Solutions:**
- Verify query syntax matches your database type (PostgreSQL, Oracle, etc.)
- Check for missing table aliases or incorrect JOIN syntax
- Ensure data types are compatible in operations
- Test the query directly in your database tool first

### Formula Errors

**Symptoms:** Formula fields show errors or incorrect values

**Solutions:**
- Verify formula syntax is correct
- Check that all referenced columns exist
- Ensure data types are compatible with formula operations
- Test formulas with sample data using Preview

### Output Generation Issues

**Symptoms:** Reports generate but output files are corrupted or missing

**Solutions:**
- For Excel: Ensure proper data type formatting
- For PDF: Check that report size fits within page boundaries
- For Parquet: Verify you have appropriate tools to view the format
- Contact your administrator if format-specific libraries are missing

### Email Delivery Failures

**Symptoms:** Scheduled reports don't arrive via email

**Solutions:**
- Verify email recipients are correct
- Check that SMTP settings are configured properly
- Review execution history for email delivery errors
- Contact your administrator to verify email server connectivity

### Performance Issues

**Symptoms:** Reports take too long to generate

**Solutions:**
- Use Preview to test with limited rows first
- Optimize SQL queries with appropriate filters
- Consider using asynchronous execution for large reports
- Simplify complex formulas
- Add date range or other filters to limit data

### Schedule Not Running

**Symptoms:** Scheduled reports don't execute automatically

**Solutions:**
- Verify schedule status is "Active"
- Check that current date is within start/end date range
- Verify next run date is calculated correctly
- Contact your administrator to check scheduler status

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the **Report Runs** history for detailed error messages
2. Review the execution details for specific error information
3. Contact your system administrator
4. Consult with your database administrator for SQL-related issues

---

**Document Version:** 1.0  
**Last Updated:** December 2025
