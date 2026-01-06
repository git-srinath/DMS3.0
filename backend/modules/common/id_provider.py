from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Support both FastAPI (package import) and legacy Flask (relative import) contexts
try:
    from backend.modules.logger import debug, warning, info, error
except ImportError:  # When running Flask app.py directly inside backend
    from modules.logger import debug, warning, info, error


CONFIG_PARAM_TYPE = "DMSCONFIG"
GLOBAL_MODE_KEY = "ID_GENERATION_MODE"
GLOBAL_BLOCK_SIZE_KEY = "ID_BLOCK_SIZE"
OVERRIDE_PREFIX = "ID_MODE_"

DEFAULT_MODE = "SEQUENCE"
DEFAULT_BLOCK_SIZE = 500

_CONFIG_LOCK = threading.Lock()
_BLOCK_LOCK = threading.Lock()
_DB_TYPE_CACHE: Optional[str] = None


@dataclass
class _IdConfig:
    default_mode: str = DEFAULT_MODE
    block_size: int = DEFAULT_BLOCK_SIZE
    overrides: Dict[str, str] = None

    def resolve_mode(self, entity: str) -> str:
        if not self.overrides:
            return self.default_mode
        return self.overrides.get(entity.upper(), self.default_mode)


_config_cache: Optional[_IdConfig] = None
_block_cache: Dict[str, Tuple[int, int]] = {}


class IdProviderError(Exception):
    """Raised when ID generation fails."""


def refresh_id_config() -> None:
    """Clear cached configuration so it will be reloaded on next request."""
    global _config_cache, _DB_TYPE_CACHE
    with _CONFIG_LOCK:
        _config_cache = None
        _DB_TYPE_CACHE = None


def _detect_db_type(cursor) -> str:
    """
    Detect database type (Oracle or PostgreSQL) from cursor/connection.
    
    Returns:
        'ORACLE' or 'POSTGRESQL'
    """
    debug("_detect_db_type: Starting detection")
    global _DB_TYPE_CACHE
    if _DB_TYPE_CACHE:
        debug(f"_detect_db_type: Using cached type: {_DB_TYPE_CACHE}")
        return _DB_TYPE_CACHE
    
    # Check if lock is already held (to avoid deadlock)
    lock_held = _CONFIG_LOCK.locked()
    debug(f"_detect_db_type: Lock already held: {lock_held}")
    
    if lock_held:
        # Lock is already held by caller, don't try to acquire it again
        debug("_detect_db_type: Lock already held, skipping lock acquisition")
        # Just check cache and do detection without lock
        if _DB_TYPE_CACHE:
            return _DB_TYPE_CACHE
    else:
        debug("_detect_db_type: No cache, acquiring lock...")
        _CONFIG_LOCK.acquire()
        try:
            debug("_detect_db_type: Lock acquired")
            if _DB_TYPE_CACHE:
                debug(f"_detect_db_type: Type cached by another thread: {_DB_TYPE_CACHE}")
                return _DB_TYPE_CACHE
        except:
            _CONFIG_LOCK.release()
            raise
    
    try:
        # Check connection module type
        debug("_detect_db_type: Checking connection module type...")
        connection = getattr(cursor, "connection", None)
        if connection:
            module_name = type(connection).__module__
            debug(f"_detect_db_type: Connection module: {module_name}")
            if "oracledb" in module_name or "cx_Oracle" in module_name:
                _DB_TYPE_CACHE = "ORACLE"
                debug(f"_detect_db_type: Detected ORACLE from module")
                return _DB_TYPE_CACHE
            if "psycopg" in module_name or "pg8000" in module_name:
                _DB_TYPE_CACHE = "POSTGRESQL"
                debug(f"_detect_db_type: Detected POSTGRESQL from module")
                return _DB_TYPE_CACHE
        
        # Fallback: try database-specific query
        debug("_detect_db_type: Module detection failed, trying query-based detection...")
        try:
            # Try Oracle-specific query
            debug("_detect_db_type: Trying Oracle query (SELECT 1 FROM dual)...")
            cursor.execute("SELECT 1 FROM dual")
            _DB_TYPE_CACHE = "ORACLE"
            debug(f"_detect_db_type: Detected ORACLE from query")
            return _DB_TYPE_CACHE
        except Exception as e:
            debug(f"_detect_db_type: Oracle query failed: {str(e)}")
            try:
                # Try PostgreSQL-specific query
                debug("_detect_db_type: Trying PostgreSQL query (SELECT version())...")
                cursor.execute("SELECT version()")
                _DB_TYPE_CACHE = "POSTGRESQL"
                debug(f"_detect_db_type: Detected POSTGRESQL from query")
                return _DB_TYPE_CACHE
            except Exception as e2:
                error(f"_detect_db_type: Both queries failed. Oracle: {str(e)}, PostgreSQL: {str(e2)}")
                raise IdProviderError(
                    "Unsupported database type. Metadata database must be Oracle or PostgreSQL."
                )
    finally:
        if not lock_held:
            debug("_detect_db_type: Releasing lock")
            _CONFIG_LOCK.release()


