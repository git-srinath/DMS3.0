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

const JobsAverageRunDurationChart = () => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { darkMode } = useTheme();

  useEffect(() => {
    fetchAverageRunDurationData();
  }, []);

  const fetchAverageRunDurationData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/jobs_average_run_duration`);
      const data = await response.json();
      
      if (Array.isArray(data)) {
        const labels = data.map(item => item[0]); // JOB_NAME
        const durations = data.map(item => item[1]); // AVG_SECONDS
        
        // Generate colors for each bar
        const colors = labels.map((_, index) => {
          const hue = (index * 137.508) % 360; // Golden angle approximation
          return `hsla(${hue}, 70%, 60%, 0.8)`;
        });
        
        const borderColors = labels.map((_, index) => {
          const hue = (index * 137.508) % 360;
          return `hsla(${hue}, 70%, 50%, 1)`;
        });
        
        setChartData({
          labels,
          datasets: [
            {
              label: 'Average Run Duration (seconds)',
              data: durations,
              backgroundColor: colors,
              borderColor: borderColors,
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
            }
          ]
        });
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching average run duration data:', error);
      setLoading(false);
    }
  };

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
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
        displayColors: false,
        callbacks: {
          label: function(context) {
            const seconds = context.parsed.x;
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = Math.floor(seconds % 60);
            return `Average Duration: ${minutes}m ${remainingSeconds}s`;
          }
        }
      }
    },
    scales: {
      x: {
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
      },
      y: {
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 11
          },
          color: '#6B7280'
        }
      }
    }
  };

  return (
    <div className={`rounded-xl shadow-sm border ${
      darkMode 
        ? 'bg-gray-800 border-gray-700' 
        : 'bg-white border-gray-200'
    }`}>
      <div className={`p-6 border-b ${
        darkMode ? 'border-gray-700' : 'border-gray-200'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className={`text-lg font-semibold ${
              darkMode ? 'text-white' : 'text-gray-900'
            }`}>Average Run Duration</h3>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Average execution time for all jobs
            </p>
          </div>
          
          {/* Stats Summary */}
          {chartData && chartData.datasets[0].data.length > 0 && (
            <div className="text-right">
              <div className={`text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Total Jobs</div>
              <div className={`text-2xl font-bold ${
                darkMode ? 'text-indigo-400' : 'text-indigo-600'
              }`}>
                {chartData.datasets[0].data.length}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto ${
                darkMode ? 'border-indigo-400' : 'border-indigo-600'
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className={`mt-2 text-sm font-medium ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>No data available</h3>
              <p className={`mt-1 text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                No average run duration data found.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsAverageRunDurationChart; 