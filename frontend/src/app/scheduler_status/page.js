'use client'

import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  useTheme as useMuiTheme,
  alpha,
  IconButton,
} from '@mui/material'
import {
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  CloudUpload as CloudUploadIcon,
  Description as ReportIcon,
  Settings as MapperIcon,
} from '@mui/icons-material'
import { useTheme } from '@/context/ThemeContext'
import axios from 'axios'
import { API_BASE_URL } from '@/app/config'

// Helper function to extract error message from API errors
const getApiErrorMessage = (error, defaultMessage = 'An error occurred') => {
  if (error.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  if (error.message) {
    return error.message
  }
  return defaultMessage
}

export default function SchedulerStatusPage() {
  const { darkMode } = useTheme()
  const muiTheme = useMuiTheme()
  const [loading, setLoading] = useState(true)
  const [schedulerData, setSchedulerData] = useState(null)
  const [error, setError] = useState(null)

  const fetchSchedulerStatus = async () => {
    try {
      // Don't set loading to true on subsequent refreshes to avoid flickering
      if (!schedulerData) {
        setLoading(true)
      }
      setError(null)
      const token = localStorage.getItem('token')
      const response = await axios.get(`${API_BASE_URL}/job/scheduler-status`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data.success) {
        console.log('[SchedulerStatus] Received data:', response.data)
        console.log('[SchedulerStatus] File upload counts:', response.data.job_counts?.file_uploads)
        setSchedulerData(response.data)
      } else {
        console.error('[SchedulerStatus] API returned success=false:', response.data)
        setError('Failed to fetch scheduler status')
      }
    } catch (err) {
      console.error('Error fetching scheduler status:', err)
      setError(getApiErrorMessage(err, 'Failed to fetch scheduler status'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSchedulerStatus()
    // Auto-refresh every 3 seconds to match file upload configuration screen
    const interval = setInterval(fetchSchedulerStatus, 3000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'PROCESSING':
        return 'warning'
      case 'WAITING':
        return 'success'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'PROCESSING':
        return <CircularProgress size={20} thickness={4} sx={{ color: muiTheme.palette.warning.main }} />
      case 'WAITING':
        return <CheckCircleIcon sx={{ color: muiTheme.palette.success.main }} />
      default:
        return <ScheduleIcon />
    }
  }

  const getJobStatusColor = (status) => {
    const upperStatus = (status || '').toUpperCase()
    switch (upperStatus) {
      case 'PROCESSING':
      case 'CLAIMED':
        return 'warning'
      case 'QUEUED':
        return 'info'
      case 'NEW':
        return 'default'
      case 'DONE':
        return 'success'
      case 'FAILED':
        return 'error'
      default:
        return 'default'
    }
  }

  if (loading && !schedulerData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box sx={{ p: 3, color: 'text.primary' }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="error" variant="h6" gutterBottom>
            Error Loading Scheduler Status
          </Typography>
          <Typography color="text.secondary" variant="body2">
            {error}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <IconButton onClick={fetchSchedulerStatus} color="primary">
              <RefreshIcon />
            </IconButton>
          </Box>
        </Paper>
      </Box>
    )
  }

  const { scheduler_status, total_active_jobs, job_counts, recent_activity } = schedulerData || {}

  return (
    <Box
      sx={{
        p: 3,
        color: 'text.primary',
        borderRadius: 2,
        backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.25) : 'transparent',
      }}
    >
      {/* Scheduler Status Card */}
      <Card sx={{ mb: 3, color: 'text.primary', backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            {getStatusIcon(scheduler_status)}
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Scheduler Status: {scheduler_status}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {scheduler_status === 'WAITING' 
                  ? 'Scheduler is waiting for new jobs to process'
                  : `Currently processing ${total_active_jobs} active job${total_active_jobs !== 1 ? 's' : ''}`}
              </Typography>
            </Box>
            <Chip
              label={scheduler_status}
              color={getStatusColor(scheduler_status)}
              sx={{ ml: 'auto', fontWeight: 600 }}
            />
            <IconButton onClick={fetchSchedulerStatus} color="primary" disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Box>
        </CardContent>
      </Card>

      {/* Job Counts Summary */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* File Uploads */}
        <Grid item xs={12} md={4}>
          <Card sx={{ color: 'text.primary', backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CloudUploadIcon color="primary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  File Uploads
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                  {job_counts?.file_uploads?.active || 0}
                </Typography>
                {(job_counts?.file_uploads?.processing || 0) > 0 && (
                  <CircularProgress size={24} thickness={4} sx={{ color: muiTheme.palette.warning.main }} />
                )}
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">New:</Typography>
                  <Chip 
                    label={job_counts?.file_uploads?.new || 0} 
                    size="small"
                    sx={{ minWidth: 40, justifyContent: 'center' }}
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Queued:</Typography>
                  <Chip 
                    label={job_counts?.file_uploads?.queued || 0} 
                    size="small" 
                    color="info"
                    sx={{ minWidth: 40, justifyContent: 'center' }}
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Processing:</Typography>
                  <Chip 
                    label={job_counts?.file_uploads?.processing || 0} 
                    size="small" 
                    color="warning"
                    icon={(job_counts?.file_uploads?.processing || 0) > 0 ? (
                      <CircularProgress size={14} thickness={4} sx={{ color: 'inherit' }} />
                    ) : null}
                    sx={{ 
                      minWidth: 40, 
                      justifyContent: 'center',
                      animation: (job_counts?.file_uploads?.processing || 0) > 0 ? 'pulse 2s infinite' : 'none',
                      '@keyframes pulse': {
                        '0%, 100%': { opacity: 1 },
                        '50%': { opacity: 0.7 },
                      },
                    }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Reports */}
        <Grid item xs={12} md={4}>
          <Card sx={{ color: 'text.primary', backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <ReportIcon color="secondary" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Reports
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                {job_counts?.reports?.active || 0}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">New:</Typography>
                  <Chip label={job_counts?.reports?.new || 0} size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Queued:</Typography>
                  <Chip label={job_counts?.reports?.queued || 0} size="small" color="info" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Processing:</Typography>
                  <Chip label={job_counts?.reports?.processing || 0} size="small" color="warning" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Mapper Jobs */}
        <Grid item xs={12} md={4}>
          <Card sx={{ color: 'text.primary', backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <MapperIcon color="success" />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Mapper Jobs
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                {job_counts?.mapper_jobs?.active || 0}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">New:</Typography>
                  <Chip label={job_counts?.mapper_jobs?.new || 0} size="small" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Queued:</Typography>
                  <Chip label={job_counts?.mapper_jobs?.queued || 0} size="small" color="info" />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Processing:</Typography>
                  <Chip label={job_counts?.mapper_jobs?.processing || 0} size="small" color="warning" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Paper sx={{ color: 'text.primary', backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper }}>
        <Box sx={{ p: 2, borderBottom: `1px solid ${alpha(muiTheme.palette.divider, 0.5)}` }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Recent Activity
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: darkMode ? alpha(muiTheme.palette.background.default, 0.55) : alpha(muiTheme.palette.grey[100], 0.7) }}>
                <TableCell sx={{ fontWeight: 600 }}>Request ID</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Map Reference</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Requested At</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recent_activity && recent_activity.length > 0 ? (
                recent_activity.map((job, index) => (
                  <TableRow key={job.request_id || index} hover>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {job.request_id?.substring(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>{job.mapref || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={job.request_type || 'N/A'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={job.status || 'UNKNOWN'}
                        size="small"
                        color={getJobStatusColor(job.status)}
                      />
                    </TableCell>
                    <TableCell>
                      {job.requested_at ? new Date(job.requested_at).toLocaleString() : '-'}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <Typography variant="body2" color="text.secondary">
                      No recent activity
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  )
}