def next_id(cursor, entity_name: str) -> int:
    """
    Generate the next identifier for the given entity.
    
    Supports only Oracle and PostgreSQL for metadata operations.

    Args:
        cursor: Database cursor with access to DMS_PARAMS/DMS_IDPOOL (metadata DB).
               Must be Oracle or PostgreSQL connection.
        entity_name: Logical entity/sequence name (e.g., 'DMS_PRCLOGSEQ').

    Returns:
        Integer identifier.
    """
    info(f"next_id called for entity: {entity_name}")
    if not cursor:
        error("Cursor is None in next_id")
        raise IdProviderError("Cursor is required to generate IDs")

    entity_key = entity_name.upper()
    info(f"Getting config for entity: {entity_key}")
    try:
        config = _get_config(cursor)
        info(f"Config retrieved: default_mode={config.default_mode}, block_size={config.block_size}")
    except Exception as e:
        error(f"Error getting config: {str(e)}", exc_info=True)
        raise
    
    mode = config.resolve_mode(entity_key).upper()
    info(f"Resolved mode for {entity_key}: {mode}")

    if mode == "SEQUENCE":
        info(f"Using SEQUENCE mode for {entity_name}")
        return _next_sequence_value(cursor, entity_name)
    if mode == "TABLE_COUNTER":
        info(f"Using TABLE_COUNTER mode for {entity_key}")
        return _next_table_counter_value(cursor, entity_key, config.block_size)

    error(f"Unsupported ID generation mode: {mode}")
    raise IdProviderError(f"Unsupported ID generation mode: {mode}. Supported: SEQUENCE, TABLE_COUNTER")


def _get_config(cursor) -> _IdConfig:
    global _config_cache
    info("_get_config called")
    if _config_cache:
        info("Using cached config")
        return _config_cache

    info("Acquiring config lock...")
    with _CONFIG_LOCK:
        info("Config lock acquired")
        if _config_cache:
            info("Config was loaded by another thread, using cached config")
            return _config_cache
        info("Loading config from database...")
        try:
            _config_cache = _load_config(cursor)
            info("Config loaded successfully")
            return _config_cache
        except Exception as e:
            error(f"Error in _load_config: {str(e)}", exc_info=True)
            raise


