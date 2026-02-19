# DMS File Management Utility - Overview Document 📁

**Status:** ✅ Production Ready  
**Date:** November 2025  
**Version:** 1.0

---

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Overview & Purpose](#overview--purpose)
3. [Core Components](#core-components)
4. [File Storage & Organization](#file-storage--organization)
5. [Supported File Formats](#supported-file-formats)
6. [Key Features](#key-features)
7. [Architecture](#architecture)
8. [Workflow](#workflow)
9. [Database Schema](#database-schema)
10. [API Endpoints](#api-endpoints)
11. [Security & Validation](#security--validation)
12. [Integration with DMS](#integration-with-dms)

---

## 1. Introduction

The **DMS File Management Utility** is a comprehensive file upload and data import system integrated into the DMS (Data Management System) application. It enables users to upload data files in various formats, configure column mappings, transform data, and load it into target database tables with full audit trails and error handling.

---

## 2. Overview & Purpose

The DMS File Management Utility serves as a comprehensive solution for importing structured and semi-structured data from files into database systems. Unlike traditional ETL tools that primarily focus on database-to-database transfers, this utility addresses the common business need of processing data files received from external systems, partners, or legacy applications that export data in various file formats.

The system provides secure file upload capabilities with comprehensive metadata tracking, ensuring that every file processed is fully documented and traceable. When a file is uploaded, the system automatically detects its format and intelligently parses its contents, extracting column information and providing users with a preview of the data before committing to a full import process.

One of the utility's most powerful features is its flexible column mapping system, which allows users to define how source columns from files map to target columns in database tables. This mapping is not limited to simple one-to-one relationships; users can apply transformations, derive values using Python expressions, and configure default values for missing data. The system supports multiple file formats including CSV, Excel spreadsheets, JSON documents, XML files, Parquet columnar files, PDF documents, and even Google Sheets, making it versatile enough to handle virtually any data source that produces file-based outputs.

Data validation is built into every step of the process, with the system enforcing data type constraints, required field validation, and primary key uniqueness checks. When errors occur, they are captured at the row level, allowing the system to continue processing valid rows while logging problematic data for later review and correction.

For organizations with regular data import requirements, the utility offers sophisticated scheduling capabilities. Users can configure automated file processing to run daily, weekly, monthly, or on custom schedules, with the system automatically calculating next run times and managing execution queues. Each execution is fully tracked, creating a complete audit trail that includes execution timestamps, row counts (processed, successful, and failed), status information, and detailed error logs.

### Use Cases

The File Management Utility addresses a wide range of data import scenarios that organizations encounter in their daily operations. One common use case is importing data from external systems that export information in file formats rather than providing direct database access. For example, a company might receive daily sales reports from a partner system as CSV files, or monthly financial data as Excel spreadsheets. The utility handles these scenarios seamlessly, allowing users to configure the import once and then either execute it manually or schedule it for automatic processing.

Batch processing of large data files is another primary use case. When organizations need to process historical data migrations, bulk updates, or periodic data refreshes, the utility's batch processing capabilities ensure efficient handling of large volumes while maintaining system performance through configurable batch sizes and transaction management.

Data migration projects often require importing data from legacy systems that may export data in various formats. The utility's multi-format support and flexible mapping capabilities make it ideal for such migrations, allowing organizations to transform legacy data structures into modern database schemas while maintaining data integrity.

Regular data loads represent perhaps the most common use case, where organizations need to import data on a recurring basis—daily customer updates, weekly inventory reports, monthly financial statements, or quarterly compliance data. The scheduling system handles these requirements automatically, ensuring data is imported consistently and on time without manual intervention.

Finally, ad-hoc uploads provide users with the flexibility to import data on demand when immediate processing is required, such as importing a one-time data correction file or processing an urgent data update that cannot wait for the next scheduled run.

---

## 3. Core Components

The File Management Utility is built upon a modular architecture consisting of six core components, each responsible for a specific aspect of the file processing pipeline. These components work together seamlessly to provide a complete solution from file upload through data loading.

### 3.1 File Parser Manager

**Location:** `backend/modules/file_upload/file_parser.py`

The File Parser Manager serves as the intelligent gateway that determines how to interpret incoming files. When a file is uploaded, the manager first examines the file's extension and content to automatically detect its format. This detection process goes beyond simple file extensions; it also analyzes file headers (magic numbers) to ensure the file type matches its extension, providing an additional layer of security against malicious uploads.

Once the file type is identified, the manager selects the appropriate specialized parser from its registry of available parsers. Each parser is designed to handle the unique characteristics of its file format—CSV files require delimiter detection and quote character handling, Excel files need sheet selection and cell type preservation, JSON files may need nested structure flattening, and so on. The manager orchestrates the parsing process, converting raw file data into structured pandas DataFrames that can be easily manipulated and transformed.

The manager also provides preview functionality, allowing users to examine the first few rows of data before committing to a full import. This preview capability is optimized for performance, reading only the necessary portion of large files to provide quick feedback without consuming excessive memory or processing time.

The system currently supports seven specialized parsers: CSV Parser for comma and tab-separated values, Excel Parser for XLSX and XLS formats, JSON Parser for structured data, Parquet Parser for columnar data formats, XML Parser for hierarchical data structures, PDF Parser for extracting tabular data from PDF documents, and Google Sheets Parser for direct integration with Google's spreadsheet platform.

### 3.2 File Upload Service

**Location:** `backend/modules/file_upload/file_upload_service.py`

The File Upload Service acts as the persistence layer for all file upload configurations. It provides comprehensive CRUD (Create, Read, Update, Delete) operations that manage the lifecycle of file upload definitions. When a user creates a new file upload configuration, the service stores all relevant metadata including file references, descriptions, target database connections, and processing options.

The service maintains relationships between main upload definitions and their associated column mappings, ensuring data consistency and referential integrity. It implements a soft delete mechanism, which means that when configurations are deleted, they are marked as inactive rather than being physically removed from the database. This approach preserves historical records and audit trails, allowing administrators to review past configurations and understand the evolution of data import processes.

Activation and deactivation of configurations are handled through the service, providing users with the ability to temporarily disable file uploads without losing their configuration. This is particularly useful for scheduled uploads that may need to be paused during maintenance windows or when source systems are unavailable.

### 3.3 File Upload Executor

**Location:** `backend/modules/file_upload/file_upload_executor.py`

The File Upload Executor is the orchestration engine that coordinates the entire file processing workflow. When a file upload job is triggered—either manually by a user or automatically by the scheduler—the executor begins by loading the complete configuration from the database, including all column mappings, transformation rules, and target database connection details.

The executor then initiates the file parsing process, working with the File Parser Manager to convert the source file into a structured format. Once parsed, it applies any configured transformations, evaluating derivation logic and computing derived values for each row. If the target table does not exist, the executor coordinates with the Table Creator to generate and execute the appropriate DDL statements.

During the data loading phase, the executor manages the interaction with the Data Loader, monitoring progress and handling any errors that occur. Throughout the entire process, it maintains detailed execution history, recording start and end times, row counts, and status information. When errors occur, the executor ensures they are properly logged with sufficient detail for troubleshooting, while allowing valid rows to continue processing.

### 3.4 Table Creator

**Location:** `backend/modules/file_upload/table_creator.py`

The Table Creator component automates the generation of database tables based on column mapping definitions. This eliminates the need for database administrators to manually create tables before importing data, significantly reducing setup time and the potential for human error.

When creating a new table, the creator analyzes all column mappings defined for a file upload configuration and generates appropriate Data Definition Language (DDL) statements. It leverages the DMS parameter mapping system to ensure data types are correctly translated for the target database platform, handling differences between database systems such as Oracle's VARCHAR2 versus PostgreSQL's VARCHAR, or NUMBER versus INTEGER types.

The creator intelligently handles primary key definitions, creating composite keys when multiple columns are designated as primary key components. It also enforces NOT NULL constraints based on column requirements, ensuring data integrity from the moment tables are created.

A particularly important feature is the automatic addition of audit columns. The system automatically adds standard audit columns (CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE) to every table, ensuring consistent audit trails across all imported data. The creator also implements protection mechanisms that prevent accidental modification of existing table structures, ensuring that once a table is created and contains data, its schema cannot be inadvertently changed.

### 3.5 Data Loader

**Location:** `backend/modules/file_upload/data_loader.py`

The Data Loader is responsible for efficiently transferring data from parsed files into target database tables. It implements sophisticated batch processing algorithms that process data in configurable batch sizes (defaulting to 1000 rows), balancing memory usage with database performance. This approach allows the system to handle files of virtually any size without overwhelming system resources.

The loader supports three distinct execution modes, each designed for different data loading scenarios. INSERT mode simply appends new rows to existing tables, making it ideal for incremental data loads where historical data should be preserved. TRUNCATE_LOAD mode clears the target table before loading new data, ensuring a complete refresh of the table contents—useful for dimension tables that need to be completely replaced periodically. UPSERT mode provides the most sophisticated capability, performing insert operations for new rows and update operations for existing rows based on primary key matching, enabling true incremental updates.

Transaction management is a critical aspect of the loader's operation. It ensures that either all rows in a batch are successfully loaded, or the entire batch is rolled back, maintaining data consistency. When individual rows within a batch fail validation or constraint checks, the loader captures detailed error information while continuing to process valid rows, maximizing data throughput even when some data quality issues exist.

The loader automatically populates audit columns with appropriate values—setting CREATED_DATE and CREATED_BY for new rows, and UPDATED_DATE and UPDATED_BY for modified rows in UPSERT operations. This ensures complete auditability without requiring users to manually configure these values.

### 3.6 Formula Evaluator

**Location:** `backend/modules/file_upload/formula_evaluator.py`

The Formula Evaluator provides the computational engine that executes derivation logic defined in column mappings. When users specify that a target column should be derived from source data using a Python expression, the evaluator is responsible for safely executing that logic for each row of data.

The evaluator uses Python's Abstract Syntax Tree (AST) parsing capabilities to analyze expressions before execution, ensuring that only safe operations are performed. This prevents malicious code injection and restricts access to system resources, while still providing users with powerful transformation capabilities such as string concatenation, mathematical operations, conditional logic, and function calls.

Column references within expressions are automatically resolved to their corresponding values from the source data, allowing users to write intuitive expressions like `first_name + ' ' + last_name` to create full names, or `price * quantity` to calculate totals. The evaluator handles data type conversions automatically, ensuring that operations produce results compatible with target column data types.

Error handling is built into every evaluation, with the evaluator catching exceptions and providing meaningful error messages that help users identify and correct issues in their derivation logic. When an expression fails for a particular row, the error is logged and the row is marked for review, but processing continues for other rows.

---

## 4. File Storage & Organization

The File Management Utility employs a dual-storage approach, maintaining physical files on the filesystem while storing comprehensive metadata and configuration information in the database. This design provides both performance benefits and complete traceability.

### 4.1 Physical Storage

**Storage Location:** `data/file_uploads/`

Files are physically stored on the server's filesystem in a dedicated directory structure. When files are initially uploaded, they are temporarily stored with generated temporary filenames that include timestamps to ensure uniqueness. This temporary storage allows the system to parse and preview files before users commit to saving the configuration, providing a safety mechanism that prevents unnecessary storage of files that may be incorrectly formatted or uploaded by mistake.

The filesystem storage structure is straightforward and organized:
```
data/
└── file_uploads/
    ├── temp_*.csv          (Temporary files during upload)
    ├── temp_*.xlsx
    ├── temp_*.json
    └── [timestamped files] (Permanent storage)
```

Temporary files are created during the upload and preview phase, allowing users to examine file contents before deciding whether to proceed with the import configuration. Once a configuration is saved, files may be retained for scheduled processing or moved to permanent storage locations based on organizational policies. The system maintains file paths in the database, allowing it to locate and process files even if they are moved or archived, as long as the paths are updated accordingly.

### 4.2 Metadata Storage

While physical files are stored on the filesystem, all metadata, configurations, and execution history are maintained in the database, providing a centralized repository for all file upload information. This database-centric approach enables powerful querying, reporting, and audit capabilities that would be difficult to achieve with filesystem-only storage.

The **DMS_FLUPLD** table serves as the main repository for file upload definitions. Each record represents a complete file upload configuration, storing the unique file reference identifier that users assign, the original filename, the physical file path, and the detected file type. The table also maintains target database connection information, specifying which database and table will receive the imported data. Configuration settings such as truncate flags, header and footer row counts, and batch processing sizes are all stored here, along with status information indicating whether the configuration is active or inactive, and scheduling details that determine when automated processing should occur.

The **DMS_FLUPLDDTL** table maintains the detailed column mapping information for each file upload configuration. This table stores the relationships between source columns in files and target columns in database tables, along with data type definitions that ensure proper data conversion. Transformation logic in the form of Python expressions is stored here, allowing complex value derivations to be preserved and reused. Primary key definitions, including composite keys with sequence numbers, are maintained in this table, as are audit column settings that determine which columns should be automatically populated with audit information.

Execution history is comprehensively tracked in the **DMS_FLUPLD_RUN** table, which records every execution attempt for each file upload configuration. Each execution record includes precise timestamps for start and end times, allowing performance analysis and troubleshooting. Row counts are meticulously tracked, showing how many rows were processed, how many succeeded, and how many failed, providing immediate visibility into data quality and processing success rates. Status information indicates whether executions completed successfully, failed completely, or completed partially with some errors. The load mode used for each execution is also recorded, providing context for understanding how data was loaded.

When errors occur during processing, they are logged in detail in the **DMS_FLUPLD_ERR** table. This table maintains row-level error information, storing the exact row index where the error occurred, the complete row data in JSON format for later analysis, standardized error codes that can be used for filtering and reporting, and detailed error messages that explain what went wrong. This comprehensive error logging enables data quality teams to identify patterns in data issues and work with source systems to improve data quality over time.

Scheduling information is managed in the **DMS_FLUPLD_SCHD** table, which stores frequency codes (daily, weekly, monthly, etc.), time parameters that specify exactly when executions should occur, calculated next run dates, and the last execution date. The table also maintains schedule status, allowing schedules to be temporarily paused without losing their configuration.

---

## 5. Supported File Formats

The File Management Utility supports a comprehensive range of file formats, each with specialized parsing capabilities designed to handle the unique characteristics and challenges of different data formats. This multi-format support ensures that organizations can import data from virtually any source system, regardless of how that system exports its data.

### 5.1 CSV Files

CSV (Comma-Separated Values) files are perhaps the most common format for data exchange, and the utility provides robust support for this format with extensions `.csv`, `.tsv` (tab-separated), and `.txt` (text files that may contain delimited data). The CSV parser employs intelligent delimiter detection algorithms that automatically identify whether files use commas, tabs, semicolons, or other delimiters, eliminating the need for users to manually specify these details.

The parser handles header rows intelligently, recognizing when the first row contains column names versus data, and can be configured to skip multiple header rows when files contain metadata or formatting information above the actual data. Similarly, footer rows containing summary information or totals can be automatically skipped. The parser also handles various quote character conventions, properly interpreting files that use single quotes, double quotes, or no quotes at all, and correctly processes escaped quotes within quoted fields.

Encoding detection is another critical feature, as CSV files may be created with various character encodings (UTF-8, Windows-1252, ISO-8859-1, etc.). The parser attempts to automatically detect the encoding, ensuring that special characters and international text are correctly interpreted.

### 5.2 Excel Files

Excel file support encompasses both modern `.xlsx` format and legacy `.xls` format, ensuring compatibility with files created across different versions of Microsoft Excel and other spreadsheet applications. The parser provides full multi-sheet support, allowing users to select which worksheet within a workbook should be processed, which is essential when workbooks contain multiple data tables or when only specific sheets contain relevant data.

The parser preserves data types as much as possible, maintaining numeric values as numbers rather than converting them to strings, and preserving date formats. Header row configuration allows users to specify which row contains column names, accommodating files that have multiple header rows or formatting above the data section.

### 5.3 JSON Files

JSON (JavaScript Object Notation) has become increasingly popular for data exchange, particularly in web-based systems and APIs. The utility's JSON parser handles both flat JSON structures, where data is presented as simple arrays of objects, and nested JSON structures that require flattening to fit into relational database tables.

The parser can extract data from nested objects and arrays, flattening hierarchical structures into tabular format. For example, a JSON object containing customer information with nested address objects can be flattened so that address fields become columns at the same level as customer fields. Array handling allows the parser to process JSON arrays, treating each array element as a row of data. Custom JSON path extraction capabilities enable users to specify exactly which parts of complex JSON structures should be extracted, providing flexibility for handling diverse JSON formats.

### 5.4 Parquet Files

Parquet is a columnar storage format that has gained popularity in big data environments due to its efficiency and compression capabilities. Files with extensions `.parquet` and `.parq` are supported, providing access to data exported from systems like Apache Spark, Hadoop, and various data lake platforms.

The parser automatically detects the schema embedded within Parquet files, extracting column names and data types without requiring user configuration. Columnar reading capabilities allow the parser to efficiently process large files by reading only the columns that are needed, rather than loading entire rows into memory. This makes Parquet particularly efficient for very large files, as the format's inherent structure aligns well with database table structures. Type preservation ensures that data types defined in Parquet files are maintained through the import process.

### 5.5 XML Files

XML (eXtensible Markup Language) remains common in enterprise systems, particularly for B2B data exchange and integration with legacy systems. The XML parser provides XPath support, allowing users to specify exactly which elements and attributes should be extracted from complex XML documents.

Nested structure handling is crucial for XML, as the hierarchical nature of XML doesn't naturally map to flat database tables. The parser can flatten nested structures, extracting data from parent and child elements into a single row. Attribute extraction capabilities allow the parser to retrieve data from XML attributes as well as element content, providing comprehensive data access. Namespace support ensures that XML documents using namespaces are correctly parsed, preventing issues with element identification.

### 5.6 PDF Files

PDF files present unique challenges, as they are primarily designed for presentation rather than data extraction. The PDF parser employs table extraction algorithms that identify and extract tabular data from PDF documents, which is particularly useful when dealing with reports or statements that contain structured data.

Text parsing capabilities allow the parser to extract and process text content from PDFs, though this requires more manual configuration as PDF text layout may not be as structured as other formats. Multi-page support ensures that data spanning multiple pages can be extracted and combined into a single dataset.

### 5.7 Google Sheets

Google Sheets integration provides direct access to data stored in Google's cloud-based spreadsheet platform. Files with the `.gsheet` extension trigger OAuth authentication flows that securely connect to Google accounts, ensuring that only authorized users can access spreadsheet data.

The parser allows users to select which specific sheet within a Google Sheets workbook should be processed, similar to Excel file handling. Real-time data access means that the parser retrieves the current state of the spreadsheet at the time of execution, ensuring that scheduled imports always work with the latest data.

---

## 6. Key Features

The File Management Utility incorporates a comprehensive set of features designed to make file-based data imports as efficient, reliable, and user-friendly as possible. These features work together to provide a complete solution that addresses both technical requirements and business needs.

### 6.1 File Upload & Preview

The file upload interface provides multiple methods for users to provide files to the system. Drag-and-drop functionality allows users to simply drag files from their file system directly into the browser interface, while traditional file browser selection provides a familiar alternative. Both methods support single file uploads, with the system handling file validation and security checks immediately upon selection.

Automatic file type detection eliminates the need for users to manually specify file formats. The system analyzes file extensions and content headers to determine the appropriate parser, reducing configuration errors and streamlining the upload process. Once a file is uploaded, the system immediately begins parsing it to extract column information and prepare a preview.

The preview functionality is optimized for performance, reading only the first N rows of data (configurable between 10 and 200 rows, with a default that balances information with speed). This preview allows users to verify that the file was parsed correctly, that column names are accurate, and that data appears in the expected format before committing to the full import configuration. Column auto-detection analyzes the preview data to suggest appropriate data types and identify potential issues such as missing values or format inconsistencies.

File metadata extraction provides users with important information about uploaded files, including file size (helping identify unusually large files that may require special handling), detected file type (allowing verification that the correct parser was selected), and character encoding (critical for ensuring special characters are correctly interpreted). This metadata is displayed to users and stored in the database for reference.

### 6.2 Column Mapping

The column mapping system provides a flexible interface for defining how source columns from files map to target columns in database tables. Users can create one-to-one mappings where source columns map directly to target columns with the same names, or they can create more complex mappings where source columns are transformed, combined, or derived before being loaded into target columns.

Data type mapping leverages the DMS parameter mapping system (DMS_PARAMS), which maintains a comprehensive catalog of data types and their translations across different database platforms. This ensures that when a user specifies a data type, it is correctly translated for the target database—for example, a VARCHAR type in the mapping might become VARCHAR2 in Oracle or VARCHAR in PostgreSQL, automatically handled by the system.

Primary key definition allows users to specify which columns (or combinations of columns) serve as primary keys in target tables. The system supports composite primary keys, where multiple columns together form a unique identifier, and automatically assigns sequence numbers to primary key components to ensure proper ordering.

Derivation logic enables users to write Python expressions that compute target column values from source data. These expressions can reference other columns, perform mathematical operations, concatenate strings, apply conditional logic, and call built-in functions. For example, a user might define a full name column as `first_name + ' ' + last_name`, or calculate a total as `quantity * unit_price`.

Default values can be specified for columns, ensuring that if source data is missing or null, appropriate default values are used instead. Required field validation ensures that columns marked as required must have values (either from source data or defaults), preventing incomplete data from being loaded.

The system automatically adds standard audit columns (CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE) to every table, ensuring consistent audit trails without requiring users to manually configure these columns.

### 6.3 Data Transformation

Data transformation capabilities allow users to modify, combine, and derive data as it moves from source files to target tables. Formula evaluation executes Python expressions for each row of data, providing powerful computational capabilities. Column concatenation allows multiple source columns to be combined into single target columns, useful for creating full names from first and last names, or combining address components into full addresses.

Data type conversion is handled automatically based on column definitions, but users can also specify explicit conversions in derivation logic when needed. Value derivation enables complex calculations and business logic to be applied during the import process, such as calculating discounts, applying tax rates, or computing derived metrics.

Lookup operations allow the system to reference data from other tables during the import process, enabling foreign key resolution and data enrichment. Conditional logic in derivation expressions allows different values to be computed based on conditions, such as applying different tax rates based on customer location or calculating different commission rates based on sales amounts.

### 6.4 Execution Modes

The system provides three distinct execution modes, each designed for different data loading scenarios. INSERT Mode simply appends new rows to existing tables, making it ideal for incremental data loads where historical data should be preserved and new data is simply added. This mode is commonly used for fact tables in data warehouses, where each import adds new transaction records without modifying existing ones.

TRUNCATE_LOAD Mode provides a complete refresh capability, clearing the target table before loading new data. This ensures that the table contains exactly the data from the current file, with no remnants from previous imports. This mode is particularly useful for dimension tables that need to be completely refreshed periodically, or for scenarios where the source file represents the complete current state of data.

UPSERT Mode provides the most sophisticated capability, performing intelligent insert and update operations based on primary key matching. When a row's primary key matches an existing row in the target table, the row is updated with new values. When no match is found, a new row is inserted. This mode enables true incremental updates, where files contain both new records and updates to existing records, and the system automatically determines which operation to perform for each row.

### 6.5 Scheduling

The scheduling system enables automated file processing, eliminating the need for manual intervention in regular data import processes. Frequency codes provide a simple way to specify how often files should be processed: `DL` for daily, `WK` for weekly, `MN` for monthly, `HY` for half-yearly, `YR` for yearly, and `ID` for on-demand execution.

Time parameters allow users to specify exactly when scheduled executions should occur, such as "10:30 AM" for daily schedules, or "MON_10:30" for weekly schedules that run every Monday at 10:30 AM. This precision ensures that data imports occur at optimal times, perhaps during off-peak hours to minimize impact on system performance, or at specific times when source files are guaranteed to be available.

Start and end dates define validity periods for schedules, allowing temporary schedules to be created for specific projects or time-bound data migrations. The system automatically calculates next run dates based on frequency codes and time parameters, ensuring that schedules are maintained accurately even when executions are delayed or skipped.

### 6.6 Error Handling

Comprehensive error handling ensures that data quality issues don't prevent successful imports, while providing detailed information for troubleshooting and data quality improvement. Row-level error tracking means that when individual rows fail validation or constraint checks, those specific rows are logged as errors while processing continues for valid rows. This maximizes data throughput and allows users to address data quality issues without blocking entire imports.

Error codes provide standardized categorization of errors, enabling filtering and reporting on specific types of issues. Error messages provide detailed explanations of what went wrong, helping users understand and correct problems. Failed row data is preserved in JSON format, allowing users to examine exactly what data caused errors and make corrections either in source files or through data quality processes.

Error reporting and filtering capabilities allow users to query error logs by file upload reference, execution run, error code, or search terms in error messages. This enables efficient troubleshooting and helps identify patterns in data quality issues. While automatic retry mechanisms are not currently implemented, the system's error logging provides all information needed for manual retry after data corrections.

### 6.7 Audit & History

Complete audit trails ensure that every file processing operation is fully documented and traceable. Execution history maintains records of all runs for each file upload configuration, regardless of success or failure. This history provides a complete picture of data import activities over time, enabling compliance reporting and operational analysis.

Row counts are meticulously tracked for each execution, showing exactly how many rows were processed, how many succeeded, and how many failed. These counts provide immediate visibility into data quality and processing success rates, and can be used to identify trends or anomalies in data imports.

Execution timestamps record precise start and end times for each run, enabling performance analysis and helping identify slow-running imports that may need optimization. Duration calculations help users understand processing times and plan for resource allocation.

User tracking maintains records of who created and updated each configuration, and who triggered each execution. This accountability is essential for compliance and helps organizations understand who is responsible for data import processes. Status tracking categorizes each execution as SUCCESS (all rows processed successfully), FAILED (execution encountered critical errors), or PARTIAL (some rows succeeded while others failed), providing immediate visibility into execution outcomes.

---

## 7. Architecture

### 7.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Upload Form  │  │ Upload Table │  │ Column Mapper│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │                 │                  │
          │  HTTP/REST API  │                  │
          │                 │                  │
┌─────────▼─────────────────▼──────────────────▼──────────────┐
│              FastAPI Backend (Python)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         File Upload Router                            │   │
│  │  (fastapi_file_upload.py)                             │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼──────────────┐                           │
│  │   File Parser Manager        │                           │
│  │   - CSV Parser               │                           │
│  │   - Excel Parser             │                           │
│  │   - JSON Parser              │                           │
│  │   - Parquet Parser           │                           │
│  │   - XML Parser               │                           │
│  └──────────────┬───────────────┘                           │
│                 │                                            │
│  ┌──────────────▼──────────────┐                           │
│  │   File Upload Executor       │                           │
│  │   - Configuration Loading     │                           │
│  │   - File Parsing              │                           │
│  │   - Transformation            │                           │
│  │   - Table Creation            │                           │
│  │   - Data Loading              │                           │
│  └──────────────┬───────────────┘                           │
│                 │                                            │
│  ┌──────────────▼──────────────┐                           │
│  │   Data Loader                │                           │
│  │   - Batch Processing          │                           │
│  │   - Transaction Management   │                           │
│  │   - Error Logging            │                           │
│  └──────────────┬───────────────┘                           │
└─────────────────┼───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌─────▼─────┐  ┌───▼────┐
│Filesys│   │ Metadata  │  │ Target │
│Storage│   │ Database  │  │Database│
└───────┘   └────────────┘  └────────┘
```

### 7.2 Data Flow

```
1. User Uploads File
   ↓
2. File Saved to Filesystem (temp location)
   ↓
3. File Parsed (File Parser Manager)
   ↓
4. Preview Generated (first N rows)
   ↓
5. User Configures:
   - File reference & description
   - Target connection & table
   - Column mappings
   - Transformations
   - Schedule (optional)
   ↓
6. Configuration Saved to Database
   ↓
7. User Triggers Execution (or scheduled)
   ↓
8. File Upload Executor:
   - Loads configuration
   - Parses file
   - Applies transformations
   - Creates table (if needed)
   - Loads data in batches
   ↓
9. Execution History Saved
   ↓
10. Errors Logged (if any)
   ↓
11. Results Available for Review
```

---

## 8. Workflow

Understanding the workflow of the File Management Utility is essential for effective use. The system follows logical, sequential processes that guide users from initial file upload through configuration, execution, and monitoring.

### 8.1 Upload & Configure Workflow

The upload and configuration workflow begins when users navigate to the File Upload Module from the DMS home page, where it appears in the "File Management" section alongside other file-related tools. This centralized location makes the utility easily accessible to users who need to import data.

Once in the module, users initiate the upload process by clicking the "New Upload" or "Upload File" button, which opens a file selection dialog. Users can either browse their local file system or use drag-and-drop functionality to select files. The system immediately begins processing the file upon selection, uploading it to the server and initiating automatic parsing.

During the upload process, the system performs initial validation, checking file size limits, verifying file type compatibility, and scanning for potential security issues. Once validation passes, the file is stored temporarily on the server, and parsing begins automatically. The parser detects the file format, extracts column information, and prepares a preview of the data.

Users are then presented with a preview showing the first N rows of data (configurable, typically 10-200 rows). This preview serves multiple purposes: it allows users to verify that the file was parsed correctly, confirms that column names are accurate, provides a sample of the data quality, and helps users understand the data structure before committing to configuration. Users can examine the preview to identify any issues with file formatting, data quality, or structure that might need attention before proceeding.

The configuration phase requires users to provide essential information about the file upload. Basic information includes a unique file reference identifier that will be used to identify this configuration in the system, a descriptive name that helps users understand the purpose of the upload, the original filename (automatically populated from the upload), and the detected file type (also auto-populated but can be overridden if needed).

Target configuration specifies where the data should be loaded: users select a target database connection from available connections, specify the target schema (database namespace), and provide the target table name. The truncate flag allows users to indicate whether the target table should be cleared before loading new data, which is important for complete refresh scenarios versus incremental loads.

File options provide fine-grained control over how files are parsed. Header row count specifies how many rows at the beginning of the file should be skipped (useful when files contain metadata or formatting above the data). Footer row count similarly allows skipping rows at the end of files that may contain summary information. Header and footer patterns can be specified for more sophisticated detection of non-data rows. Batch size configuration allows users to optimize performance by specifying how many rows should be processed in each database transaction.

Column mapping is the most detailed configuration step, requiring users to define how each source column maps to target columns. The system provides an intuitive interface showing source columns on one side and target columns on the other, with drag-and-drop or selection mechanisms for creating mappings. For each mapping, users specify the target data type, indicate whether the column is part of the primary key, define any derivation logic needed, specify default values for missing data, and mark columns as required when appropriate.

Once all configuration is complete, users save the configuration, which stores all information in the database. The system validates the configuration at this point, checking for required fields, verifying data type compatibility, and ensuring that primary key definitions are valid. Upon successful save, the configuration is ready for execution, either immediately or on a schedule.

### 8.2 Execution Workflow

Execution can be triggered in two ways: manually by users clicking an "Execute" button, or automatically by the scheduler based on configured schedules. Manual execution provides immediate control and is useful for ad-hoc imports or testing configurations. Scheduled execution enables automation for regular data imports.

When execution is triggered, the system creates a job request and adds it to the `DMS_PRCREQ` table, which serves as the job queue for the DMS scheduler. The job status progresses through states: NEW (initial creation), QUEUED (waiting for processing resources), and PROCESSING (actively being executed). This status progression allows users and administrators to monitor job progress and understand where jobs are in the execution pipeline.

During the file processing phase, the File Upload Executor loads the complete configuration from the database, including all column mappings, transformation rules, and target database connection details. It then locates and parses the source file using the appropriate parser for the file type. The parser converts the file data into a structured format that can be processed row by row.

Transformations are applied to each row as it is processed. Derivation logic is evaluated, default values are applied where needed, and data type conversions occur. If the target table does not exist, the Table Creator component generates and executes DDL statements to create the table with the appropriate structure, including all columns, data types, constraints, and primary keys.

Data loading occurs in batches, with the Data Loader processing rows in configurable batch sizes (typically 1000 rows per batch). This batch processing balances performance with transaction management, ensuring that either entire batches succeed or fail together, maintaining data consistency. Within each batch, individual row errors are captured and logged without stopping the batch processing.

Execution tracking provides real-time visibility into the processing progress. The system updates row counts as processing proceeds, showing how many rows have been processed, how many have succeeded, and how many have failed. This real-time feedback helps users understand progress and estimate completion times. Errors are logged immediately as they occur, with detailed information captured for later analysis.

Upon completion, the execution is marked with a final status: DONE indicates successful completion with all rows processed successfully, FAILED indicates that critical errors prevented completion, and PARTIAL indicates that some rows succeeded while others failed. Execution history is saved to the database, including all timestamps, row counts, status information, and any messages generated during processing. Results are immediately available for review, allowing users to examine execution outcomes, view error details, and verify that data was loaded correctly.

### 8.3 Monitoring Workflow

The monitoring workflow enables users and administrators to track file upload activities, analyze execution results, and troubleshoot issues. The Upload History view provides a comprehensive list of all file upload configurations in the system, showing key information such as file references, descriptions, target tables, status, and last execution dates.

Filtering capabilities allow users to narrow the list based on various criteria: status (active or inactive), file type, target connection, creation date, or last execution date. This filtering helps users quickly locate specific configurations or identify configurations that haven't been executed recently. Each configuration in the list provides access to detailed views showing complete configuration information and execution history.

The execution runs view provides detailed information about all execution attempts for a specific file upload configuration. Users can see a chronological list of all runs, with each entry showing the execution timestamp, status, row counts (processed, successful, failed), execution duration, and any messages generated. This history enables users to track execution patterns, identify trends in success or failure rates, and understand how execution performance has changed over time.

Error checking capabilities allow users to drill down into execution failures to understand what went wrong. Error details show the specific rows that failed, the error codes and messages associated with each failure, and the actual row data that caused the error (preserved in JSON format). Filtering by error code helps identify patterns, such as multiple rows failing for the same reason, which might indicate systematic data quality issues. Search functionality allows users to find specific error messages or search for particular data values that caused errors. Error data can be downloaded for further analysis in external tools, enabling data quality teams to work with source systems to improve data quality.

---

## 9. Database Schema

### 9.1 Main Tables

#### DMS_FLUPLD (File Upload Definition)

| Column | Type | Description |
|--------|------|-------------|
| `flupldid` | INTEGER | Primary key |
| `flupldref` | VARCHAR(100) | Unique reference identifier |
| `fluplddesc` | VARCHAR(500) | Description |
| `flnm` | VARCHAR(500) | File name |
| `flpth` | VARCHAR(1000) | File path |
| `fltyp` | VARCHAR(50) | File type (CSV, XLSX, etc.) |
| `trgconid` | INTEGER | Target connection ID |
| `trgschm` | VARCHAR(100) | Target schema |
| `trgtblnm` | VARCHAR(100) | Target table name |
| `trnctflg` | CHAR(1) | Truncate flag (Y/N) |
| `hdrrwcnt` | INTEGER | Header row count |
| `ftrrwcnt` | INTEGER | Footer row count |
| `hdrrwpttrn` | VARCHAR(200) | Header row pattern |
| `ftrrwpttrn` | VARCHAR(200) | Footer row pattern |
| `frqcd` | VARCHAR(10) | Frequency code |
| `stflg` | CHAR(1) | Status flag (A=Active, N=Inactive) |
| `batch_size` | INTEGER | Batch size for loading |
| `crtdby` | VARCHAR(100) | Created by |
| `crtdt` | TIMESTAMP | Created date |
| `uptdby` | VARCHAR(100) | Updated by |
| `uptdt` | TIMESTAMP | Updated date |
| `lstrundt` | TIMESTAMP | Last run date |
| `nxtrundt` | TIMESTAMP | Next run date |
| `curflg` | CHAR(1) | Current flag (Y/N) |

#### DMS_FLUPLDDTL (Column Mappings)

| Column | Type | Description |
|--------|------|-------------|
| `fluplddtlid` | INTEGER | Primary key |
| `flupldref` | VARCHAR(100) | Reference to DMS_FLUPLD |
| `srcclnm` | VARCHAR(100) | Source column name |
| `trgclnm` | VARCHAR(100) | Target column name |
| `trgcldtyp` | VARCHAR(50) | Target column data type |
| `trgkyflg` | CHAR(1) | Primary key flag (Y/N) |
| `trgkyseq` | INTEGER | Primary key sequence |
| `trgcldesc` | VARCHAR(500) | Column description |
| `drvlgc` | TEXT/CLOB | Derivation logic |
| `drvlgcflg` | CHAR(1) | Logic verified flag |
| `excseq` | INTEGER | Execution sequence |
| `isaudit` | CHAR(1) | Is audit column (Y/N) |
| `audttyp` | VARCHAR(20) | Audit type |
| `dfltval` | VARCHAR(500) | Default value |
| `isrqrd` | CHAR(1) | Is required (Y/N) |
| `curflg` | CHAR(1) | Current flag |

#### DMS_FLUPLD_RUN (Execution History)

| Column | Type | Description |
|--------|------|-------------|
| `runid` | INTEGER | Primary key |
| `flupldref` | VARCHAR(100) | File upload reference |
| `strttm` | TIMESTAMP | Start time |
| `ndtm` | TIMESTAMP | End time |
| `rwsprcssd` | INTEGER | Rows processed |
| `rwsstccssfl` | INTEGER | Rows successful |
| `rwsfld` | INTEGER | Rows failed |
| `stts` | VARCHAR(20) | Status (SUCCESS, FAILED, PARTIAL) |
| `mssg` | TEXT/CLOB | Message |
| `ldmde` | VARCHAR(20) | Load mode (INSERT, TRUNCATE_LOAD, UPSERT) |
| `flpth` | VARCHAR(1000) | File path used |

#### DMS_FLUPLD_ERR (Error Log)

| Column | Type | Description |
|--------|------|-------------|
| `errid` | INTEGER | Primary key |
| `flupldref` | VARCHAR(100) | File upload reference |
| `runid` | INTEGER | Execution run ID |
| `rwndx` | INTEGER | Row index |
| `rwdtjsn` | JSON/CLOB | Row data (JSON format) |
| `rrcd` | VARCHAR(50) | Error code |
| `rrmssg` | TEXT/CLOB | Error message |
| `crtdby` | VARCHAR(100) | Created by |
| `crtdt` | TIMESTAMP | Created date |

#### DMS_FLUPLD_SCHD (Schedule)

| Column | Type | Description |
|--------|------|-------------|
| `schdid` | INTEGER | Primary key |
| `flupldref` | VARCHAR(100) | File upload reference |
| `frqncy` | VARCHAR(10) | Frequency code |
| `tm_prm` | VARCHAR(100) | Time parameter |
| `nxt_run_dt` | TIMESTAMP | Next run date |
| `lst_run_dt` | TIMESTAMP | Last run date |
| `stts` | VARCHAR(20) | Status (ACTIVE, PAUSED) |
| `curflg` | CHAR(1) | Current flag |

---

## 10. API Endpoints

### 10.1 File Upload Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/file-upload/upload-file` | Upload and parse file |
| `GET` | `/file-upload/get-all-uploads` | List all configurations |
| `GET` | `/file-upload/get-by-reference/{flupldref}` | Get configuration by reference |
| `GET` | `/file-upload/get-columns/{flupldref}` | Get column mappings |
| `GET` | `/file-upload/preview-file` | Preview file contents |
| `POST` | `/file-upload/save` | Save/update configuration |
| `POST` | `/file-upload/delete` | Delete configuration |
| `POST` | `/file-upload/activate-deactivate` | Activate/deactivate |

### 10.2 Execution Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/file-upload/execute` | Queue file upload for execution |
| `GET` | `/file-upload/execute-status/{request_id}` | Get execution status |
| `GET` | `/file-upload/active-jobs` | Get all active jobs |
| `POST` | `/file-upload/cancel-job/{request_id}` | Cancel a job |

### 10.3 History & Monitoring Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/file-upload/runs` | Get execution history (with filters) |
| `GET` | `/file-upload/errors/{flupldref}` | Get error details |
| `GET` | `/file-upload/check-table-exists/{flupldref}` | Check if target table exists |

### 10.4 Schedule Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/file-upload/schedules` | Create/update schedule |
| `GET` | `/file-upload/schedules/{flupldref}` | Get schedules for upload |

### 10.5 Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/file-upload/get-connections` | Get available database connections |

---

## 11. Security & Validation

### 11.1 File Validation

**Client-Side:**
- File type validation (whitelist)
- File size limits
- File name sanitization
- Preview before upload

**Server-Side:**
- Content-Type verification
- Magic number validation (file headers)
- File size limits enforcement
- Filename sanitization
- Path traversal prevention

### 11.2 Data Validation

- **Data Type Validation**: Enforced based on column definitions
- **Required Field Validation**: Checks for required fields
- **Primary Key Validation**: Ensures uniqueness
- **Constraint Validation**: Database-level constraints

### 11.3 Access Control

- **User Permissions**: Module-level access control
- **Role-Based Access**: Role-based file upload permissions
- **Audit Logging**: All operations logged with user information

### 11.4 Error Handling

- **Row-Level Errors**: Individual row errors don't stop entire process
- **Transaction Management**: Rollback on critical errors
- **Error Isolation**: Failed rows logged separately
- **Error Reporting**: Detailed error messages and codes

---

## 12. Integration with DMS

### 12.1 Database Connections

The File Management Utility integrates with the DMS database connection system:
- Uses `DMS_DBCONDTLS` for target database connections
- Supports multiple database platforms (PostgreSQL, Oracle, MySQL, etc.)
- Automatic SQL dialect handling

### 12.2 Parameter Mapping

Uses the DMS parameter mapping system (`DMS_PARAMS`):
- Data type mapping
- Database-specific type conversions
- Consistent with Mapper module

### 12.3 Job Scheduler

Integrates with DMS job scheduler:
- Uses `DMS_PRCREQ` for job queuing
- Background processing
- Status tracking
- Progress monitoring

### 12.4 Audit System

Follows DMS audit standards:
- Standard audit columns (CRTDBY, CRTDDT, UPDTBY, UPDTDT)
- Automatic audit column population
- User tracking

### 12.5 User Interface

Integrated into DMS home page:
- "File Management" section
- "File Upload" card
- "Upload History" card
- Consistent UI/UX with other modules

---

## 13. Best Practices

Adopting best practices when using the File Management Utility ensures optimal performance, data quality, and maintainability. These practices have been developed through experience with various use cases and help organizations maximize the value they derive from the system.

### 13.1 File Naming

Effective file naming conventions significantly improve the usability and maintainability of file upload configurations. File references should be descriptive and meaningful, clearly indicating the purpose and content of the upload. For example, "CUSTOMER_DAILY_IMPORT" is much more informative than "UPLOAD_001". Including date/time information in file names for scheduled uploads helps users quickly identify which file was processed on which date, which is particularly valuable when troubleshooting issues or reviewing historical data.

Avoiding special characters in file references prevents potential issues with database queries, URL encoding, and system compatibility. Stick to alphanumeric characters and underscores for maximum compatibility. Consistent naming conventions across an organization make it easier for multiple users to understand and work with file upload configurations.

### 13.2 Column Mapping

Comprehensive column mapping is essential for successful data imports. Ensure that all required columns are mapped, as missing required columns will cause row-level errors during processing. Primary key definitions must be accurate, as they determine how UPSERT operations identify existing rows and how database constraints are enforced. Incorrect primary key definitions can lead to duplicate key errors or failed updates.

Data type selection should match the actual data being imported, but also consider the target database platform's specific requirements. The system's data type mapping helps with this, but users should verify that selected types are appropriate for their data. Derivation logic should be thoroughly tested before production use, as errors in derivation logic can cause widespread data quality issues. Test with sample data that represents the full range of possible values to ensure logic handles edge cases correctly.

### 13.3 Performance

Performance optimization requires balancing multiple factors. Batch sizes should be tuned based on row size and database performance characteristics. The default of 1000 rows works well for most scenarios, but smaller batches may be needed for very wide tables with many columns, while larger batches may improve performance for narrow tables. Monitor execution times and adjust batch sizes accordingly.

For very large files (exceeding several gigabytes), consider using the streaming parser when available, as it processes files incrementally rather than loading entire files into memory. This prevents memory exhaustion and allows processing of files that might otherwise be too large to handle. Monitor execution times regularly to identify performance regressions or opportunities for optimization. Transformation logic should be kept as simple as possible, as complex transformations can significantly impact processing time.

### 13.4 Error Handling

Proactive error management improves data quality over time. Regularly reviewing error logs helps identify patterns in data quality issues, enabling organizations to work with source systems to improve data at its origin. Addressing root causes of data quality issues is more effective than repeatedly handling the same errors.

Fixing data quality issues at the source prevents recurring problems and reduces the need for manual intervention. Use appropriate load modes for different scenarios: INSERT for incremental loads, TRUNCATE_LOAD for complete refreshes, and UPSERT for updates. Testing with sample data before full production runs helps identify configuration issues early, when they are easier to correct.

### 13.5 Scheduling

Effective scheduling ensures data imports occur at optimal times without disrupting system operations. Set appropriate frequencies that match business requirements—daily for operational data, weekly for summary data, monthly for reporting data. Use time parameters to schedule executions during off-peak hours when system resources are more available and source systems are less likely to be under heavy load.

Regular monitoring of scheduled executions helps identify issues early, such as source files that are consistently late or missing, or executions that are taking longer than expected. Setting start and end dates for temporary schedules ensures that one-time imports or project-specific configurations don't continue running indefinitely after they are no longer needed.

---

## 14. Troubleshooting

Effective troubleshooting requires a systematic approach to identifying and resolving issues. The File Management Utility provides comprehensive error logging and diagnostic information to help users quickly identify and resolve problems.

### Common Issues

**File Upload Fails:** When file uploads fail, the first step is to verify that the file size is within system limits. Very large files may exceed configured maximum sizes, requiring either file size limit adjustments or file splitting. Verify that the file format is supported by checking the file extension and ensuring the file content matches the expected format. File encoding issues can cause upload failures or parsing problems, particularly with international characters. If encoding issues are suspected, try converting the file to UTF-8 encoding before upload.

**Parsing Errors:** Parsing errors typically indicate that file structure doesn't match the expected format. For CSV files, verify that delimiter settings are correct—files may use commas, tabs, semicolons, or other delimiters, and incorrect delimiter detection can cause parsing failures. Check for inconsistent quote characters or malformed rows that might confuse the parser. For Excel files, verify that the specified sheet name exists and contains data in the expected format. Check for merged cells, empty rows, or formatting that might interfere with parsing.

**Column Mapping Issues:** Column mapping problems often manifest as data type errors or missing value errors during execution. Ensure that all required columns are mapped, as unmapped required columns will cause row-level errors. Verify that data types match the actual data being imported—for example, attempting to import text into a numeric column will fail. Check derivation logic syntax carefully, as syntax errors in Python expressions will prevent processing. Test derivation logic with sample data to identify issues before full execution.

**Execution Failures:** When executions fail completely (rather than partially), check the target database connection to ensure it is active and accessible. Verify that the database user has appropriate permissions to create tables (if needed) and insert/update data. Review error logs for specific error messages that indicate the root cause—common issues include permission problems, disk space exhaustion, or database constraint violations. Check primary key constraints to ensure that imported data doesn't violate uniqueness requirements.

**Performance Issues:** Performance problems can stem from multiple sources. For large files, reducing batch size may help by reducing memory usage and transaction overhead, though this may increase total processing time. Complex transformation logic can significantly slow processing—review and optimize derivation expressions to minimize computational overhead. Database performance issues, such as missing indexes or table locks, can slow data loading—work with database administrators to optimize target tables. For very large files, consider using streaming parsers when available, as they process data incrementally rather than loading entire files into memory.

---

## 15. Future Enhancements

### Planned Features

- **Streaming Parser**: For very large files (>1GB)
- **Incremental Loads**: Load only changed data
- **Data Quality Rules**: Custom validation rules
- **File Versioning**: Track file versions
- **Compression Support**: Handle compressed files
- **Cloud Storage Integration**: Direct upload from S3, Azure, etc.
- **Real-time Processing**: Stream processing capabilities
- **Advanced Transformations**: More transformation functions

---

## 16. Conclusion

The DMS File Management Utility provides a robust, flexible, and user-friendly solution for file-based data imports. With support for multiple file formats, intelligent parsing, flexible column mapping, and comprehensive error handling, it enables efficient data loading workflows while maintaining data quality and auditability.

The system is designed to scale with your needs, from small ad-hoc uploads to large scheduled batch processes, and integrates seamlessly with the broader DMS ecosystem.

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Production Ready ✅
