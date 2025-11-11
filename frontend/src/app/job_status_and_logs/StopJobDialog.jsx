import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, X, AlertCircle, AlertOctagon } from 'lucide-react';
import { API_BASE_URL } from '../config';

const StopJobDialog = ({ open, onClose, jobName, startDate, darkMode, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stopOption, setStopOption] = useState('');

  if (!open) return null;

  const handleStopJob = async (force) => {
    try {
      setLoading(true);
      setError(null);

      // Format date properly for Oracle
      let formattedDate = startDate;
      
      // If startDate is a valid date string, ensure it's in ISO format
      if (startDate) {
        try {
          // Try to create a Date object from the startDate
          const dateObj = new Date(startDate);
          
          // Check if it's a valid date
          if (!isNaN(dateObj.getTime())) {
            // Use the raw date components to create a date string in YYYY-MM-DD HH:MM:SS format
            // This avoids timezone issues that can cause date offsets
            const year = dateObj.getFullYear();
            const month = String(dateObj.getMonth() + 1).padStart(2, '0');
            const day = String(dateObj.getDate()).padStart(2, '0');
            const hours = String(dateObj.getHours()).padStart(2, '0');
            const minutes = String(dateObj.getMinutes()).padStart(2, '0');
            const seconds = String(dateObj.getSeconds()).padStart(2, '0');
            
            formattedDate = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
            console.log("Original date:", startDate);
            console.log("Formatted date for API:", formattedDate);
          }
        } catch (err) {
          console.error("Error formatting date:", err);
          // Keep the original date format if there's an error
        }
      }

      const response = await fetch(`${API_BASE_URL}/job/stop-running-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          mapref: jobName,
          startDate: formattedDate,
          force: force
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to stop job');
      }

      // Call onSuccess callback with the response data
      if (onSuccess) {
        onSuccess(data);
      }

      // Close dialog after successful stop
      onClose();
    } catch (err) {
      setError(err.message || 'An error occurred while stopping the job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className={`
            w-full max-w-md rounded-lg shadow-xl overflow-hidden
            ${darkMode ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'}
          `}
        >
          <div className={`px-6 py-4 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-amber-500" />
                Stop Running Job
              </h3>
              <button
                onClick={onClose}
                className={`
                  p-1 rounded-full hover:bg-opacity-20 transition-colors
                  ${darkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-200'}
                `}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="px-6 py-4">
            <div className={`mb-4 p-3 rounded-md ${darkMode ? 'bg-amber-900/30 text-amber-200' : 'bg-amber-50 text-amber-800'}`}>
              <p className="text-sm flex items-start">
                <AlertCircle className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                <span>
                  You are about to stop the job <strong>{jobName}</strong>. 
                  Please select how you would like to stop this job:
                </span>
              </p>
            </div>

            <div className="space-y-3 mb-6">
              <div 
                className={`
                  p-4 rounded-lg border-2 cursor-pointer transition-all
                  ${stopOption === 'Y' 
                    ? darkMode 
                      ? 'border-red-500 bg-red-900/20' 
                      : 'border-red-500 bg-red-50' 
                    : darkMode 
                      ? 'border-gray-700 hover:border-red-500/50' 
                      : 'border-gray-200 hover:border-red-300'}
                `}
                onClick={() => setStopOption('Y')}
              >
                <div className="flex items-start">
                  <div className={`
                    w-5 h-5 rounded-full mr-3 mt-0.5 flex items-center justify-center flex-shrink-0
                    ${stopOption === 'Y' 
                      ? 'bg-red-500 text-white' 
                      : darkMode ? 'bg-gray-700' : 'bg-gray-200'}
                  `}>
                    {stopOption === 'Y' && <span className="text-xs">✓</span>}
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-1 flex items-center">
                      <AlertOctagon className="w-4 h-4 mr-1 text-red-500" />
                      Stop Immediately (Force)
                    </h4>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Forcefully terminate the job immediately. This may leave data in an inconsistent state.
                    </p>
                  </div>
                </div>
              </div>

              <div 
                className={`
                  p-4 rounded-lg border-2 cursor-pointer transition-all
                  ${stopOption === 'N' 
                    ? darkMode 
                      ? 'border-amber-500 bg-amber-900/20' 
                      : 'border-amber-500 bg-amber-50' 
                    : darkMode 
                      ? 'border-gray-700 hover:border-amber-500/50' 
                      : 'border-gray-200 hover:border-amber-300'}
                `}
                onClick={() => setStopOption('N')}
              >
                <div className="flex items-start">
                  <div className={`
                    w-5 h-5 rounded-full mr-3 mt-0.5 flex items-center justify-center flex-shrink-0
                    ${stopOption === 'N' 
                      ? 'bg-amber-500 text-white' 
                      : darkMode ? 'bg-gray-700' : 'bg-gray-200'}
                  `}>
                    {stopOption === 'N' && <span className="text-xs">✓</span>}
                  </div>
                  <div>
                    <h4 className="font-medium text-sm mb-1">Graceful Stop</h4>
                    <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      Wait for the current iteration to complete before stopping. This is safer for data integrity.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {error && (
              <div className={`mb-4 p-3 rounded-md ${darkMode ? 'bg-red-900/30 text-red-200' : 'bg-red-50 text-red-800'}`}>
                <p className="text-sm">{error}</p>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={onClose}
                className={`
                  px-4 py-2 rounded-md text-sm font-medium transition-colors
                  ${darkMode 
                    ? 'bg-gray-700 hover:bg-gray-600 text-white' 
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-800'}
                `}
                disabled={loading}
              >
                Cancel
              </button>
              <button
                onClick={() => handleStopJob(stopOption)}
                disabled={!stopOption || loading}
                className={`
                  px-4 py-2 rounded-md text-sm font-medium transition-colors
                  ${!stopOption || loading
                    ? darkMode 
                      ? 'bg-gray-700 text-gray-400 cursor-not-allowed' 
                      : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : stopOption === 'Y'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-amber-600 hover:bg-amber-700 text-white'
                  }
                `}
              >
                {loading ? 'Stopping...' : 'Stop Job'}
              </button>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default StopJobDialog; 