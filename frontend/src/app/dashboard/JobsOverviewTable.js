'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { API_BASE_URL } from '../config';

const JobsOverviewTable = ({ onJobSelect, selectedJob }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const { darkMode } = useTheme();

  useEffect(() => {
    fetchJobsOverview();
  }, []);

  const fetchJobsOverview = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/jobs_overview`);
      const data = await response.json();
      
      if (Array.isArray(data)) {
        const formattedJobs = data.map(job => ({
          mapref: job[0],
          timesProcessed: job[1],
          avgSrcRows: job[2],
          avgTrgRows: job[3],
          maxDuration: job[4],
          minDuration: job[5]
        }));
        setJobs(formattedJobs);
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching jobs overview:', error);
      setLoading(false);
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handleJobClick = (jobName) => {
    if (onJobSelect) {
      onJobSelect(jobName);
    }
  };

  const sortedJobs = React.useMemo(() => {
    let sortableJobs = [...jobs];
    
    // Filter by search term
    if (searchTerm) {
      sortableJobs = sortableJobs.filter(job =>
        job.mapref.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Sort
    if (sortConfig.key) {
      sortableJobs.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    
    return sortableJobs;
  }, [jobs, searchTerm, sortConfig]);

  const formatDuration = (duration) => {
    if (!duration) return 'N/A';
    // Convert Oracle INTERVAL to readable format
    return duration.toString();
  };

  if (loading) {
    return (
      <div className={`rounded-xl shadow-sm border p-6 ${
        darkMode 
          ? 'bg-gray-800 border-gray-700' 
          : 'bg-white border-gray-200'
      }`}>
        <div className="animate-pulse">
          <div className={`h-6 rounded w-48 mb-4 ${
            darkMode ? 'bg-gray-600' : 'bg-gray-200'
          }`}></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, index) => (
              <div key={index} className={`h-12 rounded ${
                darkMode ? 'bg-gray-600' : 'bg-gray-200'
              }`}></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-xl shadow-sm border ${
      darkMode 
        ? 'bg-gray-800 border-gray-700' 
        : 'bg-white border-gray-200'
    }`}>
      <div className={`p-6 border-b ${
        darkMode ? 'border-gray-700' : 'border-gray-200'
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className={`text-lg font-semibold ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>Jobs Overview</h3>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Detailed information about all data warehouse jobs. Click on a job name to view its specific analytics.
            </p>
          </div>
          
          {/* Search */}
          <div className="mt-4 sm:mt-0">
            <div className="relative">
              <input
                type="text"
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`block w-full pl-10 pr-3 py-2 border rounded-md leading-5 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  darkMode 
                    ? 'border-gray-600 bg-gray-700 placeholder-gray-400 text-white' 
                    : 'border-gray-300 bg-white placeholder-gray-500 text-gray-900'
                }`}
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className={`h-5 w-5 ${
                  darkMode ? 'text-gray-500' : 'text-gray-400'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="max-h-96 overflow-y-auto">
          <table className={`min-w-full divide-y ${
            darkMode ? 'divide-gray-700' : 'divide-gray-200'
          }`}>
            <thead className={`sticky top-0 z-10 ${darkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
              <tr>
                {[
                  { key: 'mapref', label: 'Job Name (Map Ref)' },
                  { key: 'timesProcessed', label: 'Times Processed' },
                  { key: 'avgSrcRows', label: 'Avg Source Rows' },
                  { key: 'avgTrgRows', label: 'Avg Target Rows' },
                  { key: 'maxDuration', label: 'Max Duration' },
                  { key: 'minDuration', label: 'Min Duration' }
                ].map((column) => (
                  <th
                    key={column.key}
                    onClick={() => handleSort(column.key)}
                    className={`px-4 py-2 text-left text-xs font-medium uppercase tracking-wider cursor-pointer transition-colors ${
                      darkMode 
                        ? 'text-gray-400 hover:bg-gray-800' 
                        : 'text-gray-500 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center space-x-1">
                      <span>{column.label}</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                      </svg>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className={`divide-y ${
              darkMode 
                ? 'bg-gray-800 divide-gray-700' 
                : 'bg-white divide-gray-200'
            }`}>
              {sortedJobs.map((job, index) => {
                const isSelected = selectedJob === job.mapref;
                return (
                  <tr key={index} className={`transition-colors ${
                    isSelected 
                      ? (darkMode ? 'bg-blue-900/50 hover:bg-blue-900/60' : 'bg-blue-50 hover:bg-blue-100')
                      : (darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50')
                  }`}>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-6 w-6">
                          <div className={`h-6 w-6 rounded-full flex items-center justify-center ${
                            isSelected
                              ? (darkMode ? 'bg-blue-600' : 'bg-blue-500')
                              : (darkMode ? 'bg-blue-900' : 'bg-blue-100')
                          }`}>
                            <span className={`text-xs font-medium ${
                              isSelected
                                ? 'text-white'
                                : (darkMode ? 'text-blue-400' : 'text-blue-600')
                            }`}>
                              {job.mapref.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-3">
                          <button
                            onClick={() => handleJobClick(job.mapref)}
                            className={`text-sm font-medium text-left hover:underline focus:outline-none focus:underline transition-colors ${
                              isSelected
                                ? (darkMode ? 'text-blue-400' : 'text-blue-600')
                                : (darkMode ? 'text-white hover:text-blue-400' : 'text-gray-900 hover:text-blue-600')
                            }`}
                          >
                            {job.mapref}
                            {isSelected && (
                              <span className={`ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${
                                darkMode ? 'bg-blue-800 text-blue-200' : 'bg-blue-100 text-blue-800'
                              }`}>
                                Selected
                              </span>
                            )}
                          </button>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        darkMode 
                          ? 'bg-blue-900 text-blue-200' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {job.timesProcessed?.toLocaleString() || '0'}
                      </span>
                    </td>
                    <td className={`px-4 py-2.5 whitespace-nowrap text-sm ${
                      darkMode ? 'text-gray-300' : 'text-gray-900'
                    }`}>
                      {job.avgSrcRows?.toLocaleString() || '0'}
                    </td>
                    <td className={`px-4 py-2.5 whitespace-nowrap text-sm ${
                      darkMode ? 'text-gray-300' : 'text-gray-900'
                    }`}>
                      {job.avgTrgRows?.toLocaleString() || '0'}
                    </td>
                    <td className={`px-4 py-2.5 whitespace-nowrap text-sm ${
                      darkMode ? 'text-gray-300' : 'text-gray-900'
                    }`}>
                      {formatDuration(job.maxDuration)}
                    </td>
                    <td className={`px-4 py-2.5 whitespace-nowrap text-sm ${
                      darkMode ? 'text-gray-300' : 'text-gray-900'
                    }`}>
                      {formatDuration(job.minDuration)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {sortedJobs.length === 0 && (
          <div className="text-center py-12">
            <svg className={`mx-auto h-12 w-12 ${
              darkMode ? 'text-gray-500' : 'text-gray-400'
            }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className={`mt-2 text-sm font-medium ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>No jobs found</h3>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              {searchTerm ? 'Try adjusting your search criteria.' : 'No jobs available to display.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsOverviewTable; 