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
  Checkbox,
  Stack,
  Switch
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
  RemoveRedEye as EyeIcon,
  Schedule as ScheduleIcon
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
  DependencyDisplay,
  ScheduleDialog
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
  const fetchingScheduleRef = useRef(new Set()); // Track which jobs are currently being fetched to prevent duplicates
  const [scheduleSaving, setScheduleSaving] = useState({});
  
  // State for schedule dialog
  const [scheduleDialog, setScheduleDialog] = useState({ open: false, job: null });
  
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
      
      // Normalize job data - ensure JOB_SCHEDULE_STATUS is always 'Scheduled' or 'Not Scheduled'
      jobsData.forEach(job => {
        // Normalize JOB_SCHEDULE_STATUS to always be 'Scheduled' or 'Not Scheduled'
        if (!job.JOB_SCHEDULE_STATUS || (job.JOB_SCHEDULE_STATUS !== 'Scheduled' && job.JOB_SCHEDULE_STATUS !== 'Not Scheduled')) {
          // If job has JOBSCHID or is marked as scheduled, set to 'Scheduled', otherwise 'Not Scheduled'
          job.JOB_SCHEDULE_STATUS = (job.JOBSCHID || job.JOB_SCHEDULE_STATUS === 'Scheduled') ? 'Scheduled' : 'Not Scheduled';
        }
      });
      
      // Initialize schedule data for each job from the response
      const initialScheduleData = {};
      
      // Helper function to get field value with case-insensitive lookup
      // Backend normalizes column names to uppercase, so "Frequency code" becomes "FREQUENCY CODE"
      const getField = (job, fieldName) => {
        // Try exact match first
        if (job[fieldName] !== undefined) return job[fieldName];
        // Try uppercase (backend normalization)
        if (job[fieldName.toUpperCase()] !== undefined) return job[fieldName.toUpperCase()];
        // Try lowercase
        if (job[fieldName.toLowerCase()] !== undefined) return job[fieldName.toLowerCase()];
        // Try with underscores instead of spaces
        const underscoreName = fieldName.replace(/\s+/g, '_');
        if (job[underscoreName] !== undefined) return job[underscoreName];
        if (job[underscoreName.toUpperCase()] !== undefined) return job[underscoreName.toUpperCase()];
        if (job[underscoreName.toLowerCase()] !== undefined) return job[underscoreName.toLowerCase()];
        return null;
      };
      
      jobsData.forEach(job => {
        
        // Build TIMEPARAM from frequency fields if available
        // Backend normalizes column names to uppercase, so "Frequency code" becomes "FREQUENCY CODE"
        const frequencyCode = getField(job, "Frequency code") || job.FRQCD || null;
        const frequencyDay = getField(job, "Frequency day") || job.FRQDD || null;
        const frequencyHour = getField(job, "frequency hour") || job.FRQHH || null;
        // Note: API returns "frequency month" but it's actually FRQMI (frequency minute), not month
        // FRQMI represents minutes (0-59), not months
        const frequencyMinute = getField(job, "frequency month") || job["frequency_minute"] || job.FRQMI || null;
        
        let timeParam = '';
        if (frequencyCode) {
          timeParam = frequencyCode;
          if (frequencyDay) {
            timeParam += `_${frequencyDay}`;
          }
          if (frequencyHour !== undefined && frequencyHour !== null && frequencyMinute !== undefined && frequencyMinute !== null) {
            timeParam += `_${String(frequencyHour).padStart(2, '0')}:${String(frequencyMinute).padStart(2, '0')}`;
          } else if (frequencyHour !== undefined && frequencyHour !== null) {
            timeParam += `_${String(frequencyHour).padStart(2, '0')}:00`;
          }
        }
        
        // Store dates from initial job data - check multiple possible field names (case-insensitive)
        // Backend normalizes to uppercase, so "last run" becomes "LAST RUN"
        const lastRunDate = getField(job, "last run") || job["last_run"] || job.LST_RUN_DT || job.last_run || job.LAST_RUN_DT || null;
        const nextRunDate = getField(job, "next run") || job["next_run"] || job.NXT_RUN_DT || job.next_run || job.NEXT_RUN_DT || null;
        
        // Debug logging for scheduled jobs - especially for DIM_ACNT_LN2
        if (job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID || job.MAPREF === 'DIM_ACNT_LN2') {
          console.log(`[fetchJobs] Job ${job.MAPREF} (${job.JOBFLWID}) schedule data:`, {
            JOB_SCHEDULE_STATUS: job.JOB_SCHEDULE_STATUS,
            JOBSCHID: job.JOBSCHID,
            frequencyCode: frequencyCode,
            frequencyDay: frequencyDay,
            frequencyHour: frequencyHour,
            frequencyMinute: frequencyMinute,
            lastRunDate: lastRunDate,
            nextRunDate: nextRunDate,
            allJobKeys: Object.keys(job),
            // Check all possible field name variations
            fieldChecks: {
              "Frequency code": job["Frequency code"],
              "FREQUENCY CODE": job["FREQUENCY CODE"],
              "last run": job["last run"],
              "LAST RUN": job["LAST RUN"],
              "next run": job["next run"],
              "NEXT RUN": job["NEXT RUN"],
              FRQCD: job.FRQCD,
              LST_RUN_DT: job.LST_RUN_DT,
              NXT_RUN_DT: job.NXT_RUN_DT
            },
            initialScheduleData: initialScheduleData[job.JOBFLWID]
          });
        }
        
        initialScheduleData[job.JOBFLWID] = {
          JOBFLWID: job.JOBFLWID,
          MAPREF: job.MAPREF || '',
          TIMEPARAM: timeParam,
          STRT_DT: getField(job, "start date") || job["start_date"] || job.STRT_DT || null,
          END_DT: getField(job, "end date") || job["end_date"] || job.END_DT || null,
          STFLG: job.STFLG || 'A',
          LST_RUN_DT: lastRunDate,
          NXT_RUN_DT: nextRunDate,
          FRQCD: frequencyCode,
          FRQDD: frequencyDay,
          FRQHH: frequencyHour,
          // FRQMI is minutes (0-59), NOT months - API incorrectly names it "frequency month"
          FRQMI: frequencyMinute
        };
      });
      
      setJobs(jobsData);
      setScheduleData(initialScheduleData);
      setError(null);
      
      // After getting all jobs, fetch schedule details for scheduled jobs only
      // Batch the API calls to avoid overwhelming the network (max 5 concurrent)
      setTimeout(() => {
        const scheduledJobs = jobsData.filter(job => job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID);
        
        // Batch process: fetch 5 jobs at a time with delays
        const batchSize = 5;
        const delayBetweenBatches = 500; // 500ms between batches
        
        scheduledJobs.forEach((job, index) => {
          setTimeout(() => {
            fetchJobScheduleDetails(job.JOBFLWID);
          }, Math.floor(index / batchSize) * delayBetweenBatches);
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
    // Prevent duplicate requests for the same job
    if (fetchingScheduleRef.current.has(jobId)) {
      console.log(`[fetchJobScheduleDetails] Already fetching schedule for job ${jobId}, skipping duplicate request`);
      return;
    }
    
    // Get the job from the jobs list - use current jobs state
    const currentJobs = jobs.length > 0 ? jobs : [];
    const job = currentJobs.find(j => j.JOBFLWID === jobId);
    if (!job && jobs.length === 0) {
      // If jobs haven't loaded yet, wait a bit and try again
      setTimeout(() => fetchJobScheduleDetails(jobId), 500);
      return;
    }
    if (!job) {
      console.warn(`Job with JOBFLWID ${jobId} not found in jobs list`);
      return;
    }
    
    // Mark as fetching
    fetchingScheduleRef.current.add(jobId);
    
    // Set loading state for this specific job
    setScheduleLoading(prev => ({ ...prev, [jobId]: true }));
    
    try {
      console.log(`Fetching schedule details for job ${jobId}`);
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_job_schedule_details/${jobId}`);
      console.log('API Response:', response.data);
      
      // Check if there's schedule data - handle both array and object responses
      let scheduleDetails = null;
      if (response.data) {
        if (Array.isArray(response.data) && response.data.length > 0) {
          scheduleDetails = response.data[0];
        } else if (typeof response.data === 'object' && !Array.isArray(response.data)) {
          scheduleDetails = response.data;
        }
      }
      
      // Debug log for scheduled jobs - especially DIM_ACNT_LN2
      if (job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID || job.MAPREF === 'DIM_ACNT_LN2') {
        console.log(`[fetchJobScheduleDetails] Schedule details for scheduled job ${job.MAPREF} (${jobId}):`, {
          hasScheduleDetails: !!scheduleDetails,
          scheduleDetails: scheduleDetails,
          scheduleDetailsKeys: scheduleDetails ? Object.keys(scheduleDetails) : [],
          // Check all possible field name variations (case-insensitive)
          FRQCD: scheduleDetails?.FRQCD || scheduleDetails?.frqcd || scheduleDetails?.["FRQCD"] || scheduleDetails?.["frqcd"],
          LST_RUN_DT: scheduleDetails?.LST_RUN_DT || scheduleDetails?.lst_run_dt || scheduleDetails?.["LST_RUN_DT"] || scheduleDetails?.["lst_run_dt"],
          NXT_RUN_DT: scheduleDetails?.NXT_RUN_DT || scheduleDetails?.nxt_run_dt || scheduleDetails?.["NXT_RUN_DT"] || scheduleDetails?.["nxt_run_dt"],
          jobLastRun: job['last run'] || job["last run"] || job["LAST RUN"],
          jobNextRun: job['next run'] || job["next run"] || job["NEXT RUN"],
          jobFRQCD: job["Frequency code"] || job["FREQUENCY CODE"] || job.FRQCD
        });
      }
      
      // If we have schedule details, process them
      if (scheduleDetails) {
        // Helper to get field value with case-insensitive lookup
        const getScheduleField = (fieldName) => {
          return scheduleDetails[fieldName] || 
                 scheduleDetails[fieldName.toUpperCase()] || 
                 scheduleDetails[fieldName.toLowerCase()] || 
                 null;
        };

        // Get field values with case-insensitive lookup (backend may return uppercase or lowercase)
        const frqcd = getScheduleField("FRQCD");
        const frqdd = getScheduleField("FRQDD");
        const frqhh = getScheduleField("FRQHH");
        const frqmi = getScheduleField("FRQMI");
        const strtdt = getScheduleField("STRTDT") || getScheduleField("STRT_DT");
        const enddt = getScheduleField("ENDDT") || getScheduleField("END_DT");
        const lstRunDt = getScheduleField("LST_RUN_DT");
        const nxtRunDt = getScheduleField("NXT_RUN_DT");
        
        // Fallback: compute next run locally if backend didn't return it
        // Note: FRQMI is minutes (0-59), NOT months
        const computeNextRun = (details) => {
          const freq = details.FRQCD || '';
          // FRQHH is hour (0-23), FRQMI is minute (0-59) - NOT month!
          const hour = details.FRQHH !== undefined && details.FRQHH !== null ? Number(details.FRQHH) : 0;
          const minute = details.FRQMI !== undefined && details.FRQMI !== null ? Number(details.FRQMI) : 0;
          const start = details.STRT_DT || details.STRTDT || null;
          if (!freq || !start) return null;
          const base = new Date(start);
          if (isNaN(base.getTime())) return null;
          // Apply time - hour and minute (FRQMI is minutes, not months!)
          base.setHours(hour || 0, minute || 0, 0, 0);
          const now = new Date();
          let next = base;
          if (next <= now) {
            const addDays = (d) => { const n = new Date(next); n.setDate(n.getDate() + d); return n; };
            switch (freq) {
              case 'WK': next = addDays(7); break;
              case 'FN': next = addDays(14); break;
              case 'MN': next = addDays(30); break; // MN = Monthly, not related to FRQMI
              case 'HY': next = addDays(180); break;
              case 'YR': next = addDays(365); break;
              case 'ID': next = addDays(1); break;
              case 'DL':
              default: next = addDays(1); break;
            }
          }
          return next.toISOString();
        };
        
        // Extract time parameter from individual fields if they exist
        let timeParam = '';
        if (frqcd) {
          timeParam = frqcd;
          
          if (frqdd) {
            timeParam += `_${frqdd}`;
          }
          
          if (frqhh !== undefined && frqhh !== null && frqmi !== undefined && frqmi !== null) {
            timeParam += `_${String(frqhh).padStart(2, '0')}:${String(frqmi).padStart(2, '0')}`;
          } else if (frqhh !== undefined && frqhh !== null) {
            timeParam += `_${String(frqhh).padStart(2, '0')}:00`;
          }
        }
        
        // Compute next run fallback if missing
        const computedNextRun = nxtRunDt || computeNextRun({
          FRQCD: frqcd,
          FRQHH: frqhh,
          FRQMI: frqmi,
          STRT_DT: strtdt,
          STRTDT: strtdt,
        });

        // Update the schedule data with fetched values
        // Handle date fields - API returns STRTDT/ENDDT but we store as STRT_DT/END_DT
        const startDate = strtdt || null;
        const endDate = enddt || null;
        
        setScheduleData(prev => ({
          ...prev,
          [jobId]: {
            ...prev[jobId],
            JOBFLWID: jobId,
            MAPREF: getScheduleField("MAPREF") || job.MAPREF || '',
            TIMEPARAM: timeParam || prev[jobId]?.TIMEPARAM || '',
            STRT_DT: startDate || prev[jobId]?.STRT_DT || null,
            END_DT: endDate || prev[jobId]?.END_DT || null,
            STFLG: getScheduleField("STFLG") || prev[jobId]?.STFLG || '',
            JOB_SCHEDULE_STATUS: job.JOB_SCHEDULE_STATUS,
            LST_RUN_DT: lstRunDt || prev[jobId]?.LST_RUN_DT || null,
            NXT_RUN_DT: computedNextRun || nxtRunDt || prev[jobId]?.NXT_RUN_DT || null,
            // Store frequency components separately for easy access - prioritize API response
            FRQCD: frqcd || prev[jobId]?.FRQCD || job["Frequency code"] || job["FREQUENCY CODE"] || null,
            FRQDD: frqdd || prev[jobId]?.FRQDD || job["Frequency day"] || job["FREQUENCY DAY"] || null,
            FRQHH: (frqhh !== undefined && frqhh !== null) ? frqhh : (prev[jobId]?.FRQHH !== undefined && prev[jobId].FRQHH !== null ? prev[jobId].FRQHH : (job["frequency hour"] || job["FREQUENCY HOUR"] || job.FRQHH || null)),
            // FRQMI is minutes (0-59), NOT months - API incorrectly names it "frequency month"
            FRQMI: (frqmi !== undefined && frqmi !== null) ? frqmi : (prev[jobId]?.FRQMI !== undefined && prev[jobId].FRQMI !== null ? prev[jobId].FRQMI : (job["frequency month"] || job["FREQUENCY MONTH"] || job.FRQMI || null))
          }
        }));
        
        // Always update job data with schedule information so it's available for display
        // This ensures the frequency code is in the job object for getScheduleLabel to find
        setJobs(prevJobs => 
          prevJobs.map(j => 
            j.JOBFLWID === jobId 
              ? { 
                  ...j, 
                  "Frequency code": frqcd || j["Frequency code"] || j["FREQUENCY CODE"] || null,
                  FRQCD: frqcd || j.FRQCD || null, // Also set direct FRQCD field
                  "Frequency day": frqdd || j["Frequency day"] || j["FREQUENCY DAY"] || null,
                  "frequency hour": (frqhh !== undefined && frqhh !== null) ? frqhh : (j["frequency hour"] || j["FREQUENCY HOUR"] || j.FRQHH || null),
                  "frequency month": (frqmi !== undefined && frqmi !== null) ? frqmi : (j["frequency month"] || j["FREQUENCY MONTH"] || j.FRQMI || null),
                  "start date": startDate || j["start date"] || j["START DATE"] || null,
                  "end date": endDate || j["end date"] || j["END DATE"] || null,
                  "last run": lstRunDt || computedNextRun || j["last run"] || j["LAST RUN"] || null,
                  "next run": computedNextRun || nxtRunDt || j["next run"] || j["NEXT RUN"] || null,
                  LST_RUN_DT: lstRunDt || j.LST_RUN_DT || null,
                  NXT_RUN_DT: computedNextRun || nxtRunDt || j.NXT_RUN_DT || null
                } 
              : j
          )
        );
        
        // Debug log after updating - especially for DIM_ACNT_LN2
        if (job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID || job.MAPREF === 'DIM_ACNT_LN2') {
          console.log(`[fetchJobScheduleDetails] Updated job ${job.MAPREF} with schedule data:`, {
            FRQCD: frqcd,
            FRQDD: frqdd,
            FRQHH: frqhh,
            FRQMI: frqmi,
            LST_RUN_DT: lstRunDt,
            NXT_RUN_DT: computedNextRun || nxtRunDt,
            scheduleDataUpdated: scheduleData[jobId]
          });
        }
      } else {
        // Even if no schedule details from API, ensure we preserve any existing dates from job data
        // This is important for scheduled jobs that might have dates in the initial job data
        const existingLastRun = job['last run'] || job["last run"] || null;
        const existingNextRun = job['next run'] || job["next run"] || null;
        
        if (existingLastRun || existingNextRun) {
          setScheduleData(prev => ({
            ...prev,
            [jobId]: {
              ...prev[jobId],
              JOBFLWID: jobId,
              LST_RUN_DT: existingLastRun,
              NXT_RUN_DT: existingNextRun,
            }
          }));
        }
      }
    } catch (err) {
      // Only log network errors if they're not due to insufficient resources (too many requests)
      if (err.code !== 'ERR_NETWORK' || !err.message?.includes('ERR_INSUFFICIENT_RESOURCES')) {
        console.error(`Error fetching job schedule details for job ${jobId}:`, err);
      } else {
        console.warn(`[fetchJobScheduleDetails] Network resource limit reached for job ${jobId}, will retry later`);
      }
      // Even on error, try to preserve dates from job data
      const existingLastRun = getField(job, "last run") || null;
      const existingNextRun = getField(job, "next run") || null;
      
      if (existingLastRun || existingNextRun) {
        setScheduleData(prev => ({
          ...prev,
          [jobId]: {
            ...prev[jobId],
            JOBFLWID: jobId,
            LST_RUN_DT: existingLastRun,
            NXT_RUN_DT: existingNextRun,
          }
        }));
      }
    } finally {
      // Remove from fetching set and clear loading state
      fetchingScheduleRef.current.delete(jobId);
      setScheduleLoading(prev => ({ ...prev, [jobId]: false }));
    }
  };

  // Handle open schedule dialog
  const openScheduleDialog = (job) => {
    setScheduleDialog({ open: true, job });
    // Fetch schedule details when opening dialog to ensure we have the latest data
    if (job && job.JOBFLWID) {
      fetchJobScheduleDetails(job.JOBFLWID);
    }
  };

  // Handle close schedule dialog
  const closeScheduleDialog = () => {
    setScheduleDialog({ open: false, job: null });
  };

  // Handle save schedule from dialog
  const handleSaveScheduleFromDialog = async (jobId, updatedScheduleData) => {
    // Update schedule data first
    setScheduleData(prev => ({
      ...prev,
      [jobId]: updatedScheduleData
    }));
    
    // Then call the existing save schedule handler with the updated data
    // handleSaveSchedule will handle errors and show messages
    const success = await handleSaveSchedule(jobId, updatedScheduleData);
    
    // Only close dialog if save was successful
    if (success) {
      closeScheduleDialog();
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

  // Handle save schedule (save only, doesn't enable)
  const handleSaveSchedule = async (jobId, scheduleDataOverride = null) => {
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
        return false;
      }
      
      // Set saving state for this specific job
      setScheduleSaving(prev => ({ ...prev, [jobId]: true }));
      
      // Use override data if provided, otherwise use state data
      const jobData = scheduleDataOverride || scheduleData[jobId];
      
      // Ensure we have MAPREF - get it from the job if not in schedule data
      if (!jobData || !jobData.MAPREF) {
        const job = jobs.find(j => j.JOBFLWID === jobId);
        if (!job || !job.MAPREF) {
          setError('Job mapping reference (MAPREF) is missing. Cannot save schedule.');
          setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
          return false;
        }
        // Ensure MAPREF is in jobData
        if (!jobData) {
          setError('Schedule data is missing. Cannot save schedule.');
          setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
          return false;
        }
        jobData.MAPREF = job.MAPREF;
      }
      
      // Validate the schedule data before sending to backend
      const validationError = validateScheduleData(jobData);
      if (validationError) {
        setError(validationError);
        setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
        return false;
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
      
      console.log('Saving job schedule with data:', requestData);
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/save_job_schedule`, 
        requestData
      );
      
      console.log('Save schedule response:', response.data);
      
      if (response.data.success) {
        // After saving the schedule, enable it so it shows as "Scheduled" and the scheduler picks it up
        try {
          const enableResponse = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL}/job/enable_disable_job`,
            {
              MAPREF: jobData.MAPREF,
              JOB_FLG: 'E' // Enable the schedule
            }
          );
          
          if (enableResponse.data.success) {
            setSuccessMessage('Schedule saved and enabled successfully');
            
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
            
            // IMPORTANT: Reload schedule details from backend after successful save
            // This ensures the UI shows the exact data that was saved
            setTimeout(() => {
              fetchJobScheduleDetails(jobId);
            }, 500); // Small delay to ensure backend has committed the transaction
            
            return true;
          } else {
            // Schedule was saved but enabling failed
            setError(enableResponse.data.message || 'Schedule saved but failed to enable. Please enable it manually.');
            return false;
          }
        } catch (enableErr) {
          console.error('Error enabling schedule after save:', enableErr);
          // Schedule was saved but enabling failed
          setError('Schedule saved but failed to enable. Please enable it manually.');
          return false;
        }
      } else {
        setError(response.data.message || 'Failed to save schedule');
        return false;
      }
    } catch (err) {
      console.error('Error saving job schedule:', err);
      const errorMessage = err.response?.data?.message || err.response?.data?.detail?.message || err.message || 'Failed to save schedule. Please try again.';
      setError(errorMessage);
      return false;
    } finally {
      // Clear saving state for this job
      setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
      
      setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 3000);
    }
  };

  // Handle schedule job (save and enable)
  const handleScheduleJob = async (jobId) => {
    try {
      // First save the schedule
      const currentJob = jobs.find(job => job.JOBFLWID === jobId);
      if (!currentJob) {
        setError('Job not found');
        return;
      }

      // Check if job is currently enabled (scheduled)
      if (currentJob && currentJob.JOB_SCHEDULE_STATUS === 'Scheduled') {
        setNotification({
          open: true,
          message: 'Cannot schedule job while it is already enabled. Please disable the job first before rescheduling.',
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
      
      // Step 1: Save the schedule
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
      
      const saveResponse = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/save_job_schedule`, 
        requestData
      );
      
      if (!saveResponse.data.success) {
        setError(saveResponse.data.message || 'Failed to save schedule');
        setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
        return;
      }

      // Step 2: Enable the schedule
      const enableResponse = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/enable_disable_job`,
        {
          MAPREF: jobData.MAPREF,
          JOB_FLG: 'E' // Enable
        }
      );

      if (enableResponse.data.success) {
        setSuccessMessage('Job scheduled successfully! The job will run according to the configured schedule.');
        
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
                  JOBSCHID: saveResponse.data.job_schedule_id
                } 
              : job
          )
        );
        
        // Reload schedule details from backend after successful save
        setTimeout(() => {
          fetchJobScheduleDetails(jobId);
        }, 500);
      } else {
        setError(enableResponse.data.message || 'Schedule saved but failed to enable job');
      }
    } catch (err) {
      console.error('Error scheduling job:', err);
      setError(err.response?.data?.message || 'Failed to schedule job. Please try again.');
    } finally {
      // Clear saving state for this job
      setScheduleSaving(prev => ({ ...prev, [jobId]: false }));
      
      setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 5000); // Longer timeout for success message since it's important
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

  // Helper functions similar to reports page
  const getScheduleLabel = (job) => {
    // Helper to check if a value is valid (not null, undefined, or empty string)
    const isValid = (val) => val !== null && val !== undefined && val !== '';
    
    // Helper to get field value with case-insensitive lookup (backend normalizes to uppercase)
    const getField = (fieldName) => {
      // Try exact match first
      if (job[fieldName] !== undefined) return job[fieldName];
      // Try uppercase (backend normalization)
      if (job[fieldName.toUpperCase()] !== undefined) return job[fieldName.toUpperCase()];
      // Try lowercase
      if (job[fieldName.toLowerCase()] !== undefined) return job[fieldName.toLowerCase()];
      // Try with underscores instead of spaces
      const underscoreName = fieldName.replace(/\s+/g, '_');
      if (job[underscoreName] !== undefined) return job[underscoreName];
      if (job[underscoreName.toUpperCase()] !== undefined) return job[underscoreName.toUpperCase()];
      if (job[underscoreName.toLowerCase()] !== undefined) return job[underscoreName.toLowerCase()];
      return null;
    };
    
    // Try to get frequency code from multiple sources - prioritize direct job data
    // Check in order: job object -> scheduleData FRQCD -> scheduleData TIMEPARAM -> job object frequency fields
    let frequencyCode = null;
    
    // First check job object's "Frequency code" field (from API) - handle case variations
    // Backend normalizes to uppercase, so "Frequency code" becomes "FREQUENCY CODE"
    const freqCodeField = getField("Frequency code");
    if (isValid(freqCodeField)) {
      frequencyCode = freqCodeField;
    }
    // Then check scheduleData FRQCD
    else if (isValid(scheduleData[job.JOBFLWID]?.FRQCD)) {
      frequencyCode = scheduleData[job.JOBFLWID].FRQCD;
    } 
    // Then try to extract from TIMEPARAM
    else if (scheduleData[job.JOBFLWID]?.TIMEPARAM) {
      const timeParamParts = scheduleData[job.JOBFLWID].TIMEPARAM.split('_');
      if (timeParamParts.length > 0 && isValid(timeParamParts[0])) {
        frequencyCode = timeParamParts[0];
      }
    }
    // Check if job has FRQCD field directly (case variations)
    else if (isValid(job.FRQCD)) {
      frequencyCode = job.FRQCD;
    }
    // Check if job has frequency_code field
    else if (isValid(job.frequency_code)) {
      frequencyCode = job.frequency_code;
    }
    
    // If we have a valid frequency code, map it to a readable label
    if (isValid(frequencyCode)) {
      const frequencyMap = {
        'DL': 'Daily',
        'WK': 'Weekly',
        'FN': 'Fortnightly',
        'MN': 'Monthly',
        'HY': 'Half-Yearly',
        'YR': 'Yearly',
        'ID': 'Interval'
      };
      return frequencyMap[frequencyCode] || frequencyCode;
    }
    
    // If no frequency code found, trigger fetch for scheduled jobs and return blank
    const isScheduled = job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID;
    if (isScheduled) {
      // Try to fetch schedule details if not already fetched
      if (!scheduleData[job.JOBFLWID] || !scheduleData[job.JOBFLWID].FRQCD) {
        // Trigger a fetch if we haven't already
        setTimeout(() => {
          fetchJobScheduleDetails(job.JOBFLWID);
        }, 100);
      }
    }
    
    // Return blank/dash if no frequency is set
    return '-';
  };

  const getScheduleStatusColor = (job) => {
    if (job.JOB_SCHEDULE_STATUS === 'Scheduled') return "success";
    return "default";
  };

  // Format date time helper (similar to reports page)
  const formatDateTime = (isoString) => {
    if (!isoString) return '-';
    try {
      // Handle different date formats
      let date;
      if (typeof isoString === 'string') {
        // Try parsing as ISO string first
        date = new Date(isoString);
        // If invalid, try other formats
        if (isNaN(date.getTime())) {
          // Try parsing as date string without timezone
          date = new Date(isoString.replace(' ', 'T'));
        }
      } else if (isoString instanceof Date) {
        date = isoString;
      } else {
        date = new Date(isoString);
      }
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return '-';
      }
      
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
    } catch (err) {
      console.warn('Error formatting date:', isoString, err);
      return '-';
    }
  };
  
  // Helper function to get last run date from multiple sources
  const getLastRunDate = (job) => {
    // Helper to get field value with case-insensitive lookup (backend normalizes to uppercase)
    const getField = (fieldName) => {
      // Try exact match first
      if (job[fieldName] !== undefined) return job[fieldName];
      // Try uppercase (backend normalization)
      if (job[fieldName.toUpperCase()] !== undefined) return job[fieldName.toUpperCase()];
      // Try lowercase
      if (job[fieldName.toLowerCase()] !== undefined) return job[fieldName.toLowerCase()];
      // Try with underscores instead of spaces
      const underscoreName = fieldName.replace(/\s+/g, '_');
      if (job[underscoreName] !== undefined) return job[underscoreName];
      if (job[underscoreName.toUpperCase()] !== undefined) return job[underscoreName.toUpperCase()];
      if (job[underscoreName.toLowerCase()] !== undefined) return job[underscoreName.toLowerCase()];
      return null;
    };
    
    // Check scheduleData first (most up-to-date)
    const scheduleLastRun = scheduleData[job.JOBFLWID]?.LST_RUN_DT;
    if (scheduleLastRun) {
      return scheduleLastRun;
    }
    // Check job object with various field name variations (case-insensitive)
    // Backend normalizes to uppercase, so "last run" becomes "LAST RUN"
    const jobLastRun = getField("last run") || 
                      job["last_run"] || 
                      job.LST_RUN_DT || 
                      job.last_run || 
                      job.LAST_RUN_DT;
    if (jobLastRun) {
      return jobLastRun;
    }
    
    // If scheduled but no date found, try to fetch schedule details
    if ((job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID) && !scheduleData[job.JOBFLWID]?.LST_RUN_DT) {
      // Trigger a fetch if we haven't already
      if (!scheduleData[job.JOBFLWID] || !scheduleData[job.JOBFLWID].LST_RUN_DT) {
        setTimeout(() => {
          fetchJobScheduleDetails(job.JOBFLWID);
        }, 100);
      }
    }
    
    return null;
  };
  
  // Helper function to get next run date from multiple sources
  const getNextRunDate = (job) => {
    // Helper to get field value with case-insensitive lookup (backend normalizes to uppercase)
    const getField = (fieldName) => {
      // Try exact match first
      if (job[fieldName] !== undefined) return job[fieldName];
      // Try uppercase (backend normalization)
      if (job[fieldName.toUpperCase()] !== undefined) return job[fieldName.toUpperCase()];
      // Try lowercase
      if (job[fieldName.toLowerCase()] !== undefined) return job[fieldName.toLowerCase()];
      // Try with underscores instead of spaces
      const underscoreName = fieldName.replace(/\s+/g, '_');
      if (job[underscoreName] !== undefined) return job[underscoreName];
      if (job[underscoreName.toUpperCase()] !== undefined) return job[underscoreName.toUpperCase()];
      if (job[underscoreName.toLowerCase()] !== undefined) return job[underscoreName.toLowerCase()];
      return null;
    };
    
    // Check scheduleData first (most up-to-date)
    const scheduleNextRun = scheduleData[job.JOBFLWID]?.NXT_RUN_DT;
    if (scheduleNextRun) {
      return scheduleNextRun;
    }
    // Check job object with various field name variations (case-insensitive)
    // Backend normalizes to uppercase, so "next run" becomes "NEXT RUN"
    const jobNextRun = getField("next run") || 
                       job["next_run"] || 
                       job.NXT_RUN_DT || 
                       job.next_run || 
                       job.NEXT_RUN_DT;
    if (jobNextRun) {
      return jobNextRun;
    }
    
    // If scheduled but no date found, try to fetch schedule details
    if ((job.JOB_SCHEDULE_STATUS === 'Scheduled' || job.JOBSCHID) && !scheduleData[job.JOBFLWID]?.NXT_RUN_DT) {
      // Trigger a fetch if we haven't already
      if (!scheduleData[job.JOBFLWID] || !scheduleData[job.JOBFLWID].NXT_RUN_DT) {
        setTimeout(() => {
          fetchJobScheduleDetails(job.JOBFLWID);
        }, 100);
      }
    }
    
    return null;
  };

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
      } else {
        // Add truncate option for regular load as well
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
      // FastAPI HTTPException returns error in detail field
      let errorMessage = 'Failed to execute job. Please try again.';
      if (err.response?.data) {
        // Check for detail.message (when detail is an object)
        if (err.response.data.detail?.message) {
          errorMessage = err.response.data.detail.message;
        }
        // Check for detail as string
        else if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        }
        // Check for message directly
        else if (err.response.data.message) {
          errorMessage = err.response.data.message;
        }
        // Check for error field
        else if (err.response.data.error) {
          errorMessage = err.response.data.error;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
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

  // Direct toggle handler for schedule checkbox/switch (with confirmation for disable)
  const handleScheduleToggle = async (job, newStatus) => {
    // If enabling, do it directly
    if (newStatus === 'Scheduled') {
      try {
        const response = await axios.post(
          `${process.env.NEXT_PUBLIC_API_URL}/job/enable_disable_job`,
          { 
            MAPREF: job.MAPREF,
            JOB_FLG: 'E'
          }
        );

        if (response.data.success) {
          setSuccessMessage('Schedule enabled successfully');
          setJobs(prevJobs => 
            prevJobs.map(j => 
              j.MAPREF === job.MAPREF 
                ? { ...j, JOB_SCHEDULE_STATUS: 'Scheduled' } 
                : j
            )
          );
          fetchJobs();
        } else {
          setError(response.data.message || 'Failed to enable schedule');
        }
      } catch (err) {
        console.error('Error enabling schedule:', err);
        setError(err.response?.data?.message || 'Failed to enable schedule. Please try again.');
      }
    } else {
      // If disabling, show confirmation dialog
      handleEnableDisableJob(job);
    }
  };

  // Toggle handler for job active/inactive status (STFLG)
  const handleJobStatusToggle = async (job, newStatus) => {
    const stflg = newStatus === 'Active' ? 'A' : 'N';
    
    // Optimistically update the UI immediately for better UX
    setJobs(prevJobs => 
      prevJobs.map(j => 
        j.MAPREF === job.MAPREF 
          ? { ...j, STFLG: stflg } 
          : j
      )
    );
    
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/toggle_job_status`,
        { 
          MAPREF: job.MAPREF,
          STFLG: stflg
        }
      );

      if (response.data.success) {
        setSuccessMessage(response.data.message);
        // Refresh jobs to get the latest state from database
        fetchJobs();
      } else {
        // Revert optimistic update on error
        setJobs(prevJobs => 
          prevJobs.map(j => 
            j.MAPREF === job.MAPREF 
              ? { ...j, STFLG: job.STFLG } 
              : j
          )
        );
        setError(response.data.message || 'Failed to update job status');
      }
    } catch (err) {
      console.error('Error toggling job status:', err);
      // Revert optimistic update on error
      setJobs(prevJobs => 
        prevJobs.map(j => 
          j.MAPREF === job.MAPREF 
            ? { ...j, STFLG: job.STFLG } 
            : j
        )
      );
      
      // Handle different error response formats (Flask vs FastAPI)
      let errorMessage = 'Failed to update job status. Please try again.';
      if (err.response) {
        if (err.response.data) {
          if (typeof err.response.data === 'string') {
            errorMessage = err.response.data;
          } else if (err.response.data.message) {
            errorMessage = err.response.data.message;
          } else if (err.response.data.detail) {
            if (typeof err.response.data.detail === 'string') {
              errorMessage = err.response.data.detail;
            } else if (err.response.data.detail.message) {
              errorMessage = err.response.data.detail.message;
            }
          }
        } else if (err.response.status === 404) {
          errorMessage = 'Endpoint not found. Please check if the backend server is running correctly.';
        } else if (err.response.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
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
      {(error || successMessage) && (
        <Box sx={{ mb: 2 }}>
          {error && (
            <Alert 
              severity="error" 
              onClose={() => setError(null)}
              sx={{ mb: 1 }}
            >
              {error}
            </Alert>
          )}
          {successMessage && (
            <Alert 
              severity="success"
              onClose={() => setSuccessMessage(null)}
            >
              {successMessage}
            </Alert>
          )}
        </Box>
      )}

      {/* Jobs table */}
      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} elevation={darkMode ? 0 : 1} sx={{ borderRadius: 2, border: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)" }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Schema</TableCell>
                <TableCell align="center">Status</TableCell>
                <TableCell align="center">Scheduled</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Last Run</TableCell>
                <TableCell>Next Run</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredJobs.map((job) => (
                <TableRow key={job.JOBID} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>{job.MAPREF}</Typography>
                    {job.TRGSCHM && job.TRGTBNM && (
                      <Typography variant="caption" color="text.secondary">
                        {job.TRGSCHM}.{job.TRGTBNM} ({job.TRGTBTYP})
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {job.TRGSCHM || "Metadata"}
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip 
                      title={
                        (job.STFLG === 'A' ? 'Click to deactivate job' : 'Click to activate job')
                      }
                      arrow
                    >
                      <FormControlLabel
                        control={
                          <Switch
                            checked={job.STFLG === 'A'}
                            onChange={(e) => {
                              const newStatus = e.target.checked ? 'Active' : 'Inactive';
                              handleJobStatusToggle(job, newStatus);
                            }}
                            size="small"
                            color="primary"
                          />
                        }
                        label={
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              fontSize: '0.75rem', 
                              ml: 0.5,
                              color: job.STFLG === 'A' 
                                ? (darkMode ? '#60A5FA' : '#3B82F6') 
                                : 'text.secondary',
                              fontWeight: job.STFLG === 'A' ? 600 : 400
                            }}
                          >
                            {job.STFLG === 'A' ? 'Active' : 'Inactive'}
                          </Typography>
                        }
                        sx={{ m: 0, cursor: 'pointer' }}
                      />
                    </Tooltip>
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip 
                      title={
                        !job.JOBSCHID && job.JOB_SCHEDULE_STATUS !== 'Scheduled' 
                          ? 'Configure schedule first to enable' 
                          : job.JOB_SCHEDULE_STATUS === 'Scheduled' 
                            ? 'Click to disable schedule' 
                            : 'Click to enable schedule'
                      }
                      arrow
                    >
                      <FormControlLabel
                        control={
                          <Switch
                            checked={job.JOB_SCHEDULE_STATUS === 'Scheduled'}
                            onChange={(e) => {
                              const newStatus = e.target.checked ? 'Scheduled' : 'Not Scheduled';
                              handleScheduleToggle(job, newStatus);
                            }}
                            size="small"
                            color="success"
                            disabled={!job.JOBSCHID && job.JOB_SCHEDULE_STATUS !== 'Scheduled'}
                          />
                        }
                        label={
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              fontSize: '0.75rem', 
                              ml: 0.5,
                              color: (job.JOB_SCHEDULE_STATUS === 'Scheduled') 
                                ? (darkMode ? '#4ADE80' : '#22C55E') 
                                : 'text.secondary',
                              fontWeight: (job.JOB_SCHEDULE_STATUS === 'Scheduled') ? 600 : 400
                            }}
                          >
                            {(job.JOB_SCHEDULE_STATUS === 'Scheduled') ? 'Scheduled' : 'Not Scheduled'}
                          </Typography>
                        }
                        sx={{ m: 0, cursor: (!job.JOBSCHID && job.JOB_SCHEDULE_STATUS !== 'Scheduled') ? 'not-allowed' : 'pointer' }}
                      />
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '0.8125rem', color: getScheduleLabel(job) === '-' ? 'text.secondary' : 'text.primary' }}>
                      {getScheduleLabel(job)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '0.8125rem' }}>
                      {formatDateTime(getLastRunDate(job))}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '0.8125rem' }}>
                      {formatDateTime(getNextRunDate(job))}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Stack direction="row" spacing={0.5} justifyContent="center">
                      <Tooltip title="View Details">
                        <ActionButton 
                          size="small" 
                          onClick={() => handleViewDetails(job)}
                          darkMode={darkMode}
                          color="info"
                        >
                          <VisibilityIcon fontSize="small" />
                        </ActionButton>
                      </Tooltip>
                      <Tooltip title="Execute Now">
                        <ActionButton 
                          size="small" 
                          onClick={() => handleExecuteNow(job)}
                          darkMode={darkMode}
                          color="primary"
                        >
                          <PlayArrowIcon fontSize="small" />
                        </ActionButton>
                      </Tooltip>
                      <Tooltip title="Schedule Job">
                        <ActionButton 
                          size="small" 
                          onClick={() => openScheduleDialog(job)}
                          darkMode={darkMode}
                          color="success"
                        >
                          <ScheduleIcon fontSize="small" />
                        </ActionButton>
                      </Tooltip>
                      <Tooltip title="View Logic">
                        <ActionButton 
                          size="small" 
                          onClick={() => handleViewLogic(job)}
                          darkMode={darkMode}
                          color="info"
                        >
                          <CodeIcon fontSize="small" />
                        </ActionButton>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
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

      {/* Schedule Dialog */}
      <ScheduleDialog
        open={scheduleDialog.open}
        onClose={closeScheduleDialog}
        job={scheduleDialog.job}
        scheduleData={scheduleData}
        onSave={handleSaveScheduleFromDialog}
        darkMode={darkMode}
        saving={scheduleDialog.job ? (scheduleSaving[scheduleDialog.job.JOBFLWID] || false) : false}
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
        truncateLoad: truncateLoad // Available for both regular and history load
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
              fontStyle: 'italic',
              mb: 2
            }}>
              This will trigger the job execution outside of its scheduled time.
            </Typography>
            
            {/* Truncate Load Option for Regular Load */}
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <input
                type="checkbox"
                id="truncateLoadRegular"
                checked={truncateLoad}
                onChange={(e) => setTruncateLoad(e.target.checked)}
                style={{
                  marginRight: '8px',
                  accentColor: darkMode ? '#3B82F6' : '#3B82F6'
                }}
              />
              <label htmlFor="truncateLoadRegular" style={{ 
                fontSize: '0.875rem',
                color: darkMode ? '#E2E8F0' : '#4A5568',
                cursor: 'pointer'
              }}>
                Truncate & Load (Clear target table before loading data)
              </label>
            </Box>
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
