'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { API_BASE_URL } from '../config';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const JobsExecutionDurationChart = ({ selectedJob }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('7');
  const { darkMode } = useTheme();

  useEffect(() => {
    if (selectedJob) {
      fetchExecutionDurationData();
    }
  }, [selectedJob, period]);

  const fetchExecutionDurationData = async () => {
    if (!selectedJob) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/dashboard/jobs_executed_duration?mapref=${selectedJob}&period=${period}`
      );
      const data = await response.json();
      
      if (Array.isArray(data) && data.length > 0) {
        const labels = data.map(item => {
          const date = new Date(item[0]);
          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const durations = data.map(item => item[2]);
        
        setChartData({
          labels,
          datasets: [
            {
              label: 'Execution Duration (seconds)',
              data: durations,
              backgroundColor: 'rgba(147, 51, 234, 0.8)',
              borderColor: 'rgb(147, 51, 234)',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
            }
          ]
        });
      } else {
        setChartData({ labels: [], datasets: [] });
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching execution duration data:', error);
      setLoading(false);
    }
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
            weight: '500'
          }
        }
      },
      title: {
        display: false
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: function(context) {
            const seconds = context.parsed.y;
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.floor(seconds % 60);
            return `Duration: ${minutes}m ${remainingSeconds}s`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 11
          },
          color: '#6B7280',
          maxRotation: 45
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 11
          },
          color: '#6B7280',
          callback: function(value) {
            const minutes = Math.floor(value / 60);
            const seconds = Math.floor(value % 60);
            return `${minutes}m ${seconds}s`;
          }
        }
      }
    }
  };

  const periodOptions = [
    { value: '1', label: 'Last Day' },
    { value: '7', label: 'Last 7 Days' },
    { value: '30', label: 'Last 30 Days' }
  ];

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
            }`}>Execution Duration</h3>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Job execution time
              {selectedJob && (
                <span className={`ml-1 font-medium ${
                  darkMode ? 'text-purple-400' : 'text-purple-600'
                }`}>({selectedJob})</span>
              )}
            </p>
          </div>
          
          {/* Period Selector */}
          <div className="mt-4 sm:mt-0">
            <div className={`flex space-x-1 p-1 rounded-lg ${
              darkMode ? 'bg-gray-700' : 'bg-gray-100'
            }`}>
              {periodOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setPeriod(option.value)}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    period === option.value
                      ? darkMode 
                        ? 'bg-gray-600 text-purple-400 shadow-sm'
                        : 'bg-white text-purple-600 shadow-sm'
                      : darkMode
                        ? 'text-gray-300 hover:text-white'
                        : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto ${
                darkMode ? 'border-purple-400' : 'border-purple-600'
              }`}></div>
              <p className={`mt-2 text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-600'
              }`}>Loading chart data...</p>
            </div>
          </div>
        ) : chartData && chartData.labels.length > 0 ? (
          <div className="h-80">
            <Bar data={chartData} options={options} />
          </div>
        ) : (
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <svg className={`mx-auto h-12 w-12 ${
                darkMode ? 'text-gray-500' : 'text-gray-400'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className={`mt-2 text-sm font-medium ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>No data available</h3>
              <p className={`mt-1 text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                {selectedJob ? 'No execution duration data found for the selected period.' : 'Please select a job to view data.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsExecutionDurationChart; 