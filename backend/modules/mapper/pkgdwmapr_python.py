"""
Python conversion of PKGDWMAPR PL/SQL Package
This module provides Python equivalents of the Oracle PL/SQL package functions
for mapping validation and processing.

Change history:
date        who              Remarks
----------- ---------------- ----------------------------------------------------------------------------------------
13-Nov-2025 Converted        Converted from PL/SQL to Python
"""

import os
import re
from datetime import datetime
from modules.logger import logger, info, warning, error
import oracledb
from modules.common.id_provider import next_id as get_next_id

# Package constants
G_NAME = 'PKGDWMAPR_PY'
G_VER = 'V001'
G_USER = None

class PKGDWMAPRError(Exception):
    """Custom exception for PKGDWMAPR errors"""
    pass

def version():
    """Return package version"""
    return f"{G_NAME}:{G_VER}"

def _nvl(value, default):
    """Python equivalent of Oracle's NVL function"""
    return default if value is None else value

def _raise_error(proc_name, error_code, param_info, exception=None):
    """Raise an error with formatted message"""
    if exception:
        msg = f"{G_NAME}.{proc_name} - Error {error_code}: {param_info} - {str(exception)}"
    else:
        msg = f"{G_NAME}.{proc_name} - Error {error_code}: {param_info}"
    error(msg)
    raise PKGDWMAPRError(msg)

