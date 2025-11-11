import React from 'react';
import { Box, Typography, Tooltip, Chip } from '@mui/material';
import { 
  Schedule as ScheduleIcon, 
  DateRange as DateRangeIcon,
  CalendarToday as CalendarIcon
} from '@mui/icons-material';

/**
 * ScheduleSummary component displays the schedule details in a human-readable format
 * Shows summary for any job with sufficient schedule details, regardless of schedule status
 */
const ScheduleSummary = ({ scheduleData, jobId, darkMode, job }) => {
  const jobSchedule = scheduleData[jobId] || {};
  
  // Check if we have enough schedule information to display a summary
  const hasFrequencyInfo = (job && job["Frequency code"]) || (jobSchedule && jobSchedule.TIMEPARAM);
  const hasDateInfo = (job && job["start date"]) || (jobSchedule && jobSchedule.STRT_DT);
  
  // Display summary if we have the required information, regardless of official schedule status
  const hasScheduleInfo = hasFrequencyInfo && hasDateInfo;
  
  if (!hasScheduleInfo) {
    return (
      <Typography 
        variant="caption" 
        sx={{ 
          fontSize: '0.75rem',
          fontStyle: 'italic',
          color: darkMode ? 'rgba(156, 163, 175, 0.7)' : 'rgba(107, 114, 128, 0.7)'
        }}
      >
        Not scheduled
      </Typography>
    );
  }
  
  // Parse time parameter
  const getFrequencyLabel = () => {
    // If job has frequency code directly from backend, use that
    if (job && job["Frequency code"]) {
      const freq = job["Frequency code"];
      const frequencyLabels = {
        'DL': 'Daily',
        'WK': 'Weekly',
        'FN': 'Fortnightly',
        'MN': 'Monthly',
        'HY': 'Half-yearly',
        'YR': 'Yearly',
        'ID': 'Intraday'
      };
      return frequencyLabels[freq] || freq;
    }
    
    // Otherwise use the one from schedule data
    if (!jobSchedule.TIMEPARAM) return '';
    
    const parts = jobSchedule.TIMEPARAM.split('_');
    const freq = parts[0];
    
    const frequencyLabels = {
      'DL': 'Daily',
      'WK': 'Weekly',
      'FN': 'Fortnightly',
      'MN': 'Monthly',
      'HY': 'Half-yearly',
      'YR': 'Yearly',
      'ID': 'Intraday'
    };
    
    return frequencyLabels[freq] || freq;
  };
  
  const getDayLabel = () => {
    // Use job data directly if available
    if (job && job["Frequency day"]) {
      const freq = job["Frequency code"];
      const day = job["Frequency day"];
      
      // For weekly frequencies, convert day codes to day names
      if (['WK', 'FN'].includes(freq)) {
        const dayLabels = {
          'MON': 'Monday',
          'TUE': 'Tuesday',
          'WED': 'Wednesday',
          'THU': 'Thursday',
          'FRI': 'Friday',
          'SAT': 'Saturday',
          'SUN': 'Sunday'
        };
        
        return dayLabels[day] || day;
      }
      
      // For monthly/yearly, it's a day of month
      if (['MN', 'HY', 'YR'].includes(freq)) {
        // Check if it's a number and add suffix (1st, 2nd, etc.)
        const dayNum = parseInt(day, 10);
        if (!isNaN(dayNum)) {
          const suffixes = ['th', 'st', 'nd', 'rd'];
          const suffix = dayNum % 100 <= 10 || dayNum % 100 >= 14 
            ? suffixes[dayNum % 10] || 'th'
            : 'th';
          return `${dayNum}${suffix} day`;
        }
      }
      
      return day;
    }
    
    // Otherwise use jobSchedule data
    if (!jobSchedule.TIMEPARAM) return '';
    
    const parts = jobSchedule.TIMEPARAM.split('_');
    if (parts.length < 2) return '';
    
    const freq = parts[0];
    const day = parts[1];
    
    // For weekly frequencies, convert day codes to day names
    if (['WK', 'FN'].includes(freq)) {
      const dayLabels = {
        'MON': 'Monday',
        'TUE': 'Tuesday',
        'WED': 'Wednesday',
        'THU': 'Thursday',
        'FRI': 'Friday',
        'SAT': 'Saturday',
        'SUN': 'Sunday'
      };
      
      return dayLabels[day] || day;
    }
    
    // For monthly/yearly, it's a day of month
    if (['MN', 'HY', 'YR'].includes(freq)) {
      // Check if it's a number and add suffix (1st, 2nd, etc.)
      const dayNum = parseInt(day, 10);
      if (!isNaN(dayNum)) {
        const suffixes = ['th', 'st', 'nd', 'rd'];
        const suffix = dayNum % 100 <= 10 || dayNum % 100 >= 14 
          ? suffixes[dayNum % 10] || 'th'
          : 'th';
        return `${dayNum}${suffix} day`;
      }
    }
    
    return day;
  };
  
  const getTimeLabel = () => {
    // Use job data directly if available
    if (job && job["frequency hour"] !== null && job["frequency month"] !== null) {
      const hour = job["frequency hour"];
      const minute = job["frequency month"];
      
      // Format as 12-hour time
      if (hour !== null && minute !== null) {
        const hourNum = parseInt(hour, 10);
        const isPM = hourNum >= 12;
        const hour12 = hourNum % 12 || 12;
        return `${hour12}:${minute} ${isPM ? 'PM' : 'AM'}`;
      }
    }
    
    // Otherwise use jobSchedule data
    if (!jobSchedule.TIMEPARAM) return '';
    
    const parts = jobSchedule.TIMEPARAM.split('_');
    const freq = parts[0];
    
    // Time is at different indices based on frequency type
    const timeIndex = ['WK', 'MN', 'FN', 'HY', 'YR'].includes(freq) ? 2 : 1;
    
    if (parts.length <= timeIndex) return '';
    
    const timePart = parts[timeIndex];
    const [hour, minute] = timePart.split(':');
    
    // Format as 12-hour time
    if (hour && minute) {
      const hourNum = parseInt(hour, 10);
      const isPM = hourNum >= 12;
      const hour12 = hourNum % 12 || 12;
      return `${hour12}:${minute} ${isPM ? 'PM' : 'AM'}`;
    }
    
    return timePart;
  };
  
  // Format dates
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch (e) {
      return dateStr;
    }
  };
  
  // Build description
  const buildDescription = () => {
    const freq = getFrequencyLabel();
    const day = getDayLabel();
    const time = getTimeLabel();
    
    // Use direct job data for dates if available
    const startDate = job && job["start date"] 
      ? formatDate(job["start date"]) 
      : formatDate(jobSchedule.STRT_DT);
    
    const endDate = job && job["end date"] 
      ? formatDate(job["end date"]) 
      : formatDate(jobSchedule.END_DT);
    
    let description = freq;
    
    if (day) {
      description += ` on ${day}`;
    }
    
    if (time) {
      description += ` at ${time}`;
    }
    
    description += ` from ${startDate}`;
    
    if (endDate) {
      description += ` to ${endDate}`;
    }
    
    return description;
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <CalendarIcon 
        fontSize="small" 
        sx={{ 
          color: darkMode ? 'rgba(59, 130, 246, 0.8)' : 'rgba(59, 130, 246, 0.8)',
          fontSize: '1rem'
        }} 
      />
      
      <Typography 
        variant="body2" 
        sx={{
          fontSize: '0.75rem',
          color: darkMode ? 'rgba(209, 213, 219, 0.9)' : 'rgba(75, 85, 99, 0.9)',
          fontWeight: 500
        }}
      >
        {buildDescription()}
      </Typography>
    </Box>
  );
};

export default ScheduleSummary; 