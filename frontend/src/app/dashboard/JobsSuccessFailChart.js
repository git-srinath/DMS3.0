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

const JobsSuccessFailChart = () => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ totalSuccess: 0, totalFailed: 0, successRate: 0 });
  const { darkMode } = useTheme();

  useEffect(() => {
    fetchSuccessFailData();
  }, []);

  const fetchSuccessFailData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/jobs_successful_failed`);
      const data = await response.json();
      
      if (Array.isArray(data)) {
        const labels = data.map(item => item[0]); // job_name_prefix
        const failedCounts = data.map(item => item[1]); // failed_count
        const succeededCounts = data.map(item => item[2]); // succeeded_count
        
        // Calculate stats
        const totalSuccess = succeededCounts.reduce((sum, count) => sum + count, 0);
        const totalFailed = failedCounts.reduce((sum, count) => sum + count, 0);
        const successRate = totalSuccess + totalFailed > 0 ? (totalSuccess / (totalSuccess + totalFailed)) * 100 : 0;
        
        setStats({ totalSuccess, totalFailed, successRate });
        
        setChartData({
          labels,
          datasets: [
            {
              label: 'Successful',
              data: succeededCounts,
              backgroundColor: 'rgba(34, 197, 94, 0.8)',
              borderColor: 'rgb(34, 197, 94)',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
            },
            {
              label: 'Failed',
              data: failedCounts,
              backgroundColor: 'rgba(239, 68, 68, 0.8)',
              borderColor: 'rgb(239, 68, 68)',
              borderWidth: 1,
              borderRadius: 6,
              borderSkipped: false,
            }
          ]
        });
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching success/fail data:', error);
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
            return `${context.dataset.label}: ${context.parsed.y.toLocaleString()} executions`;
          },
          afterBody: function(tooltipItems) {
            const dataIndex = tooltipItems[0].dataIndex;
            const succeeded = chartData.datasets[0].data[dataIndex];
            const failed = chartData.datasets[1].data[dataIndex];
            const total = succeeded + failed;
            const successRate = total > 0 ? ((succeeded / total) * 100).toFixed(1) : 0;
            return [`Total: ${total.toLocaleString()}`, `Success Rate: ${successRate}%`];
          }
        }
      }
    },
    scales: {
      x: {
        stacked: true,
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
        stacked: true,
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
            }`}>Job Success & Failure Rate</h3>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Success and failure counts for all jobs
            </p>
          </div>
          
          {/* Stats Summary */}
          <div className="flex space-x-6">
            <div className="text-center">
              <div className={`text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Success Rate</div>
              <div className={`text-2xl font-bold ${
                darkMode ? 'text-green-400' : 'text-green-600'
              }`}>
                {stats.successRate.toFixed(1)}%
              </div>
            </div>
            <div className="text-center">
              <div className={`text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Total Success</div>
              <div className={`text-lg font-semibold ${
                darkMode ? 'text-green-400' : 'text-green-600'
              }`}>
                {stats.totalSuccess.toLocaleString()}
              </div>
            </div>
            <div className="text-center">
              <div className={`text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Total Failed</div>
              <div className={`text-lg font-semibold ${
                darkMode ? 'text-red-400' : 'text-red-600'
              }`}>
                {stats.totalFailed.toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="text-center">
              <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto ${
                darkMode ? 'border-green-400' : 'border-green-600'
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className={`mt-2 text-sm font-medium ${
                darkMode ? 'text-white' : 'text-gray-900'
              }`}>No data available</h3>
              <p className={`mt-1 text-sm ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                No success/failure data found.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobsSuccessFailChart; 