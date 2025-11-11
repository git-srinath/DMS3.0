import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Button,
  FormControl,
  Select,
  MenuItem,
  TextField,
  InputLabel,
  Autocomplete,
  CircularProgress,
  Alert,
  Tooltip,
  Divider,
  Chip,
  Stack,
  Paper
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  CalendarMonth as CalendarIcon,
  Save as SaveIcon,
  Update as UpdateIcon,
  Link as LinkIcon,
  ErrorOutline as ErrorIcon,
  InfoOutlined as InfoIcon,
  DoneAll as DoneAllIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';

// Styled components
const CompactSelect = styled(Select)(({ theme, darkMode }) => ({
  '& .MuiSelect-select': {
    padding: '6px 8px',
    fontSize: '0.75rem',
  },
  backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
  borderRadius: '6px',
  minWidth: 90,
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: darkMode ? 'rgba(99, 102, 241, 0.5)' : 'rgba(99, 102, 241, 0.5)',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: '#3B82F6',
  }
}));

const CompactTextField = styled(TextField)(({ theme, darkMode }) => ({
  '& .MuiInputBase-input': {
    padding: '6px 8px',
    fontSize: '0.75rem'
  },
  '& .MuiOutlinedInput-root': {
    backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
    borderRadius: '6px',
    '&:hover .MuiOutlinedInput-notchedOutline': {
      borderColor: darkMode ? 'rgba(99, 102, 241, 0.5)' : 'rgba(99, 102, 241, 0.5)',
    },
    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
      borderColor: '#3B82F6',
    }
  }
}));

const CompactFormControl = styled(FormControl)(({ theme, darkMode }) => ({
  '& .MuiInputLabel-root': {
    fontSize: '0.75rem',
    transform: 'translate(8px, 8px) scale(1)'
  },
  '& .MuiInputLabel-shrink': {
    transform: 'translate(14px, -6px) scale(0.75)'
  },
  '& .MuiOutlinedInput-root': {
    backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
    borderRadius: '6px',
    '&:hover .MuiOutlinedInput-notchedOutline': {
      borderColor: darkMode ? 'rgba(99, 102, 241, 0.5)' : 'rgba(99, 102, 241, 0.5)',
    },
    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
      borderColor: '#3B82F6',
    }
  }
}));

const StyledChip = styled(Chip)(({ theme, darkMode, status }) => ({
  height: '22px',
  fontSize: '0.675rem',
  fontWeight: 600,
  borderRadius: '6px',
  padding: '0 2px',
  backgroundColor: status === 'Scheduled' 
    ? (darkMode ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.1)') 
    : (darkMode ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)'),
  color: status === 'Scheduled'
    ? (darkMode ? '#4ADE80' : '#22C55E')
    : (darkMode ? '#FBBF24' : '#D97706'),
  border: '1px solid',
  borderColor: status === 'Scheduled' 
    ? (darkMode ? 'rgba(34, 197, 94, 0.3)' : 'rgba(34, 197, 94, 0.2)') 
    : (darkMode ? 'rgba(245, 158, 11, 0.3)' : 'rgba(245, 158, 11, 0.2)'),
  '.MuiChip-label': {
    padding: '0 8px'
  }
}));

const CompactButton = styled(Button)(({ theme, darkMode }) => ({
  height: '32px',
  fontSize: '0.75rem',
  padding: '4px 12px',
  minWidth: 'unset',
  borderRadius: '6px',
  whiteSpace: 'nowrap',
  textTransform: 'none',
  fontWeight: 600,
  boxShadow: 'none',
  transition: 'all 0.2s ease',
  '&:hover': {
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
  },
  '&.Mui-disabled': {
    opacity: 0.6
  }
}));

const ConfigSection = styled(Box)(({ theme, darkMode }) => ({
  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(249, 250, 251, 0.6)',
  borderRadius: '8px',
  padding: '12px',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  backdropFilter: 'blur(4px)',
  transition: 'all 0.2s ease',
  marginBottom: '12px',
}));

