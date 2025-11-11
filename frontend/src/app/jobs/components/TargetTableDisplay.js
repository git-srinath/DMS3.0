import React from 'react';
import { Box, Typography, Chip, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { Storage } from '@mui/icons-material';

const TableTypeChip = styled(Chip)(({ theme, darkMode, tableType }) => ({
  height: '20px',
  fontSize: '0.675rem',
  fontWeight: 600,
  borderRadius: '4px',
  padding: '0 2px',
  marginLeft: '8px',
  backgroundColor: 
    tableType === 'FACT' ? (darkMode ? 'rgba(236, 72, 153, 0.2)' : 'rgba(236, 72, 153, 0.1)') :
    tableType === 'DIM' ? (darkMode ? 'rgba(79, 70, 229, 0.2)' : 'rgba(79, 70, 229, 0.1)') :
    tableType === 'STG' ? (darkMode ? 'rgba(14, 165, 233, 0.2)' : 'rgba(14, 165, 233, 0.1)') :
    (darkMode ? 'rgba(107, 114, 128, 0.2)' : 'rgba(107, 114, 128, 0.1)'),
  color: 
    tableType === 'FACT' ? (darkMode ? '#F472B6' : '#EC4899') :
    tableType === 'DIM' ? (darkMode ? '#818CF8' : '#4F46E5') :
    tableType === 'STG' ? (darkMode ? '#38BDF8' : '#0EA5E9') :
    (darkMode ? '#9CA3AF' : '#6B7280'),
  border: '1px solid',
  borderColor: 
    tableType === 'FACT' ? (darkMode ? 'rgba(236, 72, 153, 0.3)' : 'rgba(236, 72, 153, 0.2)') :
    tableType === 'DIM' ? (darkMode ? 'rgba(79, 70, 229, 0.3)' : 'rgba(79, 70, 229, 0.2)') :
    tableType === 'STG' ? (darkMode ? 'rgba(14, 165, 233, 0.3)' : 'rgba(14, 165, 233, 0.2)') :
    (darkMode ? 'rgba(107, 114, 128, 0.3)' : 'rgba(107, 114, 128, 0.2)'),
}));

/**
 * Displays formatted target table information
 */
const TargetTableDisplay = ({ targetSchema, targetTable, tableType, darkMode }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center' }}>
      <Tooltip title="Database Table" placement="top">
        <Storage 
          fontSize="small" 
          sx={{ 
            mr: 1, 
            color: darkMode ? 'primary.light' : 'primary.main',
            opacity: 0.8,
            fontSize: '1rem'
          }}
        />
      </Tooltip>
      
      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 500,
              fontSize: '0.875rem',
              fontFamily: 'monospace',
              letterSpacing: '0.01em',
            }}
          >
            {targetSchema}.{targetTable}
          </Typography>
          
          <TableTypeChip
            label={tableType}
            size="small"
            tableType={tableType}
            darkMode={darkMode}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default TargetTableDisplay; 