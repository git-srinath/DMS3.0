import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  IconButton,
  Grid,
  Alert
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { format } from 'date-fns';

/**
 * DateRangeModal component for setting job start and end dates
 */
const DateRangeModal = ({
  open,
  handleClose,
  jobId,
  scheduleData,
  handleScheduleChange,
  darkMode
}) => {
  // Local state for date values
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [errors, setErrors] = useState({});

  // Get the job schedule data
  const jobSchedule = scheduleData[jobId] || {};

  // Initialize local state when modal opens
  useEffect(() => {
    if (open && jobId) {
      // Set start and end dates from existing data
      setStartDate(jobSchedule.STRT_DT ? new Date(jobSchedule.STRT_DT) : null);
      setEndDate(jobSchedule.END_DT ? new Date(jobSchedule.END_DT) : null);
      setErrors({});
    }
  }, [open, jobId, jobSchedule.STRT_DT, jobSchedule.END_DT]);

  // Validate dates
  const validateDates = () => {
    const newErrors = {};
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Set to beginning of the day for proper comparison

    if (!startDate) {
      newErrors.startDate = 'Start date is required';
    } else if (startDate < today) {
      newErrors.startDate = 'Start date cannot be in the past';
    }

    // End date is optional but if provided, must be after start date
    if (startDate && endDate && endDate < startDate) {
      newErrors.endDate = 'End date must be after start date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save button click
  const handleSave = () => {
    if (validateDates()) {
      // Format dates for storage
      const formattedStartDate = startDate ? format(startDate, 'yyyy-MM-dd') : null;
      const formattedEndDate = endDate ? format(endDate, 'yyyy-MM-dd') : null;
      
      // Update parent component
      handleScheduleChange(jobId, 'STRT_DT', formattedStartDate);
      handleScheduleChange(jobId, 'END_DT', formattedEndDate);
      handleClose();
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Dialog 
        open={open} 
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: darkMode ? '#1A202C' : '#FFFFFF',
            backgroundImage: darkMode ? 
              'linear-gradient(rgba(17, 24, 39, 0.8), rgba(30, 41, 59, 0.9))' : 
              'none',
            boxShadow: darkMode ? 
              '0 10px 25px -5px rgba(0, 0, 0, 0.3)' : 
              '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
            borderRadius: 2
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: '1px solid',
          borderColor: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          py: 1.5,
          px: 2.5
        }}>
          <Typography variant="h6" sx={{ fontWeight: 500, color: darkMode ? 'white' : 'inherit' }}>
            Set Date Range
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleClose}
            aria-label="close"
            size="small"
            sx={{ color: darkMode ? 'gray.400' : 'gray.500' }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <DialogContent sx={{ py: 2.5, px: 2.5 }}>
          <Grid container spacing={3}>
            {/* Start Date */}
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 1 }}>
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    mb: 1,
                    color: darkMode ? 'rgba(156, 163, 175, 0.9)' : 'rgba(75, 85, 99, 0.9)',
                  }}
                >
                  Start Date
                </Typography>
                <DatePicker 
                  value={startDate}
                  onChange={(newDate) => setStartDate(newDate)}
                  minDate={new Date()} // Setting minimum date to today
                  slotProps={{
                    textField: {
                      size: "small",
                      fullWidth: true,
                      error: !!errors.startDate,
                      helperText: errors.startDate,
                      sx: {
                        '& .MuiInputBase-root': {
                          backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.6)' : 'white',
                          borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : undefined
                        }
                      }
                    }
                  }}
                />
              </Box>
            </Grid>

            {/* End Date */}
            <Grid item xs={12} md={6}>
              <Box>
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    mb: 1,
                    color: darkMode ? 'rgba(156, 163, 175, 0.9)' : 'rgba(75, 85, 99, 0.9)',
                  }}
                >
                  End Date (Optional)
                </Typography>
                <DatePicker 
                  value={endDate}
                  onChange={(newDate) => setEndDate(newDate)}
                  minDate={startDate || new Date()} // Ensure end date isn't before start date
                  slotProps={{
                    textField: {
                      size: "small",
                      fullWidth: true,
                      error: !!errors.endDate,
                      helperText: errors.endDate,
                      sx: {
                        '& .MuiInputBase-root': {
                          backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.6)' : 'white',
                          borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : undefined
                        }
                      }
                    }
                  }}
                />
              </Box>
            </Grid>

            {/* Preview Box */}
            <Grid item xs={12}>
              <Box 
                sx={{ 
                  mt: 2, 
                  p: 1.5, 
                  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.5)' : 'rgba(243, 244, 246, 0.7)',
                  borderRadius: 1,
                  border: '1px solid',
                  borderColor: darkMode ? 'rgba(55, 65, 81, 0.5)' : 'rgba(209, 213, 219, 0.7)',
                }}
              >
                <Typography 
                  variant="subtitle2" 
                  sx={{ 
                    mb: 0.5, 
                    color: darkMode ? 'rgba(156, 163, 175, 0.9)' : 'rgba(75, 85, 99, 0.9)',
                    fontSize: '0.75rem'
                  }}
                >
                  Date Range Preview:
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontFamily: 'monospace', 
                    fontSize: '0.875rem',
                    color: darkMode ? 'white' : 'text.primary'
                  }}
                >
                  {startDate ? (
                    <>
                      {format(startDate, 'yyyy-MM-dd')}
                      {endDate ? ` to ${format(endDate, 'yyyy-MM-dd')}` : ''}
                    </>
                  ) : (
                    <span style={{ color: darkMode ? 'rgba(156, 163, 175, 0.7)' : 'rgba(107, 114, 128, 0.7)' }}>
                      No dates selected
                    </span>
                  )}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        
        <DialogActions sx={{ 
          borderTop: '1px solid',
          borderColor: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          px: 2.5,
          py: 1.5
        }}>
          <Button 
            onClick={handleClose}
            variant="outlined"
            size="small"
            sx={{ 
              borderRadius: '6px',
              textTransform: 'none', 
              mr: 1 
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSave}
            variant="contained"
            color="primary"
            size="small"
            sx={{ 
              borderRadius: '6px',
              textTransform: 'none' 
            }}
          >
            Apply
          </Button>
        </DialogActions>
      </Dialog>
    </LocalizationProvider>
  );
};

export default DateRangeModal; 