'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  TextField,
  Autocomplete,
  Box,
  Typography,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Tooltip,
  Divider,
} from '@mui/material'
import {
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { message } from 'antd'

/**
 * SqlPrefillDialog
 *
 * Props:
 * - open: boolean
 * - onClose: () => void
 * - onApply: ({ columns, sqlCode, sqlContent, connectionId }) => void
 * - darkMode: boolean
 * - connections: array (optional) – existing mapper connections for reuse
 */
const SqlPrefillDialog = ({
  open,
  onClose,
  onApply,
  darkMode,
  connections: initialConnections = [],
}) => {
  // SQL selection state
  const [sqlCodes, setSqlCodes] = useState([])
  const [selectedSqlCode, setSelectedSqlCode] = useState('')
  const [sqlContent, setSqlContent] = useState('')
  const [isLoadingSqlCodes, setIsLoadingSqlCodes] = useState(false)

  // Connection selection
  const [connections, setConnections] = useState(initialConnections || [])
  const [selectedConnectionId, setSelectedConnectionId] = useState(null)
  const [isLoadingConnections, setIsLoadingConnections] = useState(false)

  // Column extraction state
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractedColumns, setExtractedColumns] = useState([])
  const [selectedColumns, setSelectedColumns] = useState({})
  const [editingTargetType, setEditingTargetType] = useState({})
  
  // Key column selection state - tracks which columns are key columns and their sequence
  const [keyColumns, setKeyColumns] = useState({}) // { columnName: { isKey: boolean, keySeq: number } }

  // Data type options from parameter
  const [dataTypeOptions, setDataTypeOptions] = useState([])
  const [isLoadingDataTypes, setIsLoadingDataTypes] = useState(false)

  // Duplicate detection & registration state
  const [duplicateCheckResult, setDuplicateCheckResult] = useState(null)
  const [isCheckingDuplicate, setIsCheckingDuplicate] = useState(false)
  const [newSqlCode, setNewSqlCode] = useState('')
  const [isSavingSql, setIsSavingSql] = useState(false)

  const isDark = !!darkMode

  const resetState = useCallback(() => {
    setSelectedSqlCode('')
    setSqlContent('')
    setSelectedConnectionId(null)
    setExtractedColumns([])
    setSelectedColumns({})
    setEditingTargetType({})
    setKeyColumns({})
    setDuplicateCheckResult(null)
    setIsExtracting(false)
    setIsCheckingDuplicate(false)
    setNewSqlCode('')
    setIsSavingSql(false)
  }, [])

  // Fetch SQL codes from Manage SQL
  const fetchSqlCodes = useCallback(async () => {
    setIsLoadingSqlCodes(true)
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-all-sql-codes`
      )
      const result = await response.json()
      if (result.success) {
        setSqlCodes(result.data || [])
      } else {
        message.error(result.message || 'Failed to fetch SQL codes')
      }
    } catch (err) {
      console.error('SqlPrefillDialog: error fetching SQL codes', err)
      message.error('Network error while fetching SQL codes')
    } finally {
      setIsLoadingSqlCodes(false)
    }
  }, [])

  // Fetch connections (reuse mapper /manage-sql connections)
  const fetchConnections = useCallback(async () => {
    // If parent already provided connections, don't refetch unless empty
    if ((connections || []).length > 0) return
    setIsLoadingConnections(true)
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/manage-sql/get-connections`
      )
      const result = await response.json()
      if (Array.isArray(result)) {
        setConnections(result)
      } else {
        console.error('SqlPrefillDialog: unexpected connections response', result)
        setConnections([])
      }
    } catch (err) {
      console.error('SqlPrefillDialog: error fetching connections', err)
      message.error('Failed to load database connections')
      setConnections([])
    } finally {
      setIsLoadingConnections(false)
    }
  }, [connections])

  // Fetch data type options from parameter
  const fetchDataTypeOptions = useCallback(async () => {
    if (dataTypeOptions.length > 0) return
    setIsLoadingDataTypes(true)
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/mapper/get-parameter-mapping-datatype`
      )
      if (!response.ok) {
        throw new Error('Failed to fetch data type options')
      }
      const result = await response.json()
      setDataTypeOptions(result || [])
    } catch (err) {
      console.error('SqlPrefillDialog: error fetching datatype options', err)
      message.error('Failed to load data type options')
    } finally {
      setIsLoadingDataTypes(false)
    }
  }, [dataTypeOptions.length])

  // When dialog opens, load initial data
  useEffect(() => {
    if (open) {
      fetchSqlCodes()
      fetchConnections()
      fetchDataTypeOptions()
    } else {
      resetState()
    }
  }, [open, fetchSqlCodes, fetchConnections, fetchDataTypeOptions, resetState])

  const handleSelectSqlCode = (event, newValue) => {
    const value = newValue || ''
    setSelectedSqlCode(value)
    if (!value) return

    // When user selects a code, fetch its logic to prefill SQL content
    const loadSql = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-sql-logic?sql_code=${encodeURIComponent(
            value
          )}`
        )
        const result = await response.json()
        if (result.success && result.data) {
          setSqlContent(result.data.sql_content || '')
          if (result.data.connection_id) {
            setSelectedConnectionId(result.data.connection_id)
          }
        } else {
          message.error(result.message || 'Failed to load SQL logic')
        }
      } catch (err) {
        console.error('SqlPrefillDialog: error fetching SQL logic', err)
        message.error('Network error while fetching SQL logic')
      }
    }

    loadSql()
  }

  const handleExtractColumns = async () => {
    const trimmedSql = (sqlContent || '').trim()
    if (!selectedSqlCode && !trimmedSql) {
      message.error('Please select an SQL code or enter SQL text')
      return
    }

    setIsExtracting(true)
    setDuplicateCheckResult(null)
    try {
      const body = {
        sql_code: selectedSqlCode || null,
        sql_content: trimmedSql || null,
        connection_id: selectedConnectionId
          ? Number(selectedConnectionId)
          : null,
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/mapper/extract-sql-columns`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(body),
        }
      )

      const result = await response.json()
      if (!response.ok || !result.success) {
        message.error(
          result.detail ||
            result.message ||
            'Failed to extract columns from SQL'
        )
        return
      }

      const cols = Array.isArray(result.columns) ? result.columns : []
      if (cols.length === 0) {
        message.warning('No columns found in SQL result')
        return
      }

      setExtractedColumns(cols)

      // Default: all columns selected
      const defaultSelection = {}
      cols.forEach((c) => {
        defaultSelection[c.column_name] = {
          selected: true,
          targetDataType:
            c.suggested_data_type ||
            (c.suggested_data_type_options &&
              c.suggested_data_type_options[0]) ||
            '',
        }
      })
      setSelectedColumns(defaultSelection)

      // If server returned normalized SQL, keep it (e.g., from sql_code)
      if (result.sql_content) {
        setSqlContent(result.sql_content)
      }
    } catch (err) {
      console.error('SqlPrefillDialog: error extracting columns', err)
      message.error('Unexpected error while extracting columns')
    } finally {
      setIsExtracting(false)
    }
  }

  const handleToggleColumn = (columnName, checked) => {
    setSelectedColumns((prev) => ({
      ...prev,
      [columnName]: {
        ...(prev[columnName] || {}),
        selected: checked,
      },
    }))
  }

  const handleChangeColumnType = (columnName, newType) => {
    setSelectedColumns((prev) => ({
      ...prev,
      [columnName]: {
        ...(prev[columnName] || {}),
        targetDataType: newType || '',
      },
    }))
    // After choosing a type, collapse the editor for that row
    setEditingTargetType((prev) => ({ ...prev, [columnName]: false }))
  }

  const handleSelectAllColumns = () => {
    setSelectedColumns((prev) => {
      const updated = { ...prev }
      extractedColumns.forEach((c) => {
        const name = c.column_name
        updated[name] = {
          ...(updated[name] || {}),
          selected: true,
        }
      })
      return updated
    })
  }

  const handleDeselectAllColumns = () => {
    setSelectedColumns((prev) => {
      const updated = { ...prev }
      extractedColumns.forEach((c) => {
        const name = c.column_name
        updated[name] = {
          ...(updated[name] || {}),
          selected: false,
        }
      })
      return updated
    })
  }

  // Handle key column toggle - auto-assigns sequence number
  const handleToggleKeyColumn = (columnName, checked) => {
    // When checking key column, also ensure the column is selected
    if (checked) {
      setSelectedColumns((prev) => ({
        ...prev,
        [columnName]: {
          ...(prev[columnName] || {}),
          selected: true,
        },
      }))
    }
    
    setKeyColumns((prev) => {
      if (checked) {
        // Find the next available sequence number
        const existingSeqs = Object.values(prev)
          .filter((v) => v.isKey)
          .map((v) => v.keySeq)
        const nextSeq = existingSeqs.length > 0 ? Math.max(...existingSeqs) + 1 : 1
        return {
          ...prev,
          [columnName]: { isKey: true, keySeq: nextSeq },
        }
      } else {
        // Remove key status and resequence remaining keys
        const updated = { ...prev }
        delete updated[columnName]
        
        // Resequence remaining key columns to keep sequence contiguous
        const keyEntries = Object.entries(updated)
          .filter(([, v]) => v.isKey)
          .sort((a, b) => a[1].keySeq - b[1].keySeq)
        
        keyEntries.forEach(([name], idx) => {
          updated[name] = { isKey: true, keySeq: idx + 1 }
        })
        
        return updated
      }
    })
  }

  const selectedColumnList = useMemo(
    () =>
      extractedColumns.filter((c) => {
        const sel = selectedColumns[c.column_name]
        return sel && sel.selected
      }),
    [extractedColumns, selectedColumns]
  )

  // Function to clean and format source data type
  const formatSourceDataType = (dataType, precision, scale) => {
    if (!dataType) return '-'
    
    // Clean up the data type string - remove prefixes, suffixes, and angle brackets
    let cleaned = String(dataType)
      .replace(/<DbType\s+/gi, '') // Remove <DbType prefix
      .replace(/DB_TYPE_/gi, '')   // Remove DB_TYPE_ prefix
      .replace(/DB_/gi, '')        // Remove DB_ prefix
      .replace(/>/g, '')            // Remove closing angle bracket
      .replace(/\(/g, '')           // Remove opening parenthesis (we'll add our own)
      .replace(/\)/g, '')           // Remove closing parenthesis
      .trim()
    
    // Add precision and scale if available
    if (precision !== null && precision !== undefined) {
      if (scale !== null && scale !== undefined && scale !== 0) {
        cleaned = `${cleaned}(${precision},${scale})`
      } else {
        cleaned = `${cleaned}(${precision})`
      }
    }
    
    return cleaned
  }

  // Categorize parameter option by code/value (used to filter dropdown)
  const getOptionCategory = (option) => {
    const code = String(option?.PRCD || option?.prcd || '').toUpperCase()
    const val = String(option?.PRVAL || option?.prval || '').toUpperCase()
    const txt = `${code} ${val}`

    // Order matters: detect timestamp before time/date collisions
    if (/TIMESTAMP|DATETIME/.test(txt)) return 'timestamp'
    if (/\bDATE\b/.test(txt)) return 'date'
    if (/\bTIME\b/.test(txt)) return 'time'
    if (/(DECIMAL|NUMERIC|NUMBER|BIGINT|SMALLINT|INTEGER|\bINT\b|FLOAT|DOUBLE|MONEY)/.test(txt)) return 'numeric'
    if (/(CHAR|VARCHAR|NCHAR|NVARCHAR|STRING|TEXT|CLOB)/.test(txt)) return 'string'
    return 'other'
  }

  // Categorize source type (from DB) to drive filtering
  const getSourceCategory = (sourceType) => {
    const st = String(sourceType || '').toUpperCase()
    if (/TIMESTAMP|DATETIME/.test(st)) return 'timestamp'
    if (/\bDATE\b/.test(st)) return 'date'
    if (/\bTIME\b/.test(st)) return 'time'
    if (/(NUMBER|NUMERIC|DECIMAL|BIGINT|SMALLINT|\bINT\b|FLOAT|DOUBLE)/.test(st)) return 'numeric'
    if (/(CHAR|VARCHAR|NCHAR|NVARCHAR|STRING|TEXT|CLOB)/.test(st)) return 'string'
    return 'other'
  }

  const handleApplyToForm = async () => {
    if (selectedColumnList.length === 0) {
      message.error('Please select at least one column to apply')
      return
    }

    const trimmedSql = (sqlContent || '').trim()

    // Existing SQL code: apply directly using registered code
    if (selectedSqlCode) {
      const columnsPayload = selectedColumnList.map((c) => {
        const sel = selectedColumns[c.column_name] || {}
        const keyInfo = keyColumns[c.column_name] || {}
        return {
          columnName: c.column_name,
          sourceDataType: c.source_data_type || null,
          targetDataType: sel.targetDataType || '',
          isPrimaryKey: c.is_primary_key || false,
          nullable: c.nullable,
          isKeyColumn: keyInfo.isKey || false,
          keyColumnSeq: keyInfo.keySeq || null,
        }
      })

      onApply?.({
        columns: columnsPayload,
        sqlCode: selectedSqlCode,
        sqlContent,
        connectionId: selectedConnectionId,
      })
      onClose?.()
      return
    }

    // New SQL: must have SQL text and a code, and must be registered in Manage SQL
    if (!trimmedSql) {
      message.error('SQL content is empty. Please enter SQL text.')
      return
    }

    const codeToSave = (newSqlCode || '').trim()
    if (!codeToSave) {
      message.error('Please enter a SQL Code to register this SQL in Manage SQL')
      return
    }
    if (/\s/.test(codeToSave)) {
      message.error('SQL Code cannot contain spaces')
      return
    }

    // Build columns payload once
    const columnsPayload = selectedColumnList.map((c) => {
      const sel = selectedColumns[c.column_name] || {}
      const keyInfo = keyColumns[c.column_name] || {}
      return {
        columnName: c.column_name,
        sourceDataType: c.source_data_type || null,
        targetDataType: sel.targetDataType || '',
        isPrimaryKey: c.is_primary_key || false,
        nullable: c.nullable,
        isKeyColumn: keyInfo.isKey || false,
        keyColumnSeq: keyInfo.keySeq || null,
      }
    })

    // First, run duplicate check to inform the user (does not block usage)
    setIsCheckingDuplicate(true)
    try {
      const dupResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/mapper/check-sql-duplicate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sql_content: trimmedSql,
            similarity_threshold: 0.7,
          }),
        }
      )
      const dupResult = await dupResponse.json()
      if (dupResponse.ok) {
        setDuplicateCheckResult(dupResult)
        const hasSimilar =
          dupResult.has_exact_match ||
          (Array.isArray(dupResult.similar_queries) &&
            dupResult.similar_queries.length > 0)
        if (dupResult.has_exact_match && dupResult.exact_match_code) {
          message.warning(
            `An exact SQL already exists with code ${dupResult.exact_match_code}.`
          )
        } else if (hasSimilar) {
          message.warning(
            `Found ${dupResult.similar_queries.length} similar SQL definition(s).`
          )
        }
        // We still allow registering under a new code; this is informational.
      } else {
        message.error(
          dupResult.detail ||
            dupResult.message ||
            'Failed to check duplicate SQL'
        )
        return
      }
    } catch (err) {
      console.error('SqlPrefillDialog: error checking duplicates', err)
      message.error('Unexpected error while checking duplicate SQL')
      return
    } finally {
      setIsCheckingDuplicate(false)
    }

    // Now register the new SQL in Manage SQL via /manage-sql/save-sql
    setIsSavingSql(true)
    try {
      const saveResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/manage-sql/save-sql`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sql_code: codeToSave,
            sql_content: trimmedSql,
            connection_id: selectedConnectionId || null,
          }),
        }
      )
      const saveResult = await saveResponse.json()
      if (!saveResponse.ok || !saveResult.success) {
        message.error(
          saveResult.message ||
            saveResult.detail ||
            'Failed to register SQL in Manage SQL'
        )
        return
      }

      const finalCode = saveResult.sql_code || codeToSave
      message.success(`SQL registered as ${finalCode} and applied to mapping`)

      onApply?.({
        columns: columnsPayload,
        sqlCode: finalCode,
        sqlContent: trimmedSql,
        connectionId: selectedConnectionId,
      })
      onClose?.()
    } catch (err) {
      console.error('SqlPrefillDialog: error saving SQL to Manage SQL', err)
      message.error('Network or server error while registering SQL')
    } finally {
      setIsSavingSql(false)
    }
  }

  const handleClose = () => {
    if (isExtracting || isCheckingDuplicate) {
      return
    }
    onClose?.()
  }

  const renderSqlStep = () => (
    <>
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Prefill from SQL
        </Typography>
        <IconButton size="small" onClick={handleClose}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ pt: 1.5, pb: 1.5 }}>
        {/* SQL selection header (1–2 rows max) */}
        <Box mb={1.5}>
          <Box mb={1} display="flex" alignItems="center" gap={1}>
            {/* SQL Code selector */}
            <Autocomplete
              value={selectedSqlCode || null}
              onChange={handleSelectSqlCode}
              options={sqlCodes}
              loading={isLoadingSqlCodes}
              size="small"
              sx={{ flex: 2 }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="1. SQL Code (optional)"
                  placeholder="Choose from Manage SQL"
                />
              )}
            />
            <Tooltip title="Refresh SQL codes">
              <span>
                <IconButton
                  size="small"
                  onClick={fetchSqlCodes}
                  disabled={isLoadingSqlCodes}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>

            {/* Connection dropdown */}
            <Autocomplete
              value={
                connections.find((c) => c.conid === selectedConnectionId) ||
                null
              }
              onChange={(event, newValue) =>
                setSelectedConnectionId(newValue ? newValue.conid : null)
              }
              options={connections}
              loading={isLoadingConnections}
              size="small"
              sx={{ flex: 2 }}
              getOptionLabel={(option) =>
                `${option.connm} (${option.dbhost}/${option.dbsrvnm})`
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="2. Source Connection (optional)"
                  placeholder="Leave empty to use metadata connection"
                />
              )}
            />

            {/* New SQL Code (only when not using existing code) */}
            {!selectedSqlCode && (
              <TextField
                label="New SQL Code"
                value={newSqlCode}
                onChange={(e) =>
                  setNewSqlCode(
                    e.target.value ? e.target.value.replace(/\s/g, '') : ''
                  )
                }
                size="small"
                sx={{ flex: 1 }}
                helperText="Required for new SQL. No spaces."
              />
            )}
          </Box>

          <TextField
            label="3. SQL Text (basic query; optional if SQL code is selected)"
            value={sqlContent}
            onChange={(e) => setSqlContent(e.target.value)}
            multiline
            minRows={3}
            maxRows={4}
            fullWidth
            size="small"
          />
        </Box>

        <Divider sx={{ mb: 1 }} />

        {/* Combined Columns & Data Types section below SQL header */}
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={1}
        >
          <Typography variant="body2" fontWeight={500}>
            Columns extracted: {extractedColumns.length}
          </Typography>
          <Box display="flex" alignItems="center" gap={1}>
            <Button
              size="small"
              onClick={handleSelectAllColumns}
              disabled={extractedColumns.length === 0}
              sx={{ textTransform: 'none', fontSize: '0.75rem' }}
            >
              Select All
            </Button>
            <Button
              size="small"
              onClick={handleDeselectAllColumns}
              disabled={extractedColumns.length === 0}
              sx={{ textTransform: 'none', fontSize: '0.75rem' }}
            >
              Deselect All
            </Button>
          </Box>
        </Box>

        <Box
          sx={{
            maxHeight: 280,
            overflowY: 'auto',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={
                          selectedColumnList.length ===
                            extractedColumns.length &&
                          extractedColumns.length > 0
                        }
                        indeterminate={
                          selectedColumnList.length > 0 &&
                          selectedColumnList.length < extractedColumns.length
                        }
                        onChange={(e) =>
                          e.target.checked
                            ? handleSelectAllColumns()
                            : handleDeselectAllColumns()
                        }
                      />
                    }
                    sx={{ m: 0 }}
                  />
                </TableCell>
                <TableCell>Column</TableCell>
                <TableCell>Source Type</TableCell>
                <TableCell>Target Type (from parameter)</TableCell>
                <TableCell align="center">Key Column</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {extractedColumns.map((col) => {
                const sel = selectedColumns[col.column_name] || {}
                const targetType = sel.targetDataType || ''

                const precision =
                  typeof col.source_precision === 'number'
                    ? col.source_precision
                    : null
                const scale =
                  typeof col.source_scale === 'number' ? col.source_scale : null

                const formattedType = formatSourceDataType(
                  col.source_data_type,
                  precision,
                  scale
                )

                return (
                  <TableRow
                    key={col.column_name}
                    hover
                    selected={!!sel.selected}
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={!!sel.selected}
                        onChange={(e) =>
                          handleToggleColumn(col.column_name, e.target.checked)
                        }
                      />
                    </TableCell>
                    <TableCell>{col.column_name}</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formattedType}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {editingTargetType[col.column_name] ? (
                        <Autocomplete
                          value={
                            dataTypeOptions.find(
                              (opt) =>
                                String(opt.PRCD || opt.prcd) ===
                                String(targetType)
                            ) || null
                          }
                          onChange={(event, newValue) =>
                            handleChangeColumnType(
                              col.column_name,
                              newValue ? newValue.PRCD || newValue.prcd : ''
                            )
                          }
                          options={(function () {
                            // Filter options based on source type category
                            const srcCat = getSourceCategory(col.source_data_type)
                            let allowed = []
                            if (srcCat === 'string') allowed = ['string']
                            else if (srcCat === 'numeric') allowed = ['numeric']
                            else if (srcCat === 'date') allowed = ['date', 'timestamp', 'time']
                            else if (srcCat === 'timestamp') allowed = ['timestamp', 'date', 'time']
                            else if (srcCat === 'time') allowed = ['time', 'timestamp', 'date']
                            // If no specific category, don't filter
                            if (allowed.length === 0) return dataTypeOptions
                            const filtered = dataTypeOptions.filter((opt) =>
                              allowed.includes(getOptionCategory(opt))
                            )
                            // Fallback to all if filtering yields nothing
                            return filtered.length > 0 ? filtered : dataTypeOptions
                          })()}
                          size="small"
                          getOptionLabel={(option) => {
                            const code = option.PRCD || option.prcd || ''
                            const desc = option.PRDESC || option.prdesc || ''
                            if (code && desc) return `${code} - ${desc}`
                            if (code) return code
                            return desc || ''
                          }}
                          renderInput={(params) => (
                            <TextField
                              {...params}
                              placeholder="Select data type"
                              size="small"
                            />
                          )}
                        />
                      ) : (
                        <Box
                          display="flex"
                          alignItems="center"
                          justifyContent="space-between"
                          gap={1}
                        >
                          <Typography variant="body2">
                            {targetType || '-'}
                          </Typography>
                          <Tooltip title="Change target type">
                            <span>
                              <IconButton
                                size="small"
                                onClick={() =>
                                  setEditingTargetType((prev) => ({
                                    ...prev,
                                    [col.column_name]: true,
                                  }))
                                }
                                disabled={dataTypeOptions.length === 0}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </Box>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                        <Checkbox
                          checked={!!(keyColumns[col.column_name]?.isKey)}
                          onChange={(e) =>
                            handleToggleKeyColumn(col.column_name, e.target.checked)
                          }
                          size="small"
                        />
                        {keyColumns[col.column_name]?.isKey && (
                          <Typography
                            variant="caption"
                            sx={{
                              fontWeight: 600,
                              color: 'primary.main',
                              minWidth: 16,
                            }}
                          >
                            {keyColumns[col.column_name]?.keySeq}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </Box>

        <Typography
          variant="caption"
          color="textSecondary"
          sx={{ display: 'block', mt: 1 }}
        >
          All fields in the mapper screen remain fully editable after prefill.
          Use the source precision/scale information above to choose the most
          suitable target data type.
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: 2, py: 1.5 }}>
        <Button
          onClick={handleClose}
          sx={{ textTransform: 'none', fontSize: '0.8rem' }}
        >
          Cancel
        </Button>
        <Button
          variant="outlined"
          onClick={handleExtractColumns}
          disabled={isExtracting || isLoadingDataTypes}
          sx={{
            textTransform: 'none',
            fontSize: '0.8rem',
            mr: 1,
          }}
        >
          {isExtracting ? (
            <CircularProgress size={18} color="inherit" />
          ) : (
            'Extract Columns'
          )}
        </Button>
        <Button
          variant="contained"
          onClick={handleApplyToForm}
          disabled={
            isCheckingDuplicate || isSavingSql || selectedColumnList.length === 0
          }
          sx={{
            textTransform: 'none',
            fontSize: '0.8rem',
          }}
        >
          {isCheckingDuplicate || isSavingSql ? (
            <CircularProgress size={18} color="inherit" />
          ) : (
            'Apply to Form'
          )}
        </Button>
      </DialogActions>
    </>
  )

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      fullWidth
      maxWidth="md"
      PaperProps={{
        sx: {
          borderRadius: 2,
          overflow: 'hidden',
          bgcolor: isDark ? 'rgb(17,24,39)' : 'background.paper',
        },
      }}
    >
      {renderSqlStep()}
    </Dialog>
  )
}

export default SqlPrefillDialog