def create_update_sql(connection, p_dwmaprsqlcd, p_dwmaprsql, p_sqlconid=None):
    """
    Function to record SQL query
    Returns: dwmaprsqlid
    
    Args:
        connection: Database connection
        p_dwmaprsqlcd: SQL code identifier
        p_dwmaprsql: SQL query content
        p_sqlconid: Source database connection ID (from DWDBCONDTLS). 
                    If None, uses metadata connection.
    """
    w_procnm = 'CREATE_UPDATE_SQL'
    w_parm = f'SqlCode={p_dwmaprsqlcd}'[:100]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Validation
        if not p_dwmaprsqlcd or p_dwmaprsqlcd.strip() == '':
            w_msg = 'The mapping SQL Code cannot be null.'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        if ' ' in p_dwmaprsqlcd:
            w_msg = 'Space(s) not allowed to form mapping SQL Code.'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        if not p_dwmaprsql or len(str(p_dwmaprsql).strip()) == 0:
            w_msg = 'The SQL Query cannot be blank.'
            _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        # Validate connection ID if provided
        sqlconid_val = None
        if p_sqlconid is not None and str(p_sqlconid).strip() != '':
            try:
                sqlconid_val = int(p_sqlconid)
                # Validate connection exists and is active
                cursor.execute("""
                    SELECT conid FROM DWDBCONDTLS 
                    WHERE conid = :1 AND curflg = 'Y'
                """, [sqlconid_val])
                if not cursor.fetchone():
                    w_msg = f'Invalid or inactive source connection ID: {sqlconid_val}'
                    _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
            except ValueError:
                w_msg = f'Source connection ID must be numeric: {p_sqlconid}'
                _raise_error(w_procnm, '131', f'{w_parm}::{w_msg}')
        
        # Check if SQL code already exists
        query = """
            SELECT dwmaprsqlid, dwmaprsqlcd, dwmaprsql, sqlconid
            FROM dwmaprsql
            WHERE dwmaprsqlcd = :1
            AND curflg = 'Y'
        """
        cursor.execute(query, [p_dwmaprsqlcd])
        row = cursor.fetchone()
        
        w_return = None
        w_res = 1  # Assume different
        
        if row:
            w_rec_dwmaprsqlid, w_rec_dwmaprsqlcd, w_rec_dwmaprsql, w_rec_sqlconid = row
            # Compare the SQL text and connection ID
            if w_rec_dwmaprsql == p_dwmaprsql and w_rec_sqlconid == sqlconid_val:
                w_res = 0  # Same
            w_return = w_rec_dwmaprsqlid
        
        if w_res != 0:  # SQL is different or new
            if row:  # Update existing to set curflg = 'N'
                try:
                    cursor.execute("""
                        UPDATE dwmaprsql
                        SET curflg = 'N', recupdt = sysdate
                        WHERE dwmaprsqlcd = :1
                        AND curflg = 'Y'
                    """, [p_dwmaprsqlcd])
                except Exception as e:
                    _raise_error(w_procnm, '132', w_parm, e)
            
            # Insert new record
            try:
                # Remove trailing semicolons
                clean_sql = re.sub(r';+$', '', str(p_dwmaprsql).strip())
                
                # Generate SQL ID using ID provider (supports Oracle/PostgreSQL)
                sql_id = get_next_id(cursor, "DWMAPRSQLSEQ")
                
                cursor.execute("""
                    INSERT INTO dwmaprsql (dwmaprsqlid, dwmaprsqlcd, dwmaprsql, sqlconid, reccrdt, recupdt, curflg)
                    VALUES (:1, :2, :3, :4, sysdate, sysdate, 'Y')
                """, [sql_id, p_dwmaprsqlcd, clean_sql, sqlconid_val])
                w_return = sql_id
            except Exception as e:
                _raise_error(w_procnm, '133', w_parm, e)
        
        connection.commit()
        return w_return
        
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '134', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def create_update_mapping(connection, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp,
                         p_trgtbnm, p_frqcd, p_srcsystm, p_lgvrfyflg, p_lgvrfydt,
                         p_stflg, p_blkprcrows, p_trgconid=None, p_user=None,
                         p_chkpntstrtgy='AUTO', p_chkpntclnm=None, p_chkpntenbld='Y'):
    """
    Function to create or update mappings, returns mapping ID
    Any change is historised.
    
    Args:
        p_trgconid: Target database connection ID (from DWDBCONDTLS). 
                    If None, uses metadata connection.
        p_chkpntstrtgy: Checkpoint strategy ('AUTO', 'KEY', 'PYTHON', 'NONE')
        p_chkpntclnm: Checkpoint column name for KEY strategy
        p_chkpntenbld: Enable checkpoint ('Y'/'N')
    """
    w_procnm = 'CREATE_UPDATE_MAPPING'
    w_parm = f'Mapref={p_mapref}-{p_mapdesc}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
        w_parm = f'Mapref={p_mapref}-{p_mapdesc} User={p_user}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Validation
        w_msg = None
        if not p_mapref or p_mapref.strip() == '':
            w_msg = 'Mapping reference not provided.'
        elif _nvl(p_trgtbtyp, 'X') not in ('NRM', 'DIM', 'FCT', 'MRT'):
            w_msg = 'Invalid target table type (valid: NRM,DIM,FCT,MRT).'
        elif _nvl(p_frqcd, 'NA') not in ('NA', 'ID', 'DL', 'WK', 'FN', 'MN', 'HY', 'YR'):
            w_msg = 'Invalid frequency code (Valid: ID,DL,WK,FN,MN,HY,YR).'
        elif _nvl(p_stflg, 'N') not in ('A', 'N'):
            w_msg = 'Invalid status (Valid: A,N).'
        elif _nvl(p_lgvrfyflg, 'N') not in ('Y', 'N'):
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
        
        # Validate p_blkprcrows (may come as string from frontend)
        if not w_msg and p_blkprcrows is not None:
            try:
                blkprcrows_int = int(p_blkprcrows)
                if blkprcrows_int < 0:
                    w_msg = 'The number of Bulk Processing Rows cannot be negative.'
            except (ValueError, TypeError):
                w_msg = f'Invalid Bulk Processing Rows value "{p_blkprcrows}" - must be numeric.'
        
        # Validate p_trgconid (target connection ID) if provided
        if not w_msg and p_trgconid is not None:
            try:
                trgconid_int = int(p_trgconid)
                # Validate connection exists and is active
                cursor.execute("""
                    SELECT conid FROM DWDBCONDTLS 
                    WHERE conid = :1 AND curflg = 'Y'
                """, [trgconid_int])
                if not cursor.fetchone():
                    w_msg = f'Invalid target connection ID "{p_trgconid}". Connection not found or inactive.'
            except (ValueError, TypeError):
                w_msg = f'Invalid target connection ID "{p_trgconid}" - must be numeric.'
        
        # Validate checkpoint parameters
        if not w_msg and p_chkpntstrtgy not in ('AUTO', 'KEY', 'PYTHON', 'NONE'):
            w_msg = 'Invalid checkpoint strategy (Valid: AUTO, KEY, PYTHON, NONE).'
        if not w_msg and p_chkpntenbld not in ('Y', 'N'):
            w_msg = 'Invalid checkpoint enabled flag (Valid: Y, N).'
        
        if w_msg:
            _raise_error(w_procnm, '103', f'{w_parm}::{w_msg}')
        
        # Check if mapping already exists
        query = """
            SELECT mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd,
                   srcsystm, lgvrfyflg, lgvrfydt, stflg, blkprcrows, trgconid,
                   chkpntstrtgy, chkpntclnm, chkpntenbld
            FROM dwmapr
            WHERE mapref = :1
            AND curflg = 'Y'
        """
        cursor.execute(query, [p_mapref])
        row = cursor.fetchone()
        
        w_chg = 'Y'
        w_mapid = None
        
        if row:
            w_mapr_rec = {
                'mapid': row[0], 'mapref': row[1], 'mapdesc': row[2],
                'trgschm': row[3], 'trgtbtyp': row[4], 'trgtbnm': row[5],
                'frqcd': row[6], 'srcsystm': row[7], 'lgvrfyflg': row[8],
                'lgvrfydt': row[9], 'stflg': row[10], 'blkprcrows': row[11],
                'trgconid': row[12], 'chkpntstrtgy': row[13], 'chkpntclnm': row[14],
                'chkpntenbld': row[15]
            }
            
            # Check if there are any changes (convert numeric fields to int for comparison)
            p_blkprcrows_int = int(p_blkprcrows) if p_blkprcrows is not None else 0
            p_trgconid_int = int(p_trgconid) if p_trgconid is not None else None
            
            # Normalize checkpoint column name for comparison (handle None vs empty string)
            existing_chkpntclnm = w_mapr_rec['chkpntclnm'] if w_mapr_rec['chkpntclnm'] else None
            new_chkpntclnm = p_chkpntclnm if p_chkpntclnm and p_chkpntclnm.strip() else None
            
            if (w_mapr_rec['mapdesc'] == p_mapdesc and
                w_mapr_rec['trgschm'] == p_trgschm and
                w_mapr_rec['trgtbtyp'] == p_trgtbtyp and
                w_mapr_rec['trgtbnm'] == p_trgtbnm and
                w_mapr_rec['frqcd'] == p_frqcd and
                w_mapr_rec['srcsystm'] == p_srcsystm and
                _nvl(w_mapr_rec['blkprcrows'], 0) == p_blkprcrows_int and
                w_mapr_rec['trgconid'] == p_trgconid_int and
                _nvl(w_mapr_rec['chkpntstrtgy'], 'AUTO') == _nvl(p_chkpntstrtgy, 'AUTO') and
                existing_chkpntclnm == new_chkpntclnm and
                _nvl(w_mapr_rec['chkpntenbld'], 'Y') == _nvl(p_chkpntenbld, 'Y')):
                # No changes
                w_chg = 'N'
                w_mapid = w_mapr_rec['mapid']
            
            if w_chg == 'Y':
                # Mark old record as not current
                try:
                    cursor.execute("""
                        UPDATE dwmapr
                        SET curflg = 'N', recupdt = sysdate, uptdby = :1
                        WHERE mapid = :2
                    """, [G_USER, w_mapr_rec['mapid']])
                except Exception as e:
                    _raise_error(w_procnm, '101', f'{w_parm} mapid={w_mapr_rec["mapid"]}', e)
        
        # Insert new record if changes detected
        if w_chg == 'Y':
            try:
                # Generate mapping ID using ID provider (supports Oracle/PostgreSQL)
                map_id = get_next_id(cursor, "DWMAPRSEQ")
                
                # Ensure numeric fields are integers (may come as strings from frontend)
                blkprcrows_val = int(p_blkprcrows) if p_blkprcrows is not None else None
                trgconid_val = int(p_trgconid) if p_trgconid is not None else None
                
                cursor.execute("""
                    INSERT INTO dwmapr 
                    (mapid, mapref, mapdesc, trgschm, trgtbtyp, trgtbnm, frqcd, srcsystm,
                     lgvrfyflg, lgvrfydt, stflg, reccrdt, recupdt, curflg, blkprcrows, trgconid, crtdby, uptdby,
                     chkpntstrtgy, chkpntclnm, chkpntenbld)
                    VALUES 
                    (:1, :2, :3, :4, :5, :6, :7, :8,
                     :9, :10, :11, sysdate, sysdate, 'Y', :12, :13, :14, :15,
                     :16, :17, :18)
                """, [map_id, p_mapref, p_mapdesc, p_trgschm, p_trgtbtyp, p_trgtbnm, p_frqcd, p_srcsystm,
                      _nvl(p_lgvrfyflg, 'N'), p_lgvrfydt, _nvl(p_stflg, 'N'), blkprcrows_val,
                      trgconid_val, G_USER, G_USER, _nvl(p_chkpntstrtgy, 'AUTO'), 
                      p_chkpntclnm, _nvl(p_chkpntenbld, 'Y')])
                w_mapid = map_id
            except Exception as e:
                _raise_error(w_procnm, '102', w_parm, e)
        
        connection.commit()
        return w_mapid
        
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '103', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def create_update_mapping_detail(connection, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg,
                                 p_trgkeyseq, p_trgcldesc, p_maplogic, p_keyclnm,
                                 p_valclnm, p_mapcmbcd, p_excseq, p_scdtyp,
                                 p_lgvrfyflg, p_lgvrfydt, p_user=None):
    """
    Function to create or update mapping details, returns mapping detail ID
    Any change is historised.
    """
    w_procnm = 'CREATE_UPDATE_MAPPING_DETAIL'
    w_parm = f'Mapref={p_mapref} Trgcol={p_trgclnm}'[:400]
    
    if p_user:
        global G_USER
        G_USER = p_user
        w_parm = f'Mapref={p_mapref}-{p_trgclnm} User={p_user}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Validation
        w_msg = None
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
        elif _nvl(p_trgkeyflg, 'N') not in ('Y', 'N'):
            w_msg = 'Invalid value for Key flag (valid: Y or blank).'
        elif p_trgkeyflg == 'Y' and not p_trgkeyseq:
            w_msg = 'Key sequence must be provided for Primary key columns.'
        elif not p_maplogic:
            w_msg = 'Mapping logic must be provided.'
        elif p_maplogic and (not p_keyclnm or not p_valclnm):
            w_msg = 'Key column and value column must be provided.'
        
        # Convert and validate numeric fields (they may come as strings from frontend)
        if not w_msg:
            try:
                # Validate p_scdtyp
                scdtyp_int = int(_nvl(p_scdtyp, 1))
                if scdtyp_int not in (1, 2, 3):
                    w_msg = 'Invalid values for SCD type (valid: 1, 2, or 3).'
            except (ValueError, TypeError):
                w_msg = f'Invalid SCD type value "{p_scdtyp}" - must be numeric: 1, 2, or 3.'
        
        if not w_msg and p_trgkeyseq is not None:
            try:
                int(p_trgkeyseq)
            except (ValueError, TypeError):
                w_msg = f'Invalid key sequence value "{p_trgkeyseq}" - must be numeric.'
        
        if not w_msg and p_excseq is not None:
            try:
                int(p_excseq)
            except (ValueError, TypeError):
                w_msg = f'Invalid execution sequence value "{p_excseq}" - must be numeric.'
        
        if not w_msg and ((p_lgvrfyflg and not p_lgvrfydt) or (not p_lgvrfyflg and p_lgvrfydt)):
            w_msg = 'Both logic verification flag and date must be provide or both must be blank.'
        
        # Check if datatype is valid
        if not w_msg:
            cursor.execute("""
                SELECT prval
                FROM dwparams
                WHERE prtyp = 'Datatype'
                AND prcd = :1
            """, [p_trgcldtyp])
            dtyp_row = cursor.fetchone()
            
            if not dtyp_row:
                w_msg = f'The datatype {p_trgcldtyp} for {p_trgclnm} is invalid.\nPlease verify parameters for "Datatype".'
        
        if w_msg:
            _raise_error(w_procnm, '107', f'{w_parm}::{w_msg}')
        
        # Check if maplogic is a SQL code reference (length <= 100)
        w_msql_rec = None
        if p_maplogic and len(p_maplogic) <= 100:
            try:
                cursor.execute("""
                    SELECT dwmaprsqlid, dwmaprsqlcd
                    FROM dwmaprsql
                    WHERE dwmaprsqlcd = :1
                    AND curflg = 'Y'
                """, [p_maplogic])
                msql_row = cursor.fetchone()
                if msql_row:
                    w_msql_rec = {'dwmaprsqlid': msql_row[0], 'dwmaprsqlcd': msql_row[1]}
            except Exception as e:
                _raise_error(w_procnm, '135', w_parm, e)
        
        # Check if mapping reference exists
        try:
            cursor.execute("""
                SELECT mapref, mapid
                FROM dwmapr
                WHERE mapref = :1
                AND curflg = 'Y'
            """, [p_mapref])
            mapr_row = cursor.fetchone()
            
            if not mapr_row:
                w_msg = 'Invalid mapping reference.'
                _raise_error(w_procnm, '107', f'{w_parm}::{w_msg}')
        except PKGDWMAPRError:
            raise
        except Exception as e:
            _raise_error(w_procnm, '136', w_parm, e)
        
        # Check if mapping detail already exists
        cursor.execute("""
            SELECT mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq,
                   trgcldesc, maplogic, keyclnm, valclnm, mapcmbcd, excseq, scdtyp
            FROM dwmaprdtl
            WHERE mapref = :1
            AND trgclnm = :2
            AND curflg = 'Y'
        """, [p_mapref, p_trgclnm])
        row = cursor.fetchone()
        
        w_chg = 'Y'
        w_mapdtlid = None
        
        if row:
            w_maprdtl_rec = {
                'mapdtlid': row[0], 'mapref': row[1], 'trgclnm': row[2],
                'trgcldtyp': row[3], 'trgkeyflg': row[4], 'trgkeyseq': row[5],
                'trgcldesc': row[6], 'maplogic': row[7], 'keyclnm': row[8],
                'valclnm': row[9], 'mapcmbcd': row[10], 'excseq': row[11],
                'scdtyp': row[12]
            }
            
            # Check if there are any changes (convert numeric fields to int for comparison)
            p_trgkeyseq_int = int(p_trgkeyseq) if p_trgkeyseq is not None else None
            p_excseq_int = int(p_excseq) if p_excseq is not None else None
            p_scdtyp_int = int(p_scdtyp) if p_scdtyp is not None else None
            
            if (w_maprdtl_rec['mapref'] == p_mapref and
                w_maprdtl_rec['trgclnm'] == p_trgclnm and
                w_maprdtl_rec['trgcldtyp'] == p_trgcldtyp and
                _nvl(w_maprdtl_rec['trgkeyflg'], 'N') == _nvl(p_trgkeyflg, 'N') and
                _nvl(w_maprdtl_rec['trgkeyseq'], -1) == _nvl(p_trgkeyseq_int, -1) and
                w_maprdtl_rec['trgcldesc'] == p_trgcldesc and
                w_maprdtl_rec['maplogic'] == p_maplogic and
                w_maprdtl_rec['keyclnm'] == p_keyclnm and
                w_maprdtl_rec['valclnm'] == p_valclnm and
                w_maprdtl_rec['mapcmbcd'] == p_mapcmbcd and
                w_maprdtl_rec['excseq'] == p_excseq_int and
                w_maprdtl_rec['scdtyp'] == p_scdtyp_int):
                # No changes
                w_chg = 'N'
                w_mapdtlid = w_maprdtl_rec['mapdtlid']
            
            if w_chg == 'Y':
                # Mark old record as not current
                try:
                    cursor.execute("""
                        UPDATE dwmaprdtl
                        SET curflg = 'N', recupdt = sysdate, uptdby = :1
                        WHERE mapref = :2
                        AND mapdtlid = :3
                        AND curflg = 'Y'
                    """, [G_USER, w_maprdtl_rec['mapref'], w_maprdtl_rec['mapdtlid']])
                except Exception as e:
                    _raise_error(w_procnm, '105', f'{w_parm} Mapref={w_maprdtl_rec["mapref"]} Trgclnm={w_maprdtl_rec["trgclnm"]}', e)
        
        # Insert new record if changes detected
        if w_chg == 'Y':
            try:
                maprsqlcd_val = w_msql_rec['dwmaprsqlcd'] if w_msql_rec else None
                # Generate mapping detail ID using ID provider (supports Oracle/PostgreSQL)
                mapdtlid = get_next_id(cursor, "DWMAPRDTLSEQ")
                
                # Ensure numeric fields are integers (they may come as strings from frontend)
                trgkeyseq_val = int(p_trgkeyseq) if p_trgkeyseq is not None else None
                excseq_val = int(p_excseq) if p_excseq is not None else None
                scdtyp_val = int(_nvl(p_scdtyp, 1))
                
                cursor.execute("""
                    INSERT INTO dwmaprdtl
                    (mapdtlid, mapref, trgclnm, trgcldtyp, trgkeyflg, trgkeyseq, trgcldesc,
                     maplogic, maprsqlcd, keyclnm, valclnm, mapcmbcd, excseq, scdtyp, lgvrfyflg,
                     lgvrfydt, reccrdt, recupdt, curflg, crtdby, uptdby)
                    VALUES
                    (:1, :2, :3, :4, :5, :6, :7,
                     :8, :9, :10, :11, :12, :13, :14,
                     :15, sysdate, sysdate, 'Y', :16, :17)
                """, [mapdtlid, p_mapref, p_trgclnm, p_trgcldtyp, p_trgkeyflg, trgkeyseq_val, p_trgcldesc,
                      p_maplogic, maprsqlcd_val, p_keyclnm, p_valclnm, p_mapcmbcd, excseq_val,
                      scdtyp_val, p_lgvrfyflg, p_lgvrfydt, G_USER, G_USER])
                w_mapdtlid = mapdtlid
            except Exception as e:
                _raise_error(w_procnm, '106', w_parm, e)
        
        connection.commit()
        return w_mapdtlid
        
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '107', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def _validate_sql(connection, p_logic, p_keyclnm, p_valclnm, p_flg='Y'):
    """
    Private procedure to validate SQL
    Returns: error message (None if valid)
    """
    w_procnm = 'VALIDATE_SQL'
    w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}'[:400]
    
    p_error = None
    w_cursor = None
    
    try:
        if p_flg == 'Y':
            if not p_keyclnm:
                return 'Key column(s) not provided.'
            if not p_valclnm:
                return 'Value column(s) not provided.'
        
        if not p_logic or len(str(p_logic).strip()) == 0:
            return 'SQL provided is empty.'
        
        # Build SQL to validate
        if p_flg == 'Y':
            w_sql = f'select {p_keyclnm},{p_valclnm} from ({p_logic}) sql1 where rownum = 1'
        else:
            w_sql = str(p_logic)
        
        # Replace DWT_PARAM placeholders with NULL for validation
        w_sql = re.sub(r'DWT_PARAM\d+', 'NULL', w_sql, flags=re.IGNORECASE)
        w_sql = re.sub(r';+$', '', w_sql)  # Remove trailing semicolons
        
        # Try to parse the SQL
        cursor = connection.cursor()
        try:
            cursor.parse(w_sql)
        except Exception as e:
            p_error = str(e)
        finally:
            cursor.close()
        
        return p_error
        
    except Exception as e:
        _raise_error(w_procnm, '138', w_parm, e)

