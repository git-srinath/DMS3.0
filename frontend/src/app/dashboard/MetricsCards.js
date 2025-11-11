'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { API_BASE_URL } from '../config';

const MetricsCards = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const { darkMode } = useTheme();

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard/all_metrics`);
      const data = await response.json();
      
      if (Array.isArray(data) && data.length > 0) {
        const metricsData = data[0]; // First row contains all metrics
        setMetrics({
          totalMappings: metricsData[0],
          logicVerified: metricsData[1],
          activeMappings: metricsData[2],
          totalJobs: metricsData[3],
          activeJobs: metricsData[4],
          jobFlowCreated: metricsData[5],
          scheduleCreated: metricsData[6]
        });
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
    }
  };

  const metricCards = [
    {
      title: 'Total Mappings',
      value: metrics?.totalMappings || 0,
      icon: '📊',
      color: 'from-blue-500 to-blue-600',
      bgColor: darkMode ? 'bg-blue-900 bg-opacity-20' : 'bg-blue-50',
      textColor: darkMode ? 'text-blue-400' : 'text-blue-600'
    },
    {
      title: 'Logic Verified',
      value: metrics?.logicVerified || 0,
      icon: '✅',
      color: 'from-green-500 to-green-600',
      bgColor: darkMode ? 'bg-green-900 bg-opacity-20' : 'bg-green-50',
      textColor: darkMode ? 'text-green-400' : 'text-green-600'
    },
    {
      title: 'Active Mappings',
      value: metrics?.activeMappings || 0,
      icon: '🟢',
      color: 'from-emerald-500 to-emerald-600',
      bgColor: darkMode ? 'bg-emerald-900 bg-opacity-20' : 'bg-emerald-50',
      textColor: darkMode ? 'text-emerald-400' : 'text-emerald-600'
    },
    {
      title: 'Total Jobs',
      value: metrics?.totalJobs || 0,
      icon: '⚙️',
      color: 'from-purple-500 to-purple-600',
      bgColor: darkMode ? 'bg-purple-900 bg-opacity-20' : 'bg-purple-50',
      textColor: darkMode ? 'text-purple-400' : 'text-purple-600'
    },
    {
      title: 'Active Jobs',
      value: metrics?.activeJobs || 0,
      icon: '🔄',
      color: 'from-orange-500 to-orange-600',
      bgColor: darkMode ? 'bg-orange-900 bg-opacity-20' : 'bg-orange-50',
      textColor: darkMode ? 'text-orange-400' : 'text-orange-600'
    },
    {
      title: 'Job Flows Created',
      value: metrics?.jobFlowCreated || 0,
      icon: '🔗',
      color: 'from-indigo-500 to-indigo-600',
      bgColor: darkMode ? 'bg-indigo-900 bg-opacity-20' : 'bg-indigo-50',
      textColor: darkMode ? 'text-indigo-400' : 'text-indigo-600'
    }
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {[...Array(6)].map((_, index) => (
          <div key={index} className={`rounded-xl shadow-sm border p-6 animate-pulse ${
            darkMode 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <div className={`h-4 rounded w-20 mb-2 ${
                  darkMode ? 'bg-gray-600' : 'bg-gray-200'
                }`}></div>
                <div className={`h-8 rounded w-16 ${
                  darkMode ? 'bg-gray-600' : 'bg-gray-200'
                }`}></div>
              </div>
              <div className={`h-12 w-12 rounded-full ${
                darkMode ? 'bg-gray-600' : 'bg-gray-200'
              }`}></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {metricCards.map((card, index) => (
        <div
          key={index}
          className={`rounded-xl shadow-sm border hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 ${
            darkMode 
              ? 'bg-gray-800 border-gray-700' 
              : 'bg-white border-gray-200'
          }`}
        >
          <div className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-medium mb-1 ${
                  darkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  {card.title}
                </p>
                <p className={`text-2xl font-bold ${card.textColor}`}>
                  {card.value?.toLocaleString() || '0'}
                </p>
              </div>
              <div className={`${card.bgColor} p-3 rounded-full`}>
                <span className="text-2xl">{card.icon}</span>
              </div>
            </div>
            
            {/* Progress bar */}
            <div className="mt-4">
              <div className={`w-full rounded-full h-2 ${
                darkMode ? 'bg-gray-700' : 'bg-gray-200'
              }`}>
                <div 
                  className={`bg-gradient-to-r ${card.color} h-2 rounded-full transition-all duration-1000 ease-out`}
                  style={{ width: `${Math.min((card.value / Math.max(...metricCards.map(c => c.value))) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MetricsCards; 