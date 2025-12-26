'use client'

import React, { useState, useEffect } from 'react'
import {
  TextField,
  Button,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  CircularProgress,
  InputAdornment,
  Box,
  Stack,
  Typography,
  useTheme as useMuiTheme,
  alpha,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormLabel,
  Alert,
  LinearProgress,
  Checkbox,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CloudUpload as UploadIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  PlayCircleOutline as ExecuteIcon,
  Schedule as ScheduleIcon,
  History as HistoryIcon,
} from '@mui/icons-material'
import { message } from 'antd'
import { useTheme } from '@/context/ThemeContext'
import axios from 'axios'
import { motion } from 'framer-motion'
import { useRouter } from 'next/navigation'
import { API_BASE_URL } from '@/app/config'

const getApiErrorMessage = (error, defaultMessage) => {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      const serverMessage = error.response.data?.error || error.response.data?.message || error.response.data?.detail
      if (serverMessage) {
        return typeof serverMessage === 'string' ? serverMessage : `Operation failed: ${JSON.stringify(serverMessage)}`
      }
      return `Server Error: Received status code ${error.response.status}`
    } else if (error.request) {
      return 'Network Error: Unable to connect to the server'
    }
  }
  if (error instanceof Error) {
    if (error.message.includes('Failed to fetch')) {
      return 'Network Error: Could not connect to the backend'
    }
    return `An unexpected error occurred: ${error.message}`
  }
  return defaultMessage || 'An unknown error occurred'
}

const UploadTable = ({ handleEditUpload, handleCreateNewUpload, refreshTableRef }) => {
  const { darkMode } = useTheme()
  const muiTheme = useMuiTheme()
  const router = useRouter()

  const [allUploads, setAllUploads] = useState([])
  const [loadingUploads, setLoadingUploads] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedUpload, setSelectedUpload] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredUploads, setFilteredUploads] = useState([])
  const [showExecuteDialog, setShowExecuteDialog] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [executeResult, setExecuteResult] = useState(null)
  const [loadMode, setLoadMode] = useState('INSERT')
  const [showErrorDialog, setShowErrorDialog] = useState(false)
  const [runHistory, setRunHistory] = useState([])
  const [selectedRunId, setSelectedRunId] = useState(null)
  const [errorRows, setErrorRows] = useState([])
  const [loadingErrors, setLoadingErrors] = useState(false)
  const [errorFilterCode, setErrorFilterCode] = useState('')
  const [showScheduleDialog, setShowScheduleDialog] = useState(false)
  const [savingSchedule, setSavingSchedule] = useState(false)
  const [scheduleForm, setScheduleForm] = useState({
    frequency: 'DL', // DL, WK, MN, HY, YR, ID
    dayOfWeek: 'MON',
    dayOfMonth: 1,
    hour: '10',
    minute: '00',
    startDate: new Date().toISOString().slice(0, 10),
    endDate: '',
  })

  // Fetch all upload configurations
  const fetchUploads = async () => {
    setLoadingUploads(true)
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/file-upload/get-all-uploads`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data.success && response.data.data) {
        setAllUploads(response.data.data)
        setFilteredUploads(response.data.data)
      } else {
        setAllUploads([])
        setFilteredUploads([])
      }
    } catch (error) {
      console.error('Error fetching uploads:', error)
      message.error(getApiErrorMessage(error, 'Failed to fetch upload configurations'))
      setAllUploads([])
      setFilteredUploads([])
    } finally {
      setLoadingUploads(false)
    }
  }

  // Filter uploads based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredUploads(allUploads)
      return
    }

    const query = searchQuery.toLowerCase()
    const filtered = allUploads.filter(upload => {
      return (
        (upload.flupldref && upload.flupldref.toLowerCase().includes(query)) ||
        (upload.fluplddesc && upload.fluplddesc.toLowerCase().includes(query)) ||
        (upload.flnm && upload.flnm.toLowerCase().includes(query)) ||
        (upload.trgtblnm && upload.trgtblnm.toLowerCase().includes(query))
      )
    })
    setFilteredUploads(filtered)
  }, [searchQuery, allUploads])

  // Fetch uploads on component mount
  useEffect(() => {
    fetchUploads()
  }, [])

  // Expose refresh function to parent component
  useEffect(() => {
    if (refreshTableRef) {
      refreshTableRef.current = fetchUploads
    }
  }, [refreshTableRef])

  // Handle delete
  const handleDeleteClick = (upload) => {
    setSelectedUpload(upload)
    setShowDeleteDialog(true)
  }

  // Handle execute
  const handleExecuteClick = (upload) => {
    setSelectedUpload(upload)
    setLoadMode('INSERT')
    setExecuteResult(null)
    setShowExecuteDialog(true)
  }

  const handleScheduleClick = (upload) => {
    setSelectedUpload(upload)
    setShowScheduleDialog(true)
    setSavingSchedule(false)
    const today = new Date().toISOString().slice(0, 10)
    setScheduleForm((prev) => ({
      ...prev,
      frequency: upload.frqcd || 'DL',
      startDate: today,
    }))
  }

  const handleViewErrorsClick = async (upload) => {
    setSelectedUpload(upload)
    setShowErrorDialog(true)
    setRunHistory([])
    setSelectedRunId(null)
    setErrorRows([])
    setErrorFilterCode('')

    try {
      const token = localStorage.getItem('token')
      // Use query parameter instead of path parameter
      const params = new URLSearchParams()
      params.append('flupldref', upload.flupldref)
      params.append('limit', '100') // Get more runs for the error dialog
      
      const response = await axios.get(
        `${API_BASE_URL}/file-upload/runs?${params.toString()}`,
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.data?.success && Array.isArray(response.data.data)) {
        // Filter to only show runs with errors (rows failed > 0)
        const allRuns = response.data.data
        const runsWithErrors = allRuns.filter(run => run.rwsfld > 0)
        setRunHistory(runsWithErrors)
        if (runsWithErrors.length > 0) {
          setSelectedRunId(runsWithErrors[0].runid)
        } else {
          setSelectedRunId(null)
        }
      } else {
        setRunHistory([])
      }
    } catch (error) {
      console.error('Error fetching file upload runs:', error)
      message.error(getApiErrorMessage(error, 'Failed to fetch execution history for this upload'))
      setRunHistory([])
    }
  }

  const fetchErrorRows = async (flupldref, runid, errorCode) => {
    if (!flupldref || !runid) {
      setErrorRows([])
      return
    }

    setLoadingErrors(true)
    try {
      const token = localStorage.getItem('token')
      const params = new URLSearchParams()
      params.append('runid', runid.toString())
      if (errorCode) {
        params.append('error_code', errorCode)
      }

      const response = await axios.get(
        `${API_BASE_URL}/file-upload/errors/${encodeURIComponent(flupldref)}?${params.toString()}`,
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.data?.success && Array.isArray(response.data.data)) {
        setErrorRows(response.data.data)
      } else {
        setErrorRows([])
      }
    } catch (error) {
      console.error('Error fetching file upload errors:', error)
      message.error(getApiErrorMessage(error, 'Failed to fetch error rows'))
      setErrorRows([])
    } finally {
      setLoadingErrors(false)
    }
  }

  // Auto-fetch errors when selectedRunId changes (placed after fetchErrorRows is defined)
  useEffect(() => {
    if (showErrorDialog && selectedUpload && selectedRunId) {
      fetchErrorRows(selectedUpload.flupldref, selectedRunId, errorFilterCode)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRunId, showErrorDialog])

  const buildJobScheduleRequest = () => {
    if (!selectedUpload) return null
    const { frequency, dayOfWeek, dayOfMonth, hour, minute, startDate, endDate } = scheduleForm

    const mapref = `FLUPLD:${selectedUpload.flupldref}`
    const frqcd = frequency || 'DL'
    let frqdd = ''

    if (['WK', 'FN'].includes(frqcd)) {
      frqdd = dayOfWeek || 'MON'
    } else if (['MN', 'HY', 'YR'].includes(frqcd)) {
      frqdd = String(dayOfMonth || 1)
    }

    return {
      MAPREF: mapref,
      FRQCD: frqcd,
      FRQDD: frqdd || null,
      FRQHH: hour || '0',
      FRQMI: minute || '0',
      STRTDT: startDate || new Date().toISOString().slice(0, 10),
      ENDDT: endDate || null,
    }
  }

  const handleSaveSchedule = async () => {
    if (!selectedUpload) return

    setSavingSchedule(true)
    try {
      const { frequency, dayOfWeek, dayOfMonth, hour, minute, startDate, endDate } = scheduleForm
      const frq = frequency || 'DL'
      const hhmm = `${String(hour || '0').padStart(2, '0')}:${String(minute || '0').padStart(2, '0')}`

      let tmPrm = null
      if (frq === 'DL' || frq === 'ID') {
        tmPrm = `${frq}_${hhmm}`
      } else if (frq === 'WK' || frq === 'FN') {
        const day = dayOfWeek || 'MON'
        tmPrm = `${frq}_${day}_${hhmm}`
      } else if (['MN', 'HY', 'YR'].includes(frq)) {
        const d = dayOfMonth || 1
        tmPrm = `${frq}_${d}_${hhmm}`
      }

      const token = localStorage.getItem('token')
      const payload = {
        flupldref: selectedUpload.flupldref,
        frqncy: frq,
        tm_prm: tmPrm,
        stts: 'ACTIVE',
        strtdt: startDate || null,
        enddt: endDate || null,
      }

      const response = await axios.post(`${API_BASE_URL}/file-upload/schedules`, payload, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.data?.success) {
        message.success('Schedule saved successfully')
      } else {
        message.error(response.data?.message || 'Failed to save schedule')
      }

      setShowScheduleDialog(false)
    } catch (error) {
      console.error('Error saving file upload schedule:', error)
      message.error(getApiErrorMessage(error, 'Failed to save schedule'))
    } finally {
      setSavingSchedule(false)
    }
  }

  const handleExecuteConfirm = async () => {
    if (!selectedUpload) return

    setExecuting(true)
    setExecuteResult(null)

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/file-upload/execute`,
        {
          flupldref: selectedUpload.flupldref,
          load_mode: loadMode,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data.success) {
        setExecuteResult({
          success: true,
          message: response.data.message,
          data: response.data.data,
        })
        message.success('File upload executed successfully')
        // Refresh the table to update last run date
        fetchUploads()
      } else {
        setExecuteResult({
          success: false,
          message: response.data.message || 'Execution failed',
          data: response.data.data,
        })
        message.error(response.data.message || 'Execution failed')
      }
    } catch (error) {
      console.error('Error executing upload:', error)
      const errorMessage = getApiErrorMessage(error, 'Failed to execute file upload')
      setExecuteResult({
        success: false,
        message: errorMessage,
        data: error.response?.data?.data || null,
      })
      message.error(errorMessage)
    } finally {
      setExecuting(false)
    }
  }

  const handleDeleteConfirm = async () => {
    if (!selectedUpload) return

    try {
      const token = localStorage.getItem('token')
      await axios.post(
        `${API_BASE_URL}/file-upload/delete`,
        { flupldref: selectedUpload.flupldref },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      message.success(`Upload configuration '${selectedUpload.flupldref}' deleted successfully`)
      setShowDeleteDialog(false)
      setSelectedUpload(null)
      fetchUploads()
    } catch (error) {
      console.error('Error deleting upload:', error)
      message.error(getApiErrorMessage(error, 'Failed to delete upload configuration'))
    }
  }

  // Handle activate/deactivate
  const handleToggleStatus = async (upload) => {
    const newStatus = upload.stflg === 'A' ? 'N' : 'A'
    try {
      const token = localStorage.getItem('token')
      await axios.post(
        `${API_BASE_URL}/file-upload/activate-deactivate`,
        {
          flupldref: upload.flupldref,
          stflg: newStatus
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      message.success(`Upload configuration '${upload.flupldref}' ${newStatus === 'A' ? 'activated' : 'deactivated'} successfully`)
      fetchUploads()
    } catch (error) {
      console.error('Error updating status:', error)
      message.error(getApiErrorMessage(error, 'Failed to update upload status'))
    }
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        elevation={3}
        sx={{
          p: 3,
          backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper,
          borderRadius: 2,
        }}
      >
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h1" sx={{ fontWeight: 600 }}>
            File Upload Configurations
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNewUpload}
            sx={{ textTransform: 'none' }}
          >
            New Upload
          </Button>
        </Box>

        {/* Search Bar */}
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            placeholder="Search by reference, description, filename, or table name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchQuery && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={() => setSearchQuery('')}>
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: darkMode ? alpha(muiTheme.palette.background.default, 0.5) : muiTheme.palette.background.default,
              },
            }}
          />
        </Box>

        {/* Table */}
        {loadingUploads ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Reference</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Description</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">File Name</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">File Type</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Target Table</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Active?</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Schedule</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Next Run</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Last Run</TableCell>
                  <TableCell sx={{ fontWeight: 600 }} align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredUploads.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">
                        {allUploads.length === 0
                          ? 'No upload configurations found. Click "New Upload" to create one.'
                          : 'No uploads match your search criteria.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredUploads.map((upload) => (
                    <TableRow
                      key={upload.flupldref}
                      hover
                      sx={{
                        '&:hover': {
                          backgroundColor: darkMode
                            ? alpha(muiTheme.palette.action.hover, 0.1)
                            : muiTheme.palette.action.hover,
                        },
                      }}
                    >
                      <TableCell align="center">{upload.flupldref}</TableCell>
                      <TableCell align="center">{upload.fluplddesc || '-'}</TableCell>
                      <TableCell align="center">{upload.flnm || '-'}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={upload.fltyp || 'N/A'}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        {upload.trgschm && upload.trgtblnm
                          ? `${upload.trgschm}.${upload.trgtblnm}`
                          : '-'}
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={upload.stflg === 'A'}
                          color="success"
                          inputProps={{ 'aria-label': 'Active?' }}
                          onChange={() => handleToggleStatus(upload)}
                        />
                      </TableCell>
                      <TableCell align="center">
                        {upload.schdid ? (
                          <Tooltip title={`Schedule: ${upload.frqncy || 'N/A'} - Status: ${upload.schd_stts || 'N/A'}`}>
                            <Chip
                              size="small"
                              label={upload.schd_stts === 'ACTIVE' ? 'Scheduled' : 'Paused'}
                              color={upload.schd_stts === 'ACTIVE' ? 'success' : 'default'}
                              variant="outlined"
                            />
                          </Tooltip>
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {upload.schd_nxt_run_dt ? (
                          <Tooltip title={new Date(upload.schd_nxt_run_dt).toLocaleString()}>
                            <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>
                              {new Date(upload.schd_nxt_run_dt).toLocaleString()}
                            </Typography>
                          </Tooltip>
                        ) : (
                          <Typography variant="body2" color="text.secondary">-</Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        {upload.lstrundt
                          ? new Date(upload.lstrundt).toLocaleString()
                          : '-'}
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => handleEditUpload(upload)}
                              color="primary"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Execute">
                            <IconButton
                              size="small"
                              onClick={() => handleExecuteClick(upload)}
                              color="primary"
                              disabled={!upload.trgconid || !upload.trgtblnm}
                            >
                              <ExecuteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Schedule">
                            <IconButton
                              size="small"
                              onClick={() => handleScheduleClick(upload)}
                              color="secondary"
                            >
                              <ScheduleIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="View Errors">
                            <span>
                              <IconButton
                                size="small"
                                onClick={() => handleViewErrorsClick(upload)}
                                color="warning"
                              >
                                {/* Better icon suggestion for errors: ReportProblemOutlined */}
                                {/* Replace below if you add it to the imports */}
                                <StopIcon fontSize="small" />
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="View History">
                            <IconButton
                              size="small"
                              onClick={() => router.push(`/file_upload_history?flupldref=${encodeURIComponent(upload.flupldref)}`)}
                              color="info"
                            >
                              <HistoryIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteClick(upload)}
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Execute Dialog */}
      <Dialog
        open={showExecuteDialog}
        onClose={() => {
          if (!executing) {
            setShowExecuteDialog(false)
            setExecuteResult(null)
          }
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Execute File Upload: {selectedUpload?.flupldref}
        </DialogTitle>
        <DialogContent>
          {executing ? (
            <Box sx={{ py: 2 }}>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Executing file upload. Please wait...
              </Typography>
              <LinearProgress />
            </Box>
          ) : executeResult ? (
            <Box sx={{ py: 2 }}>
              <Alert
                severity={executeResult.success ? 'success' : 'error'}
                sx={{ mb: 2 }}
              >
                {executeResult.message}
              </Alert>
              {executeResult.data && (
                <Box>
                  <Typography variant="body2" sx={{ mb: 1, fontWeight: 600 }}>
                    Execution Summary:
                  </Typography>
                  <Typography variant="body2">
                    • Rows Processed: {executeResult.data.rows_processed || 0}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    • Rows Successful: {executeResult.data.rows_successful || 0}
                  </Typography>
                  <Typography variant="body2" color="error.main">
                    • Rows Failed: {executeResult.data.rows_failed || 0}
                  </Typography>
                  {executeResult.data.table_created && (
                    <Typography variant="body2" color="info.main">
                      • Table Created: Yes
                    </Typography>
                  )}
                  {executeResult.data.errors && executeResult.data.errors.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                        Errors ({Math.min(executeResult.data.errors.length, 100)} shown):
                      </Typography>
                      <Box
                        sx={{
                          maxHeight: 200,
                          overflow: 'auto',
                          p: 1,
                          backgroundColor: darkMode ? alpha(muiTheme.palette.error.dark, 0.1) : alpha(muiTheme.palette.error.light, 0.1),
                          borderRadius: 1,
                        }}
                      >
                        {executeResult.data.errors.slice(0, 10).map((error, idx) => (
                          <Typography key={idx} variant="caption" display="block" sx={{ mb: 0.5 }}>
                            Row {error.row_index}: {error.error_message}
                          </Typography>
                        ))}
                        {executeResult.data.errors.length > 10 && (
                          <Typography variant="caption" color="text.secondary">
                            ... and {executeResult.data.errors.length - 10} more errors
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  )}
                </Box>
              )}
            </Box>
          ) : (
            <Box sx={{ py: 2 }}>
              <DialogContentText sx={{ mb: 3 }}>
                Select the load mode for executing this file upload:
              </DialogContentText>
              <FormControl component="fieldset">
                <FormLabel component="legend">Load Mode</FormLabel>
                <RadioGroup
                  value={loadMode}
                  onChange={(e) => setLoadMode(e.target.value)}
                >
                  <FormControlLabel
                    value="INSERT"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Insert Only
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Append new rows to the table
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="TRUNCATE_LOAD"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Truncate & Load
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Delete all existing data, then insert new rows
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="UPSERT"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          Upsert (Update or Insert)
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Update existing rows (by primary key) or insert new ones
                        </Typography>
                      </Box>
                    }
                  />
                </RadioGroup>
              </FormControl>
              {selectedUpload?.trnctflg === 'Y' && loadMode === 'INSERT' && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Note: This configuration has "Truncate before load" enabled. Consider using "Truncate & Load" mode.
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {executeResult ? (
            <Button
              onClick={() => {
                setShowExecuteDialog(false)
                setExecuteResult(null)
              }}
              variant="contained"
            >
              Close
            </Button>
          ) : (
            <>
              <Button
                onClick={() => setShowExecuteDialog(false)}
                disabled={executing}
              >
                Cancel
              </Button>
              <Button
                onClick={handleExecuteConfirm}
                variant="contained"
                color="primary"
                disabled={executing}
                startIcon={executing ? <CircularProgress size={16} /> : <ExecuteIcon />}
              >
                Execute
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Error Details Dialog */}
      <Dialog
        open={showErrorDialog}
        onClose={() => {
          setShowErrorDialog(false)
          setRunHistory([])
          setErrorRows([])
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Error Rows: {selectedUpload?.flupldref}
        </DialogTitle>
        <DialogContent>
          {!selectedUpload ? (
            <DialogContentText>No upload selected.</DialogContentText>
          ) : (
            <Box sx={{ py: 1 }}>
              <Box
                sx={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 2,
                  mb: 2,
                  alignItems: 'center',
                }}
              >
                <FormControl size="small" sx={{ minWidth: 220 }}>
                  <InputLabel id="run-select-label">Run</InputLabel>
                  <Select
                    labelId="run-select-label"
                    label="Run"
                    value={selectedRunId || ''}
                    onChange={(e) => {
                      const newRunId = e.target.value
                      setSelectedRunId(newRunId)
                      fetchErrorRows(selectedUpload.flupldref, newRunId, errorFilterCode)
                    }}
                  >
                    {runHistory.map((run) => (
                      <MenuItem key={run.runid} value={run.runid}>
                        {new Date(run.strttm).toLocaleString()} – {run.stts} (
                        {run.rwsfld} failed)
                      </MenuItem>
                    ))}
                    {runHistory.length === 0 && (
                      <MenuItem value="" disabled>
                        No runs found
                      </MenuItem>
                    )}
                  </Select>
                </FormControl>

                <TextField
                  size="small"
                  label="Error Code"
                  value={errorFilterCode}
                  onChange={(e) => setErrorFilterCode(e.target.value)}
                  onBlur={() => {
                    if (selectedRunId) {
                      fetchErrorRows(selectedUpload.flupldref, selectedRunId, errorFilterCode)
                    }
                  }}
                />

                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    if (selectedRunId) {
                      fetchErrorRows(selectedUpload.flupldref, selectedRunId, errorFilterCode)
                    }
                  }}
                  disabled={!selectedRunId || loadingErrors}
                >
                  Refresh Errors
                </Button>
              </Box>

              {runHistory.length === 0 ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  No runs with errors found for this file upload.
                </Typography>
              ) : loadingErrors ? (
                <Box sx={{ py: 2 }}>
                  <LinearProgress />
                </Box>
              ) : errorRows.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No error rows found for the selected run.
                </Typography>
              ) : (
                <TableContainer
                  component={Paper}
                  sx={{
                    maxHeight: 400,
                    mt: 1,
                  }}
                >
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Row #</TableCell>
                        <TableCell>Error Code</TableCell>
                        <TableCell>Error Message</TableCell>
                        <TableCell>Row Data (JSON)</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {errorRows.map((row) => (
                        <TableRow key={row.errid}>
                          <TableCell>{(row.rwndx ?? 0) + 1}</TableCell>
                          <TableCell>
                            {row.rrcd ? (
                              <Chip
                                label={row.rrcd}
                                size="small"
                                color="error"
                                variant="outlined"
                              />
                            ) : (
                              '-'
                            )}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={row.rrmssg}>
                              <Typography
                                variant="body2"
                                sx={{
                                  maxWidth: 320,
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {row.rrmssg}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Box
                              sx={{
                                maxWidth: 360,
                                maxHeight: 80,
                                overflow: 'auto',
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                backgroundColor: darkMode
                                  ? alpha(muiTheme.palette.background.paper, 0.6)
                                  : alpha(muiTheme.palette.grey[200], 0.6),
                                p: 0.5,
                                borderRadius: 1,
                              }}
                            >
                              {row.rwdtjsn 
                                ? (typeof row.rwdtjsn === 'string' 
                                    ? row.rwdtjsn 
                                    : JSON.stringify(row.rwdtjsn, null, 2))
                                : '-'}
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setShowErrorDialog(false)
              setRunHistory([])
              setErrorRows([])
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog
        open={showScheduleDialog}
        onClose={() => {
          if (!savingSchedule) {
            setShowScheduleDialog(false)
          }
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Schedule File Upload: {selectedUpload?.flupldref}</DialogTitle>
        <DialogContent>
          {!selectedUpload ? (
            <DialogContentText>No upload selected.</DialogContentText>
          ) : (
            <Box sx={{ py: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormControl size="small" fullWidth>
                <InputLabel>Frequency</InputLabel>
                <Select
                  label="Frequency"
                  value={scheduleForm.frequency}
                  onChange={(e) =>
                    setScheduleForm((prev) => ({ ...prev, frequency: e.target.value }))
                  }
                >
                  <MenuItem value="DL">Daily</MenuItem>
                  <MenuItem value="WK">Weekly</MenuItem>
                  <MenuItem value="MN">Monthly</MenuItem>
                  <MenuItem value="HY">Half-Yearly</MenuItem>
                  <MenuItem value="YR">Yearly</MenuItem>
                  <MenuItem value="ID">Immediate / Interval</MenuItem>
                </Select>
              </FormControl>

              {(scheduleForm.frequency === 'WK' || scheduleForm.frequency === 'FN') && (
                <FormControl size="small" fullWidth>
                  <InputLabel>Day of Week</InputLabel>
                  <Select
                    label="Day of Week"
                    value={scheduleForm.dayOfWeek}
                    onChange={(e) =>
                      setScheduleForm((prev) => ({ ...prev, dayOfWeek: e.target.value }))
                    }
                  >
                    <MenuItem value="MON">Monday</MenuItem>
                    <MenuItem value="TUE">Tuesday</MenuItem>
                    <MenuItem value="WED">Wednesday</MenuItem>
                    <MenuItem value="THU">Thursday</MenuItem>
                    <MenuItem value="FRI">Friday</MenuItem>
                    <MenuItem value="SAT">Saturday</MenuItem>
                    <MenuItem value="SUN">Sunday</MenuItem>
                  </Select>
                </FormControl>
              )}

              {['MN', 'HY', 'YR'].includes(scheduleForm.frequency) && (
                <TextField
                  size="small"
                  type="number"
                  label="Day of Month"
                  value={scheduleForm.dayOfMonth}
                  onChange={(e) =>
                    setScheduleForm((prev) => ({
                      ...prev,
                      dayOfMonth: Math.max(1, Math.min(31, Number(e.target.value) || 1)),
                    }))
                  }
                  inputProps={{ min: 1, max: 31 }}
                  fullWidth
                />
              )}

              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Time (24-hour format)
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <FormControl size="small" sx={{ width: 100 }}>
                    <InputLabel>Hour</InputLabel>
                    <Select
                      label="Hour"
                      value={String(scheduleForm.hour || '00').padStart(2, '0')}
                      onChange={(e) =>
                        setScheduleForm((prev) => ({
                          ...prev,
                          hour: e.target.value,
                        }))
                      }
                    >
                      {Array.from({ length: 24 }, (_, i) => (
                        <MenuItem key={i} value={String(i).padStart(2, '0')}>
                          {String(i).padStart(2, '0')}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Typography variant="h6">:</Typography>
                  <FormControl size="small" sx={{ width: 100 }}>
                    <InputLabel>Minute</InputLabel>
                    <Select
                      label="Minute"
                      value={String(scheduleForm.minute || '00').padStart(2, '0')}
                      onChange={(e) =>
                        setScheduleForm((prev) => ({
                          ...prev,
                          minute: e.target.value,
                        }))
                      }
                    >
                      {Array.from({ length: 60 }, (_, i) => (
                        <MenuItem key={i} value={String(i).padStart(2, '0')}>
                          {String(i).padStart(2, '0')}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Stack>
              </Box>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  size="small"
                  type="date"
                  label="Start Date"
                  InputLabelProps={{ shrink: true }}
                  value={scheduleForm.startDate}
                  onChange={(e) =>
                    setScheduleForm((prev) => ({ ...prev, startDate: e.target.value }))
                  }
                  fullWidth
                />
                <TextField
                  size="small"
                  type="date"
                  label="End Date (optional)"
                  InputLabelProps={{ shrink: true }}
                  value={scheduleForm.endDate}
                  onChange={(e) =>
                    setScheduleForm((prev) => ({ ...prev, endDate: e.target.value }))
                  }
                  fullWidth
                />
              </Box>

              <DialogContentText sx={{ mt: 1 }}>
                Schedules are managed by the central job scheduler using MAPREF{' '}
                {selectedUpload && `FLUPLD:${selectedUpload.flupldref}`}.
              </DialogContentText>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setShowScheduleDialog(false)
            }}
            disabled={savingSchedule}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveSchedule}
            variant="contained"
            color="primary"
            disabled={savingSchedule || !selectedUpload}
            startIcon={savingSchedule ? <CircularProgress size={16} /> : <ScheduleIcon />}
          >
            Save Schedule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
      >
        <DialogTitle>Delete Upload Configuration</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the upload configuration "{selectedUpload?.flupldref}"?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default UploadTable

