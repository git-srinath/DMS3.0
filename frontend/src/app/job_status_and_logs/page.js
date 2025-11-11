'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Calendar, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Eye, 
  Copy, 
  Download,
  ChevronDown,
  ChevronRight,
  Activity,
  Database,
  Timer,
  AlertCircle,
  TrendingUp,
  BarChart3,
  Zap,
  PlayCircle,
  PauseCircle
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { API_BASE_URL } from '../config';
import ErrorDetailsDialog from './ErrorDetailsDialog';
import StopJobDialog from './StopJobDialog';

const JobStatusAndLogs = () => {
  const { darkMode } = useTheme();
  const [scheduledJobs, setScheduledJobs] = useState([]);
  const [columnNames, setColumnNames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [expandedJobs, setExpandedJobs] = useState(new Set());
  const [selectedError, setSelectedError] = useState(null);
  const [errorDialogOpen, setErrorDialogOpen] = useState(false);
  const [stopJobDialogOpen, setStopJobDialogOpen] = useState(false);
  const [selectedJobToStop, setSelectedJobToStop] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState('log_date');
  const [sortOrder, setSortOrder] = useState('desc');
  const [timePeriod, setTimePeriod] = useState(2); // Default to 7 days

  // Fetch scheduled jobs data
  const fetchScheduledJobs = async () => {
    try {
      setRefreshing(true);
      const response = await fetch(`${API_BASE_URL}/job/get_scheduled_jobs?period=${timePeriod}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.jobs && Array.isArray(data.jobs)) {
        // Store the grouped jobs directly from the API
        setScheduledJobs(data.jobs);
        // Set column names from summary if available
        if (data.summary && data.summary.column_names) {
          setColumnNames(data.summary.column_names.map(name => name.toLowerCase()));
        }
        // Set default sort to lastRunDate in descending order
        setSortBy('lastRunDate');
        setSortOrder('desc');
      } else if (data.error) {
        console.error('API Error:', data.error);
      }
    } catch (error) {
      console.error('Error fetching scheduled jobs:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchScheduledJobs();
  }, [timePeriod]);

  // Process grouped jobs from API into the expected format
  const groupedJobs = useMemo(() => {
    if (!scheduledJobs || !Array.isArray(scheduledJobs)) {
      return [];
    }

    return scheduledJobs.map(jobGroup => {
      const { job_name: jobName, logs } = jobGroup;
      
      // Process logs and calculate statistics
      const processedLogs = logs.map(log => ({
        logId: log.LOG_ID,
        logDate: log.LOG_DATE,
        jobName: log.JOB_NAME,
        status: log.STATUS,
        actualStartDate: log.ACTUAL_START_DATE,
        errorMessage: log.ERROR_MESSAGE,
        runDurationSeconds: log.RUN_DURATION_SECONDS,
        sessionId: log.SESSION_ID,
        sourceRows: log.SOURCE_ROWS,
        targetRows: log.TARGET_ROWS,
        param1: log.PARAM1
      }));

      // Calculate job statistics
      const totalRuns = processedLogs.length;
      const successfulRuns = processedLogs.filter(log => log.status === 'PC').length;
      const failedRuns = processedLogs.filter(log => log.status === 'FL').length;
      const inProgressRuns = processedLogs.filter(log => log.status === 'IP').length;
      const stoppedRuns = processedLogs.filter(log => log.status === 'ST').length;
      const hasFailedLogs = failedRuns > 0;

      // Get latest status and last run date (logs are already sorted by date desc from backend)
      const latestStatus = processedLogs.length > 0 ? processedLogs[0].status : 'Unknown';
      const lastRunDate = processedLogs.length > 0 ? processedLogs[0].logDate : null;

      // Calculate average duration
      const validDurations = processedLogs
        .map(log => log.runDurationSeconds)
        .filter(duration => duration && duration !== null && !isNaN(duration));
      
      const avgDuration = validDurations.length > 0 
        ? validDurations.reduce((sum, duration) => sum + parseFloat(duration), 0) / validDurations.length 
        : 0;

      return {
        jobName,
        logs: processedLogs,
        latestStatus,
        totalRuns,
        successfulRuns,
        failedRuns,
        inProgressRuns,
        stoppedRuns,
        lastRunDate,
        avgDuration,
        hasFailedLogs
      };
    });
  }, [scheduledJobs]);

  // Filter and sort jobs
  const filteredJobs = useMemo(() => {
    let filtered = groupedJobs.filter(job => {
      const matchesSearch = job.jobName.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || job.latestStatus === statusFilter;
      return matchesSearch && matchesStatus;
    });

    // Sort jobs
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      
      if (sortBy === 'lastRunDate') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [groupedJobs, searchTerm, statusFilter, sortBy, sortOrder]);

  // Toggle job expansion (auto-close others)
  const toggleJobExpansion = (jobName) => {
    const newExpanded = new Set();
    if (!expandedJobs.has(jobName)) {
      // Only add the current job (closes all others)
      newExpanded.add(jobName);
    }
    // If the job was already expanded, newExpanded remains empty (closes all)
    setExpandedJobs(newExpanded);
  };

  // Get status color and icon
  const getStatusDisplay = (status) => {
    switch (status) {
      case 'PC':
        return {
          color: 'text-green-500',
          bgColor: 'bg-green-100 dark:bg-green-900/30',
          icon: <CheckCircle size={16} />,
          label: 'Process Complete'
        };
      case 'FL':
        return {
          color: 'text-red-500',
          bgColor: 'bg-red-100 dark:bg-red-900/30',
          icon: <XCircle size={16} />,
          label: 'Failed'
        };
      case 'IP':
        return {
          color: 'text-blue-500',
          bgColor: 'bg-blue-100 dark:bg-blue-900/30',
          icon: <Activity size={16} />,
          label: 'In Progress'
        };
      case 'ST':
        return {
          color: 'text-amber-500',
          bgColor: 'bg-amber-100 dark:bg-amber-900/30',
          icon: <PauseCircle size={16} />,
          label: 'Stopped'
        };
      default:
        return {
          color: 'text-gray-500',
          bgColor: 'bg-gray-100 dark:bg-gray-900/30',
          icon: <Clock size={16} />,
          label: status || 'Unknown'
        };
    }
  };

  // Format duration from seconds
  const formatDuration = (seconds) => {
    if (!seconds || isNaN(seconds)) return 'N/A';
    const totalSeconds = parseInt(seconds);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch (error) {
      return dateString;
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  // Handle error dialog for failed jobs
  const handleViewError = (jobName, logId) => {
    const job = groupedJobs.find(j => j.jobName === jobName);
    if (!job) return;
    
    // Find the specific log entry
    let log;
    if (logId) {
      log = job.logs.find(l => l.logId === logId);
    } else {
      // If no logId provided, find the first failed log
      log = job.logs.find(l => l.status === 'FL');
    }
    
    if (!log) return;
    
    const errorDetails = [];
    
    // Check if error message exists and is not just whitespace/newlines
    const hasValidErrorMessage = log.errorMessage && log.errorMessage.trim() !== '' && log.errorMessage.trim() !== '\n';
    
    // Always create an error detail entry for failed jobs, even if no specific error message
    const errorMessage = hasValidErrorMessage ? log.errorMessage : 'Job failed but no specific error message was recorded.';
    
    errorDetails.push({
      ERROR_ID: log.logId || 'N/A',
      ERROR_TYPE: 'Job Execution Error',
      PROCESS_DATE: log.actualStartDate || log.logDate,
      KEY_VALUE: jobName,
      ERROR_MESSAGE: errorMessage,
      SESSION_ID: log.sessionId
    });
    
    setSelectedError({
      jobName,
      logId: log.logId,
      errorDetails
    });
    setErrorDialogOpen(true);
  };

  // Handle stopping a job
  const handleStopJob = (jobName, startDate) => {
    console.log("Stopping job:", jobName, "Start date (original):", startDate);
    
    if (!startDate) {
      console.error("No start date provided for job:", jobName);
      return;
    }
    
    // Log the date object to help debug
    try {
      const dateObj = new Date(startDate);
      console.log("Date object:", dateObj);
      console.log("Date components:", {
        year: dateObj.getFullYear(),
        month: dateObj.getMonth() + 1,
        day: dateObj.getDate(),
        hours: dateObj.getHours(),
        minutes: dateObj.getMinutes(),
        seconds: dateObj.getSeconds()
      });
    } catch (error) {
      console.error("Error parsing date:", error);
    }
    
    setSelectedJobToStop({
      jobName,
      startDate: startDate
    });
    setStopJobDialogOpen(true);
  };

  // Handle successful job stop
  const handleJobStopSuccess = () => {
    // Refresh the job list after stopping a job
    fetchScheduledJobs();
  };

  // Statistics
  const stats = useMemo(() => {
    const totalJobs = groupedJobs.length;
    const runningJobs = groupedJobs.filter(job => job.latestStatus === 'IP').length;
    const successfulJobs = groupedJobs.filter(job => job.latestStatus === 'PC').length;
    const failedJobs = groupedJobs.filter(job => job.latestStatus === 'FL').length;
    const stoppedJobs = groupedJobs.filter(job => job.latestStatus === 'ST').length;
    const totalRuns = groupedJobs.reduce((sum, job) => sum + job.totalRuns, 0);
    
    return { totalJobs, runningJobs, successfulJobs, failedJobs, stoppedJobs, totalRuns };
  }, [groupedJobs]);

  if (loading) {
    return (
      <div className={`min-h-screen ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} flex items-center justify-center`}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className={`w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full`}
        />
      </div>
    );
  }

  return (
    <div className={`h-screen flex flex-col ${darkMode ? 'bg-gray-900' : 'bg-gray-50'} p-2`}>
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-track {
          background: ${darkMode ? 'rgba(31, 41, 55, 0.5)' : 'rgba(243, 244, 246, 0.5)'};
          border-radius: 10px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: ${darkMode ? 'rgba(75, 85, 99, 0.8)' : 'rgba(209, 213, 219, 0.8)'};
          border-radius: 10px;
        }
        
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: ${darkMode ? 'rgba(107, 114, 128, 0.8)' : 'rgba(156, 163, 175, 0.8)'};
        }
      `}</style>
      <div className="w-full flex flex-col h-full">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-2"
        >

          {/* Filters, Search and Refresh */}
          <div className={`
            p-2 rounded-lg border mb-2
            ${darkMode ? 'bg-gray-800/70 border-gray-700' : 'bg-white border-gray-200'}
            shadow-sm
          `}>
            <div className="flex flex-col lg:flex-row gap-3 items-center">
              {/* Search */}
              <div className="flex-1 w-full lg:w-auto">
                <div className="relative">
                  <Search size={16} className={`absolute left-3 top-1/2 transform -translate-y-1/2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`} />
                  <input
                    type="text"
                    placeholder="Search by job name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className={`
                      w-full pl-10 pr-4 py-2 rounded-lg border text-sm
                      ${darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                        : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500'}
                      focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all
                    `}
                  />
                </div>
              </div>

              <div className="flex flex-col md:flex-row gap-2 w-full lg:w-auto">
                {/* Time Period Filter */}
                <div className="w-full md:w-48">
                  <select
                    value={timePeriod}
                    onChange={(e) => setTimePeriod(Number(e.target.value))}
                    className={`
                      w-full px-3 py-2 rounded-lg border text-sm
                      ${darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-gray-50 border-gray-300 text-gray-900'}
                      focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all
                    `}
                  >
                   <option value={2}>Last 2 Days</option>
                    <option value={7}>Last 7 Days</option>
                    <option value={15}>Last 15 Days</option>
                    <option value={30}>Last 30 Days</option>
                  </select>
                </div>

                {/* Status Filter */}
                <div className="w-full md:w-48">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className={`
                      w-full px-3 py-2 rounded-lg border text-sm
                      ${darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-gray-50 border-gray-300 text-gray-900'}
                      focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all
                    `}
                  >
                    <option value="all">All Statuses</option>
                    <option value="PC">Process Complete</option>
                    <option value="FL">Failed</option>
                    <option value="IP">In Progress</option>
                    <option value="ST">Stopped</option>
                  </select>
                </div>

                {/* Sort Options */}
                <div className="w-full md:w-48">
                  <select
                    value={`${sortBy}-${sortOrder}`}
                    onChange={(e) => {
                      const [field, order] = e.target.value.split('-');
                      setSortBy(field);
                      setSortOrder(order);
                    }}
                    className={`
                      w-full px-3 py-2 rounded-lg border text-sm
                      ${darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-gray-50 border-gray-300 text-gray-900'}
                      focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all
                    `}
                  >
                    <option value="lastRunDate-desc">Latest First</option>
                    <option value="lastRunDate-asc">Oldest First</option>
                    <option value="jobName-asc">Name A-Z</option>
                    <option value="jobName-desc">Name Z-A</option>
                    <option value="totalRuns-desc">Most Runs</option>
                    <option value="successfulRuns-desc">Most Successful</option>
                  </select>
                </div>
                
                {/* Refresh Button */}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={fetchScheduledJobs}
                  disabled={refreshing}
                  className={`
                    flex items-center justify-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm w-full md:w-auto
                    ${darkMode 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-blue-900/20' 
                      : 'bg-blue-500 hover:bg-blue-600 text-white shadow-blue-300/30'}
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
                  <span>Refresh</span>
                </motion.button>
              </div>
            </div>
          </div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-2">
            {[
              { 
                label: 'Total Jobs', 
                value: stats.totalJobs, 
                icon: <Database size={18} />, 
                color: 'blue',
                gradient: darkMode ? 'from-blue-900/40 to-indigo-900/30' : 'from-blue-50 to-indigo-100/70'
              },
              { 
                label: 'In Progress', 
                value: stats.runningJobs, 
                icon: <PlayCircle size={18} />, 
                color: 'blue',
                gradient: darkMode ? 'from-blue-900/40 to-indigo-900/30' : 'from-blue-50 to-indigo-100/70'
              },
              { 
                label: 'Completed', 
                value: stats.successfulJobs, 
                icon: <CheckCircle size={18} />, 
                color: 'green',
                gradient: darkMode ? 'from-green-900/40 to-emerald-900/30' : 'from-green-50 to-emerald-100/70'
              },
              { 
                label: 'Failed', 
                value: stats.failedJobs, 
                icon: <XCircle size={18} />, 
                color: 'red',
                gradient: darkMode ? 'from-red-900/40 to-rose-900/30' : 'from-red-50 to-rose-100/70'
              },
              { 
                label: 'Stopped', 
                value: stats.stoppedJobs, 
                icon: <PauseCircle size={18} />, 
                color: 'amber',
                gradient: darkMode ? 'from-amber-900/40 to-amber-900/30' : 'from-amber-50 to-amber-100/70'
              },
              { 
                label: 'Total Runs', 
                value: stats.totalRuns, 
                icon: <BarChart3 size={18} />, 
                color: 'purple',
                gradient: darkMode ? 'from-purple-900/40 to-violet-900/30' : 'from-purple-50 to-violet-100/70'
              }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`
                  p-3 rounded-md border bg-gradient-to-br ${stat.gradient}
                  ${darkMode 
                    ? 'border-gray-700' 
                    : 'border-gray-200'}
                  shadow-sm hover:shadow-md transition-all h-full
                `}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-xs font-medium ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      {stat.label}
                    </p>
                    <p className={`text-base font-bold ${darkMode ? 'text-white' : 'text-gray-900'} mt-0.5`}>
                      {stat.value}
                    </p>
                  </div>
                  <div className={`
                    p-1 rounded
                    ${stat.color === 'blue' ? 'bg-blue-100/80 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400' : ''}
                    ${stat.color === 'green' ? 'bg-green-100/80 text-green-600 dark:bg-green-900/40 dark:text-green-400' : ''}
                    ${stat.color === 'red' ? 'bg-red-100/80 text-red-600 dark:bg-red-900/40 dark:text-red-400' : ''}
                    ${stat.color === 'purple' ? 'bg-purple-100/80 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400' : ''}
                    ${stat.color === 'amber' ? 'bg-amber-100/80 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400' : ''}
                  `}>
                    <div className="w-4 h-4">{stat.icon}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Jobs Table */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className={`
            flex-1 rounded-xl border overflow-hidden flex flex-col
            ${darkMode ? 'bg-gray-800/80 border-gray-700' : 'bg-white border-gray-200'}
            shadow-sm
          `}
        >
          {/* Table Header - Static */}
          <div className={`${darkMode ? 'bg-gray-700/80' : 'bg-gray-50/90'} border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className={`px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      Job Details
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      Status
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      Statistics
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      Last Run
                    </th>
                    <th className={`px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider ${darkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      Actions
                    </th>
                  </tr>
                </thead>
              </table>
            </div>
          </div>
          
          {/* Table Body - Scrollable */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="overflow-x-auto">
              <table className="w-full">
                <tbody className={`divide-y ${darkMode ? 'divide-gray-700' : 'divide-gray-200'}`}>
                <AnimatePresence>
                  {filteredJobs.map((job, index) => {
                    const statusDisplay = getStatusDisplay(job.latestStatus);
                    const isExpanded = expandedJobs.has(job.jobName);
                    
                    return (
                      <React.Fragment key={job.jobName}>
                        <motion.tr
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          transition={{ delay: index * 0.05 }}
                          className={`
                            hover:bg-opacity-50 transition-colors cursor-pointer
                            ${darkMode ? 'hover:bg-gray-700/70' : 'hover:bg-gray-50/90'}
                          `}
                          onClick={() => toggleJobExpansion(job.jobName)}
                        >
                          <td className="px-6 py-3">
                            <div className="flex items-center space-x-3">
                              <motion.div
                                animate={{ rotate: isExpanded ? 90 : 0 }}
                                transition={{ duration: 0.2 }}
                                className={`w-6 h-6 flex items-center justify-center rounded-full ${
                                  isExpanded 
                                    ? darkMode ? 'bg-blue-900/40 text-blue-400' : 'bg-blue-100 text-blue-600' 
                                    : darkMode ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-500'
                                }`}
                              >
                                <ChevronRight size={16} />
                              </motion.div>
                              <div className="flex items-center">
                                <div className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                                  {job.jobName}
                                </div>
                                <div className={`text-xs ml-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                                  ({job.totalRuns} runs)
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-3">
                            <span className={`
                              inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium
                              ${statusDisplay.bgColor} ${statusDisplay.color}
                            `}>
                              {statusDisplay.icon}
                              <span>{statusDisplay.label}</span>
                            </span>
                          </td>
                          <td className="px-6 py-3">
                            <div className="flex items-center space-x-4 text-xs">
                              <div className="flex items-center space-x-1">
                                <CheckCircle size={14} className="text-green-500" />
                                <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                                  {job.successfulRuns}
                                </span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <XCircle size={14} className="text-red-500" />
                                <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                                  {job.failedRuns}
                                </span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <PlayCircle size={14} className="text-blue-500" />
                                <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                                  {job.inProgressRuns}
                                </span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <PauseCircle size={14} className="text-amber-500" />
                                <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                                  {job.stoppedRuns}
                                </span>
                              </div>
                              <div className="flex items-center space-x-1">
                                <Timer size={14} className="text-purple-500" />
                                <span className={`font-medium ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                                  {formatDuration(job.avgDuration)}
                                </span>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-3">
                            <div className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                              {formatDate(job.lastRunDate)}
                            </div>
                          </td>
                          <td className="px-6 py-3">
                            <div className="flex items-center space-x-2">
                              {job.latestStatus === 'FL' && (
                                <motion.button
                                  whileHover={{ scale: 1.05 }}
                                  whileTap={{ scale: 0.95 }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    // Find the most recent log (which should be failed)
                                    const latestLog = job.logs
                                      .sort((a, b) => new Date(b.logDate) - new Date(a.logDate))[0];
                                    handleViewError(job.jobName, latestLog?.logId);
                                  }}
                                  className={`
                                    flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium
                                    bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400
                                    hover:bg-red-200 dark:hover:bg-red-900/60 transition-colors
                                  `}
                                  title="View Error Details"
                                >
                                  <AlertTriangle size={12} />
                                  <span>View Error</span>
                                </motion.button>
                              )}
                              {job.latestStatus === 'IP' && (
                                <motion.button
                                  whileHover={{ scale: 1.03 }}
                                  whileTap={{ scale: 0.97 }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    // Find the most recent in-progress log
                                    const inProgressLog = job.logs.find(log => log.status === 'IP');
                                    if (inProgressLog) {
                                      console.log("Found in-progress log:", inProgressLog);
                                      handleStopJob(job.jobName, inProgressLog.actualStartDate);
                                    } else {
                                      console.error("No in-progress log found for job:", job.jobName);
                                    }
                                  }}
                                  className={`
                                    flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium
                                    bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400
                                    hover:bg-amber-200 dark:hover:bg-amber-900/60 transition-colors
                                  `}
                                >
                                  <PauseCircle size={12} />
                                  <span>Stop Job</span>
                                </motion.button>
                              )}
                            </div>
                          </td>
                        </motion.tr>
                        
                        {/* Expanded Logs */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.tr
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.3 }}
                            >
                              <td colSpan={5} className={`px-6 py-0 ${darkMode ? 'bg-gray-750/50' : 'bg-gray-50/70'}`}>
                                <div className="py-4">
                                  <div className="flex items-center justify-between mb-2">
                                    <h4 className={`text-sm font-medium ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                                      <span className="flex items-center">
                                        <Activity size={16} className={`mr-2 ${darkMode ? 'text-blue-400' : 'text-blue-600'}`} />
                                        Execution History
                                      </span>
                                    </h4>
                                    <div className="flex items-center">
                                      <span className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                                        {job.logs.length} log entries
                                      </span>
                                    </div>
                                  </div>
                                  <div className="space-y-2 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
                                    {job.logs
                                      .sort((a, b) => new Date(b.logDate) - new Date(a.logDate))
                                      .map((log, logIndex) => {
                                      const logStatusDisplay = getStatusDisplay(log.status);
                                      return (
                                        <motion.div
                                          key={`${log.logId}-${logIndex}`}
                                          initial={{ opacity: 0, x: -20 }}
                                          animate={{ opacity: 1, x: 0 }}
                                          transition={{ delay: logIndex * 0.05 }}
                                          className={`
                                            p-3 rounded-lg border
                                            ${darkMode 
                                              ? 'bg-gray-800/90 border-gray-700 hover:bg-gray-800' 
                                              : 'bg-white border-gray-200 hover:bg-gray-50/80'}
                                            transition-colors
                                          `}
                                        >
                                          <div className="flex items-center justify-between gap-3">
                                            <div className="flex flex-wrap items-center gap-3">
                                              <span className={`
                                                inline-flex items-center space-x-2 px-3 py-1 rounded-md text-xs font-medium
                                                ${logStatusDisplay.bgColor} ${logStatusDisplay.color}
                                              `}>
                                                {logStatusDisplay.icon}
                                                <span>{logStatusDisplay.label}</span>
                                              </span>
                                              {log.actualStartDate && (
                                                <div className={`text-xs flex items-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                                  <Calendar size={12} className="mr-1" />
                                                  Started: {formatDate(log.actualStartDate)}
                                                </div>
                                              )}
                                              {log.runDurationSeconds && (
                                                <div className={`text-xs flex items-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                                  <Clock size={12} className="mr-1" />
                                                  Duration: {formatDuration(log.runDurationSeconds)}
                                                </div>
                                              )}
                                              {(log.sourceRows !== null && log.sourceRows !== undefined) && (
                                                <div className={`text-xs flex items-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                                  <Database size={12} className="mr-1" />
                                                  Source: {log.sourceRows?.toLocaleString() || 'N/A'}
                                                </div>
                                              )}
                                              {(log.targetRows !== null && log.targetRows !== undefined) && (
                                                <div className={`text-xs flex items-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                                  <TrendingUp size={12} className="mr-1" />
                                                  Target: {log.targetRows?.toLocaleString() || 'N/A'}
                                                </div>
                                              )}
                                              {log.param1 && (
                                                <div className={`text-xs flex items-center ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                                                  <Zap size={12} className="mr-1" />
                                                  Param: {log.param1}
                                                </div>
                                              )}
                                            </div>
                                            <div className="flex items-center space-x-2 ml-auto">
                                              {log.status === 'FL' && (
                                                <motion.button
                                                  whileHover={{ scale: 1.03 }}
                                                  whileTap={{ scale: 0.97 }}
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleViewError(job.jobName, log.logId);
                                                  }}
                                                  className={`
                                                    flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium
                                                    bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400
                                                    hover:bg-red-200 dark:hover:bg-red-900/60 transition-colors
                                                  `}
                                                >
                                                  <AlertTriangle size={12} />
                                                  <span>View Error</span>
                                                </motion.button>
                                              )}
                                              {log.status === 'IP' && (
                                                <motion.button
                                                  whileHover={{ scale: 1.03 }}
                                                  whileTap={{ scale: 0.97 }}
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    console.log("Stop job clicked for log entry:", log);
                                                    handleStopJob(job.jobName, log.actualStartDate);
                                                  }}
                                                  className={`
                                                    flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium
                                                    bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400
                                                    hover:bg-amber-200 dark:hover:bg-amber-900/60 transition-colors
                                                  `}
                                                >
                                                  <PauseCircle size={12} />
                                                  <span>Stop Job</span>
                                                </motion.button>
                                              )}
                                              <motion.button
                                                whileHover={{ scale: 1.05 }}
                                                whileTap={{ scale: 0.95 }}
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  copyToClipboard(JSON.stringify({
                                                    jobName: job.jobName,
                                                    status: log.status,
                                                    logDate: log.logDate,
                                                    actualStartDate: log.actualStartDate,
                                                    duration: formatDuration(log.runDurationSeconds),
                                                    sourceRows: log.sourceRows,
                                                    targetRows: log.targetRows,
                                                    param1: log.param1
                                                  }, null, 2));
                                                }}
                                                className={`
                                                  p-1.5 rounded-md transition-colors
                                                  ${darkMode ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-500'}
                                                `}
                                                title="Copy Log Details"
                                              >
                                                <Copy size={14} />
                                              </motion.button>
                                            </div>
                                          </div>
                                        </motion.div>
                                      );
                                    })}
                                  </div>
                                </div>
                              </td>
                            </motion.tr>
                          )}
                        </AnimatePresence>
                      </React.Fragment>
                    );
                  })}
                </AnimatePresence>
              </tbody>
              </table>
            </div>
          </div>
          
          {filteredJobs.length === 0 && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center py-16">
                <Database size={64} className={`mx-auto mb-4 ${darkMode ? 'text-gray-600' : 'text-gray-400'} opacity-70`} />
                <h3 className={`text-xl font-medium mb-2 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  No jobs found
                </h3>
                <p className={`text-sm ${darkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                  Try adjusting your search or filter criteria
                </p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Error Dialog */}
        <ErrorDetailsDialog
          open={errorDialogOpen}
          onClose={() => setErrorDialogOpen(false)}
          errorDetails={selectedError?.errorDetails || []}
          jobId={selectedError?.logId || selectedError?.jobName}
          loading={false}
          darkMode={darkMode}
        />

        {/* Stop Job Dialog */}
        <StopJobDialog
          open={stopJobDialogOpen}
          onClose={() => setStopJobDialogOpen(false)}
          jobName={selectedJobToStop?.jobName}
          startDate={selectedJobToStop?.startDate}
          darkMode={darkMode}
          onSuccess={handleJobStopSuccess}
        />
      </div>
    </div>
  );
};

export default JobStatusAndLogs;