const SectionTitle = styled(Typography)(({ theme, darkMode }) => ({
  fontSize: '0.875rem',
  fontWeight: 600,
  color: darkMode ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.9)',
  marginBottom: '8px',
  display: 'flex',
  alignItems: 'center',
  gap: '6px'
}));

const ScheduleConfiguration = ({ 
  jobId, 
  scheduleData, 
  handleScheduleChange, 
  handleDateChange, 
  handleSaveSchedule,
  handleSaveDependency,
  jobOptions,
  darkMode,
  scheduleLoading,
  scheduleSaving,
  dependencySaving
}) => {
  // State for validation errors
  const [errors, setErrors] = useState({});
  
  // For debugging
  console.log(`ScheduleConfiguration for job ${jobId}:`, {
    scheduleData: scheduleData[jobId],
    job: jobOptions.find(j => j.JOBFLWID === jobId)
  });

  // Frequency code options
  const frequencyCodes = [
    { value: 'ID', label: 'Intraday (ID)' },
    { value: 'DL', label: 'Daily (DL)' },
    { value: 'WK', label: 'Weekly (WK)' },
    { value: 'FN', label: 'Fortnightly (FN)' },
    { value: 'MN', label: 'Monthly (MN)' },
    { value: 'HY', label: 'Half-yearly (HY)' },
    { value: 'YR', label: 'Yearly (YR)' },
    // Handle possible value coming from database
    { value: 'WKL', label: 'Weekly (WKL)' },
  ];

  // Generate day options based on frequency
  const getDayOptions = (freqCode) => {
    if (freqCode === 'WK' || freqCode === 'FN') {
      return [
        { value: 'MON', label: 'Monday (MON)' },
        { value: 'TUE', label: 'Tuesday (TUE)' },
        { value: 'WED', label: 'Wednesday (WED)' },
        { value: 'THU', label: 'Thursday (THU)' },
        { value: 'FRI', label: 'Friday (FRI)' },
        { value: 'SAT', label: 'Saturday (SAT)' },
        { value: 'SUN', label: 'Sunday (SUN)' },
      ];
    } else {
      const days = [];
      for (let i = 1; i <= 31; i++) {
        days.push({ value: i.toString().padStart(2, '0'), label: i.toString().padStart(2, '0') });
      }
      return days;
    }
  };

  // Generate hour options
  const getHourOptions = (freqCode) => {
    const hours = [];
    
    for (let i = 0; i <= 23; i++) {
      hours.push({ value: i.toString().padStart(2, '0'), label: i.toString().padStart(2, '0') });
    }
    return hours;
  };

  // Generate minute options
  const getMinuteOptions = () => {
    const minutes = [];
    for (let i = 0; i <= 59; i++) {
      minutes.push({ value: i.toString().padStart(2, '0'), label: i.toString().padStart(2, '0') });
    }
    return minutes;
  };

  // Validate all required fields and conditions
  const validateForm = () => {
    const newErrors = {};
    const jobData = scheduleData[jobId];
    
    if (!jobData) return { hasErrors: true, errors: { general: 'Job data not found' } };
    
    // Validate mapping reference (should be already present, but checking anyway)
    if (!jobData.MAPREF) {
      newErrors.mapref = 'Mapping reference must be provided.';
    }
    
    // Validate frequency code
    const validFreqCodes = ['ID', 'DL', 'WK', 'FN', 'MN', 'HY', 'YR'];
    if (!jobData.FRQCD || !validFreqCodes.includes(jobData.FRQCD)) {
      newErrors.frqcd = 'Invalid frequency code (Valid: ID,DL,WK,FN,MN,HY,YR).';
    }
    
    // Validate frequency day based on frequency code
    if (jobData.FRQCD === 'WK' || jobData.FRQCD === 'FN') {
      const validWeekDays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
      if (!jobData.FRQDD || !validWeekDays.includes(jobData.FRQDD)) {
        newErrors.frqdd = 'For Weekly/Fortnightly frequency, day must be one of MON,TUE,WED,THU,FRI,SAT,SUN.';
      }
    } else if (['MN', 'HY', 'YR'].includes(jobData.FRQCD)) {
      // For monthly/half-yearly/yearly, freq day must be calendar day
      const day = parseInt(jobData.FRQDD, 10);
      if (isNaN(day) || day < 1 || day > 31) {
        newErrors.frqdd = 'Invalid frequency day (Valid: 1 .. 31).';
      }
    }
    
    // Validate hour (0-23)
    const hour = parseInt(jobData.FRQHH, 10);
    if (isNaN(hour) || hour < 0 || hour > 23) {
      newErrors.frqhh = 'Invalid frequency hour (valid: 0 .. 23).';
    }

    // Validate minute (0-59)
    const minute = parseInt(jobData.FRQMM, 10);
    if (isNaN(minute) || minute < 0 || minute > 59) {
      newErrors.frqmm = 'Invalid frequency minute (valid: 0 .. 59).';
    }
    
    // Validate start date (must be valid date)
    if (!jobData.DTSTART) {
      newErrors.dtstart = 'Start date must be provided.';
    }
    
    // Validate end date (must be valid date and greater than start date)
    if (jobData.DTEND && new Date(jobData.DTEND) <= new Date(jobData.DTSTART)) {
      newErrors.dtend = 'End date must be after start date.';
    }
    
    // Check for any errors
    const hasErrors = Object.keys(newErrors).length > 0;
    
    setErrors(newErrors);
    return { hasErrors, errors: newErrors };
  };

  // Function to check if frequency day is valid based on current frequency code selection
  const isFreqDayValid = () => {
    const jobData = scheduleData[jobId];
    if (!jobData) return false;
    
    const freqCode = jobData.FRQCD;
    const freqDay = jobData.FRQDD;
    
    if (!freqCode || !freqDay) return false;
    
    if (freqCode === 'WK' || freqCode === 'FN') {
      const validWeekDays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
      return validWeekDays.includes(freqDay);
    } else if (['MN', 'HY', 'YR'].includes(freqCode)) {
      const day = parseInt(freqDay, 10);
      return !isNaN(day) && day >= 1 && day <= 31;
    }
    
    return true; // For other frequency codes, day may not be applicable
  };

  // Handle saving dependency
  const handleSaveDependencyClick = () => {
    const jobData = scheduleData[jobId];
    
    // Only proceed if we have job data and valid dependency
    if (jobData && jobData.DPND_MAPREF) {
      // Find the job ID for the selected dependency
      const dependentJob = jobOptions.find(job => job.MAPREF === jobData.DPND_MAPREF);
      
      if (dependentJob) {
        // Call the provided save function
        handleSaveDependency(jobId, dependentJob.JOBSCHID);
      }
    }
  };

  return (
    <Box>
      {scheduleData[jobId] ? (
        <>
          <Stack spacing={2}>
            {/* Scheduling section */}
            <ConfigSection darkMode={darkMode}>
              <SectionTitle darkMode={darkMode}>
                <CalendarIcon fontSize="small" color={darkMode ? "primary" : "secondary"} /> 
                Schedule Configuration
              </SectionTitle>
              
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, 
                gap: 1.5,
                mb: 2 
              }}>
                <CompactFormControl size="small" darkMode={darkMode}>
                  <InputLabel>Frequency</InputLabel>
                  <CompactSelect
                    value={scheduleData[jobId]?.FRQCD || ''}
                    onChange={(e) => {
                      handleScheduleChange(jobId, 'FRQCD', e.target.value);
                      // Reset day value if frequency changes to ensure it's valid
                      if ((e.target.value === 'WK' || e.target.value === 'FN') && 
                          !(scheduleData[jobId]?.FRQDD?.match(/[A-Z]+/))) {
                        handleScheduleChange(jobId, 'FRQDD', 'MON');
                      } else if (['MN', 'HY', 'YR'].includes(e.target.value) && 
                                 scheduleData[jobId]?.FRQDD?.match(/[A-Z]+/)) {
                        handleScheduleChange(jobId, 'FRQDD', '01');
                      }
                    }}
                    error={!!errors.frqcd}
                    label="Frequency"
                    darkMode={darkMode}
                  >
                    {frequencyCodes.map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </CompactSelect>
                  {errors.frqcd && <Typography color="error" variant="caption">{errors.frqcd}</Typography>}
                </CompactFormControl>

                <CompactFormControl size="small" darkMode={darkMode}>
                  <InputLabel>Day</InputLabel>
                  <CompactSelect
                    value={scheduleData[jobId]?.FRQDD || ''}
                    onChange={(e) => handleScheduleChange(jobId, 'FRQDD', e.target.value)}
                    error={!!errors.frqdd}
                    label="Day"
                    darkMode={darkMode}
                  >
                    {getDayOptions(scheduleData[jobId]?.FRQCD).map(option => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </CompactSelect>
                  {errors.frqdd && <Typography color="error" variant="caption">{errors.frqdd}</Typography>}
                </CompactFormControl>

                <Box sx={{ display: 'flex', gap: 1 }}>
                  <CompactFormControl size="small" darkMode={darkMode} sx={{ width: '50%' }}>
                    <InputLabel>Hour</InputLabel>
                    <CompactSelect
                      value={scheduleData[jobId]?.FRQHH || ''}
                      onChange={(e) => handleScheduleChange(jobId, 'FRQHH', e.target.value)}
                      error={!!errors.frqhh}
                      label="Hour"
                      darkMode={darkMode}
                    >
                      {getHourOptions().map(option => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </CompactSelect>
                    {errors.frqhh && <Typography color="error" variant="caption">{errors.frqhh}</Typography>}
                  </CompactFormControl>

                  <CompactFormControl size="small" darkMode={darkMode} sx={{ width: '50%' }}>
                    <InputLabel>Minute</InputLabel>
                    <CompactSelect
                      value={scheduleData[jobId]?.FRQMM || ''}
                      onChange={(e) => handleScheduleChange(jobId, 'FRQMM', e.target.value)}
                      error={!!errors.frqmm}
                      label="Minute"
                      darkMode={darkMode}
                    >
                      {getMinuteOptions().map(option => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </CompactSelect>
                    {errors.frqmm && <Typography color="error" variant="caption">{errors.frqmm}</Typography>}
                  </CompactFormControl>
                </Box>
              </Box>
              
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
                gap: 1.5 
              }}>
                <Box>
                  <Typography variant="caption" sx={{ 
                    display: 'block', 
                    mb: 0.5, 
                    color: darkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
                    fontWeight: 500
                  }}>
                    Start Date
                  </Typography>
                  <DatePicker 
                    value={scheduleData[jobId]?.DTSTART ? new Date(scheduleData[jobId].DTSTART) : null}
                    onChange={(date) => handleDateChange(jobId, 'DTSTART', date)}
                    slotProps={{
                      textField: {
                        size: "small",
                        error: !!errors.dtstart,
                        helperText: errors.dtstart,
                        InputProps: {
                          sx: {
                            fontSize: '0.75rem',
                            backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                            borderRadius: '6px',
                          }
                        }
                      }
                    }}
                  />
                </Box>

                <Box>
                  <Typography variant="caption" sx={{ 
                    display: 'block', 
                    mb: 0.5, 
                    color: darkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
                    fontWeight: 500
                  }}>
                    End Date (Optional)
                  </Typography>
                  <DatePicker 
                    value={scheduleData[jobId]?.DTEND ? new Date(scheduleData[jobId].DTEND) : null}
                    onChange={(date) => handleDateChange(jobId, 'DTEND', date)}
                    slotProps={{
                      textField: {
                        size: "small",
                        error: !!errors.dtend,
                        helperText: errors.dtend,
                        InputProps: {
                          sx: {
                            fontSize: '0.75rem',
                            backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                            borderRadius: '6px',
                          }
                        }
                      }
                    }}
                  />
                </Box>
              </Box>
            </ConfigSection>
            
            {/* Dependency section */}
            <ConfigSection darkMode={darkMode}>
              <SectionTitle darkMode={darkMode}>
                <LinkIcon fontSize="small" color={darkMode ? "primary" : "secondary"} /> 
                Job Dependency
              </SectionTitle>
              
              <Box sx={{ mb: 1 }}>
                <CompactFormControl fullWidth size="small" darkMode={darkMode}>
                  <Autocomplete
                    size="small"
                    options={jobOptions.filter(job => job.JOBSCHID !== jobId)}
                    getOptionLabel={(option) => `${option.MAPREF} - ${option.TRGSCHM}.${option.TRGTBNM}`}
                    isOptionEqualToValue={(option, value) => option.MAPREF === value.MAPREF}
                    value={jobOptions.find(job => job.MAPREF === scheduleData[jobId]?.DPND_MAPREF) || null}
                    onChange={(event, newValue) => {
                      handleScheduleChange(jobId, 'DPND_MAPREF', newValue?.MAPREF || null);
                    }}
                    renderInput={(params) => (
                      <TextField 
                        {...params} 
                        label="Select Dependency" 
                        placeholder="No dependency"
                        sx={{
                          '& .MuiInputBase-root': {
                            fontSize: '0.75rem',
                            backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
                            borderRadius: '6px',
                          }
                        }}
                      />
                    )}
                    renderOption={(props, option) => (
                      <MenuItem {...props} sx={{ fontSize: '0.75rem' }}>
                        <Box sx={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'space-between', 
                          width: '100%' 
                        }}>
                          <Box>
                            <Typography variant="body2" component="span" sx={{ mr: 1, fontWeight: 500 }}>
                              {option.MAPREF}
                            </Typography>
                            {option.TRGSCHM}.{option.TRGTBNM}
                          </Box>
                          <StyledChip 
                            label={option.JOB_SCHEDULE_STATUS} 
                            size="small" 
                            status={option.JOB_SCHEDULE_STATUS} 
                            darkMode={darkMode}
                          />
                        </Box>
                      </MenuItem>
                    )}
                    noOptionsText="No matching jobs found"
                    loading={scheduleLoading[jobId]}
                    loadingText="Loading job options..."
                  />
                </CompactFormControl>
              </Box>
              
              {scheduleData[jobId]?.DPND_MAPREF && (
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
                  <CompactButton
                    variant="outlined"
                    color="primary"
                    onClick={handleSaveDependencyClick}
                    startIcon={dependencySaving ? <CircularProgress size={16} /> : <SaveIcon />}
                    disabled={dependencySaving}
                    darkMode={darkMode}
                    size="small"
                  >
                    Save Dependency
                  </CompactButton>
                </Box>
              )}
            </ConfigSection>
          </Stack>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
            <CompactButton
              variant="contained"
              color="primary"
              onClick={() => {
                const { hasErrors } = validateForm();
                if (!hasErrors) {
                  handleSaveSchedule(jobId);
                }
              }}
              startIcon={scheduleSaving[jobId] ? <CircularProgress size={16} /> : <SaveIcon />}
              disabled={scheduleSaving[jobId] || scheduleLoading[jobId]}
              darkMode={darkMode}
            >
              Save Schedule
            </CompactButton>
          </Box>
        </>
      ) : (
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          py: 2 
        }}>
          <CircularProgress size={20} thickness={5} />
          <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
            Loading...
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ScheduleConfiguration; 