"use client";

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Typography, 
  Box, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  IconButton,
  CircularProgress,
  Tooltip,
  Alert,
  Collapse,
  Snackbar,
  Tabs,
  Tab,
  Fab,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Fade,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import { styled, useTheme as useMuiTheme } from '@mui/material/styles';
import { 
  Visibility as VisibilityIcon, 
  Code as CodeIcon, 
  ExpandMore as ExpandMoreIcon, 
  ExpandLess as ExpandLessIcon,
  CheckCircleOutline as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
  ViewList as ListIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  ToggleOn as ToggleOnIcon,
  ToggleOff as ToggleOffIcon,
  Warning as WarningIcon,
  RemoveRedEye as EyeIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useTheme } from '@/context/ThemeContext';
import JobDetailsDialog from './JobDetailsDialog';
import ScheduleConfiguration from './ScheduleConfiguration';
import { Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { format } from 'date-fns';
import Link from 'next/link';
import { 
  StatusIndicator, 
  MappingDetails, 
  InlineScheduleConfig,
  TargetTableDisplay,
  ScheduleSummary,
  DependencyDisplay
} from './components';

// Styled components
const StyledTableContainer = styled(TableContainer)(({ theme, darkMode }) => ({
  maxHeight: '80vh',
  borderRadius: '12px',
  overflowX: 'auto',
  boxShadow: darkMode 
    ? '0 4px 20px rgba(0, 0, 0, 0.3)' 
    : '0 4px 20px rgba(0, 0, 0, 0.08)',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  '& .MuiTableCell-head': {
    backgroundColor: darkMode ? '#1A202C' : '#F7FAFC', 
    color: darkMode ? '#E2E8F0' : '#2D3748',
    fontWeight: 600,
    fontSize: '0.8125rem',
    padding: '10px 12px',
    whiteSpace: 'nowrap',
    borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
    position: 'sticky',
    top: 0,
    zIndex: 10,
    backdropFilter: 'blur(8px)',
    height: '40px'
  },
  '& .MuiTableCell-body': {
    color: darkMode ? '#E2E8F0' : '#2D3748',
    padding: '6px 12px',
    fontSize: '0.8125rem',
    transition: 'background-color 0.2s ease',
    height: '42px',
    verticalAlign: 'middle'
  },
  '& .MuiTableRow-root:hover': {
    backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
    transition: 'background-color 0.2s ease',
  },
}));

// Define ActionButton if it's missing
const ActionButton = styled(IconButton)(({ theme, darkMode, color = 'primary' }) => ({
  padding: '4px',
  margin: '0 2px',
  width: '28px',
  height: '28px',
  backgroundColor: darkMode 
    ? (color === 'primary' ? 'rgba(59, 130, 246, 0.15)' : 
      color === 'info' ? 'rgba(6, 182, 212, 0.15)' : 
      color === 'success' ? 'rgba(34, 197, 94, 0.15)' : 
      color === 'error' ? 'rgba(239, 68, 68, 0.15)' : 
      'rgba(99, 102, 241, 0.15)') 
    : (color === 'primary' ? 'rgba(59, 130, 246, 0.1)' : 
      color === 'info' ? 'rgba(6, 182, 212, 0.1)' : 
      color === 'success' ? 'rgba(34, 197, 94, 0.1)' : 
      color === 'error' ? 'rgba(239, 68, 68, 0.1)' : 
      'rgba(99, 102, 241, 0.1)'),
  color: darkMode 
    ? (color === 'primary' ? '#60A5FA' : 
      color === 'info' ? '#06B6D4' : 
      color === 'success' ? '#4ADE80' : 
      color === 'error' ? '#F87171' : 
      '#818CF8')
    : (color === 'primary' ? '#3B82F6' : 
      color === 'info' ? '#0891B2' : 
      color === 'success' ? '#22C55E' : 
      color === 'error' ? '#EF4444' : 
      '#6366F1'),
  border: '1px solid',
  borderColor: darkMode
    ? (color === 'primary' ? 'rgba(59, 130, 246, 0.3)' : 
      color === 'info' ? 'rgba(6, 182, 212, 0.3)' : 
      color === 'success' ? 'rgba(34, 197, 94, 0.3)' : 
      color === 'error' ? 'rgba(239, 68, 68, 0.3)' : 
      'rgba(99, 102, 241, 0.3)')
    : (color === 'primary' ? 'rgba(59, 130, 246, 0.2)' : 
      color === 'info' ? 'rgba(6, 182, 212, 0.2)' : 
      color === 'success' ? 'rgba(34, 197, 94, 0.2)' : 
      color === 'error' ? 'rgba(239, 68, 68, 0.2)' : 
      'rgba(99, 102, 241, 0.2)'),
  transition: 'all 0.2s ease',
  '&:hover': {
    backgroundColor: darkMode
      ? (color === 'primary' ? 'rgba(59, 130, 246, 0.25)' : 
        color === 'info' ? 'rgba(6, 182, 212, 0.25)' : 
        color === 'success' ? 'rgba(34, 197, 94, 0.25)' : 
        color === 'error' ? 'rgba(239, 68, 68, 0.25)' : 
        'rgba(99, 102, 241, 0.25)')
      : (color === 'primary' ? 'rgba(59, 130, 246, 0.15)' : 
        color === 'info' ? 'rgba(6, 182, 212, 0.15)' : 
        color === 'success' ? 'rgba(34, 197, 94, 0.15)' : 
        color === 'error' ? 'rgba(239, 68, 68, 0.15)' : 
        'rgba(99, 102, 241, 0.15)'),
    transform: 'translateY(-1px)',
    boxShadow: '0 2px 5px rgba(0,0,0,0.1)'
  },
  '&:active': {
    transform: 'translateY(0)',
  }
}));

// New styled component for scroll-to-top button
const ScrollToTopButton = styled(Fab)(({ theme, darkMode }) => ({
  position: 'fixed',
  bottom: 24,
  right: 24,
  backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.9)' : 'rgba(59, 130, 246, 0.9)',
  color: '#FFFFFF',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: darkMode ? 'rgba(37, 99, 235, 1)' : 'rgba(37, 99, 235, 1)',
    transform: 'translateY(-2px)',
  },
  zIndex: 1000,
  boxShadow: darkMode ? '0 4px 12px rgba(0, 0, 0, 0.4)' : '0 4px 12px rgba(0, 0, 0, 0.2)',
}));

// New styled components for the filters section 
const FiltersContainer = styled(Box)(({ theme, darkMode }) => ({
  display: 'flex',
  flexWrap: 'wrap',
  gap: '8px',
  alignItems: 'center',
  padding: '8px 12px',
  borderRadius: '10px',
  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.6)' : 'rgba(249, 250, 251, 0.8)',
  backdropFilter: 'blur(8px)',
  boxShadow: darkMode ? '0 2px 4px rgba(0, 0, 0, 0.2)' : '0 1px 2px rgba(0, 0, 0, 0.1)',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  transition: 'all 0.3s ease',
}));

const StyledSearchField = styled(TextField)(({ theme, darkMode }) => ({
  '& .MuiOutlinedInput-root': {
    backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
    borderRadius: '6px',
    height: '32px',
    '&:hover .MuiOutlinedInput-notchedOutline': {
      borderColor: darkMode ? 'rgba(99, 102, 241, 0.5)' : 'rgba(99, 102, 241, 0.5)',
    },
    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
      borderColor: '#3B82F6',
    }
  },
  '& .MuiInputLabel-root': {
    fontSize: '0.75rem',
    transform: 'translate(14px, 8px) scale(1)',
    '&.MuiInputLabel-shrink': {
      transform: 'translate(14px, -6px) scale(0.75)',
    }
  },
  '& .MuiInputBase-input': {
    padding: '7px 10px',
    fontSize: '0.8125rem',
  }
}));

const StyledFormControl = styled(FormControl)(({ theme, darkMode }) => ({
  minWidth: 120,
  '& .MuiOutlinedInput-root': {
    backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.8)' : 'rgba(255, 255, 255, 0.8)',
    borderRadius: '6px',
    height: '32px',
    '&:hover .MuiOutlinedInput-notchedOutline': {
      borderColor: darkMode ? 'rgba(99, 102, 241, 0.5)' : 'rgba(99, 102, 241, 0.5)',
    },
    '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
      borderColor: '#3B82F6',
    }
  },
  '& .MuiInputLabel-root': {
    fontSize: '0.75rem',
    transform: 'translate(14px, 8px) scale(1)',
    '&.MuiInputLabel-shrink': {
      transform: 'translate(14px, -6px) scale(0.75)',
    }
  },
  '& .MuiSelect-select': {
    padding: '7px 14px 7px 10px',
    fontSize: '0.8125rem',
  }
}));

// Button styles
const StyledButton = styled(Button)(({ theme, darkMode }) => ({
  textTransform: 'none',
  fontWeight: 600,
  borderRadius: '6px',
  padding: '5px 12px',
  fontSize: '0.75rem',
  minHeight: '32px',
  boxShadow: 'none',
  transition: 'all 0.2s ease',
  '&:hover': {
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
  }
}));

// Page header styling
const PageHeader = styled(Box)(({ theme, darkMode }) => ({
  display: 'flex',
  justifyContent: 'flex-end',
  alignItems: 'center',
  marginBottom: '16px',
  padding: '12px 20px',
  borderRadius: '12px',
  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.6)' : 'rgba(249, 250, 251, 0.8)',
  backdropFilter: 'blur(8px)',
  boxShadow: darkMode ? '0 4px 6px rgba(0, 0, 0, 0.2)' : '0 1px 3px rgba(0, 0, 0, 0.1)',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
}));

const StatusChip = styled(Chip)(({ theme, darkMode, status }) => ({
  fontWeight: 600,
  fontSize: '0.7rem',
  borderRadius: '4px',
  height: '22px',
  backgroundColor: 
    status === 'Scheduled' ? (darkMode ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.1)') :
    (darkMode ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)'),
  color: 
    status === 'Scheduled' ? (darkMode ? '#4ADE80' : '#22C55E') :
    (darkMode ? '#FBBF24' : '#D97706'),
  border: '1px solid',
  borderColor: 
    status === 'Scheduled' ? (darkMode ? 'rgba(34, 197, 94, 0.3)' : 'rgba(34, 197, 94, 0.2)') :
    (darkMode ? 'rgba(245, 158, 11, 0.3)' : 'rgba(245, 158, 11, 0.2)'),
  '& .MuiChip-label': {
    padding: '0 4px',
  }
}));

const JobsPage = () => {
  const { darkMode } = useTheme();
  const contentRef = useRef(null);

  // State for jobs data
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  
  // State for selected job and dialog
  const [selectedJob, setSelectedJob] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [openLogicDialog, setOpenLogicDialog] = useState(false);
  const [openExecuteDialog, setOpenExecuteDialog] = useState(false);
  const [executingJob, setExecutingJob] = useState(null);
  
  // New state for enable/disable job functionality
  const [openEnableDisableDialog, setOpenEnableDisableDialog] = useState(false);
  const [jobToToggle, setJobToToggle] = useState(null);
  const [isEnabling, setIsEnabling] = useState(false);

  // State for schedule data
  const [scheduleData, setScheduleData] = useState({});
  const [scheduleLoading, setScheduleLoading] = useState({});
  const [scheduleSaving, setScheduleSaving] = useState({});
  
  // State for filters
  const [searchTerm, setSearchTerm] = useState('');
  const [tableTypeFilter, setTableTypeFilter] = useState('');
  const [scheduleStatusFilter, setScheduleStatusFilter] = useState('');
  
  // State for UI
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [viewMode, setViewMode] = useState('list');
  
  // State for notifications
  const [notification, setNotification] = useState({ 
    open: false, 
    message: '', 
    severity: 'info' 
  });
  
  const muiTheme = useMuiTheme();

  // Handle scroll events
  const handleScroll = () => {
    if (contentRef.current) {
      setShowScrollTop(contentRef.current.scrollTop > 300);
    }
  };
  
  // Scroll to top function
  const scrollToTop = () => {
    if (contentRef.current) {
      contentRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  // Fetch all jobs on component mount
  useEffect(() => {
    fetchJobs();
  }, []);

  // Function to resolve dependency map references after fetching jobs
  useEffect(() => {
    // Only process if we have jobs with DPND_JOBSCHID
    if (jobs.length === 0 || !jobs.some(job => job.DPND_JOBSCHID)) {
      return;
    }
    
    // For each job with a DPND_JOBSCHID, find the corresponding dependent job
    let hasChanges = false;
    const updatedJobs = jobs.map(job => {
      if (job.DPND_JOBSCHID) {
        // Find the job with matching JOBSCHID
        const dependentJob = jobs.find(j => j.JOBSCHID === job.DPND_JOBSCHID);
        
        // If found and DPND_MAPREF is not already set correctly, set it
        if (dependentJob && job.DPND_MAPREF !== dependentJob.MAPREF) {
          hasChanges = true;
          return {
            ...job,
            DPND_MAPREF: dependentJob.MAPREF
          };
        }
      }
      return job;
    });
    
    // Only update if there are changes
    if (hasChanges) {
      setJobs(updatedJobs);
    }
  }, [jobs]);

  // Add scroll event listener
  useEffect(() => {
    const currentRef = contentRef.current;
    if (currentRef) {
      currentRef.addEventListener('scroll', handleScroll);
      return () => {
        currentRef.removeEventListener('scroll', handleScroll);
      };
    }
  }, []);

  // Function to fetch all jobs
  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_all_jobs`);
      
      // Since the response structure has changed, we'll directly use the data as it comes
      const jobsData = response.data;
      setJobs(jobsData);
      
      // Initialize schedule data for each job
      const initialScheduleData = {};
      jobsData.forEach(job => {
        initialScheduleData[job.JOBFLWID] = {
          JOBFLWID: job.JOBFLWID,
          MAPREF: job.MAPREF || '',
          TIMEPARAM: '',
          STRT_DT: null,
          END_DT: null,
          STFLG: 'A' // Default status is Active
        };
      });
      
      setScheduleData(initialScheduleData);
      setError(null);
      
      // After getting all jobs, fetch schedule details for all jobs that might have schedule information
      // This ensures the summary is shown even for jobs not officially scheduled
      setTimeout(() => {
        jobsData.forEach(job => {
          fetchJobScheduleDetails(job.JOBFLWID);
        });
      }, 300); // Small delay to ensure jobs state is updated
      
    } catch (err) {
      console.error('Error fetching jobs:', err);
      setError('Failed to fetch jobs. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch job schedule details for a job
  const fetchJobScheduleDetails = async (jobId) => {
    // Get the job from the jobs list
    const job = jobs.find(j => j.JOBFLWID === jobId);
    if (!job) return;
    
    // Set loading state for this specific job
    setScheduleLoading(prev => ({ ...prev, [jobId]: true }));
    
    try {
      console.log(`Fetching schedule details for job ${jobId}`);
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_job_schedule_details/${jobId}`);
      console.log('API Response:', response.data);
      
      // Check if there's schedule data
      if (response.data && response.data.length > 0) {
        const scheduleDetails = response.data[0];
        
        // Extract time parameter from individual fields if they exist
        let timeParam = '';
        if (scheduleDetails.FRQCD) {
          timeParam = scheduleDetails.FRQCD;
          
          if (scheduleDetails.FRQDD) {
            timeParam += `_${scheduleDetails.FRQDD}`;
          }
          
          if (scheduleDetails.FRQHH !== undefined && scheduleDetails.FRQMI !== undefined) {
            timeParam += `_${scheduleDetails.FRQHH}:${scheduleDetails.FRQMI}`;
          }
        }
        
        // Update the schedule data with fetched values
        setScheduleData(prev => ({
          ...prev,
          [jobId]: {
            ...prev[jobId],
            JOBFLWID: jobId,
            MAPREF: scheduleDetails.MAPREF || job.MAPREF || '',
            TIMEPARAM: scheduleDetails.TIMEPARAM || timeParam,
            STRT_DT: scheduleDetails.STRT_DT || scheduleDetails.STRTDT,
            END_DT: scheduleDetails.END_DT || scheduleDetails.ENDDT,
            STFLG: scheduleDetails.STFLG || '',
            JOB_SCHEDULE_STATUS: job.JOB_SCHEDULE_STATUS
          }
        }));
        
        // Update job data with schedule information so it's available for display
        // even if the job is not officially scheduled
        if (!job["Frequency code"] && scheduleDetails.FRQCD) {
          setJobs(prevJobs => 
            prevJobs.map(j => 
              j.JOBFLWID === jobId 
                ? { 
                    ...j, 
                    "Frequency code": scheduleDetails.FRQCD,
                    "Frequency day": scheduleDetails.FRQDD,
                    "frequency hour": scheduleDetails.FRQHH,
                    "frequency month": scheduleDetails.FRQMI,
                    "start date": scheduleDetails.STRT_DT || scheduleDetails.STRTDT,
                    "end date": scheduleDetails.END_DT || scheduleDetails.ENDDT
                  } 
                : j
            )
          );
        }
      }
    } catch (err) {
      console.error('Error fetching job schedule details:', err);
      // Don't show error message to avoid cluttering the UI
    } finally {
      setScheduleLoading(prev => ({ ...prev, [jobId]: false }));
    }
  };

  // Handle view details dialog
  const handleViewDetails = (job) => {
    setSelectedJob(job);
    setOpenDialog(true);
  };
  
  // Handle close dialog
  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedJob(null);
  };
  
  // Handle view logic dialog
  const handleViewLogic = (job) => {
    setSelectedJob(job);
    setOpenLogicDialog(true);
  };
  
  // Handle close logic dialog
  const handleCloseLogicDialog = () => {
    setOpenLogicDialog(false);
    setSelectedJob(null);
  };

  // Handle schedule data change
  const handleScheduleChange = (jobId, field, value) => {
    setScheduleData(prev => ({
      ...prev,
      [jobId]: {
        ...prev[jobId],
        [field]: value
      }
    }));
  };

  // Handle date change for schedule
  const handleDateChange = (jobId, field, date) => {
    setScheduleData(prev => ({
      ...prev,
      [jobId]: {
        ...prev[jobId],
        [field]: date
      }
    }));
  };

  // Handle save schedule
  const handleSaveSchedule = async (jobId) => {
    try {
      // Find the job to check if it's currently enabled/scheduled
      const currentJob = jobs.find(job => job.JOBFLWID === jobId);
      
      // Check if job is currently enabled (scheduled)
      if (currentJob && currentJob.JOB_SCHEDULE_STATUS === 'Scheduled') {
        setNotification({
          open: true,
          message: 'Cannot update schedule details while job is enabled. Please disable the job first before updating schedule details.',
          severity: 'warning'
        });
        return;
      }
      
      // Set saving state for this specific job
      setScheduleSaving(prev => ({ ...prev, [jobId]: true }));
      
      const jobData = scheduleData[jobId];
      
      // Validate the schedule data before sending to backend
      const validationError = validateScheduleData(jobData);
      if (validationError) {
        setError(validationError);
        setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
        return;
      }
      
      // Extract time parameter components for backend format
      const timeParts = jobData.TIMEPARAM ? jobData.TIMEPARAM.split('_') : [];
      const frequencyCode = timeParts[0] || '';
      
      // Get day and time parameters based on frequency type
      let frequencyDay = '', frequencyHour = '', frequencyMinute = '';
      
      if (['WK', 'FN', 'MN', 'HY', 'YR'].includes(frequencyCode)) {
        frequencyDay = timeParts[1] || '';
        const timePieces = timeParts[2] ? timeParts[2].split(':') : [];
        frequencyHour = timePieces[0] || '';
        frequencyMinute = timePieces[1] || '';
      } else {
        const timePieces = timeParts[1] ? timeParts[1].split(':') : [];
        frequencyHour = timePieces[0] || '';
        frequencyMinute = timePieces[1] || '';
      }
      
      // Prepare the request data - using the parameter names expected by backend
      const requestData = {
        JOBFLWID: jobId,
        MAPREF: jobData.MAPREF,
        FRQCD: frequencyCode,
        FRQDD: frequencyDay,
        FRQHH: frequencyHour,
        FRQMI: frequencyMinute,
        STRTDT: jobData.STRT_DT,
        ENDDT: jobData.END_DT
      };
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/save_job_schedule`, 
        requestData
      );
      
      if (response.data.success) {
        setSuccessMessage('Schedule saved successfully');
        
        // Update the job status to Scheduled in the jobs list
        setJobs(prevJobs => 
          prevJobs.map(job => 
            job.JOBFLWID === jobId 
              ? { 
                  ...job, 
                  JOB_SCHEDULE_STATUS: 'Scheduled',
                  // Add the frequency components to the job object for ScheduleSummary display
                  "Frequency code": frequencyCode,
                  "Frequency day": frequencyDay,
                  "frequency hour": frequencyHour,
                  "frequency month": frequencyMinute,
                  "start date": jobData.STRT_DT,
                  "end date": jobData.END_DT,
                  JOBSCHID: response.data.job_schedule_id
                } 
              : job
          )
        );
      } else {
        setError(response.data.message || 'Failed to save schedule');
      }
    } catch (err) {
      console.error('Error saving job schedule:', err);
      setError('Failed to save schedule. Please try again.');
    } finally {
      // Clear saving state for this job
      setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
      
      setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 3000);
    }
  };

  // Validate schedule data based on backend requirements
  const validateScheduleData = (jobData) => {
    // Extract time parameter components
    const timeParts = jobData.TIMEPARAM ? jobData.TIMEPARAM.split('_') : [];
    const frequencyCode = timeParts[0] || '';
    
    // Get day and time parameters based on frequency type
    let frequencyDay, frequencyHour, frequencyMinute;
    
          if (['WK', 'FN', 'MN', 'HY', 'YR'].includes(frequencyCode)) {
        frequencyDay = timeParts[1] || '';
        const timePieces = timeParts[2] ? timeParts[2].split(':') : [];
        frequencyHour = timePieces[0] || '';
        frequencyMinute = timePieces[1] || '';
      } else {
      const timePieces = timeParts[1] ? timeParts[1].split(':') : [];
      frequencyHour = timePieces[0] || '';
      frequencyMinute = timePieces[1] || '';
    }
    
    // Validate mapping reference
    if (!jobData.MAPREF) {
      return 'Mapping reference must be provided.';
    }
    
    // Validate frequency code
    if (!frequencyCode || !['ID', 'DL', 'WK', 'FN', 'MN', 'HY', 'YR'].includes(frequencyCode)) {
      return 'Invalid frequency code (Valid: ID,DL,WK,FN,MN,HY,YR).';
    }
    
    // Validate day format for weekly/fortnightly frequency
    if (['WK', 'FN'].includes(frequencyCode)) {
      const validDays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
      if (!frequencyDay || !validDays.includes(frequencyDay)) {
        return 'Invalid Frequency Day. For Weekly/Fortlightly frequency, frequency day can be any one of "MON,TUE,WED,THU,FRI,SAT,SUN".';
      }
    }
    
    // Validate day format for monthly/half-yearly/yearly frequency
    if (['MN', 'HY', 'YR'].includes(frequencyCode)) {
      const day = parseInt(frequencyDay, 10);
      if (isNaN(day) || day < 1 || day > 31) {
        return 'Invalid frequency day (Valid: 1 .. 31).';
      }
    }
    
    // Validate hour format (0-23)
    const hour = parseInt(frequencyHour, 10);
    if (isNaN(hour) || hour < 0 || hour > 23) {
      return 'Invalid frequency hour (valid: 0 .. 23).';
    }
    
    // Validate minute format (0-59)
    const minute = parseInt(frequencyMinute, 10);
    if (isNaN(minute) || minute < 0 || minute > 59) {
      return 'Invalid frequency minute (valid: 0 .. 59).';
    }
    
    // Validate start date is provided
    if (!jobData.STRT_DT) {
      return 'Schedule start date must be provided.';
    }
    
    // Validate start date is not in the past
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Set to beginning of the day for proper comparison
    const startDate = new Date(jobData.STRT_DT);
    
    if (startDate < today) {
      return 'Schedule start date cannot be in the past.';
    }
    
    // Validate end date is after start date (if provided)
    if (jobData.END_DT) {
      const endDate = new Date(jobData.END_DT);
      if (startDate >= endDate) {
        return 'Schedule start date must be before schedule end date.';
      }
    }
    
    return null; // No validation errors
  };

  // Handle view mode change
  const handleViewModeChange = (event, newValue) => {
    setViewMode(newValue);
  };

  // Handle search filter
  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };
  
  // Handle table type filter
  const handleTableTypeFilterChange = (event) => {
    setTableTypeFilter(event.target.value);
  };
  
  // Handle schedule status filter
  const handleScheduleStatusFilterChange = (event) => {
    setScheduleStatusFilter(event.target.value);
  };

  // Add function to clear all filters
  const clearAllFilters = () => {
    setSearchTerm('');
    setTableTypeFilter('');
    setScheduleStatusFilter('');
  };

  // Handle notification close
  const handleCloseNotification = () => {
    setNotification(prev => ({
      ...prev,
      open: false
    }));
  };

  // Filter apply to jobs
  const filteredJobs = jobs.filter(job => {
    // Apply search term filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = (
        (job.JOBSCHID && job.JOBSCHID.toString().includes(searchLower)) ||
        (job.TRGSCHM && job.TRGSCHM.toLowerCase().includes(searchLower)) ||
        (job.TRGTBNM && job.TRGTBNM.toLowerCase().includes(searchLower)) ||
        (job.MAPREF && job.MAPREF.toLowerCase().includes(searchLower))
      );
      if (!matchesSearch) return false;
    }
    
    // Apply table type filter
    if (tableTypeFilter && job.TRGTBTYP !== tableTypeFilter) {
      return false;
    }
    
    // Apply schedule status filter
    if (scheduleStatusFilter) {
      if (scheduleStatusFilter === 'Scheduled' && job.JOB_SCHEDULE_STATUS !== 'Scheduled') {
        return false;
      }
      if (scheduleStatusFilter === 'Not Scheduled' && job.JOB_SCHEDULE_STATUS === 'Scheduled') {
        return false;
      }
    }
    
    return true;
  });
  
  // Get unique table types for filter dropdown
  const tableTypes = [...new Set(jobs.map(job => job.TRGTBTYP))].filter(Boolean).sort();

  // Define columns for table
  const columns = [
    { id: 'MAPREF', label: 'Job Mapping Reference', width: '18%' },
    { id: 'TRGTBNM', label: 'Target Table', width: '14%' },
    { id: 'STATUS', label: 'Status', width: '5%' },
    { id: 'SCHEDULE', label: 'Schedule Configuration', width: '17%' },
    { id: 'SUMMARY', label: 'Schedule Summary', width: '18%' },
    { id: 'DEPENDENCY', label: 'Dependency', width: '12%' },
    { id: 'view', label: 'View', width: '8%' },
    { id: 'actions', label: 'Actions', width: '8%' },
  ];

  const handleRefresh = () => {
    fetchJobs();
  };

  // Function to handle dependency updates
  const handleDependencyUpdated = (jobId, dependencyMapRef) => {
    // Find the job with this map reference to get its JOBSCHID
    const dependentJob = jobs.find(j => j.MAPREF === dependencyMapRef);
    
    // Update jobs list with the dependency info
    setJobs(prevJobs => 
      prevJobs.map(job => 
        job.JOBFLWID === jobId 
          ? { 
              ...job, 
              DPND_MAPREF: dependencyMapRef,
              DPND_JOBSCHID: dependentJob?.JOBSCHID || null
            } 
          : job
      )
    );
    
    // Show success message
    setSuccessMessage('Dependency saved successfully');
  };

  // Handle execute now
  const handleExecuteNow = async (job) => {
    setExecutingJob(job);
    setOpenExecuteDialog(true);
  };

  // Handle confirm execute
  const handleConfirmExecute = async (executeData, resetExecutingState) => {
    try {
      const payload = {
        mapref: executingJob.MAPREF,
        loadType: executeData.loadType
      };

      // Add history load specific parameters
      if (executeData.loadType === 'history') {
        payload.startDate = executeData.startDate;
        payload.endDate = executeData.endDate;
        payload.truncateLoad = executeData.truncateLoad ? 'Y' : 'N';
      }

      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/schedule-job-immediately`,
        payload
      );

      if (response.data.success) {
        setSuccessMessage(response.data.message);
        // Refresh the jobs list
        fetchJobs();
      } else {
        setError(response.data.message || 'Failed to execute job');
      }
    } catch (err) {
      console.error('Error executing job:', err);
      setError(err.response?.data?.message || 'Failed to execute job. Please try again.');
    } finally {
      // Reset the executing state in the dialog if callback is provided
      if (resetExecutingState && typeof resetExecutingState === 'function') {
        resetExecutingState();
      }
      setOpenExecuteDialog(false);
      setExecutingJob(null);
    }
  };

  // New handler for enable/disable job
  const handleEnableDisableJob = (job) => {
    // Check if job has dependencies - if any other job depends on this one
    const hasDependers = jobs.some(j => j.DPND_MAPREF === job.MAPREF);
    
    // If job is currently enabled (scheduled) and has dependers, show warning but don't proceed
    if (job.JOB_SCHEDULE_STATUS === 'Scheduled' && hasDependers) {
      setError('This job cannot be disabled as other jobs depend on it');
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    setJobToToggle({...job, hasDependers});
    setIsEnabling(job.JOB_SCHEDULE_STATUS !== 'Scheduled');
    setOpenEnableDisableDialog(true);
  };

  // Handler for confirming enable/disable
  const handleConfirmEnableDisable = async () => {
    try {
      const action = isEnabling ? 'E' : 'D'; // E for enable, D for disable
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/enable_disable_job`,
        { 
          MAPREF: jobToToggle.MAPREF,
          JOB_FLG: action
        }
      );

      if (response.data.success) {
        setSuccessMessage(response.data.message);
        
        // Update job status in the jobs list
        setJobs(prevJobs => 
          prevJobs.map(job => 
            job.MAPREF === jobToToggle.MAPREF 
              ? { 
                  ...job, 
                  JOB_SCHEDULE_STATUS: isEnabling ? 'Scheduled' : 'Not Scheduled'
                } 
              : job
          )
        );
        
        // Refresh the jobs list to get updated status
        fetchJobs();
      } else {
        setError(response.data.message || `Failed to ${isEnabling ? 'enable' : 'disable'} job`);
      }
    } catch (err) {
      console.error(`Error ${isEnabling ? 'enabling' : 'disabling'} job:`, err);
      setError(err.response?.data?.message || `Failed to ${isEnabling ? 'enable' : 'disable'} job. Please try again.`);
    } finally {
      setOpenEnableDisableDialog(false);
      setJobToToggle(null);
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
        {/* Filters */}
        <FiltersContainer darkMode={darkMode} sx={{ mb: 0, flexGrow: 1, mr: 1.5 }}>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '8px', width: '100%', alignItems: 'center' }}>
            <StyledSearchField
              placeholder="Search jobs..."
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: '0.9rem' }} />
                  </InputAdornment>
                ),
              }}
              darkMode={darkMode}
              sx={{ flexGrow: 1, minWidth: { xs: '100%', sm: '180px' } }}
            />
            
            <StyledFormControl size="small" darkMode={darkMode}>
              <InputLabel sx={{ fontSize: '0.75rem' }}>Table Type</InputLabel>
              <Select
                value={tableTypeFilter}
                onChange={handleTableTypeFilterChange}
                label="Table Type"
                MenuProps={{
                  PaperProps: {
                    sx: { maxHeight: 200 }
                  }
                }}
              >
                <MenuItem value="">All Types</MenuItem>
                {tableTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
            </StyledFormControl>
            
            <StyledFormControl size="small" darkMode={darkMode}>
              <InputLabel sx={{ fontSize: '0.75rem' }}>Status</InputLabel>
              <Select
                value={scheduleStatusFilter}
                onChange={handleScheduleStatusFilterChange}
                label="Status"
                MenuProps={{
                  PaperProps: {
                    sx: { maxHeight: 200 }
                  }
                }}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="Scheduled">Scheduled</MenuItem>
                <MenuItem value="Not Scheduled">Not Scheduled</MenuItem>
              </Select>
            </StyledFormControl>
            
            <Box sx={{ display: 'flex', gap: '6px' }}>
              <StyledButton
                variant="outlined"
                size="small"
                onClick={clearAllFilters}
                darkMode={darkMode}
                sx={{ fontSize: '0.75rem', height: '32px' }}
              >
                Clear
              </StyledButton>
              
              <StyledButton
                variant="contained"
                color="primary"
                startIcon={<RefreshIcon sx={{ fontSize: '1rem' }} />}
                onClick={handleRefresh}
                darkMode={darkMode}
                sx={{ height: '32px', fontSize: '0.75rem' }}
              >
                Refresh
              </StyledButton>
            </Box>
          </Box>
        </FiltersContainer>
      </Box>

      {/* Success/Error Messages */}
      <Collapse in={!!error || !!successMessage}>
        <Box sx={{ mb: 2 }}>
          {error && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
              }}
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}
          {successMessage && (
            <Alert 
              severity="success"
              sx={{ 
                mb: 2,
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)'
              }}
              onClose={() => setSuccessMessage(null)}
            >
              {successMessage}
            </Alert>
          )}
        </Box>
      </Collapse>

      {/* Jobs table */}
      {loading ? (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          height: '50vh',
          flexDirection: 'column',
          gap: 2
        }}>
          <CircularProgress size={60} thickness={4} />
          <Typography variant="h6" sx={{ mt: 2 }}>Loading jobs...</Typography>
        </Box>
      ) : jobs.length === 0 ? (
        <Paper 
          elevation={0}
          sx={{ 
            p: 4, 
            textAlign: 'center',
            borderRadius: '12px',
            backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.6)' : 'rgba(249, 250, 251, 0.8)',
            backdropFilter: 'blur(8px)',
            border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
          }}
        >
          <Typography variant="h5" sx={{ mb: 2 }}>No jobs found</Typography>
          <Typography color="textSecondary">
            Try clearing filters or refreshing the page
          </Typography>
        </Paper>
      ) : (
        <Box
          ref={contentRef}
          sx={{ 
            overflow: 'auto', 
            flexGrow: 1,
            maxHeight: 'calc(100vh - 130px)',
            position: 'relative',
            '&::-webkit-scrollbar': {
              width: '8px',
              height: '8px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: darkMode ? 'rgba(15, 23, 42, 0.3)' : 'rgba(243, 244, 246, 0.5)',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.5)' : 'rgba(59, 130, 246, 0.3)',
              borderRadius: '4px',
              '&:hover': {
                backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.7)' : 'rgba(59, 130, 246, 0.5)',
              }
            }
          }}
        >
          <StyledTableContainer darkMode={darkMode}>
            <Table stickyHeader size="small" aria-label="jobs table">
              <TableHead>
                <TableRow>
                  {columns.map((column) => (
                    <TableCell
                      key={column.id}
                      align={column.id === 'actions' || column.id === 'STATUS' || column.id === 'view' ? 'center' : 'left'}
                      sx={{ 
                        width: column.width,
                        px: column.id === 'actions' || column.id === 'view' ? 1 : 2,
                        position: 'sticky',
                        top: 0,
                        zIndex: 1,
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        whiteSpace: 'nowrap',
                        backgroundColor: darkMode ? '#1A202C' : '#F7FAFC'
                      }}
                    >
                      {column.label}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredJobs.map((job) => {
                  return (
                    <React.Fragment key={job.JOBID}>
                      <TableRow hover>
                        {/* Job Details - Mapping Reference */}
                        <TableCell sx={{ py: 0.5 }}>
                          <MappingDetails
                            mapRef={job.MAPREF}
                            darkMode={darkMode}
                          />
                        </TableCell>

                        {/* Target Table Details */}
                        <TableCell sx={{ py: 0.5 }}>
                          <TargetTableDisplay
                            targetSchema={job.TRGSCHM}
                            targetTable={job.TRGTBNM}
                            tableType={job.TRGTBTYP}
                            darkMode={darkMode}
                          />
                        </TableCell>

                        {/* Status - Display as icon */}
                        <TableCell align="center" sx={{ py: 0.5 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                            <StatusChip 
                              status={job.JOB_SCHEDULE_STATUS} 
                              darkMode={darkMode} 
                            />
                          </Box>
                        </TableCell>

                        {/* Schedule Configuration */}
                        <TableCell sx={{ py: 0.5 }}>
                          <InlineScheduleConfig
                            jobId={job.JOBFLWID}
                            scheduleData={scheduleData}
                            handleScheduleChange={handleScheduleChange}
                            handleDateChange={handleDateChange}
                            handleSaveSchedule={handleSaveSchedule}
                            isScheduled={job.JOB_SCHEDULE_STATUS === 'Scheduled'}
                            darkMode={darkMode}
                            scheduleLoading={scheduleLoading}
                            scheduleSaving={scheduleSaving}
                          />
                        </TableCell>
                        
                        {/* Schedule Summary */}
                        <TableCell sx={{ py: 0.5 }}>
                          <ScheduleSummary
                            scheduleData={scheduleData}
                            jobId={job.JOBFLWID}
                            darkMode={darkMode}
                            job={job}
                          />
                        </TableCell>
                        
                        {/* Dependency */}
                        <TableCell sx={{ py: 0.5 }}>
                          <DependencyDisplay
                            jobId={job.JOBFLWID}
                            mapRef={job.MAPREF}
                            dependency={job.DPND_MAPREF}
                            darkMode={darkMode}
                            onDependencyUpdated={(dependencyMapRef) => handleDependencyUpdated(job.JOBFLWID, dependencyMapRef)}
                            job={job}
                            allJobs={jobs}
                          />
                        </TableCell>
                        
                        {/* View Column */}
                        <TableCell align="center" sx={{ py: 0.5 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                            <Tooltip title="View Details">
                              <ActionButton
                                size="small"
                                color="primary"
                                darkMode={darkMode}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleViewDetails(job);
                                }}
                              >
                                <VisibilityIcon fontSize="small" sx={{ fontSize: 16 }} />
                              </ActionButton>
                            </Tooltip>

                            <Tooltip title="View SQL Logic">
                              <ActionButton
                                size="small"
                                color="info"
                                darkMode={darkMode}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleViewLogic(job);
                                }}
                              >
                                <CodeIcon fontSize="small" sx={{ fontSize: 16 }} />
                              </ActionButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                        
                        {/* Actions */}
                        <TableCell align="center" sx={{ py: 0.5 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                            <Tooltip title="Execute Now">
                              <ActionButton
                                size="small"
                                color="secondary"
                                darkMode={darkMode}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleExecuteNow(job);
                                }}
                              >
                                <PlayArrowIcon fontSize="small" sx={{ fontSize: 16 }} />
                              </ActionButton>
                            </Tooltip>

                            <Tooltip title={job.JOB_SCHEDULE_STATUS === 'Scheduled' ? "Disable Job" : "Enable Job"}>
                              <ActionButton
                                size="small"
                                color={job.JOB_SCHEDULE_STATUS === 'Scheduled' ? "success" : "error"}
                                darkMode={darkMode}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleEnableDisableJob(job);
                                }}
                              >
                                {job.JOB_SCHEDULE_STATUS === 'Scheduled' ? 
                                  <ToggleOnIcon fontSize="small" sx={{ fontSize: 16, color: '#2E7D32' }} /> :
                                  <ToggleOffIcon fontSize="small" sx={{ fontSize: 16, color: '#D32F2F' }} />
                                }
                              </ActionButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  );
                })}
                {filteredJobs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
                      {searchTerm || tableTypeFilter || scheduleStatusFilter ? (
                        <Typography variant="body1" color={darkMode ? 'gray.300' : 'gray.600'}>
                          No matching jobs found with current filters
                        </Typography>
                      ) : (
                        <Typography variant="body1" color={darkMode ? 'gray.300' : 'gray.600'}>
                          No jobs found
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </StyledTableContainer>
        </Box>
      )}
      
      {/* Scroll to top button */}
      <Fade in={showScrollTop}>
        <ScrollToTopButton
          size="small"
          aria-label="scroll to top"
          onClick={scrollToTop}
          darkMode={darkMode}
        >
          <KeyboardArrowUpIcon />
        </ScrollToTopButton>
      </Fade>

      {/* Job Details Dialog */}
      <JobDetailsDialog 
        open={openDialog}
        onClose={handleCloseDialog}
        job={selectedJob}
        allJobs={jobs}
      />

      {/* Job Logic Dialog */}
      <LogicViewDialog
        open={openLogicDialog}
        onClose={handleCloseLogicDialog}
        job={selectedJob}
      />

      {/* Execute Job Dialog */}
      <ExecuteJobDialog
        open={openExecuteDialog}
        onClose={() => {
          // Only close the dialog if the job is not currently executing
          // This is a safety measure in addition to the disabled button
          setOpenExecuteDialog(false);
        }}
        job={executingJob}
        onConfirm={handleConfirmExecute}
      />

      {/* Enable/Disable Job Dialog */}
      <EnableDisableJobDialog
        open={openEnableDisableDialog}
        onClose={() => setOpenEnableDisableDialog(false)}
        job={jobToToggle}
        isEnabling={isEnabling}
        onConfirm={handleConfirmEnableDisable}
      />

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          sx={{
            width: '100%',
            borderRadius: '8px',
            boxShadow: darkMode ? '0 4px 12px rgba(0, 0, 0, 0.3)' : '0 4px 12px rgba(0, 0, 0, 0.15)',
            backgroundColor: darkMode ? 
              (notification.severity === 'warning' ? 'rgba(234, 179, 8, 0.15)' : 'rgba(17, 24, 39, 0.95)') :
              undefined,
            border: darkMode ? 
              (notification.severity === 'warning' ? '1px solid rgba(234, 179, 8, 0.3)' : '1px solid rgba(255, 255, 255, 0.1)') :
              undefined,
            '& .MuiAlert-icon': {
              color: darkMode && notification.severity === 'warning' ? '#FBBF24' : undefined
            },
            '& .MuiAlert-message': {
              color: darkMode ? '#E2E8F0' : undefined
            }
          }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </motion.div>
    </LocalizationProvider>
  );
};

export default JobsPage;

// Logic View Dialog Component
const LogicViewDialog = ({ open, onClose, job }) => {
  const { darkMode } = useTheme();
  
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: darkMode ? '#1E293B' : 'white',
          backgroundImage: darkMode ? 
            'linear-gradient(to bottom, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))' : 
            'none',
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: darkMode ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }
      }}
    >
      <DialogTitle sx={{ 
        backgroundColor: darkMode ? '#1A202C' : '#F9FAFB', 
        color: darkMode ? 'white' : '#1A202C',
        borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        px: 3,
        py: 1.5
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <CodeIcon sx={{ mr: 1.5, color: darkMode ? 'primary.main' : 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 500, fontSize: '1rem' }}>
        SQL Logic for Job ID: {job?.JOBID}
          </Typography>
        </Box>
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: darkMode ? 'white' : 'grey.500',
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ mt: 2, p: 3, color: darkMode ? 'white' : 'text.primary' }}>
        <Paper
          elevation={darkMode ? 2 : 1}
          sx={{
            p: 1.5,
            backgroundColor: darkMode ? '#2D3748' : '#F7FAFC',
            border: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.07)',
            borderRadius: 1.5,
            maxHeight: '60vh',
            overflow: 'auto'
          }}
        >
          <pre
            style={{
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: '"Roboto Mono", "Consolas", monospace',
              fontSize: '13px',
              color: darkMode ? '#E2E8F0' : '#2D3748',
              padding: '8px'
            }}
          >
            {job?.DWLOGIC || 'No SQL logic available for this job.'}
          </pre>
        </Paper>
      </DialogContent>
      <DialogActions sx={{ 
        backgroundColor: darkMode ? '#1A202C' : '#F9FAFB',
        borderTop: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        px: 3,
        py: 1.5
      }}>
        <Button 
          onClick={onClose} 
          variant="contained" 
          color="primary"
          size="small"
          sx={{ 
            borderRadius: 1.5,
            py: 0.5,
            px: 2,
            fontSize: '0.8125rem'
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Execute Job Dialog Component
const ExecuteJobDialog = ({ open, onClose, job, onConfirm }) => {
  const { darkMode } = useTheme();
  const [loadType, setLoadType] = useState('regular');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [truncateLoad, setTruncateLoad] = useState(false);
  const [errors, setErrors] = useState({});
  const [isExecuting, setIsExecuting] = useState(false);

  // Reset form when dialog opens/closes
  useEffect(() => {
    if (open) {
      setLoadType('regular');
      setStartDate('');
      setEndDate('');
      setTruncateLoad(false);
      setErrors({});
      setIsExecuting(false);
    }
  }, [open]);

  const validateForm = () => {
    const newErrors = {};
    
    if (loadType === 'history') {
      if (!startDate) {
        newErrors.startDate = 'Start date is required for history load';
      }
      if (!endDate) {
        newErrors.endDate = 'End date is required for history load';
      }
      if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
        newErrors.endDate = 'End date must be after start date';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleExecute = () => {
    if (isExecuting) return; // Prevent multiple clicks
    
    if (validateForm()) {
      setIsExecuting(true); // Disable the button
      const executeData = {
        loadType,
        startDate: loadType === 'history' ? startDate : null,
        endDate: loadType === 'history' ? endDate : null,
        truncateLoad: loadType === 'history' ? truncateLoad : false
      };
      
      // Pass the reset callback along with the data
      onConfirm(executeData, () => setIsExecuting(false));
    }
  };

  return (
    <Dialog
      open={open}
      onClose={(event, reason) => {
        // Only allow closing if not executing
        if (!isExecuting && reason !== 'backdropClick' && reason !== 'escapeKeyDown') {
          onClose();
        }
      }}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: darkMode ? '#1E293B' : 'white',
          backgroundImage: darkMode ? 
            'linear-gradient(to bottom, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))' : 
            'none',
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: darkMode ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }
      }}
    >
      <DialogTitle sx={{ 
        backgroundColor: darkMode ? '#1A202C' : '#F9FAFB', 
        color: darkMode ? 'white' : '#1A202C',
        borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        px: 3,
        py: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <PlayArrowIcon sx={{ mr: 1, color: darkMode ? '#60A5FA' : '#3B82F6' }} />
          <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1.1rem' }}>
            Execute Job
          </Typography>
        </Box>
        {job && (
          <Box sx={{ ml: 4 }}>
            <Typography variant="body2" sx={{ 
              color: darkMode ? '#E2E8F0' : '#4A5568',
              fontWeight: 500,
              fontSize: '0.875rem'
            }}>
              {job.MAPREF}
            </Typography>
            <Typography variant="body2" sx={{ 
              color: darkMode ? '#A0AEC0' : '#718096',
              fontSize: '0.8125rem',
              mt: 0.5
            }}>
              Target: {job.TRGSCHM}.{job.TRGTBNM} ({job.TRGTBTYP})
            </Typography>
          </Box>
        )}
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: darkMode ? 'white' : 'grey.500',
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ mt: 2, p: 3, color: darkMode ? 'white' : 'text.primary' }}>
        {/* Load Type Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
            Load Type
          </Typography>
          <FormControl component="fieldset">
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant={loadType === 'regular' ? 'contained' : 'outlined'}
                onClick={() => setLoadType('regular')}
                sx={{
                  borderRadius: 1.5,
                  px: 3,
                  py: 1,
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  backgroundColor: loadType === 'regular' ? (darkMode ? '#3B82F6' : '#3B82F6') : 'transparent',
                  borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
                  color: loadType === 'regular' ? 'white' : (darkMode ? '#E2E8F0' : '#4A5568'),
                  '&:hover': {
                    backgroundColor: loadType === 'regular' ? (darkMode ? '#2563EB' : '#2563EB') : (darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)')
                  }
                }}
              >
                Regular Load
              </Button>
              <Button
                variant={loadType === 'history' ? 'contained' : 'outlined'}
                onClick={() => setLoadType('history')}
                sx={{
                  borderRadius: 1.5,
                  px: 3,
                  py: 1,
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  backgroundColor: loadType === 'history' ? (darkMode ? '#3B82F6' : '#3B82F6') : 'transparent',
                  borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
                  color: loadType === 'history' ? 'white' : (darkMode ? '#E2E8F0' : '#4A5568'),
                  '&:hover': {
                    backgroundColor: loadType === 'history' ? (darkMode ? '#2563EB' : '#2563EB') : (darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)')
                  }
                }}
              >
                History Load
              </Button>
            </Box>
          </FormControl>
        </Box>

        {/* Regular Load Description */}
        {loadType === 'regular' && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ mb: 1, fontSize: '0.9375rem' }}>
              Regular Load will execute the job with its standard configuration.
            </Typography>
            <Typography variant="body2" sx={{ 
              color: darkMode ? '#A0AEC0' : '#718096',
              fontSize: '0.8125rem',
              fontStyle: 'italic'
            }}>
              This will trigger the job execution outside of its scheduled time.
            </Typography>
          </Box>
        )}

        {/* History Load Configuration */}
        {loadType === 'history' && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ mb: 2, fontSize: '0.9375rem' }}>
              History Load allows you to process data for a specific date range.
            </Typography>
            
                         <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
               {/* Date Range */}
               <Box sx={{ display: 'flex', gap: 2 }}>
                 <Box sx={{ flex: 1 }}>
                   <Typography variant="caption" sx={{ 
                     display: 'block', 
                     mb: 0.5, 
                     color: darkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
                     fontWeight: 500,
                     fontSize: '0.75rem'
                   }}>
                     Start Date
                   </Typography>
                   <DatePicker 
                     value={startDate ? new Date(startDate) : null}
                     onChange={(date) => {
                       if (date) {
                         // Fix timezone issue by using a proper date formatting approach
                         const year = date.getFullYear();
                         const month = String(date.getMonth() + 1).padStart(2, '0');
                         const day = String(date.getDate()).padStart(2, '0');
                         setStartDate(`${year}-${month}-${day}`);
                       } else {
                         setStartDate('');
                       }
                     }}
                     slotProps={{
                       textField: {
                         size: "small",
                         fullWidth: true,
                         error: !!errors.startDate,
                         helperText: errors.startDate,
                         InputProps: {
                           sx: {
                             fontSize: '0.8125rem',
                             height: '36px',
                             backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                             borderRadius: '6px',
                             '& fieldset': {
                               borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
                             },
                             '&:hover fieldset': {
                               borderColor: darkMode ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)',
                             },
                           }
                         },
                         InputLabelProps: {
                           sx: {
                             color: darkMode ? '#E2E8F0' : '#4A5568',
                             fontSize: '0.8125rem'
                           }
                         }
                       }
                     }}
                   />
                 </Box>
                 <Box sx={{ flex: 1 }}>
                   <Typography variant="caption" sx={{ 
                     display: 'block', 
                     mb: 0.5, 
                     color: darkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.6)',
                     fontWeight: 500,
                     fontSize: '0.75rem'
                   }}>
                     End Date
                   </Typography>
                   <DatePicker 
                     value={endDate ? new Date(endDate) : null}
                     onChange={(date) => {
                       if (date) {
                         // Fix timezone issue by using a proper date formatting approach
                         const year = date.getFullYear();
                         const month = String(date.getMonth() + 1).padStart(2, '0');
                         const day = String(date.getDate()).padStart(2, '0');
                         setEndDate(`${year}-${month}-${day}`);
                       } else {
                         setEndDate('');
                       }
                     }}
                     minDate={startDate ? new Date(startDate) : undefined}
                     slotProps={{
                       textField: {
                         size: "small",
                         fullWidth: true,
                         error: !!errors.endDate,
                         helperText: errors.endDate,
                         InputProps: {
                           sx: {
                             fontSize: '0.8125rem',
                             height: '36px',
                             backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                             borderRadius: '6px',
                             '& fieldset': {
                               borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
                             },
                             '&:hover fieldset': {
                               borderColor: darkMode ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)',
                             },
                           }
                         },
                         InputLabelProps: {
                           sx: {
                             color: darkMode ? '#E2E8F0' : '#4A5568',
                             fontSize: '0.8125rem'
                           }
                         }
                       }
                     }}
                   />
                 </Box>
               </Box>

              {/* Truncate Load Option */}
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <input
                  type="checkbox"
                  id="truncateLoad"
                  checked={truncateLoad}
                  onChange={(e) => setTruncateLoad(e.target.checked)}
                  style={{
                    marginRight: '8px',
                    accentColor: darkMode ? '#3B82F6' : '#3B82F6'
                  }}
                />
                <label htmlFor="truncateLoad" style={{ 
                  fontSize: '0.875rem',
                  color: darkMode ? '#E2E8F0' : '#4A5568',
                  cursor: 'pointer'
                }}>
                  Truncate & Load (Clear target table before loading data)
                </label>
              </Box>
            </Box>
          </Box>
        )}
      </DialogContent>
      <DialogActions sx={{ 
        backgroundColor: darkMode ? '#1A202C' : '#F9FAFB',
        borderTop: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        px: 3,
        py: 2,
        gap: 1
      }}>
        <Button 
          onClick={onClose} 
          variant="outlined"
          size="small"
          disabled={isExecuting}
          sx={{ 
            borderRadius: 1.5,
            py: 0.75,
            px: 2.5,
            fontSize: '0.8125rem',
            borderColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
            color: darkMode ? '#E2E8F0' : '#4A5568',
            '&:hover': {
              borderColor: darkMode ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)',
              backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'
            }
          }}
        >
          Cancel
        </Button>
        <Button 
          onClick={handleExecute} 
          variant="contained" 
          color="primary"
          size="small"
          disabled={isExecuting}
          startIcon={isExecuting ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon sx={{ fontSize: '1rem' }} />}
          sx={{ 
            borderRadius: 1.5,
            py: 0.75,
            px: 2.5,
            fontSize: '0.8125rem',
            fontWeight: 600
          }}
        >
          {isExecuting ? 'Executing...' : `Execute ${loadType === 'history' ? 'History Load' : 'Now'}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Enable/Disable Job Dialog Component
const EnableDisableJobDialog = ({ open, onClose, job, isEnabling, onConfirm }) => {
  const { darkMode } = useTheme();
  
  // Check if this is a job with dependents (other jobs that depend on it)
  const hasDependers = job?.hasDependers;
  
  // Warning message if trying to disable a job with dependents
  const warningMessage = !isEnabling && hasDependers ? 
    "Warning: Other jobs depend on this job. Disabling it may cause dependent jobs to fail." : null;
  
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: darkMode ? '#1E293B' : 'white',
          backgroundImage: darkMode ? 
            'linear-gradient(to bottom, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))' : 
            'none',
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: darkMode ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }
      }}
    >
      <DialogTitle sx={{ 
        backgroundColor: darkMode ? '#1A202C' : '#F9FAFB', 
        color: darkMode ? 'white' : '#1A202C',
        borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        px: 3,
        py: 1.5
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {!isEnabling && (
            <ToggleOffIcon sx={{ mr: 1.5, color: warningMessage ? 'warning.main' : (darkMode ? 'primary.light' : 'primary.main') }} />
          )}
          {isEnabling && (
            <ToggleOnIcon sx={{ mr: 1.5, color: darkMode ? 'success.light' : 'success.main' }} />
          )}
          <Typography variant="h6" sx={{ fontWeight: 500, fontSize: '1rem' }}>
            {isEnabling ? 'Enable' : 'Disable'} Job: {job?.MAPREF}
          </Typography>
        </Box>
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: darkMode ? 'white' : 'grey.500',
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ mt: 2, p: 3, color: darkMode ? 'white' : 'text.primary' }}>
        <Typography variant="body1" sx={{ mb: warningMessage ? 1 : 2 }}>
          Are you sure you want to {isEnabling ? 'enable' : 'disable'} this job?
        </Typography>
        
        {warningMessage && (
          <Alert 
            severity="warning" 
            sx={{ 
              mb: 2, 
              borderRadius: 2,
              backgroundColor: darkMode ? 'rgba(234, 179, 8, 0.15)' : 'rgba(234, 179, 8, 0.08)',
              border: '1px solid',
              borderColor: darkMode ? 'rgba(234, 179, 8, 0.3)' : 'rgba(234, 179, 8, 0.2)',
              '& .MuiAlert-icon': {
                color: darkMode ? 'warning.light' : 'warning.main'
              }
            }}
          >
            {warningMessage}
          </Alert>
        )}
        
        <Button 
          onClick={onConfirm} 
          variant="contained" 
          color={isEnabling ? "success" : "primary"}
          size="small"
          sx={{ 
            borderRadius: 1.5,
            py: 0.5,
            px: 2,
            fontSize: '0.8125rem'
          }}
        >
          {isEnabling ? 'Enable' : 'Disable'}
        </Button>
      </DialogContent>
      <DialogActions sx={{ 
        backgroundColor: darkMode ? '#1A202C' : '#F9FAFB',
        borderTop: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        px: 3,
        py: 1.5
      }}>
        <Button 
          onClick={onClose} 
          variant="contained" 
          color="primary"
          size="small"
          sx={{ 
            borderRadius: 1.5,
            py: 0.5,
            px: 2,
            fontSize: '0.8125rem'
          }}
        >
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};
