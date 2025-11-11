import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Tooltip, 
  IconButton, 
  Chip,
  CircularProgress
} from '@mui/material';
import { 
  Link as LinkIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import DependencyModal from './DependencyModal';
import axios from 'axios';

/**
 * DependencyDisplay component for showing job dependencies
 * Displays either "No dependency" or the dependency as a chip
 * Clicking opens a modal to configure dependencies
 */
const DependencyDisplay = ({ 
  jobId, 
  mapRef, 
  dependency,
  darkMode,
  onDependencyUpdated,
  job,
  allJobs = []
}) => {
  const [openModal, setOpenModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [dependentMapRef, setDependentMapRef] = useState(null);

  // Find the dependent job map reference based on DPND_JOBSCHID
  useEffect(() => {
    if (job?.DPND_JOBSCHID) {
      // Find the job with matching JOBSCHID
      const dependentJob = allJobs.find(j => j.JOBSCHID === job.DPND_JOBSCHID);
      if (dependentJob) {
        setDependentMapRef(dependentJob.MAPREF);
      }
    } else {
      setDependentMapRef(null);
    }
  }, [job, allJobs]);

  // Use direct map reference if available, otherwise use resolved dependentMapRef
  const dependencyMapRef = dependency || dependentMapRef || job?.DPND_MAPREF || null;

  // Open/close modal
  const handleOpenModal = () => setOpenModal(true);
  const handleCloseModal = () => setOpenModal(false);

  // Save the job dependency
  const handleSaveDependency = async (dependencyData) => {
    setSaving(true);
    setError(null);
    try {
      // Find the job with this map reference to get its JOBSCHID
      const dependentJob = allJobs.find(j => j.MAPREF === dependencyData.DPND_MAPREF);
      
      if (!dependentJob && dependencyData.DPND_MAPREF) {
        throw new Error(`Could not find job with Map Reference: ${dependencyData.DPND_MAPREF}`);
      }
      
      // Prepare the request data in the format expected by the backend
      const requestData = {
        PARENT_MAP_REFERENCE: dependencyData.DPND_MAPREF,
        CHILD_MAP_REFERENCE: mapRef
      };

      // Call the API to save dependency
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/job/save_parent_child_job`, 
        requestData
      );
      
      if (response.data && response.data.success) {
        // Notify parent component to refresh data
        if (onDependencyUpdated) {
          onDependencyUpdated(dependencyData.DPND_MAPREF);
        }
        return true;
      } else {
        throw new Error(response.data?.message || 'Failed to save dependency');
      }
    } catch (err) {
      console.error('Error saving dependency:', err);
      setError('Failed to save');
      return false;
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center',
      gap: 1,
      position: 'relative'
    }}>
      {/* Dependency Display */}
      {dependencyMapRef ? (
        <Box 
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            cursor: 'pointer',
            '&:hover .edit-icon': {
              opacity: 1
            }
          }}
          onClick={handleOpenModal}
        >
          <Tooltip title={`This job depends on ${dependencyMapRef}`}>
            <Chip
              icon={<LinkIcon fontSize="small" />}
              label={dependencyMapRef}
              size="small"
              color="primary"
              variant="outlined"
              sx={{
                fontSize: '0.75rem',
                height: '28px',
                borderRadius: '4px',
                '& .MuiChip-label': {
                  px: 1
                },
                '& .MuiChip-icon': {
                  fontSize: '0.875rem'
                }
              }}
              clickable
            />
          </Tooltip>
          <IconButton 
            className="edit-icon"
            size="small" 
            sx={{ 
              opacity: 0,
              transition: 'opacity 0.2s',
              width: '22px',
              height: '22px',
              color: darkMode ? 'rgba(156, 163, 175, 0.8)' : 'rgba(107, 114, 128, 0.8)'
            }}
            onClick={(e) => {
              e.stopPropagation();
              handleOpenModal();
            }}
          >
            <EditIcon fontSize="small" sx={{ fontSize: '0.875rem' }} />
          </IconButton>
        </Box>
      ) : (
        <Box 
          onClick={handleOpenModal}
          sx={{ 
            display: 'flex',
            alignItems: 'center',
            gap: 0.5,
            color: darkMode ? 'rgba(156, 163, 175, 0.7)' : 'rgba(107, 114, 128, 0.7)',
            borderRadius: '4px',
            border: '1px dashed',
            borderColor: darkMode ? 'rgba(156, 163, 175, 0.3)' : 'rgba(107, 114, 128, 0.3)',
            px: 1.5,
            py: 0.5,
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              borderColor: darkMode ? 'rgba(156, 163, 175, 0.5)' : 'rgba(107, 114, 128, 0.5)',
              backgroundColor: darkMode ? 'rgba(55, 65, 81, 0.1)' : 'rgba(243, 244, 246, 0.5)'
            }
          }}
        >
          <Typography 
            variant="caption" 
            sx={{ 
              fontSize: '0.75rem',
              fontStyle: 'italic'
            }}
          >
            No dependency
          </Typography>
        </Box>
      )}
      
      {/* Loading indicator while saving */}
      {saving && (
        <CircularProgress size={16} sx={{ ml: 1 }} />
      )}
      
      {/* Error message */}
      {error && (
        <Typography 
          variant="caption" 
          color="error" 
          sx={{ fontSize: '0.7rem', ml: 1 }}
        >
          {error}
        </Typography>
      )}
      
      {/* Dependency Modal */}
      <DependencyModal
        open={openModal}
        handleClose={handleCloseModal}
        jobId={jobId}
        mapRef={mapRef}
        currentDependency={dependencyMapRef}
        darkMode={darkMode}
        onSaveDependency={handleSaveDependency}
        allJobs={allJobs}
      />
    </Box>
  );
};

export default DependencyDisplay; 