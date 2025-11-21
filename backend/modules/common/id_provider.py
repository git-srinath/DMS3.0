from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from modules.logger import debug, warning


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
    global _DB_TYPE_CACHE
    if _DB_TYPE_CACHE:
        return _DB_TYPE_CACHE
    
    with _CONFIG_LOCK:
        if _DB_TYPE_CACHE:
            return _DB_TYPE_CACHE
        
        # Check connection module type
        connection = getattr(cursor, "connection", None)
        if connection:
            module_name = type(connection).__module__
            if "oracledb" in module_name or "cx_Oracle" in module_name:
                _DB_TYPE_CACHE = "ORACLE"
                return _DB_TYPE_CACHE
            if "psycopg" in module_name or "pg8000" in module_name:
                _DB_TYPE_CACHE = "POSTGRESQL"
                return _DB_TYPE_CACHE
        
        # Fallback: try database-specific query
        try:
            # Try Oracle-specific query
            cursor.execute("SELECT 1 FROM dual")
            _DB_TYPE_CACHE = "ORACLE"
            return _DB_TYPE_CACHE
        except Exception:
            try:
                # Try PostgreSQL-specific query
                cursor.execute("SELECT version()")
                _DB_TYPE_CACHE = "POSTGRESQL"
                return _DB_TYPE_CACHE
            except Exception:
                raise IdProviderError(
                    "Unsupported database type. Metadata database must be Oracle or PostgreSQL."
                )


def next_id(cursor, entity_name: str) -> int:
    """
    Generate the next identifier for the given entity.
    
    Supports only Oracle and PostgreSQL for metadata operations.

    Args:
        cursor: Database cursor with access to DWPARAMS/DWIDPOOL (metadata DB).
               Must be Oracle or PostgreSQL connection.
        entity_name: Logical entity/sequence name (e.g., 'DWPRCLOGSEQ').

    Returns:
        Integer identifier.
    """
    if not cursor:
        raise IdProviderError("Cursor is required to generate IDs")

    entity_key = entity_name.upper()
    config = _get_config(cursor)
    mode = config.resolve_mode(entity_key).upper()

    if mode == "SEQUENCE":
        return _next_sequence_value(cursor, entity_name)
    if mode == "TABLE_COUNTER":
        return _next_table_counter_value(cursor, entity_key, config.block_size)

    raise IdProviderError(f"Unsupported ID generation mode: {mode}. Supported: SEQUENCE, TABLE_COUNTER")


def _get_config(cursor) -> _IdConfig:
    global _config_cache
    if _config_cache:
        return _config_cache

    with _CONFIG_LOCK:
        if _config_cache:
            return _config_cache
        _config_cache = _load_config(cursor)
        return _config_cache


def _load_config(cursor) -> _IdConfig:
    """
    Load ID generation configuration from DWPARAMS table.
    Supports both Oracle and PostgreSQL parameter binding.
    """
    overrides: Dict[str, str] = {}
    default_mode = DEFAULT_MODE
    block_size = DEFAULT_BLOCK_SIZE
    db_type = _detect_db_type(cursor)

    # Use database-specific parameter binding
    if db_type == "ORACLE":
        cursor.execute(
            """
            SELECT PRCD, PRVAL
            FROM DWPARAMS
            WHERE PRTYP = :prtyp
              AND (
                    PRCD = :mode_key OR
                    PRCD = :block_key OR
                    PRCD LIKE :override_prefix
                  )
            """,
            {
                "prtyp": CONFIG_PARAM_TYPE,
                "mode_key": GLOBAL_MODE_KEY,
                "block_key": GLOBAL_BLOCK_SIZE_KEY,
                "override_prefix": f"{OVERRIDE_PREFIX}%",
            },
        )
    elif db_type == "POSTGRESQL":
        cursor.execute(
            """
            SELECT PRCD, PRVAL
            FROM DWPARAMS
            WHERE PRTYP = %s
              AND (
                    PRCD = %s OR
                    PRCD = %s OR
                    PRCD LIKE %s
                  )
            """,
            (
                CONFIG_PARAM_TYPE,
                GLOBAL_MODE_KEY,
                GLOBAL_BLOCK_SIZE_KEY,
                f"{OVERRIDE_PREFIX}%",
            ),
        )
    else:
        raise IdProviderError(f"Unsupported database type for config loading: {db_type}")

    for prcd, prval in cursor.fetchall():
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
    db_type = _detect_db_type(cursor)
    sequence_identifier = _sanitize_identifier(sequence_name)
    
    if db_type == "ORACLE":
        cursor.execute(f"SELECT {sequence_identifier}.NEXTVAL FROM dual")
    elif db_type == "POSTGRESQL":
        # PostgreSQL uses nextval('sequence_name') function
        cursor.execute(f"SELECT nextval('{sequence_identifier}')")
    else:
        raise IdProviderError(f"Unsupported database type for sequences: {db_type}")
    
    row = cursor.fetchone()
    if not row or row[0] is None:
        raise IdProviderError(f"Sequence {sequence_name} returned no value")
    return int(row[0])


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
    Reserve a block of IDs from DWIDPOOL table. Supports Oracle and PostgreSQL.
    """
    db_type = _detect_db_type(cursor)
    effective_block_size = max(default_block_size, 1)

    # Use database-specific SQL syntax
    if db_type == "ORACLE":
        cursor.execute(
            """
            SELECT current_value, NVL(block_size, :default_block)
            FROM DWIDPOOL
            WHERE entity_name = :entity
            FOR UPDATE
            """,
            {"entity": entity_key, "default_block": effective_block_size},
        )
    elif db_type == "POSTGRESQL":
        cursor.execute(
            """
            SELECT current_value, COALESCE(block_size, %s)
            FROM DWIDPOOL
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
                INSERT INTO DWIDPOOL (entity_name, current_value, block_size, updated_at)
                VALUES (:entity, 0, :block_size, SYSTIMESTAMP)
                """,
                {"entity": entity_key, "block_size": effective_block_size},
            )
        elif db_type == "POSTGRESQL":
            cursor.execute(
                """
                INSERT INTO DWIDPOOL (entity_name, current_value, block_size, updated_at)
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
            UPDATE DWIDPOOL
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
            UPDATE DWIDPOOL
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
            warning("Could not commit DWIDPOOL update immediately; relying on caller transaction.")

    return next_start, next_end

