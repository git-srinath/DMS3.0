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
  CircularProgress
} from '@mui/material';
import { Close as CloseIcon, Save as SaveIcon } from '@mui/icons-material';
import axios from 'axios';

/**
 * DependencyModal component for setting job dependencies
 */
const DependencyModal = ({
  open,
  handleClose,
  jobId,
  mapRef,
  currentDependency,
  darkMode,
  onSaveDependency,
  allJobs = []
}) => {
  // State for selected dependent job
  const [selectedJob, setSelectedJob] = useState('');
  const [availableJobs, setAvailableJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initialize selected job when modal opens
  useEffect(() => {
    if (open) {
      setSelectedJob(currentDependency || '');
      if (allJobs.length > 0) {
        // Filter out the current job and unscheduled jobs from the list
        const filteredJobs = allJobs.filter(job => 
          job.MAPREF !== mapRef && 
          job.JOBSCHID !== null && 
          job.JOB_SCHEDULE_STATUS === 'Scheduled'
        );
        setAvailableJobs(filteredJobs);
        setError(null);
      } else {
        fetchAvailableJobs();
      }
    }
  }, [open, currentDependency, allJobs, mapRef]);

  // Fetch all available jobs when modal opens (fallback if allJobs not provided)
  const fetchAvailableJobs = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_all_jobs`);
      
      // Filter out the current job and unscheduled jobs from the list
      const filteredJobs = response.data.filter(job => 
        job.MAPREF !== mapRef && 
        job.JOBSCHID !== null && 
        job.JOB_SCHEDULE_STATUS === 'Scheduled'
      );
      
      setAvailableJobs(filteredJobs);
      setError(null);
    } catch (err) {
      console.error('Error fetching available jobs:', err);
      setError('Failed to fetch available jobs');
    } finally {
      setLoading(false);
    }
  };

  // Handle selection change
  const handleJobChange = (event) => {
    setSelectedJob(event.target.value);
  };

  // Handle save button click
  const handleSave = async () => {
    try {
      setLoading(true);
      
      // Prepare request data in the format expected by the parent component
      const requestData = {
        JOBFLWID: jobId,
        MAPREF: mapRef,
        DPND_MAPREF: selectedJob
      };
      
      // Call the API to save the dependency
      const success = await onSaveDependency(requestData);
      
      if (success) {
        handleClose();
      }
    } catch (err) {
      console.error('Error saving dependency:', err);
      setError('Failed to save dependency. Please try again.');
    } finally {
      setLoading(false);
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
          Set Job Dependency
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
        {loading && !availableJobs.length && (
          <Box display="flex" justifyContent="center" my={2}>
            <CircularProgress size={24} color="primary" />
          </Box>
        )}
        
        {error && (
          <Typography 
            variant="body2" 
            color="error" 
            sx={{ mb: 2 }}
          >
            {error}
          </Typography>
        )}
        
        <Typography 
          variant="subtitle2" 
          sx={{ 
            mb: 1.5, 
            color: darkMode ? 'gray.300' : 'gray.700',
            fontSize: '0.875rem'
          }}
        >
          This job ({mapRef}) will run after the selected job completes
        </Typography>
        
        <FormControl 
          fullWidth 
          variant="outlined" 
          size="small"
          disabled={loading && !availableJobs.length}
        >
          <InputLabel id="dependency-job-label">Dependent On</InputLabel>
          <Select
            labelId="dependency-job-label"
            value={selectedJob}
            onChange={handleJobChange}
            label="Dependent On"
            sx={{
              backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(255, 255, 255, 0.9)',
            }}
            MenuProps={{
              PaperProps: {
                sx: {
                  maxHeight: 300,
                }
              }
            }}
          >
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
            {availableJobs.map(job => (
              <MenuItem key={job.MAPREF} value={job.MAPREF}>
                {job.MAPREF}{job.JOB_SCHEDULE_STATUS !== 'Scheduled' ? ' (Not scheduled)' : ''}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {availableJobs.length === 0 && !loading && (
          <Typography 
            variant="caption" 
            sx={{ 
              display: 'block', 
              mt: 1.5, 
              color: darkMode ? '#F56565' : '#E53E3E',
              fontStyle: 'italic'
            }}
          >
            No scheduled jobs available to set as dependency. Jobs must be scheduled first.
          </Typography>
        )}
        
        <Typography 
          variant="caption" 
          sx={{ 
            display: 'block', 
            mt: 1.5, 
            color: darkMode ? 'gray.400' : 'gray.500',
            fontStyle: 'italic'
          }}
        >
          Note: Only scheduled jobs can be set as dependencies
        </Typography>
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
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
          disabled={loading || selectedJob === "" || availableJobs.length === 0}
        >
          Save Dependency
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DependencyModal; 