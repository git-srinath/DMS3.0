import React from 'react';
import { Box, Tooltip, Chip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  CheckCircleOutline as CheckCircleIcon,
  AccessTime as AccessTimeIcon
} from '@mui/icons-material';

const StatusChip = styled(Chip)(({ theme, darkMode, status }) => ({
  height: '24px',
  fontWeight: 600,
  fontSize: '0.75rem',
  borderRadius: '6px',
  backgroundColor: 
    status === 'Scheduled' ? (darkMode ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.1)') :
    (darkMode ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)'),
  color: 
    status === 'Scheduled' ? (darkMode ? '#4ADE80' : '#22C55E') :
    (darkMode ? '#FBBF24' : '#D97706'),
  border: '1px solid',
  borderColor: 
    status === 'Scheduled' ? (darkMode ? 'rgba(34, 197, 94, 0.3)' : 'rgba(34, 197, 94, 0.2)') :
    (darkMode ? 'rgba(245, 158, 11, 0.3)' : 'rgba(245, 158, 11, 0.2)'),
  '& .MuiChip-label': {
    padding: '0 8px',
    display: 'flex',
    alignItems: 'center',
    gap: '4px'
  }
}));

/**
 * StatusIndicator component that displays the job schedule status
 * 
 * @param {Object} props Component props
 * @param {string} props.status Status to display (e.g. "Scheduled", "Not Scheduled")
 * @param {boolean} props.darkMode Whether dark mode is enabled
 * @returns {JSX.Element} Rendered component
 */
const StatusIndicator = ({ status, darkMode }) => {
  const isScheduled = status === 'Scheduled';
  
  return (
    <Tooltip title={status || 'Status unknown'} arrow>
      <StatusChip
        label={
          <>
            {isScheduled ? (
              <CheckCircleIcon fontSize="small" sx={{ fontSize: 16 }} />
            ) : (
              <AccessTimeIcon fontSize="small" sx={{ fontSize: 16 }} />
            )}
            {status || 'Unknown'}
          </>
        }
        status={status}
        darkMode={darkMode}
        size="small"
      />
    </Tooltip>
  );
};

export default StatusIndicator; 