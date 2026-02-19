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
  Collapse,
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
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Warning as WarningIcon,
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
  const [jobRequestId, setJobRequestId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null) // QUEUED, PROCESSING, DONE, FAILED
  const [pollingInterval, setPollingInterval] = useState(null)
  const [activeJobs, setActiveJobs] = useState({}) // Map of flupldref -> { request_id, status }
  const [expandedRows, setExpandedRows] = useState({}) // Map of flupldref -> boolean for expanded state
  const [loadMode, setLoadMode] = useState('INSERT')
  const [showErrorDialog, setShowErrorDialog] = useState(false)
  const [runHistory, setRunHistory] = useState([])
  const [selectedRunId, setSelectedRunId] = useState(null)
  const [errorRows, setErrorRows] = useState([])
  const [loadingErrors, setLoadingErrors] = useState(false)
  const [errorFilterCode, setErrorFilterCode] = useState('')
  const [showScheduleDialog, setShowScheduleDialog] = useState(false)
  const [savingSchedule, setSavingSchedule] = useState(false)
  const [stopScheduleDialog, setStopScheduleDialog] = useState({ show: false, upload: null })
  const [stoppingSchedule, setStoppingSchedule] = useState(false)
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

  // Fetch all active jobs periodically to show progress in table
  const fetchActiveJobs = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/file-upload/active-jobs`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data.success) {
        const jobs = response.data.active_jobs || {}
        // Filter out any jobs that are not actually active (shouldn't happen, but safety check)
        const filteredJobs = {}
        Object.keys(jobs).forEach(flupldref => {
          const jobList = jobs[flupldref]
          if (Array.isArray(jobList) && jobList.length > 0) {
            // Only include jobs with active statuses
            const activeJobList = jobList.filter(job => {
              const status = (job?.status || '').toUpperCase()
              return status === 'NEW' || status === 'QUEUED' || status === 'PROCESSING' || status === 'CLAIMED'
            })
            if (activeJobList.length > 0) {
              filteredJobs[flupldref] = activeJobList
            }
          }
        })
        setActiveJobs(filteredJobs)
      } else {
        console.warn('[ActiveJobs] API returned success=false:', response.data)
        setActiveJobs({}) // Clear active jobs if API indicates failure
      }
    } catch (error) {
      // Log error details for debugging
      console.error('[ActiveJobs] Error fetching active jobs:', error)
      if (error.response) {
        console.error('[ActiveJobs] Response status:', error.response.status)
        console.error('[ActiveJobs] Response data:', error.response.data)
      }
    }
  }

  // Poll for active jobs every 3 seconds
  useEffect(() => {
    // Fetch immediately
    fetchActiveJobs()
    
    // Then poll every 3 seconds
    const activeJobsInterval = setInterval(() => {
      fetchActiveJobs()
    }, 3000)
    
    return () => {
      clearInterval(activeJobsInterval)
    }
  }, [])

  // Keep polling job status even if dialog is closed (for table indicator)
  useEffect(() => {
    if (!jobRequestId || !selectedUpload) return
    
    // Poll every 3 seconds to check job status (even if dialog is closed)
    const statusCheckInterval = setInterval(() => {
      if (jobRequestId) {
        pollJobStatus(jobRequestId)
      }
    }, 3000)
    
    return () => {
      clearInterval(statusCheckInterval)
    }
  }, [jobRequestId, selectedUpload])

  // Expose refresh function to parent component
  useEffect(() => {
    if (refreshTableRef) {
      refreshTableRef.current = fetchUploads
    }
  }, [refreshTableRef])

  // Handle delete
  const handleDeleteClick = async (upload) => {
    setSelectedUpload(upload)
    
    // Check if file has been processed (has last_run_dt) or if table exists
    const hasBeenProcessed = upload.last_run_dt || upload.lstrundt
    
    if (hasBeenProcessed) {
      // Check if table exists in target database
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(
          `${API_BASE_URL}/file-upload/check-table-exists/${encodeURIComponent(upload.flupldref)}`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        )
        
        const tableExists = response.data?.table_exists || false
        const targetTable = upload.trgschm && upload.trgtblnm 
          ? `${upload.trgschm}.${upload.trgtblnm}` 
          : 'target table'
        
        if (tableExists) {
          message.warning(
            `Cannot delete this configuration. The file has been processed and the table "${targetTable}" exists in the target database. ` +
            `Deleting this configuration would result in loss of metadata about the table structure and mappings.`
          )
          return
        } else if (hasBeenProcessed) {
          message.warning(
            `Cannot delete this configuration. The file has been processed at least once. ` +
            `Deleting this configuration would result in loss of execution history and metadata.`
          )
          return
        }
      } catch (error) {
        // If check fails, still block deletion if it has been processed
        if (hasBeenProcessed) {
          message.warning(
            `Cannot delete this configuration. The file has been processed at least once. ` +
            `Deleting this configuration would result in loss of execution history and metadata.`
          )
          return
        }
        // If check fails and hasn't been processed, allow deletion (table check failed)
        console.warn('Failed to check table existence, allowing deletion:', error)
      }
    }
    
    // If no processing has occurred and table doesn't exist, allow deletion
    setShowDeleteDialog(true)
  }

  // Handle cancel job
  const handleCancelJob = async (requestId, flupldref) => {
    if (!requestId) return

    try {
      const token = localStorage.getItem('token')
      const response = await axios.post(
        `${API_BASE_URL}/file-upload/cancel-job/${requestId}`,
        {},
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data.success) {
        message.success(`Job ${requestId} has been cancelled`)
        // Refresh active jobs to update UI
        fetchActiveJobs()
        // If this was the current job, clear its status
        if (jobRequestId === requestId) {
          setJobRequestId(null)
          setJobStatus(null)
          setExecuting(false)
        }
      } else {
        message.error(response.data.message || 'Failed to cancel job')
      }
    } catch (error) {
      console.error('Error cancelling job:', error)
      const errorMessage = getApiErrorMessage(error, 'Failed to cancel job')
      message.error(errorMessage)
    }
  }

  // Handle execute
  const handleExecuteClick = (upload) => {
    // If there's already a running job for this upload, show its status instead of starting new one
    if (jobRequestId && selectedUpload?.flupldref === upload.flupldref && (jobStatus === 'QUEUED' || jobStatus === 'PROCESSING' || jobStatus === 'NEW' || jobStatus === 'CLAIMED')) {
      // Just reopen the dialog to show current status
      setShowExecuteDialog(true)
      return
    }
    
    setSelectedUpload(upload)
    setLoadMode('INSERT')
    setExecuteResult(null)
    setJobRequestId(null)
    setJobStatus(null)
    if (pollingInterval) {
      clearInterval(pollingInterval)
      setPollingInterval(null)
    }
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

  const handleStopSchedule = async () => {
    if (!stopScheduleDialog.upload) return

    setStoppingSchedule(true)
    try {
      const token = localStorage.getItem('token')
      const scheduleId = stopScheduleDialog.upload.schdid
      
      if (!scheduleId) {
        message.error('Schedule ID not found')
        return
      }

      const response = await axios.delete(`${API_BASE_URL}/file-upload/schedules/${scheduleId}`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.data?.success) {
        message.success('Schedule stopped successfully')
        setStopScheduleDialog({ show: false, upload: null })
        fetchUploads()
      } else {
        message.error(response.data?.message || 'Failed to stop schedule')
      }
    } catch (error) {
      console.error('Error stopping schedule:', error)
      message.error(getApiErrorMessage(error, 'Failed to stop schedule'))
    } finally {
      setStoppingSchedule(false)
    }
  }

  const handleOpenStopScheduleDialog = (upload) => {
    if (upload.schdid) {
      setStopScheduleDialog({ show: true, upload })
    }
  }

  const handleCloseStopScheduleDialog = () => {
    setStopScheduleDialog({ show: false, upload: null })
  }

  // Poll for job status
  const pollJobStatus = async (requestId) => {
    if (!requestId) return

    try {
      const token = localStorage.getItem('token')
      const response = await axios.get(
        `${API_BASE_URL}/file-upload/execute-status/${requestId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (response.data.success) {
        const status = response.data.status
        setJobStatus(status)

        if (status === 'DONE') {
          // Job completed successfully
          setExecuting(false)
          if (pollingInterval) {
            clearInterval(pollingInterval)
            setPollingInterval(null)
          }
          
          // Fetch final results from execution history
          fetchUploads() // Refresh to get updated last run date
          
          setExecuteResult({
            success: true,
            message: 'File upload completed successfully in the background',
            data: {
              status: 'DONE',
              completed_at: response.data.completed_at,
            },
          })
          message.success('File upload completed successfully')
        } else if (status === 'FAILED') {
          // Job failed
          setExecuting(false)
          if (pollingInterval) {
            clearInterval(pollingInterval)
            setPollingInterval(null)
          }
          
          setExecuteResult({
            success: false,
            message: 'File upload failed. Check execution history for details.',
            data: {
              status: 'FAILED',
              completed_at: response.data.completed_at,
            },
          })
          message.error('File upload failed')
        } else if (status === 'NEW' || status === 'PROCESSING' || status === 'QUEUED' || status === 'CLAIMED') {
          // Job is still running, update status display
          // 'NEW' means queued but not started yet, 'PROCESSING' means actively running
          if (status === 'PROCESSING') {
            setJobStatus('PROCESSING')
          } else if (status === 'NEW' || status === 'QUEUED' || status === 'CLAIMED') {
            // Keep showing as QUEUED if status is still NEW or QUEUED
            setJobStatus('QUEUED')
          }
          // Continue polling
        } else if (status === 'CANCELLED') {
          // Job was cancelled
          setExecuting(false)
          if (pollingInterval) {
            clearInterval(pollingInterval)
            setPollingInterval(null)
          }
          
          setExecuteResult({
            success: false,
            message: 'File upload was cancelled',
            data: {
              status: 'CANCELLED',
            },
          })
          message.warning('File upload was cancelled')
        }
      }
    } catch (error) {
      console.error('Error polling job status:', error)
      // Don't show error for polling failures, just log
    }
  }

  const handleExecuteConfirm = async () => {
    if (!selectedUpload) return

    setExecuting(true)
    setExecuteResult(null)
    setJobRequestId(null)
    setJobStatus(null)

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
        const requestId = response.data.request_id
        setJobRequestId(requestId)
        setJobStatus('QUEUED') // Initial status is QUEUED
        setExecuting(true) // Keep executing flag true so dialog stays open
        
        message.success('File upload queued for background execution')
        
        // Start polling for status updates
        const interval = setInterval(() => {
          pollJobStatus(requestId)
        }, 2000) // Poll every 2 seconds
        
        setPollingInterval(interval)
        
        // Also poll immediately (with small delay to let backend update status)
        setTimeout(() => pollJobStatus(requestId), 500)
      } else {
        setExecuteResult({
          success: false,
          message: response.data.message || 'Failed to queue file upload',
          data: null,
        })
        message.error(response.data.message || 'Failed to queue file upload')
        setExecuting(false)
      }
    } catch (error) {
      console.error('Error queuing upload:', error)
      const errorMessage = getApiErrorMessage(error, 'Failed to queue file upload')
      setExecuteResult({
        success: false,
        message: errorMessage,
        data: null,
      })
      message.error(errorMessage)
      setExecuting(false)
    }
  }

  // Cleanup polling on unmount or dialog close
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [pollingInterval])

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
    <Box sx={{ width: '100%', maxWidth: '100%', overflow: 'hidden' }}>
      <Paper
        elevation={3}
        sx={{
          p: 3,
          backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper,
          borderRadius: 2,
          maxWidth: '100%',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
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

        {/* Table */}
        {loadingUploads ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer sx={{ maxWidth: '100%', overflowX: 'auto' }}>
            <Table sx={{ tableLayout: 'fixed', width: '100%' }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600, width: '12%', fontSize: '0.75rem', py: 1 }} align="left">Reference</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '15%', fontSize: '0.75rem', py: 1 }} align="left">Description</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '12%', fontSize: '0.75rem', py: 1 }} align="left">File Name</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '8%', fontSize: '0.75rem', py: 1 }} align="center">Type</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '13%', fontSize: '0.75rem', py: 1 }} align="left">Target Table</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '6%', fontSize: '0.75rem', py: 1 }} align="center">Active</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '8%', fontSize: '0.75rem', py: 1 }} align="center">Schedule</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '12%', fontSize: '0.75rem', py: 1 }} align="left">Next Run</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '12%', fontSize: '0.75rem', py: 1 }} align="left">Last Run</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: '10%', fontSize: '0.75rem', py: 1 }} align="center">Actions</TableCell>
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
                  filteredUploads.map((upload) => {
                    const activeJob = activeJobs[upload.flupldref]?.[0]
                    const hasActiveJob = activeJob && (activeJob.status === 'QUEUED' || activeJob.status === 'PROCESSING' || activeJob.status === 'NEW' || activeJob.status === 'CLAIMED')
                    const isExpanded = expandedRows[upload.flupldref] || false
                    const progress = activeJob?.progress || {}
                    const currentJobStatus = jobRequestId && selectedUpload?.flupldref === upload.flupldref ? jobStatus : null
                    const displayStatus = activeJob?.status || currentJobStatus
                    
                    // Calculate percentage
                    const percentage = progress?.percentage || (progress?.rows_processed && progress?.total_rows 
                      ? Math.min(100, Math.round((progress.rows_processed / progress.total_rows) * 100))
                      : null)
                    
                    return (
                      <React.Fragment key={upload.flupldref}>
                        <TableRow
                          hover
                          sx={{
                            '&:hover': {
                              backgroundColor: darkMode
                                ? alpha(muiTheme.palette.action.hover, 0.1)
                                : muiTheme.palette.action.hover,
                            },
                            ...(hasActiveJob && {
                              backgroundColor: darkMode
                                ? alpha(muiTheme.palette.info.main, 0.1)
                                : alpha(muiTheme.palette.info.main, 0.05),
                            }),
                            '& > td': {
                              py: 1,
                              fontSize: '0.8125rem',
                            },
                          }}
                        >
                          <TableCell align="left">
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              <Box sx={{ fontWeight: 600, fontSize: '0.875rem' }}>{upload.flupldref}</Box>
                              {/* Show running indicator, expand/collapse, and cancel button for any active job */}
                              {displayStatus && (displayStatus === 'QUEUED' || displayStatus === 'PROCESSING' || displayStatus === 'NEW' || displayStatus === 'CLAIMED') && (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
                                  <Chip
                                    icon={displayStatus === 'PROCESSING' || displayStatus === 'CLAIMED' ? <CircularProgress size={14} thickness={4} sx={{ color: 'inherit' }} /> : null}
                                    label={displayStatus === 'PROCESSING' || displayStatus === 'CLAIMED' ? 'Processing...' : displayStatus === 'NEW' ? 'Waiting...' : 'Queued'}
                                    size="small"
                                    color={displayStatus === 'PROCESSING' || displayStatus === 'CLAIMED' ? 'warning' : 'info'}
                                    onClick={() => setExpandedRows(prev => ({ ...prev, [upload.flupldref]: !prev[upload.flupldref] }))}
                                    sx={{
                                      cursor: 'pointer',
                                      animation: (displayStatus === 'PROCESSING' || displayStatus === 'CLAIMED') ? 'pulse 2s infinite' : 'none',
                                      '@keyframes pulse': {
                                        '0%, 100%': { opacity: 1 },
                                        '50%': { opacity: 0.6 },
                                      },
                                      fontWeight: 600,
                                      border: (displayStatus === 'PROCESSING' || displayStatus === 'CLAIMED') ? `2px solid ${muiTheme.palette.warning.main}` : 'none',
                                    }}
                                  />
                                  <Tooltip title={isExpanded ? "Hide progress" : "Show progress"}>
                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        setExpandedRows(prev => ({ ...prev, [upload.flupldref]: !prev[upload.flupldref] }))
                                      }}
                                      sx={{ p: 0.5 }}
                                    >
                                      {isExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="Cancel job">
                                    <IconButton
                                      size="small"
                                      color="error"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleCancelJob(activeJob?.request_id || (currentJobStatus ? jobRequestId : null), upload.flupldref)
                                      }}
                                      sx={{ p: 0.5 }}
                                    >
                                      <CancelIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              )}
                            </Box>
                          </TableCell>
                      <TableCell align="left">
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                            {upload.fluplddesc || '-'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="left">
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          <Typography variant="body2" sx={{ fontSize: '0.875rem', wordBreak: 'break-word' }}>
                            {upload.flnm || '-'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={upload.fltyp || 'N/A'}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="left">
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          <Typography variant="body2" sx={{ fontSize: '0.875rem', wordBreak: 'break-word' }}>
                            {upload.trgschm && upload.trgtblnm
                              ? `${upload.trgschm}.${upload.trgtblnm}`
                              : '-'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={upload.stflg === 'A'}
                          color="success"
                          inputProps={{ 'aria-label': 'Active?' }}
                          onChange={() => handleToggleStatus(upload)}
                          size="small"
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
                          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>-</Typography>
                        )}
                      </TableCell>
                      <TableCell align="left">
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          {upload.schd_nxt_run_dt ? (
                            <Tooltip title={new Date(upload.schd_nxt_run_dt).toLocaleString()}>
                              <Typography variant="body2" sx={{ fontSize: '0.75rem', whiteSpace: 'normal', wordBreak: 'break-word' }}>
                                {new Date(upload.schd_nxt_run_dt).toLocaleString('en-US', { 
                                  month: 'short', 
                                  day: 'numeric', 
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </Typography>
                            </Tooltip>
                          ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>-</Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="left">
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                          {upload.last_run_dt ? (
                            <Tooltip title={new Date(upload.last_run_dt).toLocaleString()}>
                              <Typography variant="body2" sx={{ fontSize: '0.75rem', whiteSpace: 'normal', wordBreak: 'break-word' }}>
                                {new Date(upload.last_run_dt).toLocaleString('en-US', { 
                                  month: 'short', 
                                  day: 'numeric', 
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </Typography>
                            </Tooltip>
                          ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>-</Typography>
                          )}
                        </Box>
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
                          <Tooltip 
                            title={
                              (() => {
                                const activeJob = activeJobs[upload.flupldref]?.[0]
                                const hasActiveJob = activeJob && (activeJob.status === 'QUEUED' || activeJob.status === 'PROCESSING' || activeJob.status === 'NEW' || activeJob.status === 'CLAIMED')
                                if (hasActiveJob) {
                                  return `File upload is already ${activeJob.status === 'PROCESSING' || activeJob.status === 'CLAIMED' ? 'processing' : activeJob.status === 'QUEUED' ? 'queued' : 'waiting to start'}. Please wait for it to complete.`
                                }
                                if (!upload.trgconid || !upload.trgtblnm) {
                                  return 'Target connection and table must be configured'
                                }
                                return 'Execute file upload'
                              })()
                            }
                          >
                            <span>
                              <IconButton
                                size="small"
                                onClick={() => handleExecuteClick(upload)}
                                color="primary"
                                disabled={
                                  (() => {
                                    const activeJob = activeJobs[upload.flupldref]?.[0]
                                    const hasActiveJob = activeJob && (activeJob.status === 'QUEUED' || activeJob.status === 'PROCESSING' || activeJob.status === 'NEW' || activeJob.status === 'CLAIMED')
                                    return hasActiveJob || !upload.trgconid || !upload.trgtblnm
                                  })()
                                }
                              >
                                <ExecuteIcon fontSize="small" />
                              </IconButton>
                            </span>
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
                          {upload.schdid && (
                            <Tooltip title="Stop Schedule">
                              <IconButton
                                size="small"
                                onClick={() => handleOpenStopScheduleDialog(upload)}
                                color="error"
                              >
                                <StopIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                    
                    {/* Expandable Progress Row */}
                    {hasActiveJob && (
                      <TableRow>
                        <TableCell colSpan={10} sx={{ py: 0, borderBottom: 'none' }}>
                          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 2, backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.3) : alpha(muiTheme.palette.background.paper, 0.5) }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                                    Upload Progress: {upload.flupldref}
                                  </Typography>
                                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                                    Target Table: {upload.trgschm && upload.trgtblnm ? `${upload.trgschm}.${upload.trgtblnm}` : 'N/A'}
                                  </Typography>
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Chip
                                    label={activeJob.status === 'PROCESSING' || activeJob.status === 'CLAIMED' 
                                      ? 'Processing' 
                                      : activeJob.status === 'NEW' 
                                      ? 'Waiting to Start' 
                                      : 'Queued'}
                                    size="small"
                                    color={(activeJob.status === 'PROCESSING' || activeJob.status === 'CLAIMED') ? 'warning' : 'info'}
                                    sx={{
                                      fontWeight: 600,
                                      animation: (activeJob.status === 'PROCESSING' || activeJob.status === 'CLAIMED') ? 'pulse 2s infinite' : 'none',
                                      '@keyframes pulse': {
                                        '0%, 100%': { opacity: 1 },
                                        '50%': { opacity: 0.7 },
                                      },
                                    }}
                                  />
                                  <Tooltip title="Cancel job">
                                    <IconButton
                                      size="small"
                                      color="error"
                                      onClick={() => handleCancelJob(activeJob?.request_id, upload.flupldref)}
                                    >
                                      <CancelIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              </Box>
                              
                              {/* Progress Bar */}
                              {percentage !== null && (
                                <Box sx={{ mb: 2 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                    <Typography variant="body2" color="text.secondary">
                                      Data Loading Progress
                                    </Typography>
                                    <Typography variant="body2" sx={{ fontWeight: 600, color: muiTheme.palette.info.main }}>
                                      {percentage}%
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={percentage} 
                                    sx={{ 
                                      height: 8, 
                                      borderRadius: 1,
                                      backgroundColor: darkMode ? alpha(muiTheme.palette.divider, 0.3) : alpha(muiTheme.palette.divider, 0.2),
                                      '& .MuiLinearProgress-bar': {
                                        borderRadius: 1,
                                      }
                                    }}
                                  />
                                </Box>
                              )}
                              
                              {/* Detailed Information */}
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                                <Box>
                                  <Typography variant="caption" color="text.secondary" display="block">
                                    Table Created
                                  </Typography>
                                  {progress?.table_created ? (
                                    <Chip label="Yes" size="small" color="success" sx={{ mt: 0.5, height: 24 }} />
                                  ) : activeJob.status === 'NEW' || activeJob.status === 'QUEUED' ? (
                                    <Chip label="Pending" size="small" color="default" sx={{ mt: 0.5, height: 24 }} />
                                  ) : (
                                    <Chip label="In Progress" size="small" color="warning" sx={{ mt: 0.5, height: 24 }} />
                                  )}
                                </Box>
                                
                                {progress?.rows_processed !== undefined && (
                                  <Box>
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      Rows Processed
                                    </Typography>
                                    <Typography variant="body2" sx={{ fontWeight: 500, mt: 0.5 }}>
                                      {progress.rows_processed.toLocaleString()}
                                      {progress?.total_rows && ` / ${progress.total_rows.toLocaleString()}`}
                                    </Typography>
                                  </Box>
                                )}
                                
                                {progress?.rows_successful !== undefined && (
                                  <Box>
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      Successful
                                    </Typography>
                                    <Typography variant="body2" sx={{ fontWeight: 500, color: 'success.main', mt: 0.5 }}>
                                      {progress.rows_successful.toLocaleString()}
                                    </Typography>
                                  </Box>
                                )}
                                
                                {progress?.rows_failed !== undefined && progress.rows_failed > 0 && (
                                  <Box>
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      Failed
                                    </Typography>
                                    <Typography variant="body2" sx={{ fontWeight: 500, color: 'error.main', mt: 0.5 }}>
                                      {progress.rows_failed.toLocaleString()}
                                    </Typography>
                                  </Box>
                                )}
                              </Box>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                  )
                  })
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
          // Allow closing even if processing, but keep polling in background
          // User can check status later via execution history
          if (executing || jobStatus === 'PROCESSING' || jobStatus === 'QUEUED') {
            // Keep polling in background, just close dialog
            message.info('Job is running in background. Check execution history or reopen this dialog for status updates.')
          }
          setShowExecuteDialog(false)
          // Don't clear jobRequestId and jobStatus - keep them for potential status checks
          // Only clear if job is done
          if (jobStatus === 'DONE' || jobStatus === 'FAILED') {
            setExecuteResult(null)
            setJobRequestId(null)
            setJobStatus(null)
            if (pollingInterval) {
              clearInterval(pollingInterval)
              setPollingInterval(null)
            }
          }
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <span>Execute File Upload: {selectedUpload?.flupldref}</span>
              {jobStatus && (
                <>
                  <Chip 
                    label={jobStatus === 'PROCESSING' ? 'Processing...' : jobStatus === 'QUEUED' ? 'Queued' : jobStatus === 'NEW' ? 'Waiting...' : jobStatus}
                    size="small"
                    color={jobStatus === 'PROCESSING' ? 'warning' : 'info'}
                  />
                  {(jobStatus === 'QUEUED' || jobStatus === 'PROCESSING' || jobStatus === 'NEW' || jobStatus === 'CLAIMED') && jobRequestId && (
                    <Tooltip title="Cancel this job">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleCancelJob(jobRequestId, selectedUpload?.flupldref)}
                        sx={{ ml: 1 }}
                      >
                        <CancelIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </>
              )}
            </Box>
            {(() => {
              if (!selectedUpload || jobStatus) return null
              const activeJob = activeJobs[selectedUpload.flupldref]?.[0]
              const hasActiveJob = activeJob && (activeJob.status === 'QUEUED' || activeJob.status === 'PROCESSING' || activeJob.status === 'NEW')
              if (hasActiveJob) {
                return (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    A file upload is already {activeJob.status === 'PROCESSING' || activeJob.status === 'CLAIMED' ? 'processing' : activeJob.status === 'QUEUED' ? 'queued' : 'waiting to start'}. 
                    Please wait for it to complete before starting a new upload.
                  </Alert>
                )
              }
              return null
            })()}
          </Box>
        </DialogTitle>
        <DialogContent>
          {executing || jobStatus ? (
            <Box sx={{ py: 2 }}>
              {jobStatus === 'QUEUED' && (
                <>
                  <Typography variant="body2" sx={{ mb: 2, fontWeight: 600 }}>
                    File upload queued for background execution
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Request ID: {jobRequestId}
                  </Typography>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    The file upload is queued and will be processed in the background. 
                    You can close this dialog and continue working. The job status will be updated automatically.
                  </Alert>
                  <LinearProgress />
                </>
              )}
              {jobStatus === 'PROCESSING' && (
                <>
                  <Typography variant="body2" sx={{ mb: 2, fontWeight: 600 }}>
                    Processing file upload...
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Request ID: {jobRequestId}
                  </Typography>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    The file is being processed in chunks. This may take a while for large files.
                  </Alert>
                  <LinearProgress />
                </>
              )}
              {jobStatus === 'NEW' && (
                <>
                  <Typography variant="body2" sx={{ mb: 2, fontWeight: 600 }}>
                    File upload queued (waiting to start)...
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Request ID: {jobRequestId}
                  </Typography>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    The file upload is queued and waiting for the scheduler to pick it up.
                    Status will update automatically when processing starts.
                  </Alert>
                  <LinearProgress />
                </>
              )}
              {!jobStatus && (
                <>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    Queuing file upload...
                  </Typography>
                  <LinearProgress />
                </>
              )}
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
                setJobRequestId(null)
                setJobStatus(null)
                if (pollingInterval) {
                  clearInterval(pollingInterval)
                  setPollingInterval(null)
                }
              }}
              variant="contained"
            >
              Close
            </Button>
          ) : (executing || jobStatus) ? (
            <Button
              onClick={() => {
                setShowExecuteDialog(false)
                // Keep polling in background, user can check status later
                message.info('Job is running in background. Check execution history for status.')
              }}
              variant="outlined"
            >
              Close (Keep Running)
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
                disabled={
                  executing || 
                  (() => {
                    if (!selectedUpload) return false
                    const activeJob = activeJobs[selectedUpload.flupldref]?.[0]
                    return activeJob && (activeJob.status === 'QUEUED' || activeJob.status === 'PROCESSING' || activeJob.status === 'NEW' || activeJob.status === 'CLAIMED')
                  })()
                }
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

      {/* Stop Schedule Dialog */}
      <Dialog
        open={stopScheduleDialog.show}
        onClose={handleCloseStopScheduleDialog}
      >
        <DialogTitle>Stop Schedule</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Are you sure you want to stop the schedule for upload configuration "{stopScheduleDialog.upload?.flupldref}"?
          </DialogContentText>
          <Typography variant="body2" color="warning.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon fontSize="small" />
            This will disable automatic file uploads for this configuration.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseStopScheduleDialog} disabled={stoppingSchedule}>Cancel</Button>
          <Button 
            onClick={handleStopSchedule} 
            color="error" 
            variant="contained"
            disabled={stoppingSchedule}
            startIcon={stoppingSchedule ? <CircularProgress size={16} /> : <StopIcon />}
          >
            Stop Schedule
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default UploadTable

