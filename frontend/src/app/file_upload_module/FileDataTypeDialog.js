'use client'

import React, { useState, useEffect, useMemo, useCallback } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Autocomplete,
  TextField,
  Box,
  Typography,
  Tooltip,
  Divider,
} from '@mui/material'
import {
  Close as CloseIcon,
  Edit as EditIcon,
} from '@mui/icons-material'
import { message } from 'antd'

/**
 * FileDataTypeDialog
 * 
 * Props:
 * - open: boolean
 * - onClose: () => void
 * - onApply: ({ columnMappings }) => void
 * - darkMode: boolean
 * - columns: array of column names from file
 * - previewData: array of preview rows
 * - existingMappings: array of existing column mappings (optional)
 */
const FileDataTypeDialog = ({
  open,
  onClose,
  onApply,
  darkMode,
  columns = [],
  previewData = [],
  existingMappings = [],
}) => {
  const [dataTypeOptions, setDataTypeOptions] = useState([])
  const [isLoadingDataTypes, setIsLoadingDataTypes] = useState(false)
  const [selectedColumns, setSelectedColumns] = useState({})
  const [editingTargetType, setEditingTargetType] = useState({})

  const isDark = !!darkMode

  // Infer column types from preview data
  const inferredTypes = useMemo(() => {
    const types = {}
    if (!previewData || previewData.length === 0 || !columns) return types

    columns.forEach((col) => {
      const values = previewData
        .map((row) => row[col])
        .filter((v) => v !== null && v !== undefined && v !== '')

      if (values.length === 0) {
        types[col] = { category: 'string', suggested: '' }
        return
      }

      // Check for dates (various formats)
      const datePatterns = [
        /^\d{4}-\d{2}-\d{2}/, // YYYY-MM-DD
        /^\d{2}\/\d{2}\/\d{4}/, // MM/DD/YYYY
        /^\d{2}-\d{2}-\d{4}/, // MM-DD-YYYY
      ]
      const looksDate = values.some((v) =>
        datePatterns.some((pattern) => pattern.test(String(v)))
      )

      // Check for timestamps
      const timestampPattern = /^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}/
      const looksTimestamp = values.some((v) =>
        timestampPattern.test(String(v))
      )

      // Check for numeric
      const numericValues = values.filter((v) => !isNaN(Number(v)) && v !== '')
      const looksNumeric = numericValues.length === values.length && numericValues.length > 0

      // Check for boolean
      const booleanValues = values.filter((v) =>
        ['true', 'false', '1', '0', 'yes', 'no', 'y', 'n'].includes(String(v).toLowerCase())
      )
      const looksBoolean = booleanValues.length === values.length && booleanValues.length > 0

      if (looksTimestamp) {
        types[col] = { category: 'timestamp', suggested: 'Timestamp' }
      } else if (looksDate) {
        types[col] = { category: 'date', suggested: 'Date' }
      } else if (looksBoolean) {
        types[col] = { category: 'boolean', suggested: 'Boolean' }
      } else if (looksNumeric) {
        // Determine if integer or decimal
        const hasDecimal = numericValues.some((v) => String(v).includes('.'))
        const maxLength = Math.max(...numericValues.map((v) => String(Math.abs(Number(v))).replace('.', '').length))
        
        if (hasDecimal) {
          types[col] = { category: 'numeric', suggested: maxLength > 10 ? 'Decimal20_2' : 'Decimal10_2' }
        } else {
          types[col] = { category: 'numeric', suggested: maxLength > 9 ? 'BigInt' : 'Integer' }
        }
      } else {
        // String - determine length
        const maxLength = Math.max(...values.map((v) => String(v).length))
        let suggested = 'String255'
        if (maxLength <= 5) suggested = 'String5'
        else if (maxLength <= 20) suggested = 'String20'
        else if (maxLength <= 50) suggested = 'String50'
        else if (maxLength <= 100) suggested = 'String100'
        else if (maxLength <= 255) suggested = 'String255'
        else suggested = 'String500'
        
        types[col] = { category: 'string', suggested }
      }
    })

    return types
  }, [columns, previewData])

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
      console.error('FileDataTypeDialog: error fetching datatype options', err)
      message.error('Failed to load data type options')
    } finally {
      setIsLoadingDataTypes(false)
    }
  }, [dataTypeOptions.length])

  // Initialize selected columns when dialog opens
  useEffect(() => {
    if (open) {
      fetchDataTypeOptions()
      
      // Initialize selected columns with inferred types or existing mappings
      const defaultSelection = {}
      columns.forEach((col) => {
        const existing = existingMappings.find((m) => m.srcclnm === col || m.trgclnm === col)
        const inferred = inferredTypes[col]
        
        defaultSelection[col] = {
          selected: true,
          targetDataType: existing?.trgcldtyp || 
                         (inferred?.suggested && findDataTypeCode(inferred.suggested)) ||
                         '',
        }
      })
      setSelectedColumns(defaultSelection)
    }
  }, [open, columns, existingMappings, inferredTypes, fetchDataTypeOptions])

  // Helper to find data type code from suggestion
  const findDataTypeCode = (suggestion) => {
    if (!suggestion || !dataTypeOptions.length) return ''
    const upperSuggestion = String(suggestion).toUpperCase()
    
    // Try exact match first
    const exact = dataTypeOptions.find(
      (opt) => String(opt.PRCD || opt.prcd || '').toUpperCase() === upperSuggestion
    )
    if (exact) return exact.PRCD || exact.prcd

    // Try partial match
    const partial = dataTypeOptions.find(
      (opt) => String(opt.PRCD || opt.prcd || '').toUpperCase().includes(upperSuggestion) ||
               upperSuggestion.includes(String(opt.PRCD || opt.prcd || '').toUpperCase())
    )
    if (partial) return partial.PRCD || partial.prcd

    return ''
  }

  // Categorize parameter option by code/value
  const getOptionCategory = (option) => {
    const code = String(option?.PRCD || option?.prcd || '').toUpperCase()
    const val = String(option?.PRVAL || option?.prval || '').toUpperCase()
    const txt = `${code} ${val}`

    if (/TIMESTAMP|DATETIME/.test(txt)) return 'timestamp'
    if (/\bDATE\b/.test(txt)) return 'date'
    if (/\bTIME\b/.test(txt)) return 'time'
    if (/(DECIMAL|NUMERIC|NUMBER|BIGINT|SMALLINT|INTEGER|\bINT\b|FLOAT|DOUBLE|MONEY)/.test(txt)) return 'numeric'
    if (/(CHAR|VARCHAR|NCHAR|NVARCHAR|STRING|TEXT|CLOB|BOOLEAN)/.test(txt)) return 'string'
    return 'other'
  }

  // Categorize inferred type to drive filtering
  const getSourceCategory = (inferredType) => {
    if (!inferredType) return 'other'
    return inferredType.category || 'other'
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
    setEditingTargetType((prev) => ({ ...prev, [columnName]: false }))
  }

  const selectedColumnList = useMemo(
    () =>
      columns.filter((c) => {
        const sel = selectedColumns[c]
        return sel && sel.selected
      }),
    [columns, selectedColumns]
  )

  const handleApply = () => {
    if (selectedColumnList.length === 0) {
      message.error('Please select at least one column to apply')
      return
    }

    // Build column mappings payload
    const columnMappings = selectedColumnList.map((col, idx) => {
      const sel = selectedColumns[col] || {}
      const existing = existingMappings.find((m) => m.srcclnm === col || m.trgclnm === col)
      
      return {
        id: existing?.id || `new-${col}-${idx}`,
        srcclnm: col,
        trgclnm: existing?.trgclnm || col,
        trgcldtyp: sel.targetDataType || '',
        excseq: existing?.excseq || idx + 1,
        trgkyflg: existing?.trgkyflg || 'N',
        isrqrd: existing?.isrqrd || 'N',
        drvlgc: existing?.drvlgc || '',
        drvlgcflg: existing?.drvlgcflg || 'N',
      }
    })

    onApply?.({ columnMappings })
    onClose?.()
  }

  const handleClose = () => {
    onClose?.()
  }

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
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Typography variant="subtitle1" fontWeight={600}>
          Review and Set Data Types
        </Typography>
        <IconButton size="small" onClick={handleClose}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ pt: 1.5, pb: 1.5 }}>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          Review inferred data types based on your file data. You can modify any data type before applying.
        </Typography>

        <Box
          sx={{
            maxHeight: 400,
            overflowY: 'auto',
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Column</TableCell>
                <TableCell>Inferred Type</TableCell>
                <TableCell>Target Type (from parameter)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {columns.map((col) => {
                const sel = selectedColumns[col] || {}
                const targetType = sel.targetDataType || ''
                const inferred = inferredTypes[col] || {}

                return (
                  <TableRow key={col} hover selected={!!sel.selected}>
                    <TableCell>{col}</TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {inferred.suggested || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {editingTargetType[col] ? (
                        <Autocomplete
                          value={
                            dataTypeOptions.find(
                              (opt) =>
                                String(opt.PRCD || opt.prcd) === String(targetType)
                            ) || null
                          }
                          onChange={(event, newValue) =>
                            handleChangeColumnType(
                              col,
                              newValue ? newValue.PRCD || newValue.prcd : ''
                            )
                          }
                          options={(function () {
                            // Filter options based on inferred type category
                            const srcCat = getSourceCategory(inferred)
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
                                    [col]: true,
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
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 2, py: 1.5 }}>
        <Button
          onClick={handleClose}
          sx={{ textTransform: 'none', fontSize: '0.8rem' }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleApply}
          disabled={selectedColumnList.length === 0 || isLoadingDataTypes}
          sx={{
            textTransform: 'none',
            fontSize: '0.8rem',
          }}
        >
          Apply to Form
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default FileDataTypeDialog