def _load_config(cursor) -> _IdConfig:
    """
    Load ID generation configuration from DMS_PARAMS table.
    Supports both Oracle and PostgreSQL parameter binding.
    """
    debug("_load_config: Function entry - starting")
    overrides: Dict[str, str] = {}
    default_mode = DEFAULT_MODE
    block_size = DEFAULT_BLOCK_SIZE
    debug("_load_config: Initialized default values")
    
    try:
        debug("_load_config: About to call _detect_db_type...")
        db_type = _detect_db_type(cursor)
        debug(f"_load_config: Database type detected: {db_type}")
        
        # For PostgreSQL, ensure clean transaction state
        if db_type == "POSTGRESQL":
            connection = getattr(cursor, "connection", None)
            if connection:
                try:
                    # Rollback any failed transaction to ensure clean state
                    if not getattr(connection, 'autocommit', False):
                        connection.rollback()
                        debug("_load_config: Rolled back any failed transaction for clean state")
                except Exception:
                    pass  # Ignore rollback errors
    except Exception as e:
        error(f"Error detecting database type in _load_config: {str(e)}", exc_info=True)
        # Use default mode if detection fails
        warning(f"Using default config due to detection failure")
        return _IdConfig(default_mode=default_mode, block_size=block_size, overrides=overrides)

    # Use database-specific parameter binding
    try:
        debug(f"_load_config: Preparing to query DMS_PARAMS with PRTYP={CONFIG_PARAM_TYPE}")
        if db_type == "ORACLE":
            query = """
                SELECT PRCD, PRVAL
                FROM DMS_PARAMS
                WHERE PRTYP = :prtyp
                  AND (
                        PRCD = :mode_key OR
                        PRCD = :block_key OR
                        PRCD LIKE :override_prefix
                      )
            """
            params = {
                "prtyp": CONFIG_PARAM_TYPE,
                "mode_key": GLOBAL_MODE_KEY,
                "block_key": GLOBAL_BLOCK_SIZE_KEY,
                "override_prefix": f"{OVERRIDE_PREFIX}%",
            }
            debug(f"_load_config: Executing Oracle query with params: {params}")
            cursor.execute(query, params)
        elif db_type == "POSTGRESQL":
            query = """
                SELECT PRCD, PRVAL
                FROM DMS_PARAMS
                WHERE PRTYP = %s
                  AND (
                        PRCD = %s OR
                        PRCD = %s OR
                        PRCD LIKE %s
                      )
            """
            params = (
                CONFIG_PARAM_TYPE,
                GLOBAL_MODE_KEY,
                GLOBAL_BLOCK_SIZE_KEY,
                f"{OVERRIDE_PREFIX}%",
            )
            debug(f"_load_config: Executing PostgreSQL query")
            debug(f"_load_config: Query parameters: PRTYP={CONFIG_PARAM_TYPE}, mode_key={GLOBAL_MODE_KEY}, block_key={GLOBAL_BLOCK_SIZE_KEY}")
            debug(f"_load_config: About to call cursor.execute()...")
            cursor.execute(query, params)
            debug(f"_load_config: cursor.execute() completed successfully")
        else:
            raise IdProviderError(f"Unsupported database type for config loading: {db_type}")
        
        debug(f"_load_config: About to call cursor.fetchall()...")
        rows = cursor.fetchall()
        debug(f"_load_config: fetchall() completed. Loaded {len(rows)} config rows from DMS_PARAMS")
        
        for prcd, prval in rows:
            key = (prcd or "").upper()
            if key == GLOBAL_MODE_KEY:
                default_mode = (prval or DEFAULT_MODE).upper()
            elif key == GLOBAL_BLOCK_SIZE_KEY:
                try:
                    block_size = int(prval)
                except (TypeError, ValueError):
                    block_size = DEFAULT_BLOCK_SIZE
            elif key.startswith(OVERRIDE_PREFIX):
                overrides[key[len(OVERRIDE_PREFIX) :].upper()] = (prval or DEFAULT_MODE).upper()
    except Exception as e:
        error(f"Error loading ID provider config from DMS_PARAMS: {str(e)}", exc_info=True)
        # Return default config if query fails
        warning(f"Using default ID generation config: mode={default_mode}, block_size={block_size}")
        return _IdConfig(default_mode=default_mode, block_size=block_size, overrides=overrides)

    debug(
        "ID Provider config loaded: default_mode=%s, block_size=%s, overrides=%s",
        default_mode,
        block_size,
        overrides,
    )

    return _IdConfig(default_mode=default_mode, block_size=block_size, overrides=overrides)


