'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { API_BASE_URL } from '../config';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const JobsProcessedRowsChart = ({ selectedJob }) => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('WEEK');
  const { darkMode } = useTheme();

  useEffect(() => {
    if (selectedJob) {
      fetchProcessedRowsData();
    }
  }, [selectedJob, period]);

  const fetchProcessedRowsData = async () => {
    if (!selectedJob) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/dashboard/jobs_processed_rows?mapref=${selectedJob}&period=${period}`
      );
      const data = await response.json();
      
      if (Array.isArray(data)) {
        const labels = data.map(item => item[1]); // TIME_GROUP
        const srcRows = data.map(item => item[2]); // TOTAL_SRCROWS
        const trgRows = data.map(item => item[3]); // TOTAL_TRGROWS
        
        setChartData({
          labels,
          datasets: [
            {
              label: 'Source Rows',
              data: srcRows,
              borderColor: 'rgb(59, 130, 246)',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              fill: true,
              tension: 0.4,
              pointBackgroundColor: 'rgb(59, 130, 246)',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              pointRadius: 6,
              pointHoverRadius: 8,
            },
            {
              label: 'Target Rows',
              data: trgRows,
              borderColor: 'rgb(16, 185, 129)',
              backgroundColor: 'rgba(16, 185, 129, 0.1)',
              fill: true,
              tension: 0.4,
              pointBackgroundColor: 'rgb(16, 185, 129)',
              pointBorderColor: '#fff',
              pointBorderWidth: 2,
              pointRadius: 6,
              pointHoverRadius: 8,
            }
          ]
        });
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching processed rows data:', error);
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
            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} rows`;
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
          color: '#6B7280'
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
            return value.toLocaleString();
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index'
    }
  };

  const periodOptions = [
    { value: 'DAY', label: 'Today' },
    { value: 'WEEK', label: 'Last 7 Days' },
    { value: 'MONTH', label: 'Last 30 Days' },
    { value: 'ALL', label: 'All' }
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
            }`}>Processed Rows</h3>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Source and target rows processed over time
              {selectedJob && (
                <span className={`ml-1 font-medium ${
                  darkMode ? 'text-blue-400' : 'text-blue-600'
                }`}>({selectedJob})</span>
              )}
            </p>
          </div>
          
          {/* Period Selector */}
          <div className="mt-4 sm:mt-0">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              className={`
                w-full sm:w-48 px-3 py-2 rounded-lg border text-sm
                ${darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white' 
                  : 'bg-gray-50 border-gray-300 text-gray-900'}
                focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all
              `}
            >
              {periodOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto ${
                darkMode ? 'border-blue-400' : 'border-blue-600'
              }`}></div>
              <p className={`mt-2 text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-600'
              }`}>Loading chart data...</p>
            </div>
          </div>
        ) : chartData && chartData.labels.length > 0 ? (
          <div className="h-80">
            <Line data={chartData} options={options} />
          </div>
        ) : (
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <svg className={`mx-auto h-12 w-12 ${
                darkMode ? 'text-gray-500' : 'text-gray-400'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className={`mt-2 text-sm font-medium ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>No data available</h3>
              <p className={`mt-1 text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                {selectedJob ? 'No processed rows data found for the selected period.' : 'Please select a job to view data.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsProcessedRowsChart; 