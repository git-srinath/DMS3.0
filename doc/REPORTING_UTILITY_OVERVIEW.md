# DMS Reporting Utility - Overview Document 📊

**Status:** ✅ Production Ready  
**Date:** December 2025  
**Version:** 1.0

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Overview & Purpose](#overview--purpose)
3. [Core Components](#core-components)
4. [Report Definition & Configuration](#report-definition--configuration)
5. [Supported Output Formats](#supported-output-formats)
6. [Key Features](#key-features)
7. [Architecture](#architecture)
8. [Workflow](#workflow)
9. [Database Schema](#database-schema)
10. [API Endpoints](#api-endpoints)
11. [Security & Validation](#security--validation)
12. [Integration with DMS](#integration-with-dms)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)
15. [Future Enhancements](#future-enhancements)
16. [Conclusion](#conclusion)

---

## 1. Introduction

The **DMS Reporting Utility** is a comprehensive report generation and management system integrated into the DMS (Data Management System) application. It enables users to define reusable report definitions based on SQL queries, configure field layouts and formatting, apply formulas and transformations, and generate reports in multiple output formats with scheduling capabilities and complete execution history tracking.

---

## 2. Overview & Purpose

The DMS Reporting Utility serves as a centralized solution for creating, managing, and executing business reports from data stored across various database systems. Unlike traditional reporting tools that require separate installations and complex configurations, this utility is fully integrated into the DMS platform, leveraging existing database connections, SQL query management, and scheduling infrastructure.

The system provides a flexible report definition framework that allows users to create reports from two primary data sources: managed SQL queries stored in the DMS Manage SQL module, or ad-hoc SQL queries entered directly during report creation. This dual approach accommodates both standardized, reusable queries and one-time reporting needs, providing maximum flexibility for different use cases.

One of the utility's most powerful features is its field-based report configuration system, which allows users to define exactly which columns should appear in reports, how they should be formatted, and how they should be ordered. Users can map source columns from SQL queries to report fields with custom names and descriptions, apply formulas to compute derived values, configure grouping and sorting, and specify output formatting preferences.

The system supports multiple output formats including CSV for data exchange, Excel for spreadsheet analysis, PDF for document distribution, JSON for API integration, XML for structured data exchange, and Parquet for big data processing. Each report can be configured to support one or more output formats, allowing the same report definition to serve different consumption needs.

For organizations with regular reporting requirements, the utility offers sophisticated scheduling capabilities. Users can configure automated report generation to run daily, weekly, monthly, or on custom schedules, with the system automatically calculating next run times and managing execution queues. Reports can be delivered via email to specified recipients, saved to file system locations, or made available for download through the web interface.

Execution history is comprehensively tracked, creating a complete audit trail that includes execution timestamps, row counts, output file locations, delivery status, and any error messages. This history enables users to track report usage patterns, verify that scheduled reports executed successfully, and troubleshoot issues when they occur.

### Use Cases

The Reporting Utility addresses a wide range of business reporting scenarios that organizations encounter in their daily operations. One common use case is operational reporting, where business users need regular access to current operational data such as daily sales summaries, inventory levels, customer activity, or transaction volumes. The utility's scheduling capabilities make it ideal for these scenarios, automatically generating and distributing reports at specified intervals.

Executive reporting represents another primary use case, where management requires high-level summaries and dashboards that aggregate data from multiple sources. The utility's formula capabilities allow complex calculations and aggregations to be embedded directly in report definitions, enabling sophisticated analytical reports without requiring separate business intelligence tools.

Compliance and regulatory reporting is a critical use case for many organizations, where reports must be generated on specific schedules, delivered to specific recipients, and maintained in audit trails. The utility's comprehensive execution history and delivery tracking provide the documentation needed for compliance requirements.

Data export and integration scenarios are also well-supported, where reports serve as data exchange mechanisms between systems. The multiple output format support ensures that reports can be consumed by downstream systems regardless of their preferred data format, whether that's CSV for ETL processes, JSON for API integration, or Parquet for data lake ingestion.

Ad-hoc reporting provides users with the flexibility to generate one-time reports on demand when immediate data access is required, such as investigating specific business questions or responding to ad-hoc data requests. The preview functionality allows users to validate report results before committing to full execution, ensuring data accuracy and reducing unnecessary processing.

Finally, scheduled distribution scenarios enable organizations to automate the delivery of regular reports to stakeholders, eliminating manual report generation tasks and ensuring consistent, timely information delivery. Email delivery capabilities allow reports to be automatically sent to distribution lists, while file system delivery enables integration with document management systems or shared network drives.

---

## 3. Core Components

The Reporting Utility is built upon a modular architecture consisting of five core components, each responsible for a specific aspect of the report generation pipeline. These components work together seamlessly to provide a complete solution from report definition through execution and delivery.

### 3.1 Report Metadata Service

**Location:** `backend/modules/reports/report_service.py`

The Report Metadata Service serves as the central repository for all report definitions and execution history. It provides comprehensive CRUD (Create, Read, Update, Delete) operations that manage the lifecycle of report definitions, including field configurations, formula definitions, layout specifications, and scheduling information.

The service maintains relationships between report definitions and their associated components—fields, formulas, layouts, and schedules—ensuring data consistency and referential integrity. It implements intelligent SQL resolution, automatically extracting SQL text from managed SQL queries when reports reference the Manage SQL module, or using ad-hoc SQL when provided directly.

When reports are created or updated, the service performs comprehensive validation, checking that SQL queries are syntactically correct, that field mappings reference valid source columns, that formulas are properly structured, and that output format configurations are valid. It also computes checksums of report definitions to detect changes and prevent accidental overwrites when multiple users are working with the same report.

The service provides preview functionality that executes report queries with configurable row limits, allowing users to validate report results before committing to full execution. Preview results are cached to improve performance when users repeatedly preview the same report configuration, reducing database load and improving response times.

Execution history management is a critical responsibility of the service, maintaining detailed records of all report executions including timestamps, row counts, output file locations, delivery status, and error information. This history enables users to track report usage, verify successful executions, and troubleshoot issues.

### 3.2 Report Executor

**Location:** `backend/modules/reports/report_executor.py`

The Report Executor is the orchestration engine that coordinates the entire report generation and delivery workflow. When a report execution is triggered—either manually by a user or automatically by the scheduler—the executor begins by loading the complete report definition from the database, including all field configurations, formulas, and output format preferences.

The executor then initiates the data retrieval process, executing the report's SQL query against the configured database connection. It applies any configured field mappings, evaluates formulas to compute derived values, and formats data according to layout specifications. Throughout this process, it monitors execution progress and handles any errors that occur.

During the output generation phase, the executor coordinates with output format writers to generate files in the requested formats. It supports multiple output formats simultaneously, allowing a single report execution to produce outputs in CSV, Excel, PDF, JSON, XML, and Parquet formats, all from the same data retrieval operation.

Delivery coordination is another critical responsibility. For email destinations, the executor packages generated files as email attachments and sends them to specified recipients using configured SMTP settings. For file system destinations, it saves files to specified locations, creating directories as needed and ensuring proper file permissions.

Throughout the entire process, the executor maintains detailed execution history, recording start and end times, row counts, output file locations, delivery status, and any error messages. When errors occur, the executor ensures they are properly logged with sufficient detail for troubleshooting, while allowing partial successes to be recorded when some output formats succeed while others fail.

### 3.3 SQL Query Resolver

**Location:** `backend/modules/reports/report_service.py` (integrated)

The SQL Query Resolver provides intelligent resolution of report data sources, handling both managed SQL queries from the DMS Manage SQL module and ad-hoc SQL queries entered directly during report creation. When a report references a managed SQL query, the resolver retrieves the complete SQL text, connection information, and metadata from the Manage SQL module, ensuring that reports always use the current version of managed queries.

For ad-hoc SQL queries, the resolver validates syntax, checks for potentially dangerous operations, and ensures that queries are compatible with the target database platform. It also handles parameter substitution, allowing reports to accept runtime parameters that are safely injected into SQL queries using parameterized queries to prevent SQL injection vulnerabilities.

The resolver provides column introspection capabilities, automatically detecting column names and data types from SQL query results. This information is used to populate field mapping interfaces, allowing users to select source columns for report fields without needing to manually type column names, reducing errors and improving usability.

Query optimization is another responsibility, with the resolver analyzing queries to identify opportunities for performance improvement, such as adding appropriate WHERE clauses for parameterized reports or suggesting index usage for frequently executed reports.

### 3.4 Formula Evaluator

**Location:** `backend/modules/reports/report_service.py` (integrated)

The Formula Evaluator provides the computational engine that executes formula logic defined in report field configurations. When users specify that a report field should be derived from source data using a formula expression, the evaluator is responsible for safely executing that logic for each row of data.

The evaluator uses Python's expression evaluation capabilities to compute derived values, supporting mathematical operations, string manipulations, date calculations, conditional logic, and function calls. Column references within formulas are automatically resolved to their corresponding values from the source data, allowing users to write intuitive expressions like `quantity * unit_price` to calculate totals, or `CONCAT(first_name, ' ', last_name)` to create full names.

Data type handling is a critical aspect of the evaluator's operation. It automatically converts data types as needed to ensure that formula results are compatible with target field data types, handling numeric conversions, string formatting, date parsing, and null value handling gracefully.

Error handling is built into every evaluation, with the evaluator catching exceptions and providing meaningful error messages that help users identify and correct issues in their formula logic. When a formula fails for a particular row, the error is logged and the row is marked for review, but processing continues for other rows, maximizing data throughput.

The evaluator also provides performance optimization, caching formula compilation results and reusing compiled expressions across multiple rows, significantly improving performance for reports with complex formulas processing large datasets.

### 3.5 Output Format Writers

**Location:** `backend/modules/reports/report_service.py` and `backend/modules/reports/report_executor.py`

The Output Format Writers provide specialized formatting capabilities for each supported output format. Each writer is responsible for converting report data (columns and rows) into the appropriate file format, handling format-specific requirements such as encoding, compression, styling, and metadata.

The CSV Writer generates comma-separated value files with proper encoding (UTF-8), quote handling, and delimiter selection. It ensures that special characters are properly escaped and that files are compatible with common spreadsheet applications and data processing tools.

The Excel Writer creates XLSX format files with proper worksheet structure, column formatting, and data type preservation. It maintains numeric formats, date formats, and text formatting to ensure that reports open correctly in Microsoft Excel and other spreadsheet applications.

The PDF Writer generates formatted PDF documents with professional styling, including headers, footers, table formatting, and page breaks. It handles large reports by automatically paginating content and ensuring that tables fit within page boundaries while maintaining readability.

The JSON Writer creates structured JSON documents with proper nesting, array handling, and data type representation. It ensures that JSON output is valid and can be consumed by downstream systems or APIs that require JSON format data.

The XML Writer generates well-formed XML documents with proper element structure, attribute handling, and namespace support. It ensures that XML output conforms to XML standards and can be validated and processed by XML-aware tools.

The Parquet Writer creates columnar Parquet files optimized for big data processing, with proper schema definition, compression, and metadata. It ensures that Parquet files are compatible with data processing frameworks like Apache Spark, Hadoop, and data lake platforms.

Each writer handles error conditions gracefully, providing meaningful error messages when format-specific issues occur, such as missing required libraries or unsupported data types for specific formats.

---

## 4. Report Definition & Configuration

Report definitions in the DMS Reporting Utility are comprehensive configurations that specify every aspect of report generation, from data source selection through output formatting and delivery. Understanding how to configure reports effectively is essential for creating useful, maintainable reporting solutions.

### 4.1 Basic Report Information

Every report definition begins with basic identifying information that helps users understand the purpose and scope of the report. The report name serves as the primary identifier, appearing in report lists, execution history, and output file names. Descriptive names that clearly indicate the report's purpose, such as "Daily Sales Summary" or "Monthly Customer Activity Report", make reports easier to find and understand.

The description field provides additional context about the report's purpose, data sources, intended audience, and any special considerations. This information is particularly valuable for organizations with many reports, helping users identify which reports meet their specific needs.

Status flags indicate whether reports are active (available for execution) or inactive (temporarily disabled). This allows administrators to disable reports without deleting them, useful for reports that are temporarily unavailable due to data source issues or reports that are being updated.

### 4.2 Data Source Configuration

Reports can be configured to use data from two primary sources: managed SQL queries or ad-hoc SQL queries. Managed SQL queries are stored in the DMS Manage SQL module and provide a centralized approach to SQL management, allowing queries to be versioned, shared, and reused across multiple reports. This approach ensures consistency and reduces duplication, as changes to managed queries automatically propagate to all reports that reference them.

Ad-hoc SQL queries are entered directly during report creation and are stored as part of the report definition. This approach provides maximum flexibility for one-time reports or reports that require highly customized queries that don't need to be shared. Ad-hoc queries are validated for syntax and security before being saved, ensuring that only safe, well-formed queries are stored.

Database connection selection determines which database the report queries will execute against. The system supports connections to multiple database platforms including PostgreSQL, Oracle, MySQL, SQL Server, and others, allowing reports to access data from any connected database system. Connection information is retrieved from the DMS database connection management system, ensuring that reports use properly configured, tested connections.

### 4.3 Field Configuration

Field configuration is one of the most important aspects of report definition, determining exactly what data appears in reports and how it is presented. Each field in a report corresponds to a column in the query result set, but fields can be configured with custom names, descriptions, and formatting that differ from the source column names.

Source column mapping specifies which column from the SQL query result set should be used for each report field. The system provides an intuitive interface that displays available columns from the query, allowing users to select columns without needing to manually type column names. This reduces errors and ensures that field mappings reference valid columns.

Field names and descriptions provide user-friendly labels for report columns. While source columns might have technical names like "CUST_ID" or "TRANS_AMT", report fields can have descriptive names like "Customer ID" or "Transaction Amount" that are more meaningful to report consumers. Descriptions provide additional context about what each field represents, helping users understand report content.

Formula configuration allows fields to be computed from source data rather than directly mapped. Formulas can reference other fields, perform calculations, apply transformations, and use built-in functions. For example, a "Total Amount" field might be computed as `quantity * unit_price * (1 - discount_rate)`, or a "Full Name" field might concatenate first and last names.

Data type specification ensures that field values are properly formatted and handled. The system supports common data types including text, numbers, dates, and booleans, with format specifications for each type. For example, date fields can be formatted as "YYYY-MM-DD" or "MM/DD/YYYY", and numeric fields can specify decimal places and thousand separators.

### 4.4 Layout Configuration

Layout configuration determines how report data is organized and presented. Grouping specifications allow reports to be organized by one or more fields, creating hierarchical structures that make reports easier to read and analyze. For example, a sales report might be grouped by region, then by product category, creating a structured view of sales data.

Sorting specifications determine the order in which report rows appear. Reports can be sorted by one or more fields, with ascending or descending order specified for each sort field. Sort specifications are particularly important for grouped reports, where data within each group should be sorted appropriately.

Panel type configuration determines whether fields appear in detail sections (showing individual rows) or summary sections (showing aggregated data). This allows reports to combine detailed transaction data with summary statistics, providing both granular and high-level views in a single report.

### 4.5 Output Format Configuration

Each report can be configured to support one or more output formats, allowing the same report definition to serve different consumption needs. The default output format specifies which format should be used when no specific format is requested, while the supported formats list indicates all formats that can be generated for the report.

Output format selection affects how data is formatted, what metadata is included, and how files are named. For example, Excel output might include formatting and styling that makes reports more readable, while CSV output focuses on data exchange compatibility. PDF output includes professional formatting suitable for document distribution, while JSON output provides structured data for API consumption.

Preview row limit configuration specifies how many rows should be included in report previews. Preview functionality allows users to validate report results before committing to full execution, and limiting preview rows improves performance and reduces resource usage. The default limit is typically 100 rows, but can be adjusted based on report characteristics and user needs.

### 4.6 Scheduling Configuration

Scheduling configuration enables automated report generation on specified schedules. Frequency codes specify how often reports should execute: daily, weekly, monthly, half-yearly, yearly, or on-demand. Time parameters specify exactly when scheduled executions should occur, such as "10:30 AM" for daily schedules or "MON_10:30" for weekly schedules.

Start and end dates define validity periods for schedules, allowing temporary schedules to be created for specific projects or time-bound reporting needs. The system automatically calculates next run dates based on frequency codes and time parameters, ensuring that schedules are maintained accurately even when executions are delayed or skipped.

Schedule status allows schedules to be temporarily paused without losing their configuration, useful when reports need to be disabled temporarily due to data source issues or maintenance windows. Multiple schedules can be configured for a single report, allowing different execution frequencies for different purposes.

---

## 5. Supported Output Formats

The Reporting Utility supports a comprehensive range of output formats, each designed to serve specific consumption needs and integration scenarios. This multi-format support ensures that reports can be consumed by virtually any downstream system or application, regardless of format preferences.

### 5.1 CSV Format

CSV (Comma-Separated Values) files are the most universal format for data exchange, compatible with virtually all data processing tools, spreadsheet applications, and database systems. The CSV writer generates properly formatted CSV files with UTF-8 encoding, ensuring that special characters and international text are correctly represented.

The writer handles quote characters intelligently, properly escaping fields that contain commas, quotes, or newlines. It ensures CSV compatibility with common tools like Microsoft Excel, Google Sheets, and data processing frameworks, making CSV output ideal for data exchange and integration scenarios.

### 5.2 Excel Format (XLSX)

Excel format provides rich formatting capabilities that make reports more readable and professional. The Excel writer creates XLSX format files (the modern Excel format) with proper worksheet structure, column headers, and data type preservation.

Numeric values are stored as numbers rather than text, ensuring that Excel can perform calculations and apply numeric formatting. Date values are stored as Excel date serial numbers, allowing Excel to apply date formatting and perform date calculations. The writer maintains data types throughout the export process, ensuring that reports open correctly in Excel with appropriate formatting.

### 5.3 PDF Format

PDF format provides professional document formatting suitable for distribution, archiving, and printing. The PDF writer generates formatted PDF documents with proper page layout, table formatting, headers, and footers.

Large reports are automatically paginated, with page breaks inserted appropriately to ensure readability. Table formatting includes proper column alignment, header styling, and row separation, making PDF reports easy to read and professional in appearance. The landscape orientation is used by default to accommodate wide reports with many columns.

### 5.4 JSON Format

JSON format provides structured data representation suitable for API integration and programmatic consumption. The JSON writer generates well-formed JSON documents with proper structure, nesting, and data type representation.

The output includes metadata such as column names, row counts, and generation timestamps, providing context for downstream consumers. JSON output is particularly useful for integration scenarios where reports need to be consumed by web applications, APIs, or data processing pipelines.

### 5.5 XML Format

XML format provides structured data representation with proper element hierarchy and attribute support. The XML writer generates well-formed XML documents that conform to XML standards, ensuring compatibility with XML-aware tools and systems.

The output includes proper XML declaration, root elements, and nested structure that represents report data in a hierarchical format. XML output is particularly useful for integration with legacy systems or enterprise applications that require XML format data.

### 5.6 Parquet Format

Parquet format provides columnar storage optimized for big data processing and analytics. The Parquet writer creates properly structured Parquet files with embedded schema definitions, compression, and metadata.

Parquet output is particularly efficient for large datasets, as the columnar format enables efficient compression and allows data processing frameworks to read only the columns they need. This makes Parquet ideal for data lake ingestion, analytics processing, and integration with big data platforms like Apache Spark and Hadoop.

### 5.7 Text Format (TXT)

Text format provides simple, human-readable output suitable for log files, console output, or basic data exchange. The text writer generates plain text files with proper column alignment and formatting, making reports readable in any text editor or console application.

---

## 6. Key Features

The Reporting Utility incorporates a comprehensive set of features designed to make report creation, execution, and management as efficient, reliable, and user-friendly as possible. These features work together to provide a complete solution that addresses both technical requirements and business needs.

### 6.1 Report Definition Management

The report definition management system provides comprehensive CRUD operations for creating, reading, updating, and deleting report definitions. Users can create new reports from scratch, clone existing reports as templates for new reports, update report configurations, and deactivate reports without deleting them.

Version control capabilities track changes to report definitions, maintaining history of modifications and allowing users to understand how reports have evolved over time. Checksum validation prevents accidental overwrites when multiple users are working with the same report, ensuring data integrity.

Search and filtering capabilities allow users to quickly locate reports by name, description, or other criteria. This is particularly valuable in organizations with many reports, enabling users to find relevant reports efficiently.

### 6.2 SQL Query Integration

Integration with the DMS Manage SQL module allows reports to reference managed SQL queries, providing centralized SQL management and reuse. Changes to managed queries automatically propagate to all reports that reference them, ensuring consistency and reducing maintenance overhead.

Ad-hoc SQL support provides flexibility for one-time reports or highly customized queries. SQL validation ensures that only safe, well-formed queries are stored, preventing SQL injection vulnerabilities and ensuring query correctness.

Column introspection automatically detects available columns from SQL queries, populating field mapping interfaces and reducing configuration errors. This eliminates the need for users to manually type column names, improving accuracy and usability.

### 6.3 Field Mapping & Formulas

Flexible field mapping allows source columns to be mapped to report fields with custom names and descriptions. This enables user-friendly report output while maintaining flexibility in underlying data structures.

Formula support provides powerful computational capabilities, allowing fields to be computed from source data using mathematical operations, string manipulations, date calculations, and conditional logic. Formula evaluation is safe and efficient, with proper error handling and performance optimization.

Data type handling ensures that field values are properly formatted and converted as needed. The system handles numeric formatting, date formatting, string manipulation, and null value handling gracefully, ensuring that report output is accurate and readable.

### 6.4 Preview Functionality

Preview functionality allows users to validate report results before committing to full execution. Preview queries execute with configurable row limits (typically 100 rows), providing quick feedback without consuming excessive resources.

Preview results are cached to improve performance when users repeatedly preview the same report configuration. This reduces database load and improves response times, making the report development process more efficient.

Preview displays show both the final SQL query that will be executed and the resulting data, allowing users to verify that queries are correct and that results match expectations. This helps identify configuration issues early in the development process.

### 6.5 Multiple Output Formats

Support for multiple output formats allows the same report definition to serve different consumption needs. Reports can be configured to support CSV, Excel, PDF, JSON, XML, Parquet, and text formats, with users selecting the appropriate format at execution time.

Simultaneous format generation allows a single report execution to produce outputs in multiple formats, reducing processing overhead and ensuring consistency across formats. This is particularly useful when reports need to be consumed by multiple downstream systems with different format requirements.

Format-specific optimizations ensure that each output format is generated efficiently and correctly. The system handles format-specific requirements such as encoding, compression, styling, and metadata appropriately for each format.

### 6.6 Execution Modes

Synchronous execution provides immediate report generation for ad-hoc reporting needs. When users request immediate report execution, the system generates the report and returns it directly, either as a file download or as data in the response.

Asynchronous execution enables background processing for large reports or scheduled executions. Reports are queued for execution, allowing the system to manage resource usage and provide progress tracking. Asynchronous execution is particularly useful for scheduled reports and large datasets.

Scheduled execution enables automated report generation on specified schedules. The system integrates with the DMS job scheduler to execute reports automatically at configured times, ensuring that regular reporting needs are met without manual intervention.

### 6.7 Delivery Options

Email delivery allows reports to be automatically sent to specified recipients as email attachments. The system supports multiple recipients, custom email subjects and bodies, and proper attachment handling. Email delivery is configured through SMTP settings, supporting various email providers and authentication methods.

File system delivery allows reports to be saved to specified file system locations. Users can specify full file paths or directory paths, with the system automatically creating directories as needed. File system delivery is useful for integration with document management systems, shared network drives, or automated processing pipelines.

Download delivery provides immediate access to reports through the web interface. Users can download reports directly from the Report Runs interface, with proper file naming and content type handling ensuring that downloads work correctly in web browsers.

### 6.8 Execution History & Audit

Comprehensive execution history tracks every report execution, regardless of success or failure. History records include execution timestamps, row counts, output file locations, delivery status, and error information, providing complete visibility into report execution activities.

Execution tracking enables users to monitor report execution progress, verify successful completions, and identify issues when they occur. Status information indicates whether executions completed successfully, failed, or are still in progress, providing immediate visibility into execution outcomes.

Audit trails maintain records of who created and updated report definitions, who triggered executions, and when activities occurred. This accountability is essential for compliance and helps organizations understand who is responsible for reporting activities.

Error logging captures detailed error information when executions fail, including error messages, stack traces, and context information. This enables efficient troubleshooting and helps identify patterns in execution failures.

### 6.9 Scheduling

Automated scheduling enables reports to be generated automatically on specified schedules without manual intervention. The system supports daily, weekly, monthly, half-yearly, and yearly frequencies, with precise time control for when executions should occur.

Schedule management allows schedules to be created, updated, paused, and deleted as needed. Multiple schedules can be configured for a single report, enabling different execution frequencies for different purposes. Schedule status tracking indicates whether schedules are active, paused, or completed.

Next run calculation automatically determines when scheduled reports should execute next, accounting for frequency codes, time parameters, and any delays or skips. This ensures that schedules are maintained accurately and that reports execute at the intended times.

---

## 7. Architecture

### 7.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Reports Page │  │ Report Runs  │  │ Report Form  │      │
│  │              │  │   Page      │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          │  HTTP/REST API  │                  │
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼──────────────┐
│              FastAPI Backend (Python)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Reports Router                                 │   │
│  │  (fastapi_reports.py)                                  │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼──────────────┐                           │
│  │   Report Metadata Service    │                           │
│  │   - Report Definitions         │                           │
│  │   - Field Configurations      │                           │
│  │   - Formula Management         │                           │
│  │   - Layout Specifications      │                           │
│  │   - Execution History          │                           │
│  └──────────────┬───────────────┘                           │
│                 │                                            │
│  ┌──────────────▼──────────────┐                           │
│  │   Report Executor             │                           │
│  │   - Query Execution           │                           │
│  │   - Formula Evaluation         │                           │
│  │   - Output Generation          │                           │
│  │   - Delivery Coordination     │                           │
│  └──────────────┬───────────────┘                           │
│                 │                                            │
│  ┌──────────────▼──────────────┐                           │
│  │   Output Format Writers       │                           │
│  │   - CSV Writer                │                           │
│  │   - Excel Writer              │                           │
│  │   - PDF Writer                │                           │
│  │   - JSON Writer               │                           │
│  │   - XML Writer                │                           │
│  │   - Parquet Writer            │                           │
│  └──────────────┬───────────────┘                           │
└─────────────────┼───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌─────▼─────┐  ┌───▼────┐
│Metadata│   │ Target    │  │ Output │
│Database│   │ Database  │  │ Files  │
└───────┘   └────────────┘  └────────┘
```

### 7.2 Data Flow

```
1. User Creates/Updates Report Definition
   ↓
2. Report Configuration Saved to Metadata Database
   ↓
3. User Triggers Execution (Manual or Scheduled)
   ↓
4. Report Executor:
   - Loads report definition
   - Resolves SQL query (Managed or Ad-hoc)
   - Executes query against target database
   ↓
5. Data Processing:
   - Applies field mappings
   - Evaluates formulas
   - Applies layout configurations
   ↓
6. Output Generation:
   - Generates files in requested formats
   - Applies format-specific formatting
   ↓
7. Delivery:
   - Email: Sends as attachment via SMTP
   - File: Saves to specified location
   - Download: Makes available via web interface
   ↓
8. Execution History Saved
   ↓
9. Results Available for Review
```

---

## 8. Workflow

Understanding the workflow of the Reporting Utility is essential for effective use. The system follows logical, sequential processes that guide users from initial report creation through configuration, execution, and monitoring.

### 8.1 Report Creation Workflow

The report creation workflow begins when users navigate to the Reports module from the DMS home page, where it appears in the main navigation menu. Once in the module, users initiate the creation process by clicking the "New Report" or "Create Report" button, which opens the report configuration form.

The first step in report creation is providing basic information: a unique report name, a descriptive description, and status settings. The report name serves as the primary identifier and will appear in report lists, execution history, and output file names, so it should be descriptive and meaningful.

Data source selection is the next critical step. Users choose between using a managed SQL query from the Manage SQL module or entering an ad-hoc SQL query directly. For managed SQL queries, users select from a list of available queries, and the system automatically retrieves the SQL text, connection information, and metadata. For ad-hoc queries, users enter SQL directly, and the system validates syntax and security.

Once a data source is selected, the system automatically introspects the query to detect available columns. Users are then presented with a field mapping interface showing source columns on one side and report fields on the other. Users can map source columns to report fields, specify custom field names and descriptions, configure formulas for computed fields, and set data types and formatting.

Layout configuration allows users to specify grouping, sorting, and panel types. Grouping creates hierarchical report structures, sorting determines row order, and panel types control whether fields appear in detail or summary sections. These configurations determine how report data is organized and presented.

Output format configuration specifies which formats the report should support. Users can select multiple formats, with one designated as the default. Preview row limit configuration specifies how many rows should be included in previews, balancing information with performance.

Once all configuration is complete, users save the report definition, which stores all information in the database. The system validates the configuration at this point, checking for required fields, verifying SQL syntax, validating formulas, and ensuring that field mappings reference valid columns. Upon successful save, the report is ready for execution.

### 8.2 Report Execution Workflow

Report execution can be triggered in three ways: manually by users clicking an "Execute" or "Generate" button, automatically by the scheduler based on configured schedules, or programmatically through API calls. Manual execution provides immediate control and is useful for ad-hoc reporting or testing configurations. Scheduled execution enables automation for regular reporting needs.

When execution is triggered, the system first determines whether execution should be synchronous (immediate) or asynchronous (queued). For synchronous execution, the system generates the report immediately and returns results directly. For asynchronous execution, the system creates a job request and adds it to the job queue for background processing.

During the data retrieval phase, the Report Executor loads the complete report definition from the database, including all field configurations, formulas, and output format preferences. It then resolves the SQL query, either retrieving it from the Manage SQL module or using the ad-hoc SQL stored in the report definition.

The executor executes the SQL query against the configured database connection, retrieving the result set. If the report includes parameters, the executor substitutes parameter values into the query using parameterized queries to ensure security and prevent SQL injection.

During the data processing phase, the executor applies field mappings, mapping source columns to report fields according to the configuration. It evaluates formulas to compute derived values for each row, applying mathematical operations, string manipulations, and conditional logic as specified. It applies layout configurations, organizing data according to grouping and sorting specifications.

Output generation occurs next, with the executor coordinating with output format writers to generate files in the requested formats. For each requested format, the appropriate writer converts the processed data into the format-specific file structure, applying formatting, styling, and metadata as needed.

Delivery coordination follows output generation. For email destinations, the executor packages generated files as email attachments and sends them to specified recipients using configured SMTP settings. For file system destinations, it saves files to specified locations, creating directories as needed. For download destinations, it makes files available through the web interface.

Throughout the entire process, the executor maintains detailed execution history, recording start and end times, row counts, output file locations, delivery status, and any error messages. This history is saved to the database immediately upon completion, making execution results available for review.

### 8.3 Monitoring Workflow

The monitoring workflow enables users and administrators to track report activities, analyze execution results, and troubleshoot issues. The Reports list view provides a comprehensive list of all report definitions in the system, showing key information such as report names, descriptions, data sources, status, and last execution dates.

Filtering capabilities allow users to narrow the list based on various criteria: status (active or inactive), data source type (managed SQL or ad-hoc), creation date, or last execution date. This filtering helps users quickly locate specific reports or identify reports that haven't been executed recently.

The Report Runs view provides detailed information about all execution attempts for reports. Users can see a chronological list of all runs, with each entry showing the execution timestamp, status, row counts, output formats generated, delivery status, and any messages generated. This history enables users to track execution patterns, identify trends in success or failure rates, and understand how execution performance has changed over time.

Execution details allow users to drill down into specific executions to understand what happened. Details show the exact SQL query that was executed, the parameters that were used, the output files that were generated, and any error messages that occurred. This information is essential for troubleshooting issues and understanding execution behavior.

Download capabilities allow users to retrieve output files from past executions. Users can download files in any format that was generated, enabling access to historical report data even after files have been removed from file system storage locations.

Schedule monitoring allows users to view and manage report schedules. Users can see when reports are scheduled to execute next, view schedule history, pause or resume schedules, and update schedule configurations. This enables proactive management of automated reporting processes.

---

## 9. Database Schema

### 9.1 Main Tables

#### DMS_RPRT_DEF (Report Definition)

| Column | Type | Description |
|--------|------|-------------|
| `rprtid` | INTEGER | Primary key |
| `rprtnm` | VARCHAR(200) | Report name |
| `dscrptn` | VARCHAR(1000) | Description |
| `sqlsrcid` | INTEGER | SQL source ID (from Manage SQL) |
| `adhcsql` | TEXT/CLOB | Ad-hoc SQL text |
| `dbcnid` | INTEGER | Database connection ID |
| `dflt_otpt_fmt` | VARCHAR(20) | Default output format |
| `spprtd_fmts` | VARCHAR(200) | Supported formats (comma-separated) |
| `prvw_rw_lmt` | INTEGER | Preview row limit |
| `is_actv` | CHAR(1) | Is active (Y/N) |
| `finl_sql` | TEXT/CLOB | Final SQL (with field mappings) |
| `chksm` | VARCHAR(64) | Checksum for change detection |
| `crtdby` | VARCHAR(100) | Created by |
| `crtddt` | TIMESTAMP | Created date |
| `uptdby` | VARCHAR(100) | Updated by |
| `uptddt` | TIMESTAMP | Updated date |
| `curflg` | CHAR(1) | Current flag (Y/N) |

#### DMS_RPRT_FLD (Report Fields)

| Column | Type | Description |
|--------|------|-------------|
| `fldid` | INTEGER | Primary key |
| `rprtid` | INTEGER | Report ID (FK to DMS_RPRT_DEF) |
| `fldnm` | VARCHAR(200) | Field name |
| `flddscrptn` | VARCHAR(500) | Field description |
| `srccolnm` | VARCHAR(200) | Source column name |
| `frmlid` | INTEGER | Formula ID (FK to DMS_RPRT_FRML) |
| `pnltyp` | VARCHAR(20) | Panel type (DETAIL, SUMMARY) |
| `isgrpby` | CHAR(1) | Is group by (Y/N) |
| `ordbyseq` | INTEGER | Order by sequence |
| `ordbydir` | VARCHAR(10) | Order by direction (ASC, DESC) |
| `dtyptyp` | VARCHAR(50) | Data type |
| `curflg` | CHAR(1) | Current flag |

#### DMS_RPRT_FRML (Report Formulas)

| Column | Type | Description |
|--------|------|-------------|
| `frmlid` | INTEGER | Primary key |
| `rprtid` | INTEGER | Report ID (FK to DMS_RPRT_DEF) |
| `frmlnm` | VARCHAR(200) | Formula name |
| `frmltxt` | TEXT/CLOB | Formula text |
| `frmltyp` | VARCHAR(50) | Formula type |
| `crtdby` | VARCHAR(100) | Created by |
| `crtddt` | TIMESTAMP | Created date |
| `curflg` | CHAR(1) | Current flag |

#### DMS_RPRT_LYOT (Report Layout)

| Column | Type | Description |
|--------|------|-------------|
| `lyotid` | INTEGER | Primary key |
| `rprtid` | INTEGER | Report ID (FK to DMS_RPRT_DEF) |
| `lyotjsn` | TEXT/CLOB | Layout JSON configuration |
| `curflg` | CHAR(1) | Current flag |

#### DMS_RPRT_SCHD (Report Schedule)

| Column | Type | Description |
|--------|------|-------------|
| `schdid` | INTEGER | Primary key |
| `rprtid` | INTEGER | Report ID (FK to DMS_RPRT_DEF) |
| `frqncy` | VARCHAR(10) | Frequency code (DL, WK, MN, etc.) |
| `tm_prm` | VARCHAR(100) | Time parameter |
| `nxt_run_dt` | TIMESTAMP | Next run date |
| `lst_run_dt` | TIMESTAMP | Last run date |
| `stts` | VARCHAR(20) | Status (ACTIVE, PAUSED) |
| `crtdby` | VARCHAR(100) | Created by |
| `crtddt` | TIMESTAMP | Created date |
| `curflg` | CHAR(1) | Current flag |

#### DMS_RPRT_RUN (Report Execution History)

| Column | Type | Description |
|--------|------|-------------|
| `runid` | INTEGER | Primary key |
| `rprtid` | INTEGER | Report ID (FK to DMS_RPRT_DEF) |
| `rqst_id` | INTEGER | Request ID (from job scheduler) |
| `strttm` | TIMESTAMP | Start time |
| `ndtm` | TIMESTAMP | End time |
| `stts` | VARCHAR(20) | Status (SUCCESS, FAILED, RUNNING) |
| `rqstdby` | VARCHAR(100) | Requested by |
| `prmtrs` | JSON/TEXT | Parameters (JSON format) |
| `mssg` | TEXT/CLOB | Message |
| `rwcnt` | INTEGER | Row count |
| `otpt_fmt` | VARCHAR(20) | Output format |
| `crtddt` | TIMESTAMP | Created date |

#### DMS_RPRT_OTPT (Report Output Files)

| Column | Type | Description |
|--------|------|-------------|
| `otptid` | INTEGER | Primary key |
| `runid` | INTEGER | Run ID (FK to DMS_RPRT_RUN) |
| `fmt` | VARCHAR(20) | Output format |
| `flpth` | VARCHAR(1000) | File path |
| `flsz` | BIGINT | File size (bytes) |
| `crtddt` | TIMESTAMP | Created date |

#### DMS_RPRT_PRVW_CCH (Report Preview Cache)

| Column | Type | Description |
|--------|------|-------------|
| `cchid` | INTEGER | Primary key |
| `rprtid` | INTEGER | Report ID (FK to DMS_RPRT_DEF) |
| `chksm` | VARCHAR(64) | Checksum of report config |
| `prvwdt` | JSON/TEXT | Preview data (JSON format) |
| `crtddt` | TIMESTAMP | Created date |
| `exprdt` | TIMESTAMP | Expiry date |

---

## 10. API Endpoints

### 10.1 Report Definition Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reports` | List all reports (with search/filter) |
| `GET` | `/api/reports/{report_id}` | Get report by ID |
| `POST` | `/api/reports` | Create new report |
| `PUT` | `/api/reports/{report_id}` | Update report |
| `DELETE` | `/api/reports/{report_id}` | Delete report |

### 10.2 Report Execution Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/reports/{report_id}/execute` | Execute report synchronously (download) |
| `POST` | `/api/reports/{report_id}/execute-async` | Queue report for async execution |
| `POST` | `/api/reports/{report_id}/preview` | Preview report (limited rows) |

### 10.3 Report History Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/report-runs` | List all report runs (with filters) |
| `GET` | `/api/reports/{report_id}/runs` | Get runs for specific report |

### 10.4 Schedule Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/report-schedules` | List all report schedules |
| `POST` | `/api/report-schedules` | Create report schedule |
| `PUT` | `/api/report-schedules/{schedule_id}` | Update report schedule |
| `DELETE` | `/api/report-schedules/{schedule_id}` | Delete report schedule |

### 10.5 Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reports/sql-sources` | List available SQL sources |
| `POST` | `/api/reports/describe-sql` | Describe SQL columns |

---

## 11. Security & Validation

### 11.1 SQL Query Validation

**Syntax Validation:**
- SQL syntax checking before saving
- Database-specific syntax validation
- Parameter placeholder validation

**Security Validation:**
- SQL injection prevention through parameterized queries
- Dangerous operation detection (DROP, DELETE, etc.)
- Access control validation for database connections

### 11.2 Formula Validation

- **Syntax Validation**: Formula syntax checking before saving
- **Security Validation**: Safe expression evaluation (no file system access, no network access)
- **Type Validation**: Data type compatibility checking

### 11.3 Access Control

- **User Permissions**: Module-level access control
- **Role-Based Access**: Role-based report permissions
- **Audit Logging**: All operations logged with user information

### 11.4 Output Validation

- **File Path Validation**: Path traversal prevention
- **File Size Limits**: Maximum file size enforcement
- **Format Validation**: Output format compatibility checking

---

## 12. Integration with DMS

### 12.1 Database Connections

The Reporting Utility integrates with the DMS database connection system:
- Uses `DMS_DBCONDTLS` for database connections
- Supports multiple database platforms (PostgreSQL, Oracle, MySQL, etc.)
- Automatic SQL dialect handling

### 12.2 Manage SQL Integration

Integrates with DMS Manage SQL module:
- References managed SQL queries
- Automatic query versioning
- Centralized SQL management

### 12.3 Job Scheduler

Integrates with DMS job scheduler:
- Uses `DMS_PRCREQ` for job queuing
- Background processing
- Status tracking
- Progress monitoring

### 12.4 Audit System

Follows DMS audit standards:
- Standard audit columns (CRTDBY, CRTDDT, UPDTBY, UPDTDT)
- User tracking
- Execution history

### 12.5 User Interface

Integrated into DMS navigation:
- "Reports" menu item
- "Report Runs" menu item
- Consistent UI/UX with other modules

---

## 13. Best Practices

Adopting best practices when using the Reporting Utility ensures optimal performance, maintainability, and user satisfaction. These practices have been developed through experience with various use cases and help organizations maximize the value they derive from the system.

### 13.1 Report Naming

Effective report naming conventions significantly improve the usability and maintainability of report definitions. Report names should be descriptive and meaningful, clearly indicating the report's purpose and content. For example, "Daily Sales Summary" is much more informative than "Report_001". Including frequency information in names for scheduled reports helps users quickly identify which reports run on which schedules.

Avoiding special characters in report names prevents potential issues with database queries, URL encoding, and system compatibility. Stick to alphanumeric characters, spaces, and underscores for maximum compatibility. Consistent naming conventions across an organization make it easier for multiple users to understand and work with reports.

### 13.2 SQL Query Management

Using managed SQL queries for reports that reference shared data sources ensures consistency and reduces duplication. When SQL queries need to be updated, changes propagate automatically to all reports that reference them, reducing maintenance overhead. Managed SQL queries also benefit from versioning and change tracking provided by the Manage SQL module.

For one-time or highly customized reports, ad-hoc SQL is appropriate, but consider converting frequently used ad-hoc queries to managed SQL queries for better maintainability. SQL queries should be optimized for performance, with appropriate WHERE clauses, JOIN conditions, and indexing considerations.

### 13.3 Field Configuration

Comprehensive field configuration improves report usability. Ensure that field names are user-friendly and descriptive, as these names appear in report output and are what end users see. Field descriptions provide additional context about what each field represents, helping users understand report content.

Formula configuration should be thoroughly tested before production use, as errors in formulas can cause widespread data quality issues. Test with sample data that represents the full range of possible values to ensure formulas handle edge cases correctly. Keep formulas as simple as possible, as complex formulas can significantly impact processing time.

### 13.4 Output Format Selection

Selecting appropriate output formats for each report's intended use case ensures that reports are consumed effectively. CSV format is ideal for data exchange and integration scenarios, Excel format is best for spreadsheet analysis, PDF format is suitable for document distribution, and JSON/XML formats are appropriate for API integration.

Configuring multiple supported formats for reports that serve different consumption needs allows users to select the appropriate format at execution time. This flexibility ensures that the same report definition can serve multiple purposes without requiring duplicate report definitions.

### 13.5 Scheduling

Effective scheduling ensures that reports are generated at optimal times without disrupting system operations. Set appropriate frequencies that match business requirements—daily for operational reports, weekly for summary reports, monthly for analytical reports. Use time parameters to schedule executions during off-peak hours when system resources are more available.

Regular monitoring of scheduled executions helps identify issues early, such as reports that are consistently failing or executions that are taking longer than expected. Setting start and end dates for temporary schedules ensures that one-time or project-specific reports don't continue running indefinitely after they are no longer needed.

### 13.6 Performance Optimization

Performance optimization requires balancing multiple factors. Preview row limits should be set appropriately—too high limits slow down previews, while too low limits may not provide sufficient information. For large reports, consider using asynchronous execution to avoid blocking user interfaces.

SQL query optimization is critical for report performance. Ensure that queries use appropriate indexes, avoid unnecessary JOINs, and include appropriate WHERE clauses to limit data retrieval. For reports that process large datasets, consider adding row limits or date range filters to prevent excessive data processing.

---

## 14. Troubleshooting

Effective troubleshooting requires a systematic approach to identifying and resolving issues. The Reporting Utility provides comprehensive error logging and diagnostic information to help users quickly identify and resolve problems.

### Common Issues

**Report Execution Fails:** When report executions fail, the first step is to check the execution history for error messages. Error messages typically indicate the root cause, such as SQL syntax errors, database connection issues, or missing data. Verify that the database connection is active and accessible, and that the SQL query is syntactically correct for the target database platform.

**SQL Query Errors:** SQL query errors typically indicate that the query syntax is incorrect or incompatible with the target database. Verify that the query uses correct syntax for the database platform (PostgreSQL, Oracle, etc.), and that all referenced tables and columns exist. Check for common issues such as missing table aliases, incorrect JOIN syntax, or incompatible data type operations.

**Formula Evaluation Errors:** Formula evaluation errors typically indicate that formula syntax is incorrect or that formula logic is incompatible with data types. Verify that formula syntax is correct, that all referenced columns exist, and that data types are compatible with formula operations. Test formulas with sample data to identify issues before full execution.

**Output Generation Errors:** Output generation errors typically indicate that required libraries are missing or that data cannot be converted to the requested format. For Excel output, ensure that the `openpyxl` package is installed. For PDF output, ensure that the `reportlab` package is installed. For Parquet output, ensure that the `pyarrow` package is installed. Verify that data types are compatible with the requested output format.

**Email Delivery Failures:** Email delivery failures typically indicate that SMTP configuration is incorrect or that email server connectivity issues exist. Verify SMTP host, port, authentication credentials, and TLS settings. Test email connectivity independently to ensure that the email server is accessible and that credentials are correct.

**Performance Issues:** Performance problems can stem from multiple sources. For large reports, consider using asynchronous execution to avoid blocking. Optimize SQL queries to reduce data retrieval time, and consider adding appropriate filters to limit data processing. For reports with complex formulas, review formula logic to identify opportunities for simplification.

**Schedule Execution Issues:** When scheduled reports don't execute, verify that schedules are active and that next run dates are correctly calculated. Check the job scheduler status to ensure that the scheduler is running and processing jobs. Review schedule configurations to ensure that frequency codes and time parameters are correct.

---

## 15. Future Enhancements

### Planned Features

- **Report Templates**: Pre-configured report templates for common use cases
- **Interactive Dashboards**: Visual dashboard creation with charts and graphs
- **Report Sharing**: Share reports with specific users or groups
- **Report Subscription**: Subscribe to reports for automatic delivery
- **Advanced Formatting**: Rich text formatting, conditional formatting, charts in Excel/PDF
- **Parameter Prompts**: Interactive parameter prompts during execution
- **Report Comparison**: Compare results from different report runs
- **Data Export APIs**: RESTful APIs for programmatic report access
- **Report Versioning**: Version control for report definitions
- **Collaborative Editing**: Multiple users editing reports simultaneously

---

## 16. Conclusion

The DMS Reporting Utility provides a robust, flexible, and user-friendly solution for report generation and management. With support for multiple data sources, flexible field configuration, powerful formula capabilities, multiple output formats, and comprehensive scheduling capabilities, it enables efficient reporting workflows while maintaining data quality and auditability.

The system is designed to scale with your needs, from small ad-hoc reports to large scheduled batch processes, and integrates seamlessly with the broader DMS ecosystem. Whether you need operational reports, executive summaries, compliance documentation, or data exports, the Reporting Utility provides the tools and capabilities needed to meet your reporting requirements.

---

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Status:** Production Ready ✅
