'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Tooltip,
  Button,
  Chip,
  Box,
  Typography,
  Autocomplete,
  TextField,
  Divider,
  CircularProgress,
} from '@mui/material'
import {
  Clear as ClearIcon,
  FormatIndentIncrease as FormatIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material'
import Editor from '@monaco-editor/react'
import { format } from 'sql-formatter'
import { message } from 'antd'

const SqlEditorDialog = ({
  open,
  onClose,
  darkMode,
  value,
  onChange,
  onSave,
  fieldName,
  sqlError,
  selectedCode,
  onCodeSelect,
}) => {
  const [sqlCodes, setSqlCodes] = useState([])
  const [fetchingCodes, setFetchingCodes] = useState(false)
  const [fetchingLogic, setFetchingLogic] = useState(false)

  const fetchAllSqlCodes = useCallback(async () => {
    setFetchingCodes(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-all-sql-codes`)
      const result = await response.json()
      
      if (result.success) {
        setSqlCodes(result.data || [])
        message.success(`Loaded ${result.count} SQL codes`)
      } else {
        message.error(result.message || 'Failed to fetch SQL codes')
      }
    } catch (error) {
      console.error('Error fetching SQL codes:', error)
      message.error('Network error while fetching SQL codes')
    } finally {
      setFetchingCodes(false)
    }
  }, [])

  // Fetch all SQL codes when dialog opens
  useEffect(() => {
    if (open && sqlCodes.length === 0) {
      fetchAllSqlCodes()
    }
  }, [open, sqlCodes.length, fetchAllSqlCodes])

  const fetchSqlLogic = useCallback(async (sqlCode) => {
    if (!sqlCode) return
    
    setFetchingLogic(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-sql-logic?sql_code=${encodeURIComponent(sqlCode)}`)
      const result = await response.json()
      
      if (result.success) {
        onChange(result.data.sql_content || '')
        message.success(`Loaded SQL logic for ${sqlCode}`)
      } else {
        message.error(result.message || 'Failed to fetch SQL logic')
      }
    } catch (error) {
      console.error('Error fetching SQL logic:', error)
      message.error('Network error while fetching SQL logic')
    } finally {
      setFetchingLogic(false)
    }
  }, [onChange])

  const wasOpenRef = useRef(false)

  useEffect(() => {
    if (open && !wasOpenRef.current) {
      if (selectedCode) {
        fetchSqlLogic(selectedCode)
      } else {
        onChange('')
      }
    }
    wasOpenRef.current = open
  }, [open, selectedCode, fetchSqlLogic, onChange])

  const handleSqlCodeSelect = (event, newValue) => {
    const normalizedValue = newValue || ''
    onCodeSelect?.(normalizedValue)
    if (normalizedValue) {
      fetchSqlLogic(normalizedValue)
    } else {
      onChange('')
    }
  }

  const handleFormatSql = () => {
    try {
      const formatted = format(value || '', {
        language: 'sql',
        indent: '  ',
        uppercase: true,
      })
      onChange(formatted)
      message.success('SQL formatted successfully')
    } catch (error) {
      message.error('Failed to format SQL')
    }
  }

  const handleCopySql = () => {
    navigator.clipboard
      .writeText(value)
      .then(() => {
        message.success('SQL copied to clipboard')
      })
      .catch((err) => {
        console.error('Failed to copy: ', err)
        message.error('Failed to copy SQL')
      })
  }



  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullWidth
      maxWidth="md"
      PaperProps={{
        style: {
          backgroundColor: darkMode ? '#1A1F2C' : 'white',
          borderRadius: '12px',
          position: 'absolute',
          bottom: '24px',
          maxHeight: 'calc(60vh)',
        },
      }}
    >
      <DialogTitle
        sx={{
          color: darkMode ? 'white' : 'inherit',
          borderBottom: `1px solid ${
            darkMode ? 'rgba(75, 85, 99, 0.2)' : 'rgba(229, 231, 235, 1)'
          }`,
          padding: '12px 20px',
          fontSize: '1rem',
        }}
      >
        <div className="flex justify-between items-center">
          <span className="flex items-center gap-2">
            SQL Logic Editor
            {fieldName && (
              <Chip
                label={fieldName}
                size="small"
                sx={{
                  backgroundColor: darkMode
                    ? 'rgba(37, 99, 235, 0.2)'
                    : 'rgba(37, 99, 235, 0.1)',
                  color: darkMode
                    ? 'rgb(96, 165, 250)'
                    : 'rgb(37, 99, 235)',
                  fontSize: '0.75rem',
                }}
              />
            )}
          </span>
          <IconButton onClick={onClose} size="small">
            <ClearIcon fontSize="small" />
          </IconButton>
        </div>
      </DialogTitle>
      <DialogContent sx={{ padding: '16px 20px' }}>
        {/* SQL Code Search Section - Always Visible */}
        <Box mb={2}>
          <Autocomplete
            value={selectedCode || null}
            onChange={handleSqlCodeSelect}
            options={sqlCodes}
            loading={fetchingCodes || fetchingLogic}
            loadingText={fetchingCodes ? "Loading SQL codes..." : "Loading SQL logic..."}
            noOptionsText="No SQL codes available"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: darkMode ? 'rgba(55, 65, 81, 0.5)' : 'rgba(249, 250, 251, 1)',
                borderColor: darkMode ? 'rgba(75, 85, 99, 0.5)' : 'rgba(209, 213, 219, 1)',
                '&:hover': {
                  borderColor: darkMode ? 'rgba(96, 165, 250, 0.5)' : 'rgba(59, 130, 246, 0.5)',
                },
              },
              '& .MuiInputLabel-root': {
                color: darkMode ? '#9CA3AF' : '#6B7280',
              },
              '& .MuiAutocomplete-input': {
                color: darkMode ? 'white' : 'inherit',
              },
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="Search SQL templates..."
                variant="outlined"
                InputProps={{
                  ...params.InputProps,
                  endAdornment: (
                    <>
                      {fetchingCodes || fetchingLogic ? (
                        <CircularProgress color="inherit" size={20} />
                      ) : null}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                }}
              />
            )}
            renderOption={(props, option) => (
              <li {...props} key={option}>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    color: darkMode ? 'white' : 'inherit',
                    fontSize: '0.875rem'
                  }}
                >
                  {option}
                </Typography>
              </li>
            )}
          />
          <Divider sx={{ mt: 2, borderColor: darkMode ? 'rgba(75, 85, 99, 0.3)' : 'rgba(229, 231, 235, 1)' }} />
        </Box>

        {/* SQL Editor */}
        <div
          className={`h-[120px] rounded-lg overflow-hidden border ${
            darkMode ? 'border-gray-700' : 'border-gray-200'
          }`}
        >
          <Editor
            height="100%"
            defaultLanguage="sql"
            theme={darkMode ? 'vs-dark' : 'vs'}
            value={value}
            onChange={onChange}
            options={{
              minimap: { enabled: false },
              fontSize: 12,
              wordWrap: 'on',
              lineNumbers: 'on',
              lineHeight: 18,
            }}
          />
        </div>
        {sqlError && (
          <Box
            mt={2}
            p={1}
            bgcolor={
              darkMode ? 'rgba(220, 38, 38, 0.2)' : 'rgba(254, 226, 226, 1)'
            }
            borderRadius={1}
          >
            <Typography
              color="error"
              variant="body2"
              sx={{ fontSize: '0.75rem' }}
            >
              {sqlError}
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions
        sx={{
          padding: '8px 20px',
          borderTop: `1px solid ${
            darkMode ? 'rgba(75, 85, 99, 0.2)' : 'rgba(229, 231, 235, 1)'
          }`,
        }}
      >
        <div className="flex gap-2">
          <Tooltip title="Format SQL">
            <IconButton
              size="small"
              onClick={handleFormatSql}
              sx={{
                backgroundColor: darkMode
                  ? 'rgba(16, 185, 129, 0.15)'
                  : 'rgba(16, 185, 129, 0.1)',
              }}
            >
              <FormatIcon
                fontSize="small"
                className={darkMode ? 'text-green-400' : 'text-green-600'}
              />
            </IconButton>
          </Tooltip>
          <Tooltip title="Copy to Clipboard">
            <IconButton
              size="small"
              onClick={handleCopySql}
              sx={{
                backgroundColor: darkMode
                  ? 'rgba(59, 130, 246, 0.15)'
                  : 'rgba(59, 130, 246, 0.1)',
              }}
            >
              <CopyIcon
                fontSize="small"
                className={darkMode ? 'text-blue-400' : 'text-blue-600'}
              />
            </IconButton>
          </Tooltip>
        </div>
        <div>
          <Button
            onClick={onClose}
            sx={{
              textTransform: 'none',
              color: darkMode ? '#9CA3AF' : 'inherit',
              borderRadius: '6px',
              fontSize: '0.8rem',
              height: '32px',
            }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={onSave}
            sx={{
              textTransform: 'none',
              borderRadius: '6px',
              fontSize: '0.8rem',
              height: '32px',
              background: 'linear-gradient(45deg, #2563EB, #3B82F6)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1D4ED8, #2563EB)',
              },
            }}
          >
            Save
          </Button>
        </div>
      </DialogActions>
    </Dialog>
  )
}

export default SqlEditorDialog 