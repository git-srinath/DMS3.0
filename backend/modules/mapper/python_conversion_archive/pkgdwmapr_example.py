"""
Example usage of PKGDMS_MAPR Python module

This file demonstrates how to use the PKGDMS_MAPR module to:
1. Create SQL mappings
2. Create and manage mappings
3. Add mapping details
4. Validate mappings
5. Activate/deactivate mappings
6. Delete mappings

Note: This is for demonstration purposes. Adjust connection parameters for your environment.
"""

import os
import sys
import oracledb
from datetime import datetime
from modules.mapper.pkgdms_mapr import (
    PKGDMS_MAPR,
    PKGDMS_MAPRError,
    create_update_mapping_with_user,
    create_update_mapping_detail_with_user,
    validate_mapping_details_with_user,
    activate_deactivate_mapping_with_user
)


def example_1_basic_usage():
    """Example 1: Basic mapping creation and management"""
    print("=" * 80)
    print("Example 1: Basic Mapping Creation")
    print("=" * 80)
    
    # Create database connection (adjust parameters for your environment)
    connection = oracledb.connect(
        user=os.getenv('DB_USER', 'dw_user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        dsn=os.getenv('DB_DSN', 'localhost:1521/XEPDB1')
    )
    
    try:
        # Initialize PKGDMS_MAPR
        pkg = PKGDMS_MAPR(connection, user='example_user')
        
        # 1. Create a mapping
        print("\n1. Creating mapping...")
        mapid = pkg.create_update_mapping(
            p_mapref='EXAMPLE_CUST_001',
            p_mapdesc='Example Customer Dimension Mapping',
            p_trgschm='DW_SCHEMA',
            p_trgtbtyp='DIM',
            p_trgtbnm='DIM_CUSTOMER',
            p_frqcd='DL',
            p_srcsystm='ERP_SYSTEM',
            p_stflg='N',
            p_blkprcrows=1000
        )
        print(f"✓ Mapping created with ID: {mapid}")
        
        # 2. Add primary key mapping detail
        print("\n2. Adding primary key column...")
        detail1_id = pkg.create_update_mapping_detail(
            p_mapref='EXAMPLE_CUST_001',
            p_trgclnm='CUSTOMER_ID',
            p_trgcldtyp='NUMBER',
            p_trgkeyflg='Y',
            p_trgkeyseq=1,
            p_trgcldesc='Customer unique identifier',
            p_maplogic='SELECT customer_id, customer_id FROM source_customers',
            p_keyclnm='customer_id',
            p_valclnm='customer_id',
            p_mapcmbcd='MAIN',
            p_excseq=1,
            p_scdtyp=1
        )
        print(f"✓ Primary key detail created with ID: {detail1_id}")
        
        # 3. Add more mapping details
        print("\n3. Adding additional columns...")
        detail2_id = pkg.create_update_mapping_detail(
            p_mapref='EXAMPLE_CUST_001',
            p_trgclnm='CUSTOMER_NAME',
            p_trgcldtyp='VARCHAR2',
            p_trgkeyflg='N',
            p_trgkeyseq=None,
            p_trgcldesc='Customer name',
            p_maplogic='SELECT customer_id, customer_name FROM source_customers',
            p_keyclnm='customer_id',
            p_valclnm='customer_name',
            p_mapcmbcd='MAIN',
            p_excseq=1,
            p_scdtyp=2
        )
        print(f"✓ Name column detail created with ID: {detail2_id}")
        
        detail3_id = pkg.create_update_mapping_detail(
            p_mapref='EXAMPLE_CUST_001',
            p_trgclnm='EMAIL',
            p_trgcldtyp='VARCHAR2',
            p_trgkeyflg='N',
            p_trgkeyseq=None,
            p_trgcldesc='Customer email',
            p_maplogic='SELECT customer_id, email FROM source_customers',
            p_keyclnm='customer_id',
            p_valclnm='email',
            p_mapcmbcd='MAIN',
            p_excseq=1,
            p_scdtyp=2
        )
        print(f"✓ Email column detail created with ID: {detail3_id}")
        
        # 4. Validate the mapping
        print("\n4. Validating mapping...")
        valid, error_msg = pkg.validate_mapping_details('EXAMPLE_CUST_001')
        
        if valid == 'Y':
            print("✓ All validations passed!")
        else:
            print(f"✗ Validation errors: {error_msg}")
        
        # 5. Commit changes
        connection.commit()
        print("\n✓ All changes committed successfully!")
        
    except PKGDMS_MAPRError as e:
        print(f"\n✗ PKGDMS_MAPR Error:")
        print(f"  Procedure: {e.proc_name}")
        print(f"  Error Code: {e.error_code}")
        print(f"  Parameters: {e.params}")
        print(f"  Message: {e.message}")
        connection.rollback()
    except Exception as e:
        print(f"\n✗ Unexpected error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()
        print("\nDatabase connection closed.")


def example_2_sql_mapping():
    """Example 2: Using SQL code mappings"""
    print("\n" + "=" * 80)
    print("Example 2: SQL Code Mapping")
    print("=" * 80)
    
    connection = oracledb.connect(
        user=os.getenv('DB_USER', 'dw_user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        dsn=os.getenv('DB_DSN', 'localhost:1521/XEPDB1')
    )
    
    try:
        pkg = PKGDMS_MAPR(connection, user='example_user')
        
        # 1. Create reusable SQL query
        print("\n1. Creating reusable SQL query...")
        sql_code = 'CUSTOMER_BASE_QUERY'
        sql_text = """
            SELECT 
                c.customer_id,
                c.customer_name,
                c.email,
                c.phone,
                a.address_line1,
                a.city,
                a.state,
                a.country
            FROM source_customers c
            LEFT JOIN source_addresses a ON c.customer_id = a.customer_id
            WHERE c.status = 'ACTIVE'
        """
        
        sql_id = pkg.create_update_sql(sql_code, sql_text)
        print(f"✓ SQL query created with ID: {sql_id}, Code: {sql_code}")
        
        # 2. Create mapping that references the SQL code
        print("\n2. Creating mapping with SQL reference...")
        mapid = pkg.create_update_mapping(
            p_mapref='EXAMPLE_CUST_002',
            p_mapdesc='Customer mapping using SQL reference',
            p_trgschm='DW_SCHEMA',
            p_trgtbtyp='DIM',
            p_trgtbnm='DIM_CUSTOMER_FULL',
            p_frqcd='DL',
            p_srcsystm='ERP_SYSTEM',
            p_stflg='N',
            p_blkprcrows=1000
        )
        print(f"✓ Mapping created with ID: {mapid}")
        
        # 3. Add mapping detail using SQL code reference
        print("\n3. Adding column using SQL code reference...")
        detail_id = pkg.create_update_mapping_detail(
            p_mapref='EXAMPLE_CUST_002',
            p_trgclnm='CUSTOMER_ID',
            p_trgcldtyp='NUMBER',
            p_trgkeyflg='Y',
            p_trgkeyseq=1,
            p_trgcldesc='Customer ID',
            p_maplogic=sql_code,  # Reference to SQL code instead of inline SQL
            p_keyclnm='customer_id',
            p_valclnm='customer_id',
            p_mapcmbcd='MAIN',
            p_excseq=1,
            p_scdtyp=1
        )
        print(f"✓ Detail created with ID: {detail_id}")
        
        connection.commit()
        print("\n✓ SQL mapping example completed successfully!")
        
    except PKGDMS_MAPRError as e:
        print(f"\n✗ Error: {e.message}")
        connection.rollback()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()


def example_3_validation():
    """Example 3: Comprehensive validation"""
    print("\n" + "=" * 80)
    print("Example 3: Validation Examples")
    print("=" * 80)
    
    connection = oracledb.connect(
        user=os.getenv('DB_USER', 'dw_user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        dsn=os.getenv('DB_DSN', 'localhost:1521/XEPDB1')
    )
    
    try:
        pkg = PKGDMS_MAPR(connection, user='example_user')
        
        # 1. Validate SQL syntax
        print("\n1. Validating SQL syntax...")
        
        valid_sql = "SELECT customer_id, customer_name FROM customers"
        result = pkg.validate_sql(valid_sql)
        print(f"Valid SQL test: {result}")
        
        invalid_sql = "SELECT * FROM non_existent_table_xyz"
        result = pkg.validate_sql(invalid_sql)
        print(f"Invalid SQL test: {result}")
        
        # 2. Validate mapping logic with error messages
        print("\n2. Validating mapping logic...")
        
        result, error = pkg.validate_logic2(
            p_logic='SELECT customer_id, customer_name FROM customers',
            p_keyclnm='customer_id',
            p_valclnm='customer_name'
        )
        
        if result == 'Y':
            print("✓ Logic validation passed")
        else:
            print(f"✗ Logic validation failed: {error}")
        
        # 3. Validate all mapping details for a reference
        print("\n3. Validating complete mapping...")
        
        # Assuming 'EXAMPLE_CUST_001' exists from example 1
        valid, error_msg = pkg.validate_mapping_details('EXAMPLE_CUST_001')
        
        if valid == 'Y':
            print("✓ Mapping validation passed - ready for activation")
        else:
            print(f"✗ Mapping validation failed:\n{error_msg}")
        
        connection.commit()
        
    except PKGDMS_MAPRError as e:
        print(f"\n✗ Error: {e.message}")
        connection.rollback()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()


def example_4_activation():
    """Example 4: Activating and deactivating mappings"""
    print("\n" + "=" * 80)
    print("Example 4: Activation/Deactivation")
    print("=" * 80)
    
    connection = oracledb.connect(
        user=os.getenv('DB_USER', 'dw_user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        dsn=os.getenv('DB_DSN', 'localhost:1521/XEPDB1')
    )
    
    try:
        pkg = PKGDMS_MAPR(connection, user='example_user')
        
        # 1. Activate mapping (automatically validates first)
        print("\n1. Activating mapping...")
        success, message = pkg.activate_deactivate_mapping('EXAMPLE_CUST_001', 'A')
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
        
        # 2. Deactivate mapping
        print("\n2. Deactivating mapping...")
        success, message = pkg.activate_deactivate_mapping('EXAMPLE_CUST_001', 'N')
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
        
        connection.commit()
        
    except PKGDMS_MAPRError as e:
        print(f"\n✗ Error: {e.message}")
        connection.rollback()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()


def example_5_deletion():
    """Example 5: Deleting mappings and details"""
    print("\n" + "=" * 80)
    print("Example 5: Deletion Operations")
    print("=" * 80)
    
    connection = oracledb.connect(
        user=os.getenv('DB_USER', 'dw_user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        dsn=os.getenv('DB_DSN', 'localhost:1521/XEPDB1')
    )
    
    try:
        pkg = PKGDMS_MAPR(connection, user='example_user')
        
        # 1. Delete a specific mapping detail
        print("\n1. Deleting mapping detail...")
        success, message = pkg.delete_mapping_details('EXAMPLE_CUST_001', 'EMAIL')
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
        
        # 2. Delete entire mapping
        print("\n2. Deleting entire mapping...")
        success, message = pkg.delete_mapping('EXAMPLE_CUST_001')
        
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
        
        connection.commit()
        
    except PKGDMS_MAPRError as e:
        print(f"\n✗ Error: {e.message}")
        connection.rollback()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()


def example_6_convenience_functions():
    """Example 6: Using convenience functions with user parameter"""
    print("\n" + "=" * 80)
    print("Example 6: Convenience Functions")
    print("=" * 80)
    
    connection = oracledb.connect(
        user=os.getenv('DB_USER', 'dw_user'),
        password=os.getenv('DB_PASSWORD', 'password'),
        dsn=os.getenv('DB_DSN', 'localhost:1521/XEPDB1')
    )
    
    try:
        # Using convenience functions that include user parameter
        print("\n1. Creating mapping with convenience function...")
        mapid = create_update_mapping_with_user(
            connection=connection,
            p_mapref='EXAMPLE_CUST_003',
            p_mapdesc='Mapping using convenience function',
            p_trgschm='DW_SCHEMA',
            p_trgtbtyp='DIM',
            p_trgtbnm='DIM_CUSTOMER_CONV',
            p_frqcd='DL',
            p_srcsystm='ERP_SYSTEM',
            p_lgvrfyflg=None,
            p_lgvrfydt=None,
            p_stflg='N',
            p_blkprcrows=1000,
            p_user='convenience_user'
        )
        print(f"✓ Mapping created with ID: {mapid}")
        
        print("\n2. Adding detail with convenience function...")
        detail_id = create_update_mapping_detail_with_user(
            connection=connection,
            p_mapref='EXAMPLE_CUST_003',
            p_trgclnm='CUSTOMER_ID',
            p_trgcldtyp='NUMBER',
            p_trgkeyflg='Y',
            p_trgkeyseq=1,
            p_trgcldesc='Customer ID',
            p_maplogic='SELECT customer_id, customer_id FROM customers',
            p_keyclnm='customer_id',
            p_valclnm='customer_id',
            p_mapcmbcd='MAIN',
            p_excseq=1,
            p_scdtyp=1,
            p_lgvrfyflg=None,
            p_lgvrfydt=None,
            p_user='convenience_user'
        )
        print(f"✓ Detail created with ID: {detail_id}")
        
        print("\n3. Validating with convenience function...")
        valid, error = validate_mapping_details_with_user(
            connection=connection,
            p_mapref='EXAMPLE_CUST_003',
            p_user='convenience_user'
        )
        
        if valid == 'Y':
            print("✓ Validation passed")
        else:
            print(f"✗ Validation failed: {error}")
        
        connection.commit()
        print("\n✓ Convenience functions example completed!")
        
    except ValueError as e:
        print(f"\n✗ Error: {str(e)}")
        connection.rollback()
    except PKGDMS_MAPRError as e:
        print(f"\n✗ Error: {e.message}")
        connection.rollback()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        connection.rollback()
    finally:
        connection.close()


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("PKGDMS_MAPR Python Module - Usage Examples")
    print("=" * 80)
    print("\nNote: These examples require a valid Oracle database connection.")
    print("Set environment variables: DB_USER, DB_PASSWORD, DB_DSN")
    print("=" * 80)
    
    try:
        # Run examples
        example_1_basic_usage()
        
        # Uncomment other examples as needed
        # example_2_sql_mapping()
        # example_3_validation()
        # example_4_activation()
        # example_5_deletion()
        # example_6_convenience_functions()
        
        print("\n" + "=" * 80)
        print("All examples completed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