def _next_sequence_value(cursor, sequence_name: str) -> int:
    """
    Get next value from sequence. Supports Oracle and PostgreSQL.
    """
    try:
        db_type = _detect_db_type(cursor)
        info(f"Getting next sequence value for {sequence_name} on {db_type}")
        sequence_identifier = _sanitize_identifier(sequence_name)
        
        if db_type == "ORACLE":
            query = f"SELECT {sequence_identifier}.NEXTVAL FROM dual"
            info(f"Executing Oracle sequence query: {query}")
            cursor.execute(query)
        elif db_type == "POSTGRESQL":
            # PostgreSQL uses nextval('sequence_name') function
            query = f"SELECT nextval('{sequence_identifier}')"
            info(f"Executing PostgreSQL sequence query: {query}")
            cursor.execute(query)
        else:
            raise IdProviderError(f"Unsupported database type for sequences: {db_type}")
        
        row = cursor.fetchone()
        if not row or row[0] is None:
            raise IdProviderError(f"Sequence {sequence_name} returned no value")
        seq_value = int(row[0])
        info(f"Sequence {sequence_name} returned value: {seq_value}")
        return seq_value
    except Exception as e:
        error(f"Error getting next sequence value for {sequence_name}: {str(e)}", exc_info=True)
        raise


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_.\$]+$")


def _sanitize_identifier(identifier: str) -> str:
    if not identifier or not _IDENTIFIER_PATTERN.match(identifier):
        raise IdProviderError(f"Invalid identifier for ID generation: {identifier}")
    return identifier


def _next_table_counter_value(cursor, entity_key: str, default_block_size: int) -> int:
    with _BLOCK_LOCK:
        cached = _block_cache.get(entity_key)
        if cached:
            next_value, max_value = cached
            if next_value <= max_value:
                _block_cache[entity_key] = (next_value + 1, max_value)
                return next_value

    start, end = _reserve_block(cursor, entity_key, default_block_size)
    with _BLOCK_LOCK:
        _block_cache[entity_key] = (start + 1, end)
    return start


def _reserve_block(cursor, entity_key: str, default_block_size: int) -> Tuple[int, int]:
    """
    Reserve a block of IDs from DMS_IDPOOL table. Supports Oracle and PostgreSQL.
    """
    db_type = _detect_db_type(cursor)
    effective_block_size = max(default_block_size, 1)

    # Use database-specific SQL syntax
    if db_type == "ORACLE":
        cursor.execute(
            """
            SELECT current_value, NVL(block_size, :default_block)
            FROM DMS_IDPOOL
            WHERE entity_name = :entity
            FOR UPDATE
            """,
            {"entity": entity_key, "default_block": effective_block_size},
        )
    elif db_type == "POSTGRESQL":
        cursor.execute(
            """
            SELECT current_value, COALESCE(block_size, %s)
            FROM DMS_IDPOOL
            WHERE entity_name = %s
            FOR UPDATE
            """,
            (effective_block_size, entity_key),
        )
    else:
        raise IdProviderError(f"Unsupported database type for table counter: {db_type}")

    row = cursor.fetchone()

    if not row:
        # Insert new row if entity doesn't exist
        if db_type == "ORACLE":
            cursor.execute(
                """
                INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size, updated_at)
                VALUES (:entity, 0, :block_size, SYSTIMESTAMP)
                """,
                {"entity": entity_key, "block_size": effective_block_size},
            )
        elif db_type == "POSTGRESQL":
            cursor.execute(
                """
                INSERT INTO DMS_IDPOOL (entity_name, current_value, block_size, updated_at)
                VALUES (%s, 0, %s, CURRENT_TIMESTAMP)
                """,
                (entity_key, effective_block_size),
            )
        current_value = 0
        block_size = effective_block_size
    else:
        current_value, block_size = row
        block_size = block_size or effective_block_size

    next_start = int(current_value) + 1
    next_end = next_start + int(block_size) - 1

    # Update the counter
    if db_type == "ORACLE":
        cursor.execute(
            """
            UPDATE DMS_IDPOOL
            SET current_value = :current_value,
                block_size = :block_size,
                updated_at = SYSTIMESTAMP
            WHERE entity_name = :entity
            """,
            {
                "current_value": next_end,
                "block_size": block_size,
                "entity": entity_key,
            },
        )
    elif db_type == "POSTGRESQL":
        cursor.execute(
            """
            UPDATE DMS_IDPOOL
            SET current_value = %s,
                block_size = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE entity_name = %s
            """,
            (next_end, block_size, entity_key),
        )

    connection = getattr(cursor, "connection", None)
    if connection:
        try:
            connection.commit()
        except Exception:
            warning("Could not commit DMS_IDPOOL update immediately; relying on caller transaction.")

    return next_start, next_end

