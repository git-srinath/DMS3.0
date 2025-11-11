'use client'

import React, { useState, useEffect } from 'react'
import { useTheme } from '@/context/ThemeContext'
import ReferenceTable from './ReferenceTable'
import ReferenceForm from './ReferenceForm'
import LockDialog from './LockDialog'
import { checkReferenceLock, overrideReferenceLock, releaseReferenceLock } from './lockUtils'
import { message } from 'antd'

const MapperModule = () => {
  const { darkMode } = useTheme()
  // const muiTheme = useMuiTheme()

  // New state variables for the table view
  const [showReferenceTable, setShowReferenceTable] = useState(true)
  const [showMapperForm, setShowMapperForm] = useState(false)
  
  const [selectedReference, setSelectedReference] = useState(null)
  
  // Add state for lock dialog
  const [showLockDialog, setShowLockDialog] = useState(false)
  const [lockInfo, setLockInfo] = useState(null)
  const [isOverridingLock, setIsOverridingLock] = useState(false)
  const [pendingReference, setPendingReference] = useState(null)

  // Function to handle creating a new reference
  const handleCreateNewReference = () => {
    // Reset form data
    setSelectedReference(null)

    // Show the mapper form and hide the reference table
    setShowReferenceTable(false)
    setShowMapperForm(true)
  }

  // Function to handle editing an existing reference
  const handleEditReference = async (reference) => {
    if (reference) {
      // Check if the reference is locked by another user
      const lockStatus = await checkReferenceLock(reference);
      
      if (lockStatus.isLocked) {
        // Show lock dialog
        setLockInfo(lockStatus);
        setShowLockDialog(true);
        setPendingReference(reference);
        return;
      }
      
      // If not locked, proceed with editing
      setSelectedReference(reference);
      setShowReferenceTable(false);
      setShowMapperForm(true);
    }
  }

  // Function to handle lock failure from within the ReferenceForm
  const handleLockFailed = (lockStatus) => {
    if (lockStatus.isLocked) {
      // Show lock dialog
      setLockInfo(lockStatus);
      setShowLockDialog(true);
      
      // Return to table view
      setShowMapperForm(false);
      setShowReferenceTable(true);
      setSelectedReference(null);
    }
  }

  // Function to return to the reference table view
  const handleReturnToReferenceTable = () => {
    // Release any existing lock if there's a selected reference
    if (selectedReference) {
      console.log(`Page component: Releasing lock for reference: ${selectedReference}`);
      
      // Clean up local storage first
      localStorage.removeItem(`mapper_lock_${selectedReference}`);
      
      // Then call API
      releaseReferenceLock(selectedReference)
        .then(result => {
          console.log(`Page component: Lock release result for ${selectedReference}:`, result);
        })
        .catch(error => {
          console.error('Page component: Error releasing lock:', error);
        });
    }
    
    setShowMapperForm(false);
    setShowReferenceTable(true);
    setSelectedReference(null);
  }
  
  // Function to handle overriding a lock
  const handleOverrideLock = async () => {
    setIsOverridingLock(true);
    try {
      const result = await overrideReferenceLock(pendingReference);
      
      if (result) {
        // Lock override successful
        message.success('Lock overridden successfully');
        setShowLockDialog(false);
        
        // Proceed with editing
        setSelectedReference(pendingReference);
        setShowReferenceTable(false);
        setShowMapperForm(true);
      } else {
        message.error('Failed to override lock');
      }
    } catch (error) {
      console.error('Error overriding lock:', error);
      message.error('Failed to override lock');
    } finally {
      setIsOverridingLock(false);
      setPendingReference(null);
    }
  }
  
  // Function to close lock dialog
  const handleCloseLockDialog = () => {
    setShowLockDialog(false);
    setPendingReference(null);
    setLockInfo(null);
  }

  return (
    <div
      className={`p-4 min-h-screen ${
        darkMode
          ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900'
          : 'bg-gradient-to-br from-gray-50 via-white to-gray-50'
      } 
      text-${darkMode ? 'white' : 'gray-800'}`}
      style={{ fontSize: 'clamp(0.875rem, 1vw, 1rem)' }}
    >
      {/* Reference Table View */}
      {showReferenceTable && (
        <ReferenceTable
          handleEditReference={handleEditReference}
          handleCreateNewReference={handleCreateNewReference}
        />
      )}

      {/* Mapper Configuration Form - Updated */}
      {showMapperForm && (
        <ReferenceForm
          handleReturnToReferenceTable={handleReturnToReferenceTable}
          reference={selectedReference}
          onLockFailed={handleLockFailed}
        />
      )}
      
      {/* Lock Dialog */}
      <LockDialog 
        open={showLockDialog}
        onClose={handleCloseLockDialog}
        lockInfo={lockInfo}
        onOverrideLock={handleOverrideLock}
        isOverriding={isOverridingLock}
      />

      <style jsx global>{`
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        ::-webkit-scrollbar-track {
          background: ${darkMode ? '#1F2937' : '#F3F4F6'};
        }

        ::-webkit-scrollbar-thumb {
          background: ${darkMode ? '#4B5563' : '#9CA3AF'};
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: ${darkMode ? '#6B7280' : '#6B7280'};
        }

        /* Add smooth transitions for all elements */
        * {
          transition: background-color 0.2s ease, border-color 0.2s ease,
            box-shadow 0.2s ease;
        }

        /* Enhance table row hover effect */
        .MuiTableRow-root:hover {
          transition: background-color 0.15s ease !important;
        }

        /* Make buttons more interactive */
        .MuiButton-root,
        .MuiIconButton-root {
          transition: transform 0.1s ease, box-shadow 0.2s ease !important;
        }

        .MuiButton-root:active,
        .MuiIconButton-root:active {
          transform: scale(0.97);
        }

        /* Scaling adjustments */
        .mapper-module-container {
          /* Used to apply scale transformation to the whole component */
          /* transform origin is set to top to avoid layout shift issues */
          margin-bottom: -5vh; /* Compensate for the reduction in height; reduced from -10vh to -5vh */
        }

        /* Adjust typography sizes to be more proportional */
        .MuiTypography-root {
          font-size: 0.9em;
        }

        /* Make form controls more compact */
        .MuiOutlinedInput-root {
          font-size: 0.9rem;
        }

        .MuiInputLabel-root {
          font-size: 0.8rem;
        }

        /* Adjust button sizes for better proportions */
        .MuiButton-root {
          font-size: 0.85rem;
          padding: 4px 16px;
        }

        /* Adjust table cells for better proportions */
        .MuiTableCell-root {
          padding: 8px 12px;
          font-size: 0.85rem;
        }
      `}</style>
    </div>
  )
}

export default MapperModule
