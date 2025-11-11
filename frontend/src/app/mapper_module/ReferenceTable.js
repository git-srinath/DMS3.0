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
  Checkbox,
  Tooltip,
  CircularProgress,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  Menu,
  ListItemIcon,
  ListItemText,
  Autocomplete,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Box,
  Typography,
  useTheme as useMuiTheme,
  alpha,
  Chip,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  Lock as LockIcon,
} from '@mui/icons-material'
import { message } from 'antd'
import { useTheme } from '@/context/ThemeContext'

import axios from 'axios'
import { motion } from 'framer-motion'

const getApiErrorMessage = (error, defaultMessage) => {
  // Check if it's an Axios error
  if (axios.isAxiosError(error)) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const serverMessage = error.response.data?.error || error.response.data?.message;
      if (serverMessage) {
        return `Operation failed: ${serverMessage}`;
      }
      return `Server Error: Received status code ${error.response.status}. If the problem persists, please contact support.`;
    } else if (error.request) {
      // The request was made but no response was received
      return 'Network Error: Unable to connect to the server. Please check your internet connection and try again.';
    }
  }

  // This could be a standard Error from fetch (network error) or other JS errors
  if (error instanceof Error) {
    if (error.message.includes('Failed to fetch')) {
      return 'Network Error: Could not connect to the backend. Please ensure the server is running and accessible.';
    }
    return `An unexpected error occurred: ${error.message}`;
  }
  
  // Fallback for other types of thrown values
  return defaultMessage || 'An unknown error occurred. Please try again.';
};

const ReferenceTable = ({ handleEditReference, handleCreateNewReference }) => {
  const { darkMode } = useTheme()
  const muiTheme = useMuiTheme()

  // New state variables for the table view
  const [allReferences, setAllReferences] = useState([])
  const [loadingReferences, setLoadingReferences] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedReference, setSelectedReference] = useState(null)

  // Add search state for references table
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredReferences, setFilteredReferences] = useState([])

  // Add state variables for filter options
  const [filterAnchorEl, setFilterAnchorEl] = useState(null)
  const [filters, setFilters] = useState({
    tableType: [],
    status: [],
    sourceSystem: [],
    logicVerification: [],
  })

  const [tableTypeOptions, setTableTypeOptions] = useState([])

  const [sourceSystemOptions, setSourceSystemOptions] = useState([])

  const [statusOptions] = useState([
    { label: 'Active', value: 'A' },
    { label: 'Inactive', value: 'I' },
  ])
  const [logicVerOptions] = useState([
    { label: 'Verified', value: 'Y' },
    { label: 'Unverified', value: 'N' },
  ])

  // Add state for tracking locked references
  const [lockedReferences, setLockedReferences] = useState({})
  const [loadingLocks, setLoadingLocks] = useState(false)

  // Function to fetch lock status for all references
  const fetchLockStatus = async () => {
    setLoadingLocks(true)
    const lockStatus = {}
    
    try {
      // Fetch all locks at once
      const response = await axios.get('/api/mapper/locks', {
        headers: {
          'x-skip-rewrite': '1'
        }
      })
      
      if (response.data.success && response.data.locks) {
        // Create a map of reference to lock info
        response.data.locks.forEach(lock => {
          lockStatus[lock.reference] = {
            isLocked: true,
            lockedBy: lock.username,
            lockedAt: lock.lockedAt
          }
        })
      }
      
      setLockedReferences(lockStatus)
    } catch (error) {
      console.error('Error fetching lock status:', error)
      message.error(getApiErrorMessage(error, 'Failed to fetch lock status'))
    } finally {
      setLoadingLocks(false)
    }
  }

  // Fetch all mapper references
  const fetchAllReferences = async () => {
    setLoadingReferences(true)
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/mapper/get-all-mapper-reference`
      )
      if (response.data) {
        setAllReferences(response.data)
        setFilteredReferences(response.data) // Initialize filtered references with all references
        
        // After fetching references, fetch their lock status
        fetchLockStatus()
      }
    } catch (error) {
      console.error('Error fetching mapper references:', error)
      message.error(getApiErrorMessage(error, 'Failed to load mapper references'))
    } finally {
      setLoadingReferences(false)
    }
  }

  // Function to handle showing the delete confirmation dialog
  const handleShowDeleteDialog = (reference) => {
    setSelectedReference(reference)
    setShowDeleteDialog(true)
  }

  // Function to handle canceling the delete action
  const handleCancelDelete = () => {
    setShowDeleteDialog(false)
    setSelectedReference(null)
  }

  // Function to handle confirming the delete action
  const handleConfirmDelete = async () => {
    try {
      setLoadingReferences(true)
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/mapper/delete-mapper-reference`,
        {
          mapref: selectedReference,
        }
      )

      if (response.data.success) {
        message.success(
          response.data.message || 'Mapper reference deleted successfully'
        )
        setShowDeleteDialog(false)
        setSelectedReference(null)
        // Refresh the references list
        fetchAllReferences()
      } else {
        message.error(
          response.data.message || 'Failed to delete mapper reference'
        )
      }
    } catch (error) {
      console.error('Error deleting mapper reference:', error)
      message.error(getApiErrorMessage(error, 'Failed to delete mapper reference. Please try again.'))
    } finally {
      setLoadingReferences(false)
    }
  }

  useEffect(() => {
    fetchAllReferences()
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      fetchLockStatus();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval); // Cleanup on unmount
  }, []); // Note: separate useEffect to avoid re-fetching all references

  // Modify the fetchReferenceDetails function to handle navigation

  // Format date for display in the reference table
  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // Add a new function to handle search in references table
  const handleReferenceSearch = (event) => {
    const query = event.target.value
    setSearchQuery(query)

    // Use the query value directly instead of relying on searchQuery state
    applyFiltersWithQuery(query)
  }

  // Add a new function that takes the query as a parameter
  const applyFiltersWithQuery = (currentQuery) => {
    if (
      currentQuery.trim() === '' &&
      !filters.tableType.length &&
      !filters.status.length &&
      !filters.sourceSystem.length &&
      !filters.logicVerification.length
    ) {
      setFilteredReferences(allReferences)
      return
    }

    const filtered = allReferences.filter((reference) => {
      // Text search filter using the passed-in query parameter
      const textMatch =
        currentQuery.trim() === '' ||
        reference[0]
          ?.toString()
          .toLowerCase()
          .includes(currentQuery.toLowerCase()) ||
        reference[1]
          ?.toString()
          .toLowerCase()
          .includes(currentQuery.toLowerCase()) ||
        reference[2]
          ?.toString()
          .toLowerCase()
          .includes(currentQuery.toLowerCase()) ||
        reference[5]
          ?.toString()
          .toLowerCase()
          .includes(currentQuery.toLowerCase()) ||
        (reference[8]
          ?.toString()
          .toLowerCase()
          .includes(currentQuery.toLowerCase())) ||
        (reference[9]
          ?.toString()
          .toLowerCase()
          .includes(currentQuery.toLowerCase()))

      // Table type filter
      const tableTypeMatch =
        filters.tableType.length === 0 ||
        filters.tableType.includes(reference[3])

      // Status filter
      const statusMatch =
        filters.status.length === 0 || filters.status.includes(reference[7])

      // Source system filter
      const sourceSystemMatch =
        filters.sourceSystem.length === 0 ||
        filters.sourceSystem.includes(reference[5])

      // Logic verification filter
      const logicVerMatch =
        filters.logicVerification.length === 0 ||
        filters.logicVerification.includes(reference[6])

      // Return true only if all filters match
      return (
        textMatch &&
        tableTypeMatch &&
        statusMatch &&
        sourceSystemMatch &&
        logicVerMatch
      )
    })

    setFilteredReferences(filtered)
  }

  // Modify the original applyFilters function to use the current searchQuery state
  const applyFilters = () => {
    applyFiltersWithQuery(searchQuery)
  }

  const clearFilters = () => {
    setFilters({
      tableType: [],
      status: [],
      sourceSystem: [],
      logicVerification: [],
    })

    if (searchQuery.trim() === '') {
      setFilteredReferences(allReferences)
    } else {
      // Use the current searchQuery value
      applyFiltersWithQuery(searchQuery)
    }

    handleFilterClose()
  }

  // Add useEffect to extract unique table types and source systems from references
  useEffect(() => {
    if (allReferences.length > 0) {
      // Extract unique table types
      const tableTypes = [
        ...new Set(allReferences.map((ref) => ref[3]).filter(Boolean)),
      ].map((type) => ({ label: type, value: type }))
      setTableTypeOptions(tableTypes)

      // Extract unique source systems
      const sourceSystems = [
        ...new Set(allReferences.map((ref) => ref[5]).filter(Boolean)),
      ].map((system) => ({ label: system, value: system }))
      setSourceSystemOptions(sourceSystems)
    }
  }, [allReferences])

  // Add functions to handle filter
  const handleFilterClick = (event) => {
    setFilterAnchorEl(event.currentTarget)
  }

  const handleFilterClose = () => {
    setFilterAnchorEl(null)
  }

  const handleFilterChange = (filterType, value) => {
    setFilters((prev) => {
      const newFilters = { ...prev }

      // Toggle filter value
      if (newFilters[filterType].includes(value)) {
        newFilters[filterType] = newFilters[filterType].filter(
          (v) => v !== value
        )
      } else {
        newFilters[filterType] = [...newFilters[filterType], value]
      }

      return newFilters
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full"
    >
      <div
        className={`transition-all duration-300 ${
          darkMode ? 'text-gray-100' : 'text-gray-800'
        }`}
      >
        {/* Reorganized header section - all elements in a single row */}
        <div className="flex items-center justify-between mb-3 gap-2">
          {/* Search field - now in line with other controls */}
          <div className="flex items-center flex-grow gap-2 max-w-xl">
            <TextField
              placeholder="Search references..."
              variant="outlined"
              size="small"
              fullWidth
              value={searchQuery}
              onChange={handleReferenceSearch}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: searchQuery && (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSearchQuery('')
                        applyFiltersWithQuery('')
                      }}
                      edge="end"
                    >
                      <ClearIcon fontSize="small" />
                    </IconButton>
                  </InputAdornment>
                ),
                style: { borderRadius: '8px' },
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  height: '40px',
                  backgroundColor: darkMode ? 'rgba(31, 41, 55, 0.5)' : 'white',
                  '&:hover fieldset': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.5)'
                      : 'rgba(59, 130, 246, 0.5)',
                  },
                  fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)', // Responsive font sizing
                },
              }}
            />

            {/* Filter Button */}
            <Tooltip title="Filter References">
              <IconButton
                onClick={handleFilterClick}
                sx={{
                  backgroundColor: darkMode ? 'rgba(31, 41, 55, 0.5)' : 'white',
                  border: '1px solid',
                  borderColor: darkMode
                    ? 'rgba(75, 85, 99, 0.2)'
                    : 'rgba(229, 231, 235, 1)',
                  borderRadius: '8px',
                  height: '40px',
                  width: '40px',
                  '&:hover': {
                    backgroundColor: darkMode
                      ? 'rgba(55, 65, 81, 0.7)'
                      : 'rgba(249, 250, 251, 0.9)',
                  },
                  position: 'relative',
                }}
              >
                <SettingsIcon fontSize="small" />
                {/* Indicator dot if filters are active */}
                {(filters.tableType.length > 0 ||
                  filters.status.length > 0 ||
                  filters.sourceSystem.length > 0 ||
                  filters.logicVerification.length > 0) && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      backgroundColor: '#2563EB',
                    }}
                  />
                )}
              </IconButton>
            </Tooltip>
          </div>

          {/* Create New Reference Button */}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNewReference}
            sx={{
              textTransform: 'none',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #2563EB, #3B82F6)',
              '&:hover': {
                background: 'linear-gradient(135deg, #1D4ED8, #2563EB)',
              },
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              px: 2,
              py: 1,
              height: '40px',
              fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)', // Responsive font sizing
            }}
          >
            Create New Reference
          </Button>
        </div>

        <div
          className={`rounded-lg border ${
            darkMode
              ? 'border-gray-700 bg-gray-800/20 backdrop-blur-sm'
              : 'border-gray-200 bg-white/90 backdrop-blur-sm'
          } overflow-hidden shadow-md mb-4 transition-all duration-300`}
        >
          <TableContainer
            sx={{
              maxHeight: 'calc(100vh - 240px)',
              backgroundColor: 'transparent',
              borderRadius: 1,
            }}
          >
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Reference
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Description
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Target Schema
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Table Type
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Frequency
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Source System
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Status
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Logic Verification
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Created By
                  </TableCell>
                  <TableCell
                    sx={{
                      backgroundColor: darkMode ? '#1A1F2C' : '#F9FAFB',
                      color: darkMode ? 'white' : 'black',
                      fontWeight: 'bold',
                      borderBottom: darkMode
                        ? '1px solid rgba(75, 85, 99, 0.2)'
                        : '1px solid rgba(229, 231, 235, 1)',
                    }}
                  >
                    Actions
                  </TableCell>
                </TableRow>
              </TableHead>

              <TableBody>
                {loadingReferences ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center" sx={{ py: 3 }}>
                      <CircularProgress size={30} />
                      <Typography
                        variant="body2"
                        sx={{
                          mt: 1,
                          color: darkMode ? 'gray.400' : 'gray.600',
                        }}
                      >
                        Loading references...
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : filteredReferences.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={10} align="center" sx={{ py: 3 }}>
                      <Typography
                        variant="body1"
                        sx={{ color: darkMode ? 'gray.400' : 'gray.600' }}
                      >
                        {allReferences.length === 0
                          ? 'No references found'
                          : `No references found matching "${searchQuery}"`}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredReferences.map((reference, index) => {
                    // Check if this reference is locked
                    const isLocked = lockedReferences[reference[0]] !== undefined
                    const lockInfo = lockedReferences[reference[0]]
                    
                    return (
                      <TableRow
                        key={reference[0]}
                        hover
                        sx={{
                          cursor: 'pointer',
                          height: { xs: 'auto', md: '32px' }, // Adjusted for better scaling
                          '&:hover': {
                            backgroundColor: darkMode
                              ? alpha(muiTheme.palette.primary.main, 0.1)
                              : alpha(muiTheme.palette.primary.main, 0.05),
                          },
                          borderBottom: darkMode
                            ? '1px solid rgba(75, 85, 99, 0.1)'
                            : '1px solid rgba(229, 231, 235, 0.7)',
                        }}
                      >
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          <div className="flex items-center">
                            {reference[0]}
                            {isLocked && (
                              <Tooltip 
                                title={`Locked by ${lockInfo.lockedBy} at ${new Date(lockInfo.lockedAt).toLocaleString()}`}
                                arrow
                              >
                                <LockIcon 
                                  fontSize="small" 
                                  className="ml-2 text-amber-500"
                                  sx={{ fontSize: '16px' }}
                                />
                              </Tooltip>
                            )}
                          </div>
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[1] || '-'}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[2] || '-'}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[3] || '-'}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[4] || '-'}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[5] || '-'}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[7] === 'A' ? (
                            <Chip
                              label="Active"
                              size="small"
                              sx={{
                                backgroundColor: darkMode
                                  ? 'rgba(16, 185, 129, 0.2)'
                                  : 'rgba(16, 185, 129, 0.1)',
                                color: darkMode
                                  ? 'rgb(16, 185, 129)'
                                  : 'rgb(5, 150, 105)',
                                borderRadius: '4px',
                                fontWeight: '500',
                              }}
                            />
                          ) : (
                            <Chip
                              label="Inactive"
                              size="small"
                              sx={{
                                backgroundColor: darkMode
                                  ? 'rgba(239, 68, 68, 0.2)'
                                  : 'rgba(239, 68, 68, 0.1)',
                                color: darkMode
                                  ? 'rgb(239, 68, 68)'
                                  : 'rgb(220, 38, 38)',
                                borderRadius: '4px',
                                fontWeight: '500',
                              }}
                            />
                          )}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[6] === 'Y' ? (
                            <Chip
                              label="Verified"
                              size="small"
                              sx={{
                                backgroundColor: darkMode
                                  ? 'rgba(37, 99, 235, 0.2)'
                                  : 'rgba(37, 99, 235, 0.1)',
                                color: darkMode
                                  ? 'rgb(96, 165, 250)'
                                  : 'rgb(37, 99, 235)',
                                borderRadius: '4px',
                                fontWeight: '500',
                              }}
                            />
                          ) : (
                            <Chip
                              label="Unverified"
                              size="small"
                              sx={{
                                backgroundColor: darkMode
                                  ? 'rgba(245, 158, 11, 0.2)'
                                  : 'rgba(245, 158, 11, 0.1)',
                                color: darkMode
                                  ? 'rgb(251, 191, 36)'
                                  : 'rgb(217, 119, 6)',
                                borderRadius: '4px',
                                fontWeight: '500',
                              }}
                            />
                          )}
                        </TableCell>
                        <TableCell
                          sx={{
                            color: darkMode ? 'white' : 'inherit',
                            fontSize: 'clamp(0.8rem, 0.875vw, 0.875rem)',
                          }}
                        >
                          {reference[8] || '-'}
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <Tooltip title="Edit Reference">
                              <IconButton
                                size="small"
                                onClick={() =>
                                  handleEditReference(reference[0])
                                }
                                sx={{
                                  backgroundColor: darkMode
                                    ? alpha(muiTheme.palette.primary.main, 0.2)
                                    : alpha(muiTheme.palette.primary.main, 0.1),
                                  '&:hover': {
                                    backgroundColor: darkMode
                                      ? alpha(
                                          muiTheme.palette.primary.main,
                                          0.3
                                        )
                                      : alpha(
                                          muiTheme.palette.primary.main,
                                          0.2
                                        ),
                                  },
                                }}
                              >
                                <EditIcon
                                  fontSize="small"
                                  sx={{
                                    color: darkMode
                                      ? muiTheme.palette.primary.light
                                      : muiTheme.palette.primary.main,
                                  }}
                                />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete Reference">
                              <IconButton
                                size="small"
                                onClick={() =>
                                  handleShowDeleteDialog(reference[0])
                                }
                                sx={{
                                  backgroundColor: darkMode
                                    ? alpha(muiTheme.palette.error.main, 0.2)
                                    : alpha(muiTheme.palette.error.main, 0.1),
                                  '&:hover': {
                                    backgroundColor: darkMode
                                      ? alpha(muiTheme.palette.error.main, 0.3)
                                      : alpha(muiTheme.palette.error.main, 0.2),
                                  },
                                }}
                              >
                                <DeleteIcon
                                  fontSize="small"
                                  sx={{
                                    color: darkMode
                                      ? muiTheme.palette.error.light
                                      : muiTheme.palette.error.main,
                                  }}
                                />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    )
                  })
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={showDeleteDialog}
        onClose={handleCancelDelete}
        PaperProps={{
          style: {
            backgroundColor: darkMode ? '#1F2937' : 'white',
            borderRadius: '12px',
            padding: '8px',
          },
        }}
      >
        <DialogTitle sx={{ color: darkMode ? 'white' : 'inherit' }}>
          Confirm Deletion
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: darkMode ? '#D1D5DB' : 'inherit' }}>
            Are you sure you want to delete the reference "{selectedReference}"?
            This operation cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ padding: '16px' }}>
          <Button
            onClick={handleCancelDelete}
            sx={{
              textTransform: 'none',
              color: darkMode ? '#9CA3AF' : 'inherit',
            }}
            disabled={loadingReferences}
          >
            Cancel
          </Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={loadingReferences}
            startIcon={
              loadingReferences ? (
                <CircularProgress size={20} color="inherit" />
              ) : null
            }
            sx={{
              textTransform: 'none',
              borderRadius: '8px',
            }}
          >
            {loadingReferences ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Filter Menu */}
      <Menu
        anchorEl={filterAnchorEl}
        open={Boolean(filterAnchorEl)}
        onClose={handleFilterClose}
        PaperProps={{
          sx: {
            mt: 1.5,
            width: 300,
            maxHeight: 'calc(100vh - 100px)',
            backgroundColor: darkMode ? '#1F2937' : 'white',
            border: '1px solid',
            borderColor: darkMode
              ? 'rgba(75, 85, 99, 0.2)'
              : 'rgba(229, 231, 235, 1)',
            borderRadius: '8px',
            boxShadow: darkMode
              ? '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)'
              : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
        }}
      >
        <Box p={2}>
          <Typography
            variant="subtitle1"
            sx={{
              fontWeight: 'bold',
              mb: 2,
              color: darkMode ? 'white' : 'inherit',
            }}
          >
            Filter References
          </Typography>

          {/* Table Type Filter */}
          <Box mb={2}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 1,
                fontWeight: 'medium',
                color: darkMode ? '#D1D5DB' : 'inherit',
              }}
            >
              Table Type
            </Typography>
            <FormControl fullWidth size="small">
              <Select
                multiple
                value={filters.tableType}
                onChange={(e) => {
                  setFilters({ ...filters, tableType: e.target.value })
                }}
                renderValue={(selected) => selected.join(', ')}
                MenuProps={{
                  PaperProps: {
                    style: {
                      maxHeight: 224,
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                    },
                  },
                }}
                sx={{
                  backgroundColor: darkMode ? 'rgba(31, 41, 55, 0.5)' : 'white',
                  color: darkMode ? 'white' : 'inherit',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(75, 85, 99, 0.5)'
                      : 'rgba(209, 213, 219, 0.8)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.5)'
                      : 'rgba(59, 130, 246, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.8)'
                      : 'rgba(59, 130, 246, 0.8)',
                  },
                }}
              >
                {tableTypeOptions.map((option) => (
                  <MenuItem
                    key={option.value}
                    value={option.value}
                    sx={{
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                      color: darkMode ? 'white' : 'inherit',
                      '&.Mui-selected': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.2)'
                          : 'rgba(37, 99, 235, 0.1)',
                      },
                      '&.Mui-selected:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.3)'
                          : 'rgba(37, 99, 235, 0.2)',
                      },
                      '&:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(55, 65, 81, 0.7)'
                          : 'rgba(249, 250, 251, 0.9)',
                      },
                    }}
                  >
                    <Checkbox
                      checked={filters.tableType.indexOf(option.value) > -1}
                      sx={{
                        color: darkMode
                          ? 'rgba(156, 163, 175, 0.8)'
                          : 'rgba(107, 114, 128, 0.8)',
                        '&.Mui-checked': {
                          color: darkMode
                            ? 'rgb(96, 165, 250)'
                            : 'rgb(37, 99, 235)',
                        },
                        padding: '4px',
                      }}
                    />
                    <ListItemText primary={option.label} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Status Filter */}
          <Box mb={2}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 1,
                fontWeight: 'medium',
                color: darkMode ? '#D1D5DB' : 'inherit',
              }}
            >
              Status
            </Typography>
            <FormControl fullWidth size="small">
              <Select
                multiple
                value={filters.status}
                onChange={(e) => {
                  setFilters({ ...filters, status: e.target.value })
                }}
                renderValue={(selected) => {
                  return selected
                    .map(
                      (value) =>
                        statusOptions.find((option) => option.value === value)
                          ?.label
                    )
                    .join(', ')
                }}
                MenuProps={{
                  PaperProps: {
                    style: {
                      maxHeight: 224,
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                    },
                  },
                }}
                sx={{
                  backgroundColor: darkMode ? 'rgba(31, 41, 55, 0.5)' : 'white',
                  color: darkMode ? 'white' : 'inherit',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(75, 85, 99, 0.5)'
                      : 'rgba(209, 213, 219, 0.8)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.5)'
                      : 'rgba(59, 130, 246, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.8)'
                      : 'rgba(59, 130, 246, 0.8)',
                  },
                }}
              >
                {statusOptions.map((option) => (
                  <MenuItem
                    key={option.value}
                    value={option.value}
                    sx={{
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                      color: darkMode ? 'white' : 'inherit',
                      '&.Mui-selected': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.2)'
                          : 'rgba(37, 99, 235, 0.1)',
                      },
                      '&.Mui-selected:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.3)'
                          : 'rgba(37, 99, 235, 0.2)',
                      },
                      '&:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(55, 65, 81, 0.7)'
                          : 'rgba(249, 250, 251, 0.9)',
                      },
                    }}
                  >
                    <Checkbox
                      checked={filters.status.indexOf(option.value) > -1}
                      sx={{
                        color: darkMode
                          ? 'rgba(156, 163, 175, 0.8)'
                          : 'rgba(107, 114, 128, 0.8)',
                        '&.Mui-checked': {
                          color:
                            option.value === 'A'
                              ? darkMode
                                ? 'rgb(16, 185, 129)'
                                : 'rgb(5, 150, 105)'
                              : darkMode
                              ? 'rgb(239, 68, 68)'
                              : 'rgb(220, 38, 38)',
                        },
                        padding: '4px',
                      }}
                    />
                    <ListItemText primary={option.label} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Source System Filter */}
          <Box mb={2}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 1,
                fontWeight: 'medium',
                color: darkMode ? '#D1D5DB' : 'inherit',
              }}
            >
              Source System
            </Typography>
            <FormControl fullWidth size="small">
              <Select
                multiple
                value={filters.sourceSystem}
                onChange={(e) => {
                  setFilters({ ...filters, sourceSystem: e.target.value })
                }}
                renderValue={(selected) => selected.join(', ')}
                MenuProps={{
                  PaperProps: {
                    style: {
                      maxHeight: 224,
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                    },
                  },
                }}
                sx={{
                  backgroundColor: darkMode ? 'rgba(31, 41, 55, 0.5)' : 'white',
                  color: darkMode ? 'white' : 'inherit',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(75, 85, 99, 0.5)'
                      : 'rgba(209, 213, 219, 0.8)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.5)'
                      : 'rgba(59, 130, 246, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.8)'
                      : 'rgba(59, 130, 246, 0.8)',
                  },
                }}
              >
                {sourceSystemOptions.map((option) => (
                  <MenuItem
                    key={option.value}
                    value={option.value}
                    sx={{
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                      color: darkMode ? 'white' : 'inherit',
                      '&.Mui-selected': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.2)'
                          : 'rgba(37, 99, 235, 0.1)',
                      },
                      '&.Mui-selected:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.3)'
                          : 'rgba(37, 99, 235, 0.2)',
                      },
                      '&:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(55, 65, 81, 0.7)'
                          : 'rgba(249, 250, 251, 0.9)',
                      },
                    }}
                  >
                    <Checkbox
                      checked={filters.sourceSystem.indexOf(option.value) > -1}
                      sx={{
                        color: darkMode
                          ? 'rgba(156, 163, 175, 0.8)'
                          : 'rgba(107, 114, 128, 0.8)',
                        '&.Mui-checked': {
                          color: darkMode
                            ? 'rgb(96, 165, 250)'
                            : 'rgb(37, 99, 235)',
                        },
                        padding: '4px',
                      }}
                    />
                    <ListItemText primary={option.label} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Logic Verification Filter */}
          <Box mb={2}>
            <Typography
              variant="subtitle2"
              sx={{
                mb: 1,
                fontWeight: 'medium',
                color: darkMode ? '#D1D5DB' : 'inherit',
              }}
            >
              Logic Verification
            </Typography>
            <FormControl fullWidth size="small">
              <Select
                multiple
                value={filters.logicVerification}
                onChange={(e) => {
                  setFilters({ ...filters, logicVerification: e.target.value })
                }}
                renderValue={(selected) => {
                  return selected
                    .map(
                      (value) =>
                        logicVerOptions.find((option) => option.value === value)
                          ?.label
                    )
                    .join(', ')
                }}
                MenuProps={{
                  PaperProps: {
                    style: {
                      maxHeight: 224,
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                    },
                  },
                }}
                sx={{
                  backgroundColor: darkMode ? 'rgba(31, 41, 55, 0.5)' : 'white',
                  color: darkMode ? 'white' : 'inherit',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(75, 85, 99, 0.5)'
                      : 'rgba(209, 213, 219, 0.8)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.5)'
                      : 'rgba(59, 130, 246, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: darkMode
                      ? 'rgba(147, 197, 253, 0.8)'
                      : 'rgba(59, 130, 246, 0.8)',
                  },
                }}
              >
                {logicVerOptions.map((option) => (
                  <MenuItem
                    key={option.value}
                    value={option.value}
                    sx={{
                      backgroundColor: darkMode ? '#1F2937' : 'white',
                      color: darkMode ? 'white' : 'inherit',
                      '&.Mui-selected': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.2)'
                          : 'rgba(37, 99, 235, 0.1)',
                      },
                      '&.Mui-selected:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(37, 99, 235, 0.3)'
                          : 'rgba(37, 99, 235, 0.2)',
                      },
                      '&:hover': {
                        backgroundColor: darkMode
                          ? 'rgba(55, 65, 81, 0.7)'
                          : 'rgba(249, 250, 251, 0.9)',
                      },
                    }}
                  >
                    <Checkbox
                      checked={
                        filters.logicVerification.indexOf(option.value) > -1
                      }
                      sx={{
                        color: darkMode
                          ? 'rgba(156, 163, 175, 0.8)'
                          : 'rgba(107, 114, 128, 0.8)',
                        '&.Mui-checked': {
                          color:
                            option.value === 'Y'
                              ? darkMode
                                ? 'rgb(96, 165, 250)'
                                : 'rgb(37, 99, 235)'
                              : darkMode
                              ? 'rgb(251, 191, 36)'
                              : 'rgb(217, 119, 6)',
                        },
                        padding: '4px',
                      }}
                    />
                    <ListItemText primary={option.label} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Filter actions */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={clearFilters}
              sx={{
                textTransform: 'none',
                color: darkMode ? 'rgb(156, 163, 175)' : 'inherit',
                borderColor: darkMode
                  ? 'rgba(75, 85, 99, 0.5)'
                  : 'rgba(209, 213, 219, 0.8)',
                borderRadius: '6px',
                '&:hover': {
                  backgroundColor: darkMode
                    ? 'rgba(75, 85, 99, 0.1)'
                    : 'rgba(249, 250, 251, 0.8)',
                  borderColor: darkMode
                    ? 'rgba(107, 114, 128, 0.8)'
                    : 'rgba(209, 213, 219, 1)',
                },
              }}
            >
              Clear All
            </Button>
            <Button
              variant="contained"
              size="small"
              onClick={applyFilters}
              sx={{
                textTransform: 'none',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, #2563EB, #3B82F6)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #1D4ED8, #2563EB)',
                },
              }}
            >
              Apply Filters
            </Button>
          </Box>
        </Box>
      </Menu>
    </motion.div>
  )
}

export default ReferenceTable
