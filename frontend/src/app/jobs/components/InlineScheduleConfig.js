import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Chip, 
  Tooltip, 
  CircularProgress,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  Schedule as ScheduleIcon,
  DateRange as DateRangeIcon,
  Save as SaveIcon,
  Update as UpdateIcon,
  Cached as CachedIcon
} from '@mui/icons-material';
import TimeParameterModal from './TimeParameterModal';
import DateRangeModal from './DateRangeModal';

/**
 * InlineScheduleConfig component for configuring job schedules
 */
const InlineScheduleConfig = ({
  jobId,
  scheduleData = {},
  handleScheduleChange,
  handleSaveSchedule,
  darkMode,
  scheduleSaving
}) => {
  const [openTimeParam, setOpenTimeParam] = useState(false);
  const [openDateRange, setOpenDateRange] = useState(false);
  
  // Handling modal open/close
  const handleOpenTimeParam = () => setOpenTimeParam(true);
  const handleCloseTimeParam = () => setOpenTimeParam(false);
  const handleOpenDateRange = () => setOpenDateRange(true);
  const handleCloseDateRange = () => setOpenDateRange(false);
  
  // Current job schedule data
  const jobSchedule = scheduleData[jobId] || {};
  
  // Determine if schedule is complete
  const canSaveSchedule = 
    jobSchedule.TIMEPARAM && 
    jobSchedule.STRT_DT;
  
  const isUpdate = Boolean(jobSchedule.JOB_SCHEDULE_STATUS === 'Scheduled');
  
  // Get the frequency code for display
  const getFrequencyDisplay = () => {
    if (!jobSchedule.TIMEPARAM) return '';
    
    const matches = jobSchedule.TIMEPARAM.match(/^([A-Z]+)/);
    return matches ? matches[0] : '';
  };
  
  // Map frequency code to display name
  const getFrequencyLabel = (code) => {
    if (!code) return '';
    
    const frequencyLabels = {
      'DL': 'Daily',
      'WK': 'Weekly',
      'FN': 'Fortnightly',
      'MN': 'Monthly',
      'HY': 'Half-yearly',
      'YR': 'Yearly',
      'ID': 'Intraday'
    };
    
    return frequencyLabels[code] || code;
  };
  
  // Handle frequency change
  const handleFrequencyChange = (event) => {
    const newFreq = event.target.value;
    
    // Build updated TIMEPARAM
    let newTimeParam = newFreq;
    
    // If we have an existing time parameter and it has time info,
    // preserve that when changing frequency
    if (jobSchedule.TIMEPARAM) {
      const parts = jobSchedule.TIMEPARAM.split('_');
      
      // Default day info based on new frequency
      let dayInfo = '';
      if (['WK', 'FN'].includes(newFreq)) {
        dayInfo = 'MON'; // Default to Monday for weekly/fortnightly
      } else if (['MN', 'HY', 'YR'].includes(newFreq)) {
        dayInfo = '01'; // Default to 1st day for monthly/half-yearly/yearly
      }
      
      // Add day info for frequencies that need it
      if (['WK', 'MN', 'FN', 'HY', 'YR'].includes(newFreq)) {
        newTimeParam += `_${dayInfo}`;
      }
      
      // Add time info if we have it
      const timeIndex = ['WK', 'MN', 'FN', 'HY', 'YR'].includes(parts[0]) ? 2 : 1;
      if (parts.length > timeIndex) {
        newTimeParam += `_${parts[timeIndex]}`;
      } else {
        // Default time
        newTimeParam += '_00:00';
      }
    } else {
      // Default time param with default values
      if (['WK', 'MN', 'FN', 'HY', 'YR'].includes(newFreq)) {
        newTimeParam += '_01_00:00'; // Default day and time
      } else {
        newTimeParam += '_00:00'; // Default time only
      }
    }
    
    handleScheduleChange(jobId, 'TIMEPARAM', newTimeParam);
  };
  
  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center',
      gap: 1,
      width: '100%'
    }}>
      {/* Frequency Selector */}
      <FormControl 
        variant="outlined" 
        size="small"
        sx={{ 
          minWidth: 100
        }}
      >
        <Select
          value={getFrequencyDisplay()}
          onChange={handleFrequencyChange}
          displayEmpty
          sx={{
            fontSize: '0.75rem',
            height: '32px',
            backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(255, 255, 255, 0.9)',
            '& .MuiSelect-select': {
              paddingTop: '4px',
              paddingBottom: '4px',
            }
          }}
        >
          <MenuItem value="">
            <em>Frequency</em>
          </MenuItem>
          <MenuItem value="DL">DL</MenuItem>
          <MenuItem value="WK">WK</MenuItem>
          <MenuItem value="FN">FN</MenuItem>
          <MenuItem value="MN">MN</MenuItem>
          <MenuItem value="HY">HY</MenuItem>
          <MenuItem value="YR">YR</MenuItem>
          <MenuItem value="ID">ID</MenuItem>
        </Select>
      </FormControl>
      
      {/* Time Parameter Button */}
      <Button
        onClick={handleOpenTimeParam}
        startIcon={<ScheduleIcon sx={{ fontSize: 16 }} />}
        variant="outlined"
        size="small"
        sx={{
          textTransform: 'none',
          fontSize: '0.75rem',
          height: '32px',
          py: 0.5,
          px: 1,
          backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(255, 255, 255, 0.9)',
          borderColor: jobSchedule.TIMEPARAM ? 
            (darkMode ? 'rgba(59, 130, 246, 0.5)' : 'rgba(59, 130, 246, 0.5)') : 
            (darkMode ? 'rgba(75, 85, 99, 0.4)' : 'rgba(209, 213, 219, 0.8)'),
          color: jobSchedule.TIMEPARAM ? 
            (darkMode ? 'rgba(59, 130, 246, 0.9)' : 'rgba(59, 130, 246, 0.9)') : 
            (darkMode ? 'rgba(156, 163, 175, 0.9)' : 'rgba(107, 114, 128, 0.8)'),
          minWidth: 0,
          flex: '0 0 auto'
        }}
      >
        Time
      </Button>
      
      {/* Date Range Button */}
      <Button
        onClick={handleOpenDateRange}
        startIcon={<DateRangeIcon sx={{ fontSize: 16 }} />}
        variant="outlined"
        size="small"
        sx={{
          textTransform: 'none',
          fontSize: '0.75rem',
          height: '32px',
          py: 0.5,
          px: 1,
          backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(255, 255, 255, 0.9)',
          borderColor: jobSchedule.STRT_DT ? 
            (darkMode ? 'rgba(59, 130, 246, 0.5)' : 'rgba(59, 130, 246, 0.5)') : 
            (darkMode ? 'rgba(75, 85, 99, 0.4)' : 'rgba(209, 213, 219, 0.8)'),
          color: jobSchedule.STRT_DT ? 
            (darkMode ? 'rgba(59, 130, 246, 0.9)' : 'rgba(59, 130, 246, 0.9)') : 
            (darkMode ? 'rgba(156, 163, 175, 0.9)' : 'rgba(107, 114, 128, 0.8)'),
          minWidth: 0,
          flex: '0 0 auto'
        }}
      >
        Date
      </Button>
      
      {/* Save/Update Button - Moved next to Date */}
      <Tooltip title={isUpdate ? "Update Schedule" : "Save Schedule"}>
        <span>
          <IconButton
            onClick={() => handleSaveSchedule(jobId)}
            disabled={!canSaveSchedule || scheduleSaving?.[jobId]}
            color="primary"
            size="small"
            sx={{
              fontSize: '0.75rem',
              width: '32px',
              height: '32px',
              borderRadius: '4px',
              border: '1px solid',
              borderColor: darkMode ? 'rgba(59, 130, 246, 0.5)' : 'rgba(59, 130, 246, 0.3)',
              backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.05)',
              '&:hover': {
                backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.1)'
              },
              '&.Mui-disabled': {
                opacity: 0.4
              }
            }}
          >
            {scheduleSaving?.[jobId] ? (
              <CircularProgress size={14} color="inherit" />
            ) : isUpdate ? (
              <UpdateIcon fontSize="small" />
            ) : (
              <SaveIcon fontSize="small" />
            )}
          </IconButton>
        </span>
      </Tooltip>
      
      {/* Modals */}
      <TimeParameterModal
        open={openTimeParam}
        handleClose={handleCloseTimeParam}
        jobId={jobId}
        scheduleData={scheduleData}
        handleScheduleChange={handleScheduleChange}
        darkMode={darkMode}
      />
      
      <DateRangeModal
        open={openDateRange}
        handleClose={handleCloseDateRange}
        jobId={jobId}
        scheduleData={scheduleData}
        handleScheduleChange={handleScheduleChange}
        darkMode={darkMode}
      />
    </Box>
  );
};

export default InlineScheduleConfig; 