def validate_sql(connection, p_logic):
    """
    Function to validate SQL
    Returns: 'Y' if valid, 'N' if invalid
    """
    w_procnm = 'VALIDATE_SQL'
    w_parm = 'SQL Validate with Clob.'
    
    try:
        w_err = _validate_sql(connection, p_logic, None, None, 'N')
        
        if w_err:
            return 'N'
        else:
            return 'Y'
    except Exception as e:
        _raise_error(w_procnm, '139', w_parm, e)

def validate_logic(connection, p_logic, p_keyclnm, p_valclnm):
    """
    Function to validate mapping logic
    Returns: 'Y' if valid, 'N' if invalid
    """
    w_procnm = 'VALIDATE_LOGIC'
    w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}:{p_logic}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Check if this is a SQL code reference
        w_rec = None
        if p_logic and len(p_logic) <= 100:
            cursor.execute("""
                SELECT dwmaprsqlcd, dwmaprsql
                FROM dwmaprsql
                WHERE dwmaprsqlcd = :1
                AND curflg = 'Y'
            """, [p_logic[:100]])
            row = cursor.fetchone()
            if row:
                w_rec = {'dwmaprsqlcd': row[0], 'dwmaprsql': row[1]}
        
        # Get the actual SQL logic
        if w_rec:
            w_logic = w_rec['dwmaprsql']
        else:
            w_logic = p_logic
        
        # Validate the SQL
        w_error = _validate_sql(connection, w_logic, p_keyclnm, p_valclnm, 'Y')
        
        if w_error:
            return 'N'
        else:
            return 'Y'
    
    except Exception as e:
        _raise_error(w_procnm, '109', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def validate_logic2(connection, p_logic, p_keyclnm, p_valclnm):
    """
    Function to validate mapping logic with error output
    Returns: (is_valid, error_message)
    """
    w_procnm = 'VALIDATE_LOGIC2'
    w_parm = f'KeyColumn={p_keyclnm} ValColumn={p_valclnm}:{p_logic}'[:400]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Check if this is a SQL code reference
        w_rec = None
        if p_logic and len(p_logic) <= 100:
            cursor.execute("""
                SELECT dwmaprsqlcd, dwmaprsql
                FROM dwmaprsql
                WHERE dwmaprsqlcd = :1
                AND curflg = 'Y'
            """, [p_logic[:100]])
            row = cursor.fetchone()
            if row:
                w_rec = {'dwmaprsqlcd': row[0], 'dwmaprsql': row[1]}
        
        # Get the actual SQL logic
        if w_rec:
            w_logic = w_rec['dwmaprsql']
        else:
            w_logic = p_logic
        
        # Validate the SQL
        p_err = _validate_sql(connection, w_logic, p_keyclnm, p_valclnm, 'Y')
        
        if p_err:
            return 'N', p_err
        else:
            return 'Y', None
    
    except Exception as e:
        _raise_error(w_procnm, '110', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def validate_logic_for_mapref(connection, p_mapref, p_user=None):
    """
    Function to validate all mapping logic for a mapping reference
    Returns: 'Y' if all valid, 'N' if any invalid
    """
    w_procnm = 'VALIDATE_LOGIC'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
        w_parm = f'Mapref={p_mapref} User={p_user}'[:200]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Get all mapping details
        cursor.execute("""
            SELECT m.mapref, md.mapdtlid, m.trgtbnm, md.trgclnm,
                   md.keyclnm, md.valclnm, md.maplogic
            FROM dwmapr m, dwmaprdtl md
            WHERE m.mapref = :1
            AND m.curflg = 'Y'
            AND md.mapref = m.mapref
            AND md.curflg = 'Y'
        """, [p_mapref])
        
        rows = cursor.fetchall()
        w_return = 'Y'
        
        for row in rows:
            mapref, mapdtlid, trgtbnm, trgclnm, keyclnm, valclnm, maplogic = row
            
            w_pm = f'TB:{trgtbnm}-TC:{trgclnm}:Key:{keyclnm}-Val:{valclnm}-{maplogic}'[:400]
            
            try:
                w_res, w_err = validate_logic2(connection, maplogic, keyclnm, valclnm)
                
                if w_res == 'N' and w_err:
                    # Insert error record
                    try:
                        # Generate error ID using ID provider (supports Oracle/PostgreSQL)
                        err_id = get_next_id(cursor, "DWMAPERRSEQ")
                        cursor.execute("""
                            INSERT INTO dwmaperr(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                            VALUES (:1, :2, :3, :4, 'ERR', :5, sysdate)
                        """, [err_id, mapdtlid, mapref, maplogic, w_err])
                    except Exception as e:
                        _raise_error(w_procnm, '111', w_pm, e)
                
                if w_return == 'Y':
                    w_return = w_res
                
                # Update mapping detail with verification result
                cursor.execute("""
                    UPDATE dwmaprdtl
                    SET lgvrfydt = sysdate, lgvrfyflg = :1
                    WHERE mapref = :2
                    AND mapdtlid = :3
                    AND curflg = 'Y'
                """, [w_res, mapref, mapdtlid])
                
            except Exception as e:
                _raise_error(w_procnm, '112', w_pm, e)
        
        # Additional validation: Check for duplicate value columns within mapping code
        if w_return == 'Y':
            cursor.execute("""
                SELECT valclnm, mapcmbcd, count(*) cnt
                FROM dwmaprdtl
                WHERE curflg = 'Y'
                AND mapref = :1
                GROUP BY valclnm, mapcmbcd
                HAVING count(*) > 1
            """, [p_mapref])
            c2_row = cursor.fetchone()
            
            if c2_row and c2_row[2] > 1:
                w_err = f'Target value column name ({c2_row[0]}) cannot repeat within a mapping code({c2_row[1]}). Please use alias if required.'
                w_return = 'N'
                
                try:
                    # Generate error ID using ID provider (supports Oracle/PostgreSQL)
                    err_id = get_next_id(cursor, "DWMAPERRSEQ")
                    cursor.execute("""
                        INSERT INTO dwmaperr(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                        VALUES (:1, null, :2, null, 'ERR', :3, sysdate)
                    """, [err_id, p_mapref, w_err])
                except Exception as e:
                    _raise_error(w_procnm, '127', w_parm, e)
        
        # Additional validation: Check for SQL code and mapping combination consistency
        if w_return == 'Y':
            cursor.execute("""
                SELECT maprsqlcd, mapcmbcd, count(*) cnt
                FROM (SELECT DISTINCT maprsqlcd, mapcmbcd
                      FROM dwmaprdtl
                      WHERE curflg = 'Y'
                      AND mapref = :1) x
                GROUP BY maprsqlcd, mapcmbcd
                HAVING count(*) > 1
            """, [p_mapref])
            c2_row = cursor.fetchone()
            
            if c2_row and c2_row[2] > 1:
                w_err = 'For a "Mapping Combination"/"SQL Query Code", more than 1 "SQL Query Code"/"Mapping Combination" is not allowed'
                w_return = 'N'
                
                try:
                    # Generate error ID using ID provider (supports Oracle/PostgreSQL)
                    err_id = get_next_id(cursor, "DWMAPERRSEQ")
                    cursor.execute("""
                        INSERT INTO dwmaperr(maperrid, mapdtlid, mapref, maplogic, errtyp, errmsg, reccrdt)
                        VALUES (:1, null, :2, null, 'ERR', :3, sysdate)
                    """, [err_id, p_mapref, w_err])
                except Exception as e:
                    _raise_error(w_procnm, '140', w_parm, e)
        
        # Update mapping record if all validations passed
        if w_return == 'Y':
            try:
                cursor.execute("""
                    UPDATE dwmapr
                    SET lgvrfydt = sysdate, lgvrfyflg = :1, lgvrfby = :2
                    WHERE mapref = :3
                    AND curflg = 'Y'
                """, [w_return, G_USER, p_mapref])
            except Exception as e:
                _raise_error(w_procnm, '113', f'MapRef={p_mapref}', e)
        
        connection.commit()
        return w_return
        
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '129', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def validate_mapping_details(connection, p_mapref, p_user=None):
    """
    Function to validate mapping details
    Returns: (is_valid, error_message)
    """
    w_procnm = 'VALIDATE_MAPPING_DETAILS'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        w_msg = None
        w_return = 'Y'
        
        # Validate logic first
        try:
            w_flg = validate_logic_for_mapref(connection, p_mapref, G_USER)
            
            if _nvl(w_flg, 'N') == 'N':
                w_msg = 'Some/All target columns logic validation failed, please verify logic(SQL).'
                w_return = 'N'
        except Exception as e:
            _raise_error(w_procnm, '115', w_parm, e)
        
        # Check primary key
        if not w_msg:
            try:
                cursor.execute("""
                    SELECT trgkeyseq, count(*) cnt
                    FROM dwmaprdtl
                    WHERE curflg = 'Y'
                    AND mapref = :1
                    AND trgkeyflg = 'Y'
                    GROUP BY trgkeyseq
                """, [p_mapref])
                pk_row = cursor.fetchone()
                
                if not pk_row or pk_row[1] == 0:
                    w_msg = 'Primary key not specified, primary key(s) is mandatory.'
                    w_return = 'N'
                elif pk_row[0] and pk_row[1] > 1:
                    w_msg = 'Primary sequence cannot repeat within mapping.'
                    w_return = 'N'
            except Exception as e:
                _raise_error(w_procnm, '125', w_parm, e)
        
        # Check for duplicate column names
        if not w_msg:
            try:
                cursor.execute("""
                    SELECT trgclnm, count(*) cnt
                    FROM dwmaprdtl
                    WHERE curflg = 'Y'
                    AND mapref = :1
                    GROUP BY trgclnm
                    HAVING count(*) > 1
                """, [p_mapref])
                cl_row = cursor.fetchone()
                
                if cl_row and cl_row[1] > 1:
                    w_msg = 'Target column name cannot repeat within mapping.'
                    w_return = 'N'
            except Exception as e:
                _raise_error(w_procnm, '126', w_parm, e)
        
        # Check for duplicate value columns
        if not w_msg:
            try:
                cursor.execute("""
                    SELECT valclnm, mapcmbcd, count(*) cnt
                    FROM dwmaprdtl
                    WHERE curflg = 'Y'
                    AND mapref = :1
                    GROUP BY valclnm, mapcmbcd
                    HAVING count(*) > 1
                """, [p_mapref])
                c2_row = cursor.fetchone()
                
                if c2_row and c2_row[2] > 1:
                    w_msg = f'Target value column name ({c2_row[0]}) cannot repeat within a mapping code({c2_row[1]}). Please use alias if required.'
                    w_return = 'N'
            except Exception as e:
                _raise_error(w_procnm, '130', w_parm, e)
        
        return w_return, w_msg
        
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '116', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def activate_deactivate_mapping(connection, p_mapref, p_stflg, p_user=None):
    """
    Procedure to activate or deactivate a mapping
    Returns: error_message (None if successful)
    """
    w_procnm = 'ACTIVATE_DEACTIVATE_MAPPING'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    if p_user:
        global G_USER
        G_USER = p_user
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        w_msg = None
        
        # Validation
        if _nvl(p_stflg, 'N') not in ('A', 'N'):
            w_msg = 'Invalid status flag (valid: A or N).'
        
        # If activating, validate mappings first
        if p_stflg == 'A' and not w_msg:
            try:
                w_flg, w_val_msg = validate_mapping_details(connection, p_mapref, G_USER)
                
                if _nvl(w_flg, 'N') == 'N':
                    w_msg = f'{w_val_msg}\nCannot activate mapping few columns logic failed.'
            except Exception as e:
                _raise_error(w_procnm, '118', w_parm, e)
            
            # If validation passed, update mapping status
            if not w_msg:
                cursor.execute("""
                    UPDATE dwmapr
                    SET stflg = :1, actby = :2, actdt = sysdate
                    WHERE mapref = :3
                    AND curflg = 'Y'
                """, [p_stflg, G_USER, p_mapref])
                connection.commit()
        
        return w_msg
        
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '119', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def delete_mapping(connection, p_mapref):
    """
    Procedure to delete mapping
    Returns: error_message (None if successful)
    """
    w_procnm = 'DELETE_MAPPING'
    w_parm = f'Mapref={p_mapref}'[:200]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Check if job exists for this mapping
        cursor.execute("""
            SELECT mapref, jobid
            FROM dwjob
            WHERE mapref = :1
            AND curflg = 'Y'
        """, [p_mapref])
        job_row = cursor.fetchone()
        
        if job_row:
            return f'The mapping "{p_mapref}" cannot be deleted because related job exists.'
        else:
            try:
                # Delete mapping details
                cursor.execute("""
                    DELETE FROM dwmaprdtl
                    WHERE mapref = :1
                """, [p_mapref])
                
                # Delete mapping
                cursor.execute("""
                    DELETE FROM dwmapr
                    WHERE mapref = :1
                """, [p_mapref])
                
                connection.commit()
                return None
                
            except Exception as e:
                _raise_error(w_procnm, '121', w_parm, e)
    
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '122', w_parm, e)
    finally:
        if cursor:
            cursor.close()

def delete_mapping_details(connection, p_mapref, p_trgclnm):
    """
    Procedure to delete mapping details
    Returns: error_message (None if successful)
    """
    w_procnm = 'DELETE_MAPPING_DETAILS'
    w_parm = f'Mapref={p_mapref} Trgclnm={p_trgclnm}'[:200]
    
    cursor = None
    try:
        cursor = connection.cursor()
        
        # Check if job detail exists for this mapping detail
        cursor.execute("""
            SELECT mapref, jobdtlid
            FROM dwjobdtl
            WHERE mapref = :1
            AND trgclnm = :2
            AND curflg = 'Y'
        """, [p_mapref, p_trgclnm])
        jd_row = cursor.fetchone()
        
        if jd_row:
            return f'The mapping detail for "{p_mapref}-{p_trgclnm}" cannot be deleted because related job detail exists.'
        else:
            try:
                # Delete mapping detail
                cursor.execute("""
                    DELETE FROM dwmaprdtl
                    WHERE mapref = :1
                    AND trgclnm = :2
                """, [p_mapref, p_trgclnm])
                
                connection.commit()
                return None
                
            except Exception as e:
                _raise_error(w_procnm, '123', w_parm, e)
    
    except PKGDWMAPRError:
        raise
    except Exception as e:
        _raise_error(w_procnm, '124', w_parm, e)
    finally:
        if cursor:
            cursor.close()

