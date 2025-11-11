import React from 'react';
import { Box, Typography, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { DeviceHub } from '@mui/icons-material';

const MapRefContainer = styled(Box)(({ theme, darkMode }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: '6px 12px',
  borderRadius: '8px',
  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(249, 250, 251, 0.7)',
  border: '1px solid',
  borderColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
  transition: 'all 0.2s ease',
  boxShadow: darkMode ? '0 2px 5px rgba(0, 0, 0, 0.15)' : '0 1px 3px rgba(0, 0, 0, 0.05)',
  '&:hover': {
    backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.5)' : 'rgba(249, 250, 251, 0.9)',
    transform: 'translateY(-1px)',
    boxShadow: darkMode ? '0 3px 6px rgba(0, 0, 0, 0.2)' : '0 2px 5px rgba(0, 0, 0, 0.08)',
  }
}));

/**
 * MappingDetails component displays the mapping reference
 * 
 * @param {Object} props Component props
 * @param {string} props.mapRef Mapping reference value
 * @param {boolean} props.darkMode Whether dark mode is enabled
 * @returns {JSX.Element} Rendered component
 */
const MappingDetails = ({ mapRef, darkMode }) => {
  if (!mapRef) return null;
  
  return (
    <Tooltip title="Job Mapping Reference" placement="top">
      <MapRefContainer darkMode={darkMode}>
        <DeviceHub 
          fontSize="small" 
          sx={{ 
            mr: 1, 
            color: darkMode ? 'primary.light' : 'primary.main',
            opacity: 0.8,
            fontSize: '1rem'
          }}
        />
        <Typography
          variant="body2"
          sx={{
            fontWeight: 600,
            fontSize: '0.875rem',
            fontFamily: 'monospace',
            letterSpacing: '0.02em',
            color: darkMode ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.8)',
          }}
        >
          {mapRef}
        </Typography>
      </MapRefContainer>
    </Tooltip>
  );
};

export default MappingDetails; 