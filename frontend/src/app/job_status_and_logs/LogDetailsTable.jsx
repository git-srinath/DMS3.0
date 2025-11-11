import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Chip,
  Badge,
  useMediaQuery
} from '@mui/material';
import { styled, alpha, useTheme as useMuiTheme } from '@mui/material/styles';
import { 
  Error as ErrorIcon, 
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon, 
  TrendingDown as TrendingDownIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { motion } from 'framer-motion';

// Styled components
const StyledTableContainer = styled(TableContainer)(({ theme, darkMode }) => ({
  borderRadius: theme.shape.borderRadius,
  overflow: 'auto',
  maxHeight: '60vh',
  '&::-webkit-scrollbar': {
    width: '8px',
    height: '8px',
  },
  '&::-webkit-scrollbar-track': {
    backgroundColor: darkMode ? alpha('#FFFFFF', 0.05) : alpha('#000000', 0.05),
    borderRadius: '8px',
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: darkMode ? alpha('#FFFFFF', 0.2) : alpha('#000000', 0.2),
    borderRadius: '8px',
    '&:hover': {
      backgroundColor: darkMode ? alpha('#FFFFFF', 0.3) : alpha('#000000', 0.3),
    }
  },
}));

const StyledTable = styled(Table)(({ theme, darkMode }) => ({
  '& .MuiTableCell-head': {
    backgroundColor: darkMode ? alpha(theme.palette.primary.dark, 0.3) : alpha(theme.palette.primary.light, 0.1),
    color: darkMode ? theme.palette.primary.light : theme.palette.primary.dark,
    fontWeight: 600,
    fontSize: '0.8rem',
    padding: '12px 16px',
    whiteSpace: 'nowrap',
    position: 'sticky',
    top: 0,
    zIndex: 10,
  }
}));

const StyledTableRow = styled(TableRow)(({ theme, darkMode, status }) => {
  let bgColor = 'transparent';
  let hoverColor = darkMode ? alpha('#FFFFFF', 0.05) : alpha('#000000', 0.03);
  
  // Status-based coloring - Updated for new status codes
  if (status === 'FL') {
    bgColor = darkMode ? alpha(theme.palette.error.dark, 0.1) : alpha(theme.palette.error.light, 0.05);
    hoverColor = darkMode ? alpha(theme.palette.error.dark, 0.15) : alpha(theme.palette.error.light, 0.1);
  } else if (status === 'PC' || status === 'SC') {
    bgColor = darkMode ? alpha(theme.palette.success.dark, 0.05) : alpha(theme.palette.success.light, 0.03);
    hoverColor = darkMode ? alpha(theme.palette.success.dark, 0.1) : alpha(theme.palette.success.light, 0.07);
  } else if (status === 'IP' || status === 'RN') {
    bgColor = darkMode ? alpha(theme.palette.info.dark, 0.05) : alpha(theme.palette.info.light, 0.03);
    hoverColor = darkMode ? alpha(theme.palette.info.dark, 0.1) : alpha(theme.palette.info.light, 0.07);
  }
  
  return {
    backgroundColor: bgColor,
    transition: 'background-color 0.2s ease',
    '&:hover': {
      backgroundColor: hoverColor,
    },
    '& > .MuiTableCell-root': {
      borderBottom: darkMode 
        ? `1px solid ${alpha('#FFFFFF', 0.1)}` 
        : `1px solid ${alpha('#000000', 0.1)}`,
      padding: '10px 16px',
    },
  };
});

const ActionButton = styled(IconButton)(({ theme, darkMode }) => ({
  backgroundColor: darkMode ? alpha(theme.palette.error.main, 0.1) : alpha(theme.palette.error.main, 0.05),
  '&:hover': {
    backgroundColor: darkMode ? alpha(theme.palette.error.main, 0.2) : alpha(theme.palette.error.main, 0.1),
  },
  marginRight: theme.spacing(0.75),
  padding: 6,
  transition: 'all 0.2s ease',
}));

const LogStatusChip = styled(Chip)(({ theme, status, darkMode }) => {
  let color;
  let backgroundColor;
  let borderColor;
  
  if (status === 'PC' || status === 'SC') {
    color = darkMode ? theme.palette.success.light : theme.palette.success.dark;
    backgroundColor = darkMode ? alpha(theme.palette.success.main, 0.2) : alpha(theme.palette.success.main, 0.1);
    borderColor = darkMode ? alpha(theme.palette.success.main, 0.3) : alpha(theme.palette.success.main, 0.2);
  } else if (status === 'FL') {
    color = darkMode ? theme.palette.error.light : theme.palette.error.dark;
    backgroundColor = darkMode ? alpha(theme.palette.error.main, 0.2) : alpha(theme.palette.error.main, 0.1);
    borderColor = darkMode ? alpha(theme.palette.error.main, 0.3) : alpha(theme.palette.error.main, 0.2);
  } else if (status === 'IP' || status === 'RN') {
    color = darkMode ? theme.palette.info.light : theme.palette.info.dark;
    backgroundColor = darkMode ? alpha(theme.palette.info.main, 0.2) : alpha(theme.palette.info.main, 0.1);
    borderColor = darkMode ? alpha(theme.palette.info.main, 0.3) : alpha(theme.palette.info.main, 0.2);
  } else {
    color = darkMode ? theme.palette.grey[300] : theme.palette.grey[700];
    backgroundColor = darkMode ? alpha(theme.palette.grey[500], 0.2) : alpha(theme.palette.grey[500], 0.1);
    borderColor = darkMode ? alpha(theme.palette.grey[500], 0.3) : alpha(theme.palette.grey[500], 0.2);
  }
  
  return {
    color: color,
    backgroundColor: backgroundColor,
    fontWeight: 500,
    fontSize: '0.75rem',
    borderRadius: '16px',
    border: `1px solid ${borderColor}`,
    '& .MuiChip-icon': {
      color: 'inherit',
      marginRight: '4px',
    },
    transition: 'all 0.2s ease',
  };
});

const ValueWithTrend = styled(Box)(({ theme, value, comparison = 0, darkMode }) => {
  const change = value - comparison;
  const hasChange = comparison > 0 && change !== 0;
  
  let color = 'inherit';
  if (hasChange) {
    color = change > 0 
      ? (darkMode ? theme.palette.success.light : theme.palette.success.main)
      : (darkMode ? theme.palette.error.light : theme.palette.error.main);
  }
  
  return {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-start',
    color: color,
    fontWeight: hasChange ? 500 : 400,
    gap: '4px',
    transition: 'all 0.2s ease',
  };
});

const ErrorBadge = styled(Badge)(({ theme }) => ({
  '& .MuiBadge-badge': {
    backgroundColor: theme.palette.error.main,
    color: theme.palette.error.contrastText,
    fontWeight: 'bold',
    fontSize: '0.65rem',
    height: '18px',
    minWidth: '18px',
  }
}));

// Function to get log status label
const getLogStatusLabel = (status) => {
  if (!status) return 'Unknown';
  if (status === 'PC') return 'Process Complete';
  if (status === 'FL') return 'Failed';
  if (status === 'IP') return 'In Progress';
  // Legacy status support
  if (status === 'SC') return 'Success';
  if (status === 'RN') return 'Running';
  return status;
};

// Function to get status icon
const getStatusIcon = (status) => {
  if (!status) return <InfoIcon fontSize="small" />;
  if (status === 'PC' || status === 'SC') return <CheckCircleIcon fontSize="small" />;
  if (status === 'FL') return <ErrorIcon fontSize="small" />;
  if (status === 'IP' || status === 'RN') return <InfoIcon fontSize="small" />;
  return null;
};

// Format date safely
const formatDate = (dateStr, formatString = 'yyyy-MM-dd') => {
  if (!dateStr) return '-';
  try {
    return format(new Date(dateStr), formatString);
  } catch (error) {
    console.error(`Error formatting date: ${dateStr}`, error);
    return dateStr || '-';
  }
};

const LogDetailsTable = ({ logDetails, darkMode, onViewErrors }) => {
  const muiTheme = useMuiTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));
  
  // Make sure logDetails is an array
  const logs = Array.isArray(logDetails) ? logDetails : [];
  
  // Filter out any undefined or badly formed records
  const validLogs = logs.filter(log => log && typeof log === 'object');
  
  return (
    <StyledTableContainer darkMode={darkMode}>
      <StyledTable stickyHeader darkMode={darkMode} size={isMobile ? "small" : "medium"}>
        <TableHead>
          <TableRow>
            <TableCell>Log Date</TableCell>
            <TableCell>Log ID</TableCell>
            <TableCell>Session ID</TableCell>
            <TableCell>Start Time</TableCell>
            <TableCell>Duration</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="center">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {validLogs.map((log, index) => {
            // Format duration from seconds
            const formatDuration = (seconds) => {
              if (!seconds || isNaN(seconds)) return 'N/A';
              const totalSeconds = parseInt(seconds);
              const hours = Math.floor(totalSeconds / 3600);
              const minutes = Math.floor((totalSeconds % 3600) / 60);
              const secs = totalSeconds % 60;
              
              if (hours > 0) {
                return `${hours}h ${minutes}m ${secs}s`;
              } else if (minutes > 0) {
                return `${minutes}m ${secs}s`;
              } else {
                return `${secs}s`;
              }
            };
            
            return (
              <StyledTableRow 
                key={log.logId || index}
                component={motion.tr}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                darkMode={darkMode}
                status={log.status}
              >
                <TableCell>
                  {formatDate(log.logDate, 'yyyy-MM-dd HH:mm:ss')}
                </TableCell>
                <TableCell>{log.logId || 'N/A'}</TableCell>
                <TableCell>{log.sessionId || '-'}</TableCell>
                <TableCell>
                  {formatDate(log.actualStartDate, 'yyyy-MM-dd HH:mm:ss')}
                </TableCell>
                <TableCell>
                  {formatDuration(log.runDurationSeconds)}
                </TableCell>
                <TableCell>
                  <LogStatusChip
                    status={log.status}
                    darkMode={darkMode}
                    label={getLogStatusLabel(log.status)}
                    size="small"
                    icon={getStatusIcon(log.status)}
                  />
                </TableCell>
                <TableCell align="center">
                  {log.status === 'FL' && (
                    <Tooltip title="View Error Details">
                      <ActionButton
                        darkMode={darkMode}
                        onClick={() => onViewErrors(log.logId || log.sessionId, log.errorMessage)}
                        size="small"
                      >
                        <ErrorIcon fontSize="small" />
                      </ActionButton>
                    </Tooltip>
                  )}
                </TableCell>
              </StyledTableRow>
            );
          })}
        </TableBody>
      </StyledTable>
    </StyledTableContainer>
  );
};

export default LogDetailsTable; 