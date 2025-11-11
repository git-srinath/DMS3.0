import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const useJobLogs = () => {
  const [scheduledJobs, setScheduledJobs] = useState([]);
  const [logDetails, setLogDetails] = useState([]);
  const [errorDetails, setErrorDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [logLoading, setLogLoading] = useState(false);
  const [errorLoading, setErrorLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all scheduled jobs
  const fetchScheduledJobs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_scheduled_jobs`);
      
      // Check the structure of the response
      console.log('Scheduled jobs API response:', response.data);
      
      // Handle different response structures
      let jobsData = [];
      if (response.data && Array.isArray(response.data.scheduled_jobs)) {
        // If it's an array inside scheduled_jobs property
        jobsData = response.data.scheduled_jobs;
      } else if (response.data && Array.isArray(response.data)) {
        // If it's directly an array
        jobsData = response.data;
      }
      
      // Transform data if needed
      const formattedJobs = jobsData.map(job => {
        // Check if job is a nested array (some APIs return data this way)
        if (Array.isArray(job)) {
          return {
            MAP_REFERENCE: job[0] || '',
            STATUS: job[1] || '',
            FREQUENCY_CODE: job[2] || '',
            FREQUENCY_DAY: job[3] || '',
            FREQUENCY_HOUR: job[4] || '',
            FREQUENCY_MINUTE: job[5] || ''
          };
        }
        
        // Otherwise, expect an object
        return {
          MAP_REFERENCE: job.MAP_REFERENCE || '',
          STATUS: job.STATUS || '',
          FREQUENCY_CODE: job.FREQUENCY_CODE || '',
          FREQUENCY_DAY: job.FREQUENCY_DAY || '',
          FREQUENCY_HOUR: job.FREQUENCY_HOUR || '',
          FREQUENCY_MINUTE: job.FREQUENCY_MINUTE || ''
        };
      });
      
      console.log('Formatted scheduled jobs:', formattedJobs);
      setScheduledJobs(formattedJobs);
      setError(null);
    } catch (err) {
      console.error('Error fetching scheduled jobs:', err);
      setError('Failed to fetch scheduled jobs. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch job logs for a specific map reference
  const fetchJobLogs = useCallback(async (mapReference) => {
    setLogLoading(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_job_and_process_log_details/${mapReference}`);
      
      // Log response for debugging
      console.log('Job logs API response:', response.data);
      
      // Get the log details array
      let logData = [];
      if (response.data && Array.isArray(response.data.job_and_process_log_details)) {
        logData = response.data.job_and_process_log_details;
      } else if (response.data && Array.isArray(response.data)) {
        logData = response.data;
      }
      
      // Format the log data if it's in a nested array format
      const formattedLogs = logData.map(log => {
        if (Array.isArray(log)) {
          return {
            PROCESS_DATE: log[0],
            MAP_REFERENCE: log[1],
            JOB_ID: log[2],
            SOURCE_ROWS: log[3],
            TARGET_ROWS: log[4],
            ERROR_ROWS: log[5],
            START_DATE: log[6],
            END_DATE: log[7],
            STATUS: log[8]
          };
        }
        return log;
      });
      
      console.log('Formatted job logs:', formattedLogs);
      setLogDetails(formattedLogs);
      return formattedLogs;
    } catch (err) {
      console.error('Error fetching job log details:', err);
      setError('Failed to fetch job log details. Please try again later.');
      return [];
    } finally {
      setLogLoading(false);
    }
  }, []);

  // Fetch error details for a specific job ID
  const fetchErrorDetails = useCallback(async (jobId) => {
    setErrorLoading(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_error_details/${jobId}`);
      
      // Log response for debugging
      console.log('Error details API response:', response.data);
      
      // Get the error details array
      let errorData = [];
      if (response.data && Array.isArray(response.data.error_details)) {
        errorData = response.data.error_details;
      } else if (response.data && Array.isArray(response.data)) {
        errorData = response.data;
      }
      
      // Format the error data if it's in a nested array format
      const formattedErrors = errorData.map(error => {
        if (Array.isArray(error)) {
          return {
            ERROR_ID: error[0],
            PROCESS_DATE: error[1],
            ERROR_TYPE: error[2],
            DATABASE_ERROR_MESSAGE: error[3],
            ERROR_MESSAGE: error[4],
            KEY_VALUE: error[5]
          };
        }
        return error;
      });
      
      console.log('Formatted error details:', formattedErrors);
      setErrorDetails(formattedErrors);
      return formattedErrors;
    } catch (err) {
      console.error('Error fetching error details:', err);
      setError('Failed to fetch error details. Please try again later.');
      return [];
    } finally {
      setErrorLoading(false);
    }
  }, []);

  // Load scheduled jobs on hook initialization
  useEffect(() => {
    fetchScheduledJobs();
  }, [fetchScheduledJobs]);

  // Clear error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return {
    scheduledJobs,
    logDetails,
    errorDetails,
    loading,
    logLoading,
    errorLoading,
    error,
    fetchScheduledJobs,
    fetchJobLogs,
    fetchErrorDetails,
    setError
  };
};

export default useJobLogs; 