"""
Python equivalent of PKGDWMAPR PL/SQL Package Body
Package for validating and processing mappings provided.

Change history:
date        who              Remarks
----------- ---------------- ----------------------------------------------------------------------------------------
12-Nov-2025 Python Port      Python conversion of PKGDWMAPR PL/SQL package
"""

import os
import re
import oracledb
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from modules.logger import logger, info, warning, error

# Get Oracle schemas from environment
# DWT_SCHEMA: For metadata (mappings, jobs, SQL queries, parameters)
# CDR_SCHEMA: For actual data tables (to be used during data loading)
DWT_SCHEMA = os.getenv("DWT_SCHEMA", "")
CDR_SCHEMA = os.getenv("CDR_SCHEMA", "")

# Add dot separator if schema is specified
DWT_SCHEMA_PREFIX = f"{DWT_SCHEMA}." if DWT_SCHEMA else ""
CDR_SCHEMA_PREFIX = f"{CDR_SCHEMA}." if CDR_SCHEMA else ""

# Backward compatibility: Support old SCHEMA variable
if not DWT_SCHEMA and os.getenv("SCHEMA"):
    DWT_SCHEMA = os.getenv("SCHEMA")
    DWT_SCHEMA_PREFIX = f"{DWT_SCHEMA}." if DWT_SCHEMA else ""
    info("PKGDWMAPR: Using legacy SCHEMA variable as DWT_SCHEMA for backward compatibility")

# Log schema configuration for debugging
if DWT_SCHEMA:
    info(f"PKGDWMAPR: DWT metadata schema prefix: '{DWT_SCHEMA_PREFIX}'")
else:
    info("PKGDWMAPR: No DWT_SCHEMA set, using no prefix for metadata tables")

if CDR_SCHEMA:
    info(f"PKGDWMAPR: CDR data schema prefix: '{CDR_SCHEMA_PREFIX}' (for future data operations)")
else:
    info("PKGDWMAPR: No CDR_SCHEMA set (will be needed for data loading operations)")


class PKGDWMAPRError(Exception):
    """Custom exception for PKGDWMAPR errors"""
    def __init__(self, package_name: str, proc_name: str, error_code: str, params: str, message: str = None):
        self.package_name = package_name
        self.proc_name = proc_name
        self.error_code = error_code
        self.params = params
        self.message = message or f"Error in {package_name}.{proc_name} [{error_code}]: {params}"
        super().__init__(self.message)
        error(f"PKGDWMAPR Error: {self.message}")


class PKGDWMAPR:
    """
    Python implementation of PKGDWMAPR PL/SQL package
    Handles mapping creation, validation, and management
    """
    
    # Package constants
    G_NAME = 'PKGDWMAPR'
    G_VER = 'V001'
    
    def __init__(self, connection: oracledb.Connection, user: str = None):
        """
        Initialize the PKGDWMAPR class
        
        Args:
            connection: Oracle database connection
            user: Current user ID
        """
        self.connection = connection
        self.g_user = user
    
    @staticmethod
    def version() -> str:
        """Return package version"""
        return f"{PKGDWMAPR.G_NAME}:{PKGDWMAPR.G_VER}"
    
    def set_user(self, user: str):
        """Set the current user"""
        self.g_user = user
    
    # -------------------------------------------------------------------------
    # CREATE_UPDATE_SQL - Function to record SQL query
    # -------------------------------------------------------------------------
    
    def create_update_sql(self, p_dwmaprsqlcd: str, p_dwmaprsql: str) -> int:
        """
        Create or update SQL query mapping
        
        Args:
            p_dwmaprsqlcd: SQL code identifier
            p_dwmaprsql: SQL query text (CLOB)
            
        Returns:
            dwmaprsqlid: SQL mapping ID
            
        Raises:
            PKGDWMAPRError: If validation or database operation fails
        """
        w_procnm = 'CREATE_UPDATE_SQL'
        w_parm = f'SqlCode={p_dwmaprsqlcd}'[:100]
        w_msg = None
        
        try:
            # Validate inputs
            if not p_dwmaprsqlcd or p_dwmaprsqlcd.strip() == '':
                w_msg = 'The mapping SQL Code cannot be null.'
            elif ' ' in p_dwmaprsqlcd:
                w_msg = 'Space(s) not allowed to form mapping SQL Code.'
            elif not p_dwmaprsql or len(p_dwmaprsql.strip()) == 0:
                w_msg = 'The SQL Query cannot be blank.'
            
            if w_msg:
                w_parm = f"{w_parm}::{w_msg}"
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '134', w_parm)
            
            cursor = self.connection.cursor()
            
            # Check if SQL code already exists
            cursor.execute(f"""
                SELECT dwmaprsqlid, dwmaprsqlcd, dwmaprsql
                FROM {DWT_SCHEMA_PREFIX}DWMAPRsql 
                WHERE dwmaprsqlcd = :sqlcd
                AND curflg = 'Y'
            """, {'sqlcd': p_dwmaprsqlcd})
            
            w_rec = cursor.fetchone()
            w_return = None
            
            if w_rec:
                # Record exists, compare SQL
                try:
                    # Read CLOB value properly
                    existing_sql = w_rec[2]
                    if hasattr(existing_sql, 'read'):
                        # It's a CLOB object, read it
                        existing_sql = existing_sql.read()
                    elif existing_sql is not None:
                        # Convert to string
                        existing_sql = str(existing_sql)
                    
                    # Remove trailing semicolons from both for comparison
                    existing_sql_clean = re.sub(r';$', '', existing_sql.strip()) if existing_sql else ''
                    new_sql_clean = re.sub(r';$', '', p_dwmaprsql.strip()) if p_dwmaprsql else ''
                    
                    # Compare the cleaned SQL
                    if existing_sql_clean == new_sql_clean:
                        w_res = 0  # Same
                        info(f"SQL code '{p_dwmaprsqlcd}' unchanged - reusing existing ID: {w_rec[0]}")
                    else:
                        w_res = 1  # Different
                        info(f"SQL code '{p_dwmaprsqlcd}' has changes - will create new version")
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '131', f"{w_parm} - {str(e)}")
                
                w_return = w_rec[0]
            else:
                info(f"SQL code '{p_dwmaprsqlcd}' is new - will create first version")
                w_res = 1
            
            # If SQL is different or new, update/insert
            if w_res != 0:
                if w_rec:
                    # Update existing record to set curflg = 'N'
                    try:
                        cursor.execute(f"""
                            UPDATE {DWT_SCHEMA_PREFIX}DWMAPRsql
                            SET curflg = 'N',
                                recupdt = SYSDATE
                            WHERE dwmaprsqlcd = :sqlcd
                            AND curflg = 'Y'
                        """, {'sqlcd': p_dwmaprsqlcd})
                    except Exception as e:
                        raise PKGDWMAPRError(self.G_NAME, w_procnm, '132', f"{w_parm} - {str(e)}")
                
                # Insert new record
                try:
                    # Remove trailing semicolons
                    clean_sql = re.sub(r';$', '', p_dwmaprsql)
                    
                    # Create a variable to capture the returned ID
                    ret_id_var = cursor.var(oracledb.NUMBER)
                    
                    cursor.execute(f"""
                        INSERT INTO {DWT_SCHEMA_PREFIX}DWMAPRsql
                        (dwmaprsqlid, dwmaprsqlcd, dwmaprsql, reccrdt, recupdt, curflg)
                        VALUES ({DWT_SCHEMA_PREFIX}DWMAPRSQLSEQ.nextval, :sqlcd, :sql, SYSDATE, SYSDATE, 'Y')
                        RETURNING dwmaprsqlid INTO :ret_id
                    """, {
                        'sqlcd': p_dwmaprsqlcd,
                        'sql': clean_sql,
                        'ret_id': ret_id_var
                    })
                    
                    # Get the returned value
                    w_return = ret_id_var.getvalue()
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '133', f"{w_parm} - {str(e)}")
            
            self.connection.commit()
            cursor.close()
            
            return w_return
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '134', f"{w_parm} - {str(e)}")
    
    # -------------------------------------------------------------------------
    # CREATE_UPDATE_MAPPING - Function to create or update mappings
    # -------------------------------------------------------------------------
    
    def create_update_mapping(
        self,
        p_mapref: str,
        p_mapdesc: str,
        p_trgschm: str,
        p_trgtbtyp: str,
        p_trgtbnm: str,
        p_frqcd: str,
        p_srcsystm: str,
        p_lgvrfyflg: str = None,
        p_lgvrfydt: datetime = None,
        p_stflg: str = 'N',
        p_blkprcrows: int = None
    ) -> int:
        """
        Create or update a mapping record
        
        Args:
            p_mapref: Mapping reference
            p_mapdesc: Mapping description
            p_trgschm: Target schema name
            p_trgtbtyp: Target table type (NRM, DIM, FCT, MRT)
            p_trgtbnm: Target table name
            p_frqcd: Frequency code (NA, ID, DL, WK, FN, MN, HY, YR)
            p_srcsystm: Source system
            p_lgvrfyflg: Logic verification flag (Y/N)
            p_lgvrfydt: Logic verification date
            p_stflg: Status flag (A/N)
            p_blkprcrows: Bulk processing rows
            
        Returns:
            mapid: Mapping ID
            
        Raises:
            PKGDWMAPRError: If validation or database operation fails
        """
        w_procnm = 'CREATE_UPDATE_MAPPING'
        w_parm = f'Mapref={p_mapref}-{p_mapdesc}'[:200]
        w_msg = None
        
        try:
            # Normalize/convert input types to handle string inputs from web forms
            # Convert p_blkprcrows to int
            if p_blkprcrows is not None:
                try:
                    p_blkprcrows = int(p_blkprcrows)
                except (ValueError, TypeError):
                    p_blkprcrows = None
            
            # Validate inputs
            if not p_mapref or p_mapref.strip() == '':
                w_msg = 'Mapping reference not provided.'
            elif p_trgtbtyp not in ['NRM', 'DIM', 'FCT', 'MRT']:
                w_msg = 'Invalid target table type (valid: NRM,DIM,FCT,MRT).'
            elif p_frqcd and p_frqcd not in ['NA', 'ID', 'DL', 'WK', 'FN', 'MN', 'HY', 'YR']:
                w_msg = 'Invalid frequency code (Valid: ID,DL,WK,FN,MN,HY,YR).'
            elif p_stflg not in ['A', 'N']:
                w_msg = 'Invalid status (Valid: A,N).'
            elif p_lgvrfyflg and p_lgvrfyflg not in ['Y', 'N']:
                w_msg = 'Invalid verification flag (Valid: Y,N).'
            elif not p_srcsystm:
                w_msg = 'Source system not provided.'
            elif not p_trgschm:
                w_msg = 'Target Schema name not provided.'
            elif ' ' in p_trgschm:
                w_msg = 'Target schema name must not contain blank spaces'
            elif re.search(r'[^A-Za-z0-9_]', p_trgschm):
                w_msg = 'Special characters not allowed to form target schema name.'
            elif re.match(r'^\d', p_trgschm):
                w_msg = 'Target schema name must not start with number.'
            elif ' ' in p_trgtbnm:
                w_msg = 'Target table name must not contain blank spaces'
            elif re.search(r'[^A-Za-z0-9_]', p_trgtbnm):
                w_msg = 'Special characters not allowed to form target table name.'
            elif re.match(r'^\d', p_trgtbnm):
                w_msg = 'Target table must not start with number.'
            elif (p_lgvrfyflg and not p_lgvrfydt) or (not p_lgvrfyflg and p_lgvrfydt):
                w_msg = 'Both logic verification flag and date must be provide or both must be blank.'
            elif p_blkprcrows is not None and p_blkprcrows < 0:
                w_msg = 'The number of Bulk Processing Rows cannot be negative.'
            
            if w_msg:
                w_parm = f"{w_parm}::{w_msg}"
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '103', w_parm)
            
            cursor = self.connection.cursor()
            
            # Check if mapping reference already exists
            cursor.execute(f"""
                SELECT * 
                FROM {DWT_SCHEMA_PREFIX}DWMAPR 
                WHERE mapref = :mapref
                AND curflg = 'Y'
            """, {'mapref': p_mapref})
            
            columns = [col[0] for col in cursor.description]
            w_mapr_rec = cursor.fetchone()
            
            info(f"CREATE_UPDATE_MAPPING: Mapping '{p_mapref}' {'exists' if w_mapr_rec else 'is new'}")
            
            if w_mapr_rec:
                w_mapr_dict = dict(zip(columns, w_mapr_rec))
                
                # Check if any values changed
                p_lgvrfyflg_val = p_lgvrfyflg or 'N'
                p_stflg_val = p_stflg or 'N'
                p_blkprcrows_val = p_blkprcrows or 0
                
                # Normalize datetime values for comparison
                # Convert both to None if either is None, otherwise compare dates only
                existing_lgvrfydt = w_mapr_dict['LGVRFYDT']
                new_lgvrfydt = p_lgvrfydt
                
                # Convert datetime objects to date for comparison (ignore time component)
                if existing_lgvrfydt is not None and hasattr(existing_lgvrfydt, 'date'):
                    existing_lgvrfydt = existing_lgvrfydt.date()
                if new_lgvrfydt is not None and hasattr(new_lgvrfydt, 'date'):
                    new_lgvrfydt = new_lgvrfydt.date()
                
                info(f"CREATE_UPDATE_MAPPING: Comparing existing LGVRFYDT={existing_lgvrfydt} with new={new_lgvrfydt}")
                
                w_chg = 'N'
                if (w_mapr_dict['MAPDESC'] != p_mapdesc or
                    w_mapr_dict['TRGSCHM'] != p_trgschm or
                    w_mapr_dict['TRGTBTYP'] != p_trgtbtyp or
                    w_mapr_dict['TRGTBNM'] != p_trgtbnm or
                    w_mapr_dict['FRQCD'] != p_frqcd or
                    w_mapr_dict['SRCSYSTM'] != p_srcsystm or
                    #w_mapr_dict['LGVRFYFLG'] != p_lgvrfyflg_val or
                    #existing_lgvrfydt != new_lgvrfydt or
                    #w_mapr_dict['STFLG'] != p_stflg_val or
                    (w_mapr_dict['BLKPRCROWS'] or 0) != p_blkprcrows_val):
                    w_chg = 'Y'
                
                if w_chg == 'N':
                    # No changes, return existing ID
                    w_mapid = w_mapr_dict['MAPID']
                    info(f"CREATE_UPDATE_MAPPING: No changes detected for '{p_mapref}', returning existing mapid={w_mapid}")
                    cursor.close()
                    return w_mapid
                else:
                    info(f"CREATE_UPDATE_MAPPING: Changes detected for '{p_mapref}', will create new version")
                    # Update existing record to set curflg = 'N'
                    try:
                        cursor.execute(f"""
                            UPDATE {DWT_SCHEMA_PREFIX}DWMAPR
                            SET curflg = 'N',
                                recupdt = SYSDATE,
                                uptdby = :p_user
                            WHERE mapid = :mapid
                        """, {
                            'p_user': self.g_user,
                            'mapid': w_mapr_dict['MAPID']
                        })
                    except Exception as e:
                        raise PKGDWMAPRError(self.G_NAME, w_procnm, '101', 
                                           f"{w_parm} mapid={w_mapr_dict['MAPID']} - {str(e)}")
            
            # Insert new record
            try:
                # Create a variable to capture the returned ID
                ret_id_var = cursor.var(oracledb.NUMBER)
                info(f"Full table name: {DWT_SCHEMA_PREFIX}DWMAPR")
                # Debug: Log the sequence and table reference being used
                info(f"CREATE_UPDATE_MAPPING: Inserting into table '{DWT_SCHEMA_PREFIX}DWMAPR'")
                info(f"CREATE_UPDATE_MAPPING: Using sequence '{DWT_SCHEMA_PREFIX}DWMAPRSEQ.nextval'")
                info(f"CREATE_UPDATE_MAPPING: DWT_SCHEMA='{DWT_SCHEMA}', DWT_SCHEMA_PREFIX='{DWT_SCHEMA_PREFIX}'")
                
                cursor.execute(f"""
                    INSERT INTO {DWT_SCHEMA_PREFIX}DWMAPR 
                    (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
                     lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, crtdby, uptdby)
                    VALUES ({DWT_SCHEMA_PREFIX}DWMAPRSEQ.nextval, :mapref, :mapdesc, :trgschm, :trgtbtyp, :trgtbnm, 
                           :frqcd, :srcsystm, :lgvrfyflg, :lgvrfydt, :stflg, SYSDATE, SYSDATE, 'Y', 
                           :blkprcrows, :p_user, :p_user)
                    RETURNING mapid INTO :ret_id
                """, {
                    'mapref': p_mapref,
                    'mapdesc': p_mapdesc,
                    'trgschm': p_trgschm,
                    'trgtbtyp': p_trgtbtyp,
                    'trgtbnm': p_trgtbnm,
                    'frqcd': p_frqcd,
                    'srcsystm': p_srcsystm,
                    'lgvrfyflg': p_lgvrfyflg or 'N',
                    'lgvrfydt': p_lgvrfydt,
                    'stflg': p_stflg or 'N',
                    'blkprcrows': p_blkprcrows,
                    'p_user': self.g_user,
                    'ret_id': ret_id_var
                })
                
                # Get the returned value
                w_mapid = ret_id_var.getvalue()
            except Exception as e:
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '102', f"{w_parm} - {str(e)}")
            
            self.connection.commit()
            cursor.close()
            
            return w_mapid
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '103', w_parm)
    
    # -------------------------------------------------------------------------
    # CREATE_UPDATE_MAPPING_DETAIL - Function to create or update mapping details
    # -------------------------------------------------------------------------
    
    def create_update_mapping_detail(
        self,
        p_mapref: str,
        p_trgclnm: str,
        p_trgcldtyp: str,
        p_trgkeyflg: str = None,
        p_trgkeyseq: int = None,
        p_trgcldesc: str = None,
        p_maplogic: str = None,
        p_keyclnm: str = None,
        p_valclnm: str = None,
        p_mapcmbcd: str = None,
        p_excseq: int = None,
        p_scdtyp: int = 1,
        p_lgvrfyflg: str = None,
        p_lgvrfydt: datetime = None
    ) -> int:
        """
        Create or update mapping detail record
        
        Args:
            p_mapref: Mapping reference
            p_trgclnm: Target column name
            p_trgcldtyp: Target column data type
            p_trgkeyflg: Target key flag (Y/N)
            p_trgkeyseq: Target key sequence
            p_trgcldesc: Target column description
            p_maplogic: Mapping logic/SQL
            p_keyclnm: Key column name
            p_valclnm: Value column name
            p_mapcmbcd: Mapping combination code
            p_excseq: Execution sequence
            p_scdtyp: SCD type (1, 2, 3)
            p_lgvrfyflg: Logic verification flag (Y/N)
            p_lgvrfydt: Logic verification date
            
        Returns:
            mapdtlid: Mapping detail ID
            
        Raises:
            PKGDWMAPRError: If validation or database operation fails
        """
        w_procnm = 'CREATE_UPDATE_MAPPING_DETAIL'
        w_parm = f'Mapref={p_mapref} Trgcol={p_trgclnm}'[:400]
        w_msg = None
        
        try:
            # Normalize/convert input types to handle string inputs from web forms
            # Convert p_scdtyp to int
            if p_scdtyp is not None:
                try:
                    p_scdtyp = int(p_scdtyp)
                except (ValueError, TypeError):
                    p_scdtyp = 1  # Default to 1 if conversion fails
            else:
                p_scdtyp = 1  # Default to 1 if None
            
            # Convert p_trgkeyseq to int
            if p_trgkeyseq is not None:
                try:
                    p_trgkeyseq = int(p_trgkeyseq)
                except (ValueError, TypeError):
                    p_trgkeyseq = None
            
            # Convert p_excseq to int
            if p_excseq is not None:
                try:
                    p_excseq = int(p_excseq)
                except (ValueError, TypeError):
                    p_excseq = None
            
            info(f"CREATE_UPDATE_MAPPING_DETAIL: p_scdtyp={p_scdtyp} (type: {type(p_scdtyp).__name__})")
            
            # Validate inputs
            if not p_mapref:
                w_msg = 'Mapping reference not provided.'
            elif not p_trgclnm:
                w_msg = 'Target column name not provided.'
            elif ' ' in p_trgclnm:
                w_msg = 'Target column name must not contain blank spaces'
            elif re.search(r'[^A-Za-z0-9_]', p_trgclnm):
                w_msg = 'Special characters not allowed to form target column name.'
            elif re.match(r'^\d', p_trgclnm):
                w_msg = 'Target column name must not start with number.'
            elif not p_trgcldtyp:
                w_msg = 'Target column data type is not provided.'
            elif p_trgkeyflg and p_trgkeyflg not in ['Y', 'N']:
                w_msg = 'Invalid value for Key flag (valid: Y or blank).'
            elif p_trgkeyflg == 'Y' and not p_trgkeyseq:
                w_msg = 'Key sequence must be provided for Primary key columns.'
            elif not p_maplogic:
                w_msg = 'Mapping logic must be provided.'
            elif p_maplogic and (not p_keyclnm or not p_valclnm):
                w_msg = 'Key column and value column must be provided.'
            elif p_scdtyp not in [1, 2, 3]:
                w_msg = f'Invalid value for SCD type: {p_scdtyp}. Must be 1, 2, or 3.'
            elif (p_lgvrfyflg and not p_lgvrfydt) or (not p_lgvrfyflg and p_lgvrfydt):
                w_msg = 'Both logic verification flag and date must be provide or both must be blank.'
            
            cursor = self.connection.cursor()
            
            # Validate data type
            cursor.execute(f"""
                SELECT prval
                FROM {DWT_SCHEMA_PREFIX}DWPARAMS
                WHERE prtyp = 'Datatype'
                AND prcd = :dtyp
            """, {'dtyp': p_trgcldtyp})
            
            w_dtyp_rec = cursor.fetchone()
            
            if not w_dtyp_rec:
                w_msg = (f'The datatype {p_trgcldtyp} for {p_trgclnm} is invalid.\n'
                        'Please verify parameters for "Datatype".')
            
            if w_msg:
                w_parm = f"{w_parm}::{w_msg}"
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '107', w_parm)
            
            # Check if mapping logic is an SQL code reference
            w_msql_rec = None
            if p_maplogic and len(p_maplogic) <= 100:
                cursor.execute(f"""
                    SELECT dwmaprsqlid, dwmaprsqlcd
                    FROM {DWT_SCHEMA_PREFIX}DWMAPRsql
                    WHERE dwmaprsqlcd = :sqlcd
                    AND curflg = 'Y'
                """, {'sqlcd': p_maplogic})
                
                w_msql_rec = cursor.fetchone()
            
            # Verify mapping reference exists
            cursor.execute(f"""
                SELECT * 
                FROM {DWT_SCHEMA_PREFIX}DWMAPR 
                WHERE mapref = :mapref
                AND curflg = 'Y'
            """, {'mapref': p_mapref})
            
            w_mapr_rec = cursor.fetchone()
            
            if not w_mapr_rec:
                w_msg = 'Invalid mapping reference.'
                w_parm = f"{w_parm}::{w_msg}"
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '107', w_parm)
            
            # Check if mapping detail already exists
            cursor.execute(f"""
                SELECT * 
                FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl 
                WHERE mapref = :mapref
                AND trgclnm = :trgclnm
                AND curflg = 'Y'
            """, {'mapref': p_mapref, 'trgclnm': p_trgclnm})
            
            columns = [col[0] for col in cursor.description]
            w_maprdtl_rec = cursor.fetchone()
            
            if w_maprdtl_rec:
                w_maprdtl_dict = dict(zip(columns, w_maprdtl_rec))
                
                # Check if any values changed
                p_trgkeyflg_val = p_trgkeyflg or 'N'
                p_trgkeyseq_val = p_trgkeyseq or -1
                
                # Read CLOB value for MAPLOGIC if needed
                existing_maplogic = w_maprdtl_dict['MAPLOGIC']
                if hasattr(existing_maplogic, 'read'):
                    # It's a CLOB object, read it
                    existing_maplogic = existing_maplogic.read()
                elif existing_maplogic is not None:
                    # Convert to string
                    existing_maplogic = str(existing_maplogic)
                
                w_chg = 'N'
                if (w_maprdtl_dict['MAPREF'] != p_mapref or
                    w_maprdtl_dict['TRGCLNM'] != p_trgclnm or
                    w_maprdtl_dict['TRGCLDTYP'] != p_trgcldtyp or
                    (w_maprdtl_dict['TRGKEYFLG'] or 'N') != p_trgkeyflg_val or
                    (w_maprdtl_dict['TRGKEYSEQ'] or -1) != p_trgkeyseq_val or
                    w_maprdtl_dict['TRGCLDESC'] != p_trgcldesc or
                    existing_maplogic != p_maplogic or
                    w_maprdtl_dict['KEYCLNM'] != p_keyclnm or
                    w_maprdtl_dict['VALCLNM'] != p_valclnm or
                    w_maprdtl_dict['MAPCMBCD'] != p_mapcmbcd or
                    w_maprdtl_dict['EXCSEQ'] != p_excseq or
                    w_maprdtl_dict['SCDTYP'] != p_scdtyp or
                    w_maprdtl_dict['LGVRFYFLG'] != p_lgvrfyflg or
                    w_maprdtl_dict['LGVRFYDT'] != p_lgvrfydt):
                    w_chg = 'Y'
                
                if w_chg == 'N':
                    # No changes, return existing ID
                    w_mapdtlid = w_maprdtl_dict['MAPDTLID']
                    cursor.close()
                    return w_mapdtlid
                else:
                    # Update existing record to set curflg = 'N'
                    try:
                        cursor.execute(f"""
                            UPDATE {DWT_SCHEMA_PREFIX}DWMAPRdtl
                            SET curflg = 'N',
                                recupdt = SYSDATE,
                                uptdby = :p_user
                            WHERE mapref = :mapref
                            AND mapdtlid = :mapdtlid
                            AND curflg = 'Y'
                        """, {
                            'p_user': self.g_user,
                            'mapref': w_maprdtl_dict['MAPREF'],
                            'mapdtlid': w_maprdtl_dict['MAPDTLID']
                        })
                    except Exception as e:
                        raise PKGDWMAPRError(self.G_NAME, w_procnm, '105',
                                           f"{w_parm} Mapref={w_maprdtl_dict['MAPREF']} "
                                           f"Trgclnm={w_maprdtl_dict['TRGCLNM']} - {str(e)}")
            
            # Insert new record
            try:
                maprsqlcd = w_msql_rec[1] if w_msql_rec else None
                
                # Create a variable to capture the returned ID
                ret_id_var = cursor.var(oracledb.NUMBER)
                info(f"Full table name: {DWT_SCHEMA_PREFIX}DWMAPRdtl")
                cursor.execute(f"""
                    INSERT INTO {DWT_SCHEMA_PREFIX}DWMAPRDTL 
                    (mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq, trgcldesc,
                     maplogic, maprsqlcd, keyclnm, valclnm, mapcmbcd, excseq, scdtyp, lgvrfyflg,
                     lgvrfydt, reccrdt, recupdt, curflg, crtdby, uptdby)
                    VALUES ({DWT_SCHEMA_PREFIX}DWMAPRDTLSEQ.nextval, :mapref, :trgclnm, :trgcldtyp, :trgkeyflg, 
                           :trgkeyseq, :trgcldesc, :maplogic, :maprsqlcd, :keyclnm, :valclnm, 
                           :mapcmbcd, :excseq, :scdtyp, :lgvrfyflg, :lgvrfydt, SYSDATE, SYSDATE, 
                           'Y', :p_user, :p_user)
                    RETURNING mapdtlid INTO :ret_id
                """, {
                    'mapref': p_mapref,
                    'trgclnm': p_trgclnm,
                    'trgcldtyp': p_trgcldtyp,
                    'trgkeyflg': p_trgkeyflg,
                    'trgkeyseq': p_trgkeyseq,
                    'trgcldesc': p_trgcldesc,
                    'maplogic': p_maplogic,
                    'maprsqlcd': maprsqlcd,
                    'keyclnm': p_keyclnm,
                    'valclnm': p_valclnm,
                    'mapcmbcd': p_mapcmbcd,
                    'excseq': p_excseq,
                    'scdtyp': p_scdtyp,
                    'lgvrfyflg': p_lgvrfyflg,
                    'lgvrfydt': p_lgvrfydt,
                    'p_user': self.g_user,
                    'ret_id': ret_id_var
                })
                
                # Get the returned value
                w_mapdtlid = ret_id_var.getvalue()
            except Exception as e:
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '106', f"{w_parm} - {str(e)}")
            
            self.connection.commit()
            cursor.close()
            
            return w_mapdtlid
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '107', w_parm)
    
    # -------------------------------------------------------------------------
    # VALIDATE_SQL - Private method to validate SQL
    # -------------------------------------------------------------------------
    
    def _validate_sql(
        self,
        p_logic: str,
        p_keyclnm: str = None,
        p_valclnm: str = None,
        p_flg: str = 'Y'
    ) -> Tuple[bool, str]:
        """
        Validate SQL query syntax
        
        Args:
            p_logic: SQL logic to validate
            p_keyclnm: Key column name
            p_valclnm: Value column name
            p_flg: Flag to wrap SQL with select statement (Y/N)
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        w_procnm = 'VALIDATE_SQL'
        w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}'[:400]
        p_error = None
        
        try:
            # Validate columns if flg is Y
            if p_flg == 'Y':
                if not p_keyclnm:
                    return False, 'Key column(s) not provided.'
                if not p_valclnm:
                    return False, 'Value column(s) not provided.'
            
            # Check if SQL is empty
            if not p_logic or len(p_logic.strip()) == 0:
                return False, 'SQL provided is empty.'
            
            # Build SQL for validation
            if p_flg == 'Y':
                w_logic = f"SELECT {p_keyclnm},{p_valclnm} FROM ({p_logic}) sql1 WHERE ROWNUM = 1"
            else:
                w_logic = p_logic
            
            # Replace DWT_PARAM placeholders with NULL
            w_logic = re.sub(r'DWT_PARAM\d+', 'NULL', w_logic, flags=re.IGNORECASE)
            w_logic = re.sub(r';$', '', w_logic)  # Remove trailing semicolons
            
            # Try to parse the SQL
            cursor = self.connection.cursor()
            try:
                cursor.parse(w_logic)
            except Exception as e:
                p_error = str(e)
            finally:
                cursor.close()
            
            if p_error:
                return False, p_error
            
            return True, None
            
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '138', w_parm)
    
    def validate_sql(self, p_logic: str) -> str:
        """
        Public wrapper for SQL validation
        
        Args:
            p_logic: SQL logic to validate
            
        Returns:
            'Y' if valid, 'N' if invalid
        """
        w_procnm = 'VALIDATE_SQL'
        w_parm = 'SQL Validate with Clob.'
        
        try:
            success, error_msg = self._validate_sql(p_logic, None, None, 'N')
            return 'Y' if success else 'N'
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '139', w_parm)
    
    # -------------------------------------------------------------------------
    # VALIDATE_LOGIC - Function to validate mapping logic
    # -------------------------------------------------------------------------
    
    def validate_logic2(
        self,
        p_logic: str,
        p_keyclnm: str,
        p_valclnm: str
    ) -> Tuple[str, str]:
        """
        Validate mapping logic and return result with error message
        
        Args:
            p_logic: Mapping logic (SQL or SQL code)
            p_keyclnm: Key column name
            p_valclnm: Value column name
            
        Returns:
            Tuple of (validation_flag: str, error_message: str)
            validation_flag: 'Y' if valid, 'N' if invalid
        """
        w_procnm = 'VALIDATE_LOGIC2'
        w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}:{p_logic}'[:400]
        
        try:
            cursor = self.connection.cursor()
            
            # Check if logic is an SQL code reference
            cursor.execute(f"""
                SELECT dwmaprsqlcd, dwmaprsql
                FROM {DWT_SCHEMA_PREFIX}DWMAPRsql
                WHERE dwmaprsqlcd = :sqlcd
                AND curflg = 'Y'
            """, {'sqlcd': p_logic[:100]})
            
            w_rec = cursor.fetchone()
            cursor.close()
            
            # Get actual SQL
            if w_rec:
                # Read CLOB value properly
                w_logic = w_rec[1]
                if hasattr(w_logic, 'read'):
                    # It's a CLOB object, read it
                    w_logic = w_logic.read()
                elif w_logic is not None:
                    # Convert to string
                    w_logic = str(w_logic)
            else:
                w_logic = p_logic  # Use provided logic
            
            # Validate the SQL
            success, error_msg = self._validate_sql(w_logic, p_keyclnm, p_valclnm, 'Y')
            
            w_return = 'Y' if success else 'N'
            return w_return, error_msg
            
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '110', w_parm)
    
    def validate_logic(self, p_logic: str, p_keyclnm: str, p_valclnm: str) -> str:
        """
        Validate mapping logic
        
        Args:
            p_logic: Mapping logic (SQL or SQL code)
            p_keyclnm: Key column name
            p_valclnm: Value column name
            
        Returns:
            'Y' if valid, 'N' if invalid
        """
        w_procnm = 'VALIDATE_LOGIC'
        w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}:{p_logic}'[:400]
        
        try:
            w_return, _ = self.validate_logic2(p_logic, p_keyclnm, p_valclnm)
            return w_return
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '109', w_parm)
    
    # -------------------------------------------------------------------------
    # VALIDATE_LOGIC (for mapping reference) - Validate all mappings
    # -------------------------------------------------------------------------
    
    def validate_all_logic(self, p_mapref: str) -> str:
        """
        Validate all mapping details for a given mapping reference
        
        Args:
            p_mapref: Mapping reference
            
        Returns:
            'Y' if all valid, 'N' if any invalid
        """
        w_procnm = 'VALIDATE_LOGIC'
        w_parm = f'Mapref={p_mapref}'[:200]
        w_return = 'Y'
        
        try:
            cursor = self.connection.cursor()
            
            # Get all mapping details for this reference
            cursor.execute(f"""
                SELECT m.mapref, md.mapdtlid, m.trgtbnm, md.trgclnm,
                       md.keyclnm, md.valclnm, md.maplogic
                FROM {DWT_SCHEMA_PREFIX}DWMAPR m, {DWT_SCHEMA_PREFIX}DWMAPRdtl md
                WHERE m.mapref = :mapref
                AND m.curflg = 'Y'
                AND md.mapref = m.mapref
                AND md.curflg = 'Y'
            """, {'mapref': p_mapref})
            
            map_records = cursor.fetchall()
            
            # Validate each mapping detail
            for map_rec in map_records:
                mapref, mapdtlid, trgtbnm, trgclnm, keyclnm, valclnm, maplogic = map_rec
                
                # Read CLOB value for maplogic if needed
                if hasattr(maplogic, 'read'):
                    # It's a CLOB object, read it
                    maplogic = maplogic.read()
                elif maplogic is not None:
                    # Convert to string
                    maplogic = str(maplogic)
                
                w_pm = (f'TB:{trgtbnm}-TC:{trgclnm}:Key:{keyclnm}-Val:{valclnm}-{maplogic}')[:400]
                
                try:
                    w_res, w_err = self.validate_logic2(maplogic, keyclnm, valclnm)
                    
                    # If validation failed, insert error record
                    if w_res == 'N' and w_err:
                        try:
                            cursor.execute(f"""
                                INSERT INTO {DWT_SCHEMA_PREFIX}DWMAPERR
                                (maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                                VALUES ({DWT_SCHEMA_PREFIX}DWMAPERRSEQ.nextval, :mapdtlid, :mapref, :maplogic, 
                                       'ERR', :errmsg, SYSDATE)
                            """, {
                                'mapdtlid': mapdtlid,
                                'mapref': mapref,
                                'maplogic': maplogic,
                                'errmsg': w_err
                            })
                        except Exception as e:
                            raise PKGDWMAPRError(self.G_NAME, w_procnm, '111', w_pm)
                    
                    if w_return == 'Y':
                        w_return = w_res
                    
                    # Update mapping detail with validation result
                    cursor.execute(f"""
                        UPDATE {DWT_SCHEMA_PREFIX}DWMAPRdtl
                        SET lgvrfydt = SYSDATE,
                            lgvrfyflg = :lgvrfyflg
                        WHERE mapref = :mapref
                        AND mapdtlid = :mapdtlid
                        AND curflg = 'Y'
                    """, {
                        'lgvrfyflg': w_res,
                        'mapref': mapref,
                        'mapdtlid': mapdtlid
                    })
                    
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '112', w_pm)
            
            # Additional validations if all logic is valid
            if w_return == 'Y':
                # Check for duplicate value column names within mapping combination codes
                cursor.execute(f"""
                    SELECT valclnm, mapcmbcd, COUNT(*) cnt
                    FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                    WHERE curflg = 'Y'
                    AND mapref = :mapref
                    GROUP BY valclnm, mapcmbcd
                    HAVING COUNT(*) > 1
                """, {'mapref': p_mapref})
                
                w_c2_rec = cursor.fetchone()
                
                if w_c2_rec and w_c2_rec[2] > 1:
                    w_err = (f'Target value column name ({w_c2_rec[0]}) cannot repeat within '
                            f'a mapping code ({w_c2_rec[1]}). Please use alias if required.')
                    w_return = 'N'
                    
                    try:
                        cursor.execute(f"""
                            INSERT INTO {DWT_SCHEMA_PREFIX}DWMAPERR
                            (maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES ({DWT_SCHEMA_PREFIX}DWMAPERRSEQ.nextval, NULL, :mapref, NULL, 'ERR', :errmsg, SYSDATE)
                        """, {'mapref': p_mapref, 'errmsg': w_err})
                    except Exception as e:
                        raise PKGDWMAPRError(self.G_NAME, w_procnm, '127', w_parm)
                
                # Check for multiple mapping combinations per SQL code
                cursor.execute(f"""
                    SELECT maprsqlcd, mapcmbcd, COUNT(*) cnt
                    FROM (
                        SELECT DISTINCT maprsqlcd, mapcmbcd
                        FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                        WHERE curflg = 'Y'
                        AND mapref = :mapref
                    ) x
                    GROUP BY maprsqlcd, mapcmbcd
                    HAVING COUNT(*) > 1
                """, {'mapref': p_mapref})
                
                w_c2_rec = cursor.fetchone()
                
                if w_c2_rec and w_c2_rec[2] > 1:
                    w_err = ('For a "Mapping Combination"/"SQL Query Code", more than 1 '
                            '"SQL Query Code"/"Mapping Combination" is not allowed')
                    w_return = 'N'
                    
                    try:
                        cursor.execute(f"""
                            INSERT INTO {DWT_SCHEMA_PREFIX}DWMAPERR
                            (maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES ({DWT_SCHEMA_PREFIX}DWMAPERRSEQ.nextval, NULL, :mapref, NULL, 'ERR', :errmsg, SYSDATE)
                        """, {'mapref': p_mapref, 'errmsg': w_err})
                    except Exception as e:
                        raise PKGDWMAPRError(self.G_NAME, w_procnm, '140', w_parm)
            
            # If all validations passed, update mapping record
            if w_return == 'Y':
                try:
                    cursor.execute(f"""
                        UPDATE {DWT_SCHEMA_PREFIX}DWMAPR
                        SET lgvrfydt = SYSDATE,
                            lgvrfyflg = :lgvrfyflg,
                            lgvrfby = :p_user
                        WHERE mapref = :mapref
                        AND curflg = 'Y'
                    """, {
                        'lgvrfyflg': w_return,
                        'p_user': self.g_user,
                        'mapref': p_mapref
                    })
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '113', w_parm)
            
            self.connection.commit()
            cursor.close()
            
            return w_return
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '129', w_parm)
    
    # -------------------------------------------------------------------------
    # VALIDATE_MAPPING_DETAILS - Validate complete mapping details
    # -------------------------------------------------------------------------
    
    def validate_mapping_details(self, p_mapref: str) -> Tuple[str, str]:
        """
        Validate all mapping details for a given mapping reference
        
        Args:
            p_mapref: Mapping reference
            
        Returns:
            Tuple of (validation_flag: str, error_message: str)
            validation_flag: 'Y' if valid, 'N' if invalid
        """
        w_procnm = 'VALIDATE_MAPPING_DETAILS'
        w_parm = f'Mapref={p_mapref}'[:200]
        w_msg = None
        w_return = 'Y'
        
        try:
            cursor = self.connection.cursor()
            
            # First validate all logic
            try:
                w_flg = self.validate_all_logic(p_mapref)
                
                if w_flg == 'N':
                    w_msg = 'Some/All target columns logic validation failed, please verify logic(SQL).'
                    w_return = 'N'
            except Exception as e:
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '115', w_parm)
            
            # Check primary key specifications
            if not w_msg:
                try:
                    cursor.execute(f"""
                        SELECT trgkeyseq, COUNT(*) cnt
                        FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                        WHERE curflg = 'Y'
                        AND mapref = :mapref
                        AND trgkeyflg = 'Y'
                        GROUP BY trgkeyseq
                    """, {'mapref': p_mapref})
                    
                    w_pk_rec = cursor.fetchone()
                    
                    if not w_pk_rec or (w_pk_rec and w_pk_rec[1] == 0):
                        w_msg = 'Primary key not specified, primary key(s) is mandatory.'
                        w_return = 'N'
                    elif w_pk_rec and w_pk_rec[0] and w_pk_rec[1] > 1:
                        w_msg = 'Primary sequence cannot repeat within mapping.'
                        w_return = 'N'
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '125', w_parm)
            
            # Check for duplicate column names
            if not w_msg:
                try:
                    cursor.execute(f"""
                        SELECT trgclnm, COUNT(*) cnt
                        FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                        WHERE curflg = 'Y'
                        AND mapref = :mapref
                        GROUP BY trgclnm
                        HAVING COUNT(*) > 1
                    """, {'mapref': p_mapref})
                    
                    w_cl_rec = cursor.fetchone()
                    
                    if w_cl_rec and w_cl_rec[1] > 1:
                        w_msg = 'Target column name cannot repeat within mapping.'
                        w_return = 'N'
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '126', w_parm)
            
            # Check for duplicate value column names within mapping codes
            if not w_msg:
                try:
                    cursor.execute(f"""
                        SELECT valclnm, mapcmbcd, COUNT(*) cnt
                        FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                        WHERE curflg = 'Y'
                        AND mapref = :mapref
                        GROUP BY valclnm, mapcmbcd
                        HAVING COUNT(*) > 1
                    """, {'mapref': p_mapref})
                    
                    w_c2_rec = cursor.fetchone()
                    
                    if w_c2_rec and w_c2_rec[2] > 1:
                        w_msg = (f'Target value column name ({w_c2_rec[0]}) cannot repeat within '
                                f'a mapping code ({w_c2_rec[1]}). Please use alias if required.')
                        w_return = 'N'
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '130', w_parm)
            
            cursor.close()
            
            return w_return, w_msg
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '116', w_parm)
    
    # -------------------------------------------------------------------------
    # ACTIVATE_DEACTIVATE_MAPPING - Procedure to activate or deactivate mapping
    # -------------------------------------------------------------------------
    
    def activate_deactivate_mapping(self, p_mapref: str, p_stflg: str) -> Tuple[bool, str]:
        """
        Activate or deactivate a mapping
        
        Args:
            p_mapref: Mapping reference
            p_stflg: Status flag (A=Active, N=Not Active)
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        w_procnm = 'ACTIVATE_DEACTIVATE_MAPPING'
        w_parm = f'Mapref={p_mapref}'[:200]
        w_msg = None
        
        try:
            # Validate status flag
            if p_stflg not in ['A', 'N']:
                w_msg = 'Invalid status flag (valid: A or N).'
            
            # If activating, validate mappings first
            if p_stflg == 'A' and not w_msg:
                try:
                    w_flg, w_err = self.validate_mapping_details(p_mapref)
                    
                    if w_flg == 'N':
                        w_msg = f"{w_err}\nCannot activate mapping few columns logic failed."
                except Exception as e:
                    raise PKGDWMAPRError(self.G_NAME, w_procnm, '118', w_parm)
                
                # If validation passed, update status
                if not w_msg:
                    cursor = self.connection.cursor()
                    cursor.execute(f"""
                        UPDATE {DWT_SCHEMA_PREFIX}DWMAPR
                        SET stflg = :stflg,
                            actby = :p_user,
                            actdt = SYSDATE
                        WHERE mapref = :mapref
                        AND curflg = 'Y'
                    """, {
                        'stflg': p_stflg,
                        'p_user': self.g_user,
                        'mapref': p_mapref
                    })
                    self.connection.commit()
                    cursor.close()
            
            if w_msg:
                return False, w_msg
            
            return True, 'Mapping status updated successfully.'
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '119', w_parm)
    
    # -------------------------------------------------------------------------
    # DELETE_MAPPING - Procedure to delete mapping
    # -------------------------------------------------------------------------
    
    def delete_mapping(self, p_mapref: str) -> Tuple[bool, str]:
        """
        Delete a mapping and its details
        
        Args:
            p_mapref: Mapping reference
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        w_procnm = 'DELETE_MAPPING'
        w_parm = f'Mapref={p_mapref}'[:200]
        
        try:
            cursor = self.connection.cursor()
            
            # Check if job exists for this mapping
            cursor.execute(f"""
                SELECT mapref, jobid
                FROM {DWT_SCHEMA_PREFIX}DWJOB
                WHERE mapref = :mapref
                AND curflg = 'Y'
            """, {'mapref': p_mapref})
            
            w_job_rec = cursor.fetchone()
            
            if w_job_rec:
                error_msg = f'The mapping "{p_mapref}" cannot be deleted because related job exists.'
                cursor.close()
                return False, error_msg
            
            # Delete mapping details first
            try:
                cursor.execute(f"""
                    DELETE FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                    WHERE mapref = :mapref
                """, {'mapref': p_mapref})
                
                # Delete mapping
                cursor.execute(f"""
                    DELETE FROM {DWT_SCHEMA_PREFIX}DWMAPR
                    WHERE mapref = :mapref
                """, {'mapref': p_mapref})
                
                self.connection.commit()
            except Exception as e:
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '121', w_parm)
            
            cursor.close()
            
            return True, f'Mapping "{p_mapref}" deleted successfully.'
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '122', w_parm)
    
    # -------------------------------------------------------------------------
    # DELETE_MAPPING_DETAILS - Procedure to delete mapping details
    # -------------------------------------------------------------------------
    
    def delete_mapping_details(self, p_mapref: str, p_trgclnm: str) -> Tuple[bool, str]:
        """
        Delete a specific mapping detail
        
        Args:
            p_mapref: Mapping reference
            p_trgclnm: Target column name
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        w_procnm = 'DELETE_MAPPING_DETAILS'
        w_parm = f'Mapref={p_mapref} Trgclnm={p_trgclnm}'[:200]
        
        try:
            cursor = self.connection.cursor()
            
            # Check if job detail exists for this mapping detail
            cursor.execute(f"""
                SELECT mapref, jobdtlid
                FROM {DWT_SCHEMA_PREFIX}DWJOBdtl
                WHERE mapref = :mapref
                AND trgclnm = :trgclnm
                AND curflg = 'Y'
            """, {'mapref': p_mapref, 'trgclnm': p_trgclnm})
            
            w_jd_rec = cursor.fetchone()
            
            if w_jd_rec:
                error_msg = (f'The mapping detail for "{p_mapref}-{p_trgclnm}" cannot be deleted '
                           'because related job detail exists.')
                cursor.close()
                return False, error_msg
            
            # Delete mapping detail
            try:
                cursor.execute(f"""
                    DELETE FROM {DWT_SCHEMA_PREFIX}DWMAPRdtl
                    WHERE mapref = :mapref
                    AND trgclnm = :trgclnm
                """, {'mapref': p_mapref, 'trgclnm': p_trgclnm})
                
                self.connection.commit()
            except Exception as e:
                raise PKGDWMAPRError(self.G_NAME, w_procnm, '123', w_parm)
            
            cursor.close()
            
            return True, f'Mapping detail "{p_mapref}-{p_trgclnm}" deleted successfully.'
            
        except PKGDWMAPRError:
            raise
        except Exception as e:
            raise PKGDWMAPRError(self.G_NAME, w_procnm, '124', w_parm)


# -----------------------------------------------------------------------------
# Convenience functions with user parameter
# -----------------------------------------------------------------------------

def create_update_mapping_with_user(
    connection: oracledb.Connection,
    p_mapref: str,
    p_mapdesc: str,
    p_trgschm: str,
    p_trgtbtyp: str,
    p_trgtbnm: str,
    p_frqcd: str,
    p_srcsystm: str,
    p_lgvrfyflg: str,
    p_lgvrfydt: datetime,
    p_stflg: str,
    p_blkprcrows: int,
    p_user: str
) -> int:
    """
    Create or update mapping with user parameter
    
    Args:
        connection: Database connection
        p_user: User ID
        ... other parameters ...
        
    Returns:
        mapid: Mapping ID
    """
    if not p_user:
        raise ValueError('Session user not provided.')
    
    pkg = PKGDWMAPR(connection, p_user)
    return pkg.create_update_mapping(
        p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm,
        p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt, p_stflg, p_blkprcrows
    )


def create_update_mapping_detail_with_user(
    connection: oracledb.Connection,
    p_mapref: str,
    p_trgclnm: str,
    p_trgcldtyp: str,
    p_trgkeyflg: str,
    p_trgkeyseq: int,
    p_trgcldesc: str,
    p_maplogic: str,
    p_keyclnm: str,
    p_valclnm: str,
    p_mapcmbcd: str,
    p_excseq: int,
    p_scdtyp: int,
    p_lgvrfyflg: str,
    p_lgvrfydt: datetime,
    p_user: str
) -> int:
    """
    Create or update mapping detail with user parameter
    
    Args:
        connection: Database connection
        p_user: User ID
        ... other parameters ...
        
    Returns:
        mapdtlid: Mapping detail ID
    """
    if not p_user:
        raise ValueError('Session user not provided.')
    
    pkg = PKGDWMAPR(connection, p_user)
    return pkg.create_update_mapping_detail(
        p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, p_trgkeyseq,
        p_trgcldesc, p_maplogic, p_keyclnm, p_valclnm, p_mapcmbcd,
        p_excseq, p_scdtyp, p_lgvrfyflg, p_lgvrfydt
    )


def validate_logic_with_user(
    connection: oracledb.Connection,
    p_mapref: str,
    p_user: str
) -> str:
    """
    Validate all mapping logic with user parameter
    
    Args:
        connection: Database connection
        p_mapref: Mapping reference
        p_user: User ID
        
    Returns:
        'Y' if valid, 'N' if invalid
    """
    if not p_user:
        raise ValueError('Session user not provided.')
    
    pkg = PKGDWMAPR(connection, p_user)
    return pkg.validate_all_logic(p_mapref)


def validate_mapping_details_with_user(
    connection: oracledb.Connection,
    p_mapref: str,
    p_user: str
) -> Tuple[str, str]:
    """
    Validate mapping details with user parameter
    
    Args:
        connection: Database connection
        p_mapref: Mapping reference
        p_user: User ID
        
    Returns:
        Tuple of (validation_flag: str, error_message: str)
    """
    if not p_user:
        raise ValueError('Session user not provided.')
    
    pkg = PKGDWMAPR(connection, p_user)
    return pkg.validate_mapping_details(p_mapref)


def activate_deactivate_mapping_with_user(
    connection: oracledb.Connection,
    p_mapref: str,
    p_stflg: str,
    p_user: str
) -> Tuple[bool, str]:
    """
    Activate or deactivate mapping with user parameter
    
    Args:
        connection: Database connection
        p_mapref: Mapping reference
        p_stflg: Status flag (A/N)
        p_user: User ID
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    if not p_user:
        raise ValueError('Session user not provided.')
    
    pkg = PKGDWMAPR(connection, p_user)
    return pkg.activate_deactivate_mapping(p_mapref, p_stflg)


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Example usage (requires valid database connection)
    print(f"PKGDWMAPR Python Package - Version: {PKGDWMAPR.version()}")
    print("This module provides Python equivalents of PKGDWMAPR PL/SQL package functions")

