import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Box,
  Typography
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

const frequencyOptions = [
  { value: 'DL', label: 'Daily (DL)' },
  { value: 'WK', label: 'Weekly (WK)' },
  { value: 'FN', label: 'Fortnightly (FN)' },
  { value: 'MN', label: 'Monthly (MN)' },
  { value: 'HY', label: 'Half-Yearly (HY)' },
  { value: 'YR', label: 'Yearly (YR)' },
  { value: 'ID', label: 'Interval (ID)' },
];

const weekdayOptions = [
  { value: 'MON', label: 'Monday' },
  { value: 'TUE', label: 'Tuesday' },
  { value: 'WED', label: 'Wednesday' },
  { value: 'THU', label: 'Thursday' },
  { value: 'FRI', label: 'Friday' },
  { value: 'SAT', label: 'Saturday' },
  { value: 'SUN', label: 'Sunday' },
];

const formatDateTime = (isoString) => {
  if (!isoString) return '-';
  try {
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return isoString || '-';
  }
};

const ScheduleDialog = ({ 
  open, 
  onClose, 
  job, 
  scheduleData, 
  onSave, 
  darkMode,
  saving = false 
}) => {
  const [formData, setFormData] = useState({
    frequency: '',
    day: '',
    hour: '00',
    minute: '00',
    startDate: null,
    endDate: null,
  });

  // Initialize form when dialog opens or job changes
  useEffect(() => {
    if (open && job && scheduleData[job.JOBFLWID]) {
      const schedule = scheduleData[job.JOBFLWID];
      const timeParam = schedule.TIMEPARAM || '';
      
      // Parse time parameter (format: FRQCD_DAY_TIME or FRQCD_TIME)
      // Also check for direct frequency components (FRQCD, FRQDD, FRQHH, FRQMI)
      let frequency = '';
      let day = '';
      let hour = '00';
      let minute = '00';
      
      // First try to get from TIMEPARAM
      if (timeParam) {
        const parts = timeParam.split('_');
        frequency = parts[0] || '';
        
        if (['WK', 'FN', 'MN', 'HY', 'YR'].includes(frequency)) {
          day = parts[1] || '';
          const timePart = parts[2] || '';
          if (timePart.includes(':')) {
            const [h, m] = timePart.split(':');
            hour = h || '00';
            minute = m || '00';
          }
        } else if (frequency === 'DL' || frequency === 'ID') {
          const timePart = parts[1] || '';
          if (timePart.includes(':')) {
            const [h, m] = timePart.split(':');
            hour = h || '00';
            minute = m || '00';
          }
        }
      }
      
      // If TIMEPARAM doesn't have all info, try direct frequency components
      if (!frequency && schedule.FRQCD) {
        frequency = schedule.FRQCD;
      }
      if (!day && schedule.FRQDD) {
        day = schedule.FRQDD;
      }
      if (schedule.FRQHH !== undefined && schedule.FRQHH !== null) {
        hour = String(schedule.FRQHH).padStart(2, '0');
      }
      if (schedule.FRQMI !== undefined && schedule.FRQMI !== null) {
        minute = String(schedule.FRQMI).padStart(2, '0');
      }
      
      // Parse dates - handle both date strings and Date objects
      let startDate = null;
      let endDate = null;
      
      if (schedule.STRT_DT) {
        try {
          startDate = schedule.STRT_DT instanceof Date ? schedule.STRT_DT : new Date(schedule.STRT_DT);
          // Check if date is valid
          if (isNaN(startDate.getTime())) {
            startDate = null;
          }
        } catch (e) {
          startDate = null;
        }
      }
      
      if (schedule.END_DT) {
        try {
          endDate = schedule.END_DT instanceof Date ? schedule.END_DT : new Date(schedule.END_DT);
          // Check if date is valid
          if (isNaN(endDate.getTime())) {
            endDate = null;
          }
        } catch (e) {
          endDate = null;
        }
      }
      
      setFormData({
        frequency,
        day,
        hour: hour.padStart(2, '0'),
        minute: minute.padStart(2, '0'),
        startDate,
        endDate,
      });
    } else if (open) {
      // Reset form for new schedule
      setFormData({
        frequency: '',
        day: '',
        hour: '00',
        minute: '00',
        startDate: null,
        endDate: null,
      });
    }
  }, [open, job, scheduleData]);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Auto-set default day when frequency changes
    if (field === 'frequency') {
      if (value === 'WK' || value === 'FN') {
        setFormData(prev => ({ ...prev, day: prev.day || 'MON' }));
      } else if (['MN', 'HY', 'YR'].includes(value)) {
        setFormData(prev => ({ ...prev, day: prev.day || '01' }));
      } else {
        setFormData(prev => ({ ...prev, day: '' }));
      }
    }
  };

  const handleSave = () => {
    if (!job) return;
    
    // Build time parameter string
    let timeParam = formData.frequency;
    if (['WK', 'FN', 'MN', 'HY', 'YR'].includes(formData.frequency)) {
      if (formData.day) {
        timeParam += `_${formData.day}`;
      }
      timeParam += `_${formData.hour}:${formData.minute}`;
    } else if (formData.frequency === 'DL' || formData.frequency === 'ID') {
      timeParam += `_${formData.hour}:${formData.minute}`;
    }
    
    // Format dates - use local date to avoid timezone issues
    const formatLocalDate = (date) => {
      if (!date) return null;
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };
    
    const startDate = formData.startDate ? formatLocalDate(formData.startDate) : null;
    const endDate = formData.endDate ? formatLocalDate(formData.endDate) : null;
    
    // Update schedule data - ensure MAPREF is always included
    const existingSchedule = scheduleData[job.JOBFLWID] || {};
    const updatedScheduleData = {
      ...existingSchedule,
      JOBFLWID: job.JOBFLWID,
      MAPREF: job.MAPREF || existingSchedule.MAPREF, // Ensure MAPREF is always present
      TIMEPARAM: timeParam,
      STRT_DT: startDate,
      END_DT: endDate,
    };
    
    onSave(job.JOBFLWID, updatedScheduleData);
  };

  const canSave = formData.frequency && formData.startDate;

  const currentSchedule = job && scheduleData[job.JOBFLWID] ? scheduleData[job.JOBFLWID] : null;
  const lastRun = currentSchedule?.LST_RUN_DT || job?.['last run'] || null;
  const nextRun = currentSchedule?.NXT_RUN_DT || job?.['next run'] || null;

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      fullWidth 
      maxWidth="sm"
    >
      <DialogTitle>Schedule Job</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {/* Job Name (read-only) */}
          {job && (
            <TextField
              label="Job"
              value={job.MAPREF || ''}
              fullWidth
              InputProps={{ readOnly: true }}
              size="small"
            />
          )}

          {/* Schedule pattern */}
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Frequency</InputLabel>
              <Select
                label="Frequency"
                value={formData.frequency}
                onChange={(e) => handleChange('frequency', e.target.value)}
              >
                <MenuItem value="">
                  <em>Select Frequency</em>
                </MenuItem>
                {frequencyOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>

          {/* Weekly / Monthly specific selectors */}
          {['WK', 'FN'].includes(formData.frequency) && (
            <FormControl fullWidth size="small">
              <InputLabel>Day of Week</InputLabel>
              <Select
                label="Day of Week"
                value={formData.day}
                onChange={(e) => handleChange('day', e.target.value)}
              >
                {weekdayOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}

          {['MN', 'HY', 'YR'].includes(formData.frequency) && (
            <FormControl fullWidth size="small">
              <InputLabel>Day of Month</InputLabel>
              <Select
                label="Day of Month"
                value={formData.day}
                onChange={(e) => handleChange('day', e.target.value)}
              >
                {Array.from({ length: 31 }, (_, i) => {
                  const day = String(i + 1).padStart(2, '0');
                  return (
                    <MenuItem key={day} value={day}>
                      {day}
                    </MenuItem>
                  );
                })}
              </Select>
            </FormControl>
          )}

          {/* Time (Hour / Minute) */}
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Time (24-hour format)
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <FormControl size="small" sx={{ width: 100 }}>
                <InputLabel>Hour</InputLabel>
                <Select
                  label="Hour"
                  value={formData.hour}
                  onChange={(e) => handleChange('hour', e.target.value.padStart(2, '0'))}
                >
                  {Array.from({ length: 24 }, (_, i) => {
                    const hour = String(i).padStart(2, '0');
                    return (
                      <MenuItem key={hour} value={hour}>
                        {hour}
                      </MenuItem>
                    );
                  })}
                </Select>
              </FormControl>
              <Typography variant="h6">:</Typography>
              <FormControl size="small" sx={{ width: 100 }}>
                <InputLabel>Minute</InputLabel>
                <Select
                  label="Minute"
                  value={formData.minute}
                  onChange={(e) => handleChange('minute', e.target.value.padStart(2, '0'))}
                >
                  {Array.from({ length: 60 }, (_, i) => {
                    const minute = String(i).padStart(2, '0');
                    return (
                      <MenuItem key={minute} value={minute}>
                        {minute}
                      </MenuItem>
                    );
                  })}
                </Select>
              </FormControl>
            </Stack>
          </Box>

          {/* Date Range */}
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <DatePicker
                label="Start Date"
                value={formData.startDate}
                onChange={(date) => handleChange('startDate', date)}
                slotProps={{
                  textField: {
                    size: 'small',
                    fullWidth: true,
                    required: true
                  }
                }}
              />
              <DatePicker
                label="End Date (Optional)"
                value={formData.endDate}
                onChange={(date) => handleChange('endDate', date)}
                slotProps={{
                  textField: {
                    size: 'small',
                    fullWidth: true
                  }
                }}
              />
            </Stack>
          </LocalizationProvider>

          {/* Read-only schedule info */}
          {(lastRun || nextRun) && (
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Next Run At"
                value={formatDateTime(nextRun)}
                InputProps={{ readOnly: true }}
                fullWidth
                size="small"
              />
              <TextField
                label="Last Run At"
                value={formatDateTime(lastRun)}
                InputProps={{ readOnly: true }}
                fullWidth
                size="small"
              />
            </Stack>
          )}
        </Stack>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button 
          onClick={handleSave} 
          variant="contained" 
          disabled={!canSave || saving}
        >
          {saving ? "Saving..." : "Save Schedule"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ScheduleDialog;

