import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  IconButton,
  TextField,
  Grid,
  Button,
  Paper,
  InputAdornment,
  CircularProgress,
  Chip,
  Collapse,
  Fade,
  useMediaQuery,
  DialogActions
} from '@mui/material';
import { styled, alpha, useTheme as useMuiTheme } from '@mui/material/styles';
import {
  Close as CloseIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  CalendarMonth as CalendarIcon,
  Info as InfoIcon,
  FilterAlt as FilterIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { motion, AnimatePresence } from 'framer-motion';
import LogDetailsTable from './LogDetailsTable';

const FilterPaper = styled(Paper)(({ theme, darkMode }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  backgroundColor: darkMode ? alpha('#1A202C', 0.7) : '#FFFFFF',
  boxShadow: darkMode ? '0 4px 6px rgba(0, 0, 0, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.1)',
  borderRadius: '8px',
  backdropFilter: 'blur(8px)',
  transition: 'all 0.3s ease',
}));

const StyledDialog = styled(Dialog)(({ theme, darkMode }) => ({
  '& .MuiDialog-paper': {
    backgroundColor: darkMode ? '#1A202C' : '#FFFFFF',
    backgroundImage: 'none',
    boxShadow: darkMode ? '0 4px 20px rgba(0, 0, 0, 0.5)' : '0 4px 20px rgba(0, 0, 0, 0.15)',
    borderRadius: '12px',
    overflow: 'hidden',
    minHeight: '50vh'
  },
  '& .MuiDialogTitle-root': {
    padding: theme.spacing(2),
    borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)'
  },
  '& .MuiDialogContent-root': {
    padding: theme.spacing(3)
  }
}));

const FilterToggleButton = styled(Button)(({ theme, darkMode, isActive }) => ({
  backgroundColor: isActive 
    ? (darkMode ? alpha(theme.palette.primary.main, 0.3) : alpha(theme.palette.primary.main, 0.1))
    : 'transparent',
  color: isActive
    ? (darkMode ? theme.palette.primary.light : theme.palette.primary.main)
    : (darkMode ? alpha(theme.palette.common.white, 0.7) : alpha(theme.palette.common.black, 0.6)),
  '&:hover': {
    backgroundColor: isActive 
      ? (darkMode ? alpha(theme.palette.primary.main, 0.4) : alpha(theme.palette.primary.main, 0.15))
      : (darkMode ? alpha(theme.palette.common.white, 0.05) : alpha(theme.palette.common.black, 0.05))
  },
  borderRadius: '20px',
  paddingLeft: theme.spacing(2),
  paddingRight: theme.spacing(2),
  transition: 'all 0.2s ease',
  textTransform: 'none',
  fontWeight: 500,
  border: isActive 
    ? `1px solid ${darkMode ? theme.palette.primary.dark : theme.palette.primary.light}`
    : `1px solid ${darkMode ? alpha(theme.palette.common.white, 0.1) : alpha(theme.palette.common.black, 0.1)}`
}));

const ActionButton = styled(Button)(({ theme, darkMode }) => ({
  color: darkMode ? theme.palette.primary.light : theme.palette.primary.main,
  backgroundColor: darkMode ? alpha(theme.palette.primary.main, 0.1) : alpha(theme.palette.primary.main, 0.05),
  '&:hover': {
    backgroundColor: darkMode ? alpha(theme.palette.primary.main, 0.2) : alpha(theme.palette.primary.main, 0.1),
  },
  borderRadius: '20px',
  textTransform: 'none',
  fontWeight: 500,
  boxShadow: 'none',
  transition: 'all 0.2s ease',
}));

const FilterChip = styled(Chip)(({ theme, darkMode }) => ({
  borderRadius: '16px',
  backgroundColor: darkMode ? alpha(theme.palette.primary.main, 0.2) : alpha(theme.palette.primary.main, 0.1),
  color: darkMode ? theme.palette.primary.light : theme.palette.primary.main,
  fontWeight: 500,
  '& .MuiChip-deleteIcon': {
    color: darkMode ? alpha(theme.palette.primary.light, 0.7) : alpha(theme.palette.primary.main, 0.7),
    '&:hover': {
      color: darkMode ? theme.palette.primary.light : theme.palette.primary.main,
    }
  },
  transition: 'all 0.2s ease',
  border: `1px solid ${darkMode ? alpha(theme.palette.primary.main, 0.3) : alpha(theme.palette.primary.main, 0.2)}`,
  '&:hover': {
    backgroundColor: darkMode ? alpha(theme.palette.primary.main, 0.3) : alpha(theme.palette.primary.main, 0.15),
  }
}));

const EmptyStateContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(6),
  textAlign: 'center',
  minHeight: '300px'
}));

const LogDetailsDialog = ({
  open,
  onClose,
  mapReference,
  logDetails,
  loading,
  darkMode,
  onViewErrors
}) => {
  const muiTheme = useMuiTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('sm'));
  
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [filteredLogDetails, setFilteredLogDetails] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [activeFilters, setActiveFilters] = useState(0);

  // Reset filters when dialog is opened with new data
  useEffect(() => {
    if (open) {
      // Reset filters when dialog opens
      if (!searchTerm && !startDate && !endDate) {
        setFilteredLogDetails(Array.isArray(logDetails) ? logDetails : []);
      }
    }
  }, [open, logDetails]);

  // Update filtered logs when source data or filters change
  useEffect(() => {
    filterLogDetails();
    
    // Count active filters
    let count = 0;
    if (searchTerm) count++;
    if (startDate) count++;
    if (endDate) count++;
    setActiveFilters(count);
  }, [logDetails, searchTerm, startDate, endDate]);

  // Filter log details based on search term and date range
  const filterLogDetails = () => {
    // Make sure logDetails is an array
    if (!Array.isArray(logDetails) || logDetails.length === 0) {
      setFilteredLogDetails([]);
      return;
    }

    let filtered = [...logDetails];
    
    // Filter by search term
    if (searchTerm) {
      const lowerSearchTerm = searchTerm.toLowerCase();
      filtered = filtered.filter(log => {
        if (!log) return false;
        
        return (
          (log.jobName?.toString() || '').toLowerCase().includes(lowerSearchTerm) ||
          (log.logId?.toString() || '').toLowerCase().includes(lowerSearchTerm) ||
          (log.status?.toString() || '').toLowerCase().includes(lowerSearchTerm) ||
          (log.sessionId?.toString() || '').toLowerCase().includes(lowerSearchTerm)
        );
      });
    }
    
    // Filter by date range
    if (startDate) {
      const startDateObj = new Date(startDate);
      startDateObj.setHours(0, 0, 0, 0); // Start of day
      
      filtered = filtered.filter(log => {
        if (!log || !log.logDate) return false;
        
        try {
          const logDateObj = new Date(log.logDate);
          return logDateObj >= startDateObj;
        } catch (error) {
          console.error('Error parsing log date', error);
          return false;
        }
      });
    }
    
    if (endDate) {
      const endDateObj = new Date(endDate);
      // Set time to end of day
      endDateObj.setHours(23, 59, 59, 999);
      
      filtered = filtered.filter(log => {
        if (!log || !log.logDate) return false;
        
        try {
          const logDateObj = new Date(log.logDate);
          return logDateObj <= endDateObj;
        } catch (error) {
          console.error('Error parsing log date', error);
          return false;
        }
      });
    }
    
    setFilteredLogDetails(filtered);
  };

  // Function to handle search term change
  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  // Function to reset filters
  const resetFilters = () => {
    setStartDate(null);
    setEndDate(null);
    setSearchTerm('');
  };

  // Function to toggle filters visibility
  const toggleFilters = () => {
    setShowFilters(prev => !prev);
  };

  // Function to format date for display
  const formatDate = (date) => {
    if (!date) return '';
    try {
      return new Date(date).toLocaleDateString();
    } catch (error) {
      return '';
    }
  };

  return (
    <StyledDialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      darkMode={darkMode}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6" component="span" fontWeight={600}>
            Job Logs for {mapReference || 'Unknown Job'}
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={onClose}
            aria-label="close"
            sx={{ 
              transition: 'transform 0.2s ease',
              '&:hover': { transform: 'rotate(90deg)' }
            }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {/* Filter Controls */}
        <Box mb={2} display="flex" flexWrap="wrap" alignItems="center" gap={1}>
          <TextField
            variant="outlined"
            placeholder="Search logs..."
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ 
              flexGrow: 1, 
              minWidth: { xs: '100%', sm: '200px' }, 
              maxWidth: { sm: '300px' }
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: searchTerm ? (
                <InputAdornment position="end">
                  <IconButton 
                    size="small" 
                    onClick={() => setSearchTerm('')}
                    edge="end"
                  >
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ) : null,
              sx: { 
                borderRadius: '20px',
                backgroundColor: darkMode ? alpha('#FFFFFF', 0.05) : alpha('#000000', 0.03),
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: darkMode ? alpha('#FFFFFF', 0.1) : alpha('#000000', 0.05),
                }
              }
            }}
          />
          
          <FilterToggleButton 
            startIcon={<FilterIcon />}
            size="small"
            onClick={toggleFilters}
            darkMode={darkMode}
            isActive={showFilters || activeFilters > 0}
          >
            {isMobile ? `Filters${activeFilters ? ` (${activeFilters})` : ''}` : 'Filter by Date'}
            {!isMobile && activeFilters > 0 && (
              <Box 
                component="span"
                sx={{ 
                  ml: 1, 
                  height: 18, 
                  width: 18, 
                  borderRadius: '50%', 
                  bgcolor: 'primary.main',
                  color: 'white',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem'
                }}
              >
                {activeFilters}
              </Box>
            )}
          </FilterToggleButton>
          
          {(startDate || endDate) && (
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2 }}
              >
                <Box display="flex" gap={1} flexWrap="wrap">
                  {startDate && (
                    <FilterChip 
                      label={`From: ${formatDate(startDate)}`}
                      darkMode={darkMode}
                      onDelete={() => setStartDate(null)}
                      size="small"
                    />
                  )}
                  {endDate && (
                    <FilterChip 
                      label={`To: ${formatDate(endDate)}`}
                      darkMode={darkMode}
                      onDelete={() => setEndDate(null)}
                      size="small"
                    />
                  )}
                </Box>
              </motion.div>
            </AnimatePresence>
          )}
          
          {activeFilters > 0 && (
            <Button 
              size="small" 
              onClick={resetFilters}
              sx={{ 
                color: darkMode ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)',
                textTransform: 'none',
                ml: 'auto'
              }}
            >
              Clear all
            </Button>
          )}
        </Box>
        
        {/* Date Filters */}
        <Collapse in={showFilters}>
          <FilterPaper darkMode={darkMode}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={5}>
                  <DatePicker
                    label="Start Date"
                    value={startDate}
                    onChange={(newValue) => setStartDate(newValue)}
                    slotProps={{ 
                      textField: { 
                        size: "small",
                        fullWidth: true,
                        InputProps: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <CalendarIcon fontSize="small" />
                            </InputAdornment>
                          ),
                        }
                      } 
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={5}>
                  <DatePicker
                    label="End Date"
                    value={endDate}
                    onChange={(newValue) => setEndDate(newValue)}
                    slotProps={{ 
                      textField: { 
                        size: "small",
                        fullWidth: true,
                        InputProps: {
                          startAdornment: (
                            <InputAdornment position="start">
                              <CalendarIcon fontSize="small" />
                            </InputAdornment>
                          ),
                        }
                      } 
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={2}>
                  <ActionButton
                    fullWidth
                    onClick={resetFilters}
                    darkMode={darkMode}
                    size="small"
                    variant="contained"
                  >
                    Reset
                  </ActionButton>
                </Grid>
              </Grid>
            </LocalizationProvider>
          </FilterPaper>
        </Collapse>
        
        {/* Log Details Table */}
        {loading ? (
          <EmptyStateContainer>
            <CircularProgress size={40} sx={{ mb: 2 }} />
            <Typography variant="subtitle1" color="text.secondary">
              Loading log details...
            </Typography>
          </EmptyStateContainer>
        ) : !Array.isArray(filteredLogDetails) || filteredLogDetails.length === 0 ? (
          <EmptyStateContainer>
            <InfoIcon sx={{ fontSize: 64, color: 'text.secondary', opacity: 0.5, mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No log data found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: '400px' }}>
              {startDate || endDate || searchTerm ? 
                "No logs match your current filters. Try adjusting or clearing your filters to see more results." : 
                "There are no logs available for this job yet. Logs will appear here after the job has been executed."
              }
            </Typography>
            {(startDate || endDate || searchTerm) && (
              <Button
                variant="outlined"
                color="primary"
                sx={{ mt: 2 }}
                onClick={resetFilters}
              >
                Clear Filters
              </Button>
            )}
          </EmptyStateContainer>
        ) : (
          <LogDetailsTable 
            logDetails={filteredLogDetails}
            darkMode={darkMode}
            onViewErrors={onViewErrors}
          />
        )}
      </DialogContent>
      
      <DialogActions sx={{ p: 2 }}>
        <Button 
          onClick={onClose} 
          variant="outlined" 
          color="primary"
        >
          Close
        </Button>
      </DialogActions>
    </StyledDialog>
  );
};

export default LogDetailsDialog; 