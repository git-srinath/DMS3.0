import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  IconButton,
  Grid
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

/**
 * TimeParameterModal component for setting job day and time parameters
 */
const TimeParameterModal = ({
  open,
  handleClose,
  jobId,
  scheduleData,
  handleScheduleChange,
  darkMode
}) => {
  // Local state for form values
  const [localDay, setLocalDay] = useState('');
  const [localHour, setLocalHour] = useState('');
  const [localMinute, setLocalMinute] = useState('');
  const [errors, setErrors] = useState({});

  // Get the job schedule data
  const jobSchedule = scheduleData[jobId] || {};
  
  // Get current frequency code
  const getFrequencyCode = () => {
    if (!jobSchedule.TIMEPARAM) return '';
    const parts = jobSchedule.TIMEPARAM.split('_');
    return parts[0] || '';
  };
  
  // Initialize local state when modal opens
  useEffect(() => {
    if (open && jobId) {
      // Parse existing TIMEPARAM if available
      if (jobSchedule.TIMEPARAM) {
        try {
          const parts = jobSchedule.TIMEPARAM.split('_');
          const frequencyCode = parts[0] || '';
          
          // For day-based frequencies
          if (['WK', 'MN', 'FN', 'HY', 'YR'].includes(frequencyCode)) {
            setLocalDay(parts[1] || '');
            
            // Set hour and minute
            if (parts.length > 2) {
              const timeParts = parts[2].split(':');
              setLocalHour(timeParts[0] || '00');
              setLocalMinute(timeParts[1] || '00');
            } else {
              setLocalHour('00');
              setLocalMinute('00');
            }
          } else {
            // For frequencies without day component
            setLocalDay('');
            
            // Set hour and minute
            if (parts.length > 1) {
              const timeParts = parts[1].split(':');
              setLocalHour(timeParts[0] || '00');
              setLocalMinute(timeParts[1] || '00');
            } else {
              setLocalHour('00');
              setLocalMinute('00');
            }
          }
        } catch (error) {
          console.error('Error parsing TIMEPARAM', error);
          setLocalHour('00');
          setLocalMinute('00');
        }
      } else {
        // Default values
        setLocalDay('MON'); // Default day
        setLocalHour('00');
        setLocalMinute('00');
      }
      
      setErrors({});
    }
  }, [open, jobId, jobSchedule.TIMEPARAM]);

  // Get current frequency code
  const frequencyCode = getFrequencyCode();
  
  // Check if day selection is needed
  const isDaySelectionNeeded = ['WK', 'MN', 'FN', 'HY', 'YR'].includes(frequencyCode);
  
  // Day options based on frequency
  const getDayOptions = () => {
    if (['WK', 'FN'].includes(frequencyCode)) {
      // Weekdays for weekly/fortnightly
      return [
        { value: 'MON', label: 'MON' },
        { value: 'TUE', label: 'TUE' },
        { value: 'WED', label: 'WED' },
        { value: 'THU', label: 'THU' },
        { value: 'FRI', label: 'FRI' },
        { value: 'SAT', label: 'SAT' },
        { value: 'SUN', label: 'SUN' }
      ];
    } else if (['MN', 'HY', 'YR'].includes(frequencyCode)) {
      // Calendar days for monthly/half-yearly/yearly
      return Array.from({ length: 31 }, (_, i) => ({
        value: String(i + 1).padStart(2, '0'),
        label: String(i + 1)
      }));
    }
    return [];
  };

  // Hour options (0-23)
  const hourOptions = Array.from({ length: 24 }, (_, i) => ({
    value: String(i).padStart(2, '0'),
    label: String(i).padStart(2, '0')
  }));

  // Minute options (0-59)
  const minuteOptions = Array.from({ length: 60 }, (_, i) => ({
    value: String(i).padStart(2, '0'),
    label: String(i).padStart(2, '0')
  }));

  // Validate form
  const validateForm = () => {
    const newErrors = {};

    if (isDaySelectionNeeded && !localDay) {
      newErrors.day = 'Day is required for this frequency';
    }

    if (!localHour) {
      newErrors.hour = 'Hour is required';
    }

    if (!localMinute) {
      newErrors.minute = 'Minute is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save button click
  const handleSave = () => {
    if (validateForm()) {
      // Get current parts
      const currentParts = jobSchedule.TIMEPARAM ? 
        jobSchedule.TIMEPARAM.split('_') : [frequencyCode];
      
      // Build TIMEPARAM string
      let timeParam = currentParts[0] || frequencyCode;
      
      if (isDaySelectionNeeded) {
        timeParam += `_${localDay}`;
      }
      
      timeParam += isDaySelectionNeeded ? 
        `_${localHour}:${localMinute}` : 
        `_${localHour}:${localMinute}`;
      
      // Update parent component
      handleScheduleChange(jobId, 'TIMEPARAM', timeParam);
      handleClose();
    }
  };

  return (
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
          Set Time Parameters
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
        <Grid container spacing={2}>
          {/* Day Selection (for applicable frequencies) */}
          {isDaySelectionNeeded && (
            <Grid item xs={12}>
              <FormControl 
                fullWidth 
                variant="outlined" 
                size="small"
                error={!!errors.day}
              >
                <InputLabel id="day-label">Day</InputLabel>
                <Select
                  labelId="day-label"
                  value={localDay}
                  onChange={(e) => setLocalDay(e.target.value)}
                  label="Day"
                >
                  {getDayOptions().map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
                {errors.day && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                    {errors.day}
                  </Typography>
                )}
              </FormControl>
            </Grid>
          )}

          {/* Time Selection */}
          <Grid item xs={12}>
            <Typography variant="subtitle2" sx={{ mb: 1, color: darkMode ? 'gray.300' : 'gray.700' }}>
              Time (24-hour format)
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <FormControl 
                variant="outlined" 
                size="small" 
                sx={{ flex: 1 }}
                error={!!errors.hour}
              >
                <InputLabel id="hour-label">Hour</InputLabel>
                <Select
                  labelId="hour-label"
                  value={localHour}
                  onChange={(e) => setLocalHour(e.target.value)}
                  label="Hour"
                >
                  {hourOptions.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <Typography variant="h6" sx={{ alignSelf: 'center', color: darkMode ? 'gray.300' : 'gray.700' }}>:</Typography>
              
              <FormControl 
                variant="outlined" 
                size="small" 
                sx={{ flex: 1 }}
                error={!!errors.minute}
              >
                <InputLabel id="minute-label">Minute</InputLabel>
                <Select
                  labelId="minute-label"
                  value={localMinute}
                  onChange={(e) => setLocalMinute(e.target.value)}
                  label="Minute"
                >
                  {minuteOptions.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            {errors.hour && (
              <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                {errors.hour}
              </Typography>
            )}
            {errors.minute && (
              <Typography variant="caption" color="error" sx={{ mt: 0.5, display: 'block' }}>
                {errors.minute}
              </Typography>
            )}
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions sx={{ 
        p: 2, 
        borderTop: '1px solid',
        borderColor: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
      }}>
        <Button 
          onClick={handleClose} 
          variant="outlined"
          size="small"
          sx={{ 
            color: darkMode ? 'gray.300' : 'gray.600',
            borderColor: darkMode ? 'gray.600' : 'gray.300',
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
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TimeParameterModal; 