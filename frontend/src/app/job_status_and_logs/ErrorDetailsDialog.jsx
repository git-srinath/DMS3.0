import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box,
  IconButton,
  Button,
  CircularProgress,
  Grid,
  Paper,
  Tooltip,
  Snackbar,
  Alert,
  useMediaQuery
} from '@mui/material';
import { styled, alpha, useTheme as useMuiTheme } from '@mui/material/styles';
import {
  Close as CloseIcon,
  ErrorOutline as ErrorIcon,
  Schedule as ScheduleIcon,
  Dns as DnsIcon,
  VpnKey as VpnKeyIcon,
  ConfirmationNumber as ConfirmationNumberIcon,
  ContentCopy as ContentCopyIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { motion } from 'framer-motion';

// Format date safely
const formatDate = (dateStr, formatString = 'yyyy-MM-dd HH:mm:ss') => {
  if (!dateStr) return 'N/A';
  try {
    return format(new Date(dateStr), formatString);
  } catch (error) {
    console.error(`Error formatting date: ${dateStr}`, error);
    return dateStr || 'N/A';
  }
};

const StyledDialog = styled(Dialog)(({ theme, darkMode }) => ({
  '& .MuiDialog-paper': {
    width: '900px',
    maxWidth: '90vw',
    borderRadius: '16px',
    overflow: 'hidden',
    backgroundColor: darkMode ? '#1e293b' : '#f8fafc', // slate-800 : slate-50
    border: `1px solid ${darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`,
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
  },
}));

const ErrorHeader = styled(DialogTitle)(({ theme, darkMode }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1.5),
  color: darkMode ? '#f8fafc' : '#b91c1c', // slate-50 : red-900
  backgroundColor: darkMode ? '#b91c1c' : '#fecaca', // red-700 : red-200
  padding: `${theme.spacing(1.5)} ${theme.spacing(3)}`,
  borderBottom: `1px solid ${darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`,
}));

const InfoCard = styled(Paper)(({ theme, darkMode }) => ({
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(0.5),
  padding: theme.spacing(2),
  borderRadius: '12px',
  backgroundColor: darkMode ? alpha('#475569', 0.2) : alpha('#e2e8f0', 0.5), // slate-600/20% : slate-200/50%
  border: `1px solid ${darkMode ? alpha('#475569', 0.5) : alpha('#e2e8f0', 1)}`, // slate-600/50% : slate-200
  textAlign: 'center',
  flex: 1,
  minWidth: '180px',
  transition: 'all 0.2s ease-in-out',
    '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: `0 4px 10px ${alpha(darkMode ? '#000' : '#94a3b8', 0.15)}`, // black/15% : slate-400/15%
  },
}));

const InfoLabel = styled(Typography)(({ theme, darkMode }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: theme.spacing(1),
  fontSize: '0.75rem',
  fontWeight: 600,
  textTransform: 'uppercase',
  color: darkMode ? '#94a3b8' : '#64748b', // slate-400 : slate-500
}));

const InfoValue = styled(Typography)(({ theme, darkMode }) => ({
  fontSize: '0.9rem',
  fontWeight: 500,
  color: darkMode ? '#f1f5f9' : '#1e293b', // slate-100 : slate-800
  wordBreak: 'break-all',
}));

const ErrorMessageContainer = styled(Box)(({ theme, darkMode }) => ({
  marginTop: theme.spacing(3),
  position: 'relative',
}));

const ErrorMessagePaper = styled(Paper)(({ theme, darkMode }) => ({
  padding: theme.spacing(2.5),
  fontFamily: 'monospace',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  fontSize: '0.875rem',
  lineHeight: 1.6,
  borderRadius: '12px',
  color: darkMode ? '#e2e8f0' : '#334155', // slate-200 : slate-700
  backgroundColor: darkMode ? '#0f172a' : '#ffffff', // slate-900 : white
  border: `1px solid ${darkMode ? alpha('#dc2626', 0.5) : alpha('#ef4444', 0.3)}`, // red-600/50% : red-500/30%
  maxHeight: '28vh',
  overflowY: 'auto',
  boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.1)',
}));

const ErrorDetailsDialog = ({ 
  open, 
  onClose, 
  errorDetails, 
  jobId, 
  loading, 
  darkMode 
}) => {
  const muiTheme = useMuiTheme();
  const [copySuccess, setCopySuccess] = useState(false);
  
  const error = Array.isArray(errorDetails) && errorDetails.length > 0 ? errorDetails[0] : null;
  
  const handleCopyError = (text) => {
    navigator.clipboard.writeText(text);
    setCopySuccess(true);
  };

  return (
    <>
    <StyledDialog
      open={open}
      onClose={onClose}
      darkMode={darkMode}
    >
      <ErrorHeader darkMode={darkMode}>
          <ErrorIcon sx={{ fontSize: '2rem' }} />
          <Typography variant="h6" component="div" fontWeight={600}>
            Job Execution Failed - {error ? error.KEY_VALUE || 'Unknown Job' : '...'}
            </Typography>
          <IconButton
            onClick={onClose}
            sx={{ position: 'absolute', right: 12, top: 12, color: 'inherit' }}
          >
            <CloseIcon />
          </IconButton>
      </ErrorHeader>
      
        <DialogContent sx={{ p: 3, bgcolor: darkMode ? '#1e293b' : '#f8fafc' }}>
        {loading ? (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
              <CircularProgress color="error" />
            </Box>
        ) : !error ? (
            <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="300px" textAlign="center">
              <InfoIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary">No Error Details</Typography>
              <Typography color="text.secondary">Specific error information is not available for this job.</Typography>
            </Box>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <Grid container spacing={2} justifyContent="center" sx={{ mt: 2 }}>
                <Grid item xs={12} sm={6} md={4}>
                  <InfoCard darkMode={darkMode}>
                    <InfoLabel darkMode={darkMode}><ScheduleIcon fontSize="small" /> Start Date</InfoLabel>
                    <InfoValue darkMode={darkMode}>{formatDate(error.PROCESS_DATE)}</InfoValue>
                  </InfoCard>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <InfoCard darkMode={darkMode}>
                    <InfoLabel darkMode={darkMode}><VpnKeyIcon fontSize="small" /> Log ID</InfoLabel>
                    <InfoValue darkMode={darkMode}>{error.ERROR_ID || 'N/A'}</InfoValue>
                  </InfoCard>
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <InfoCard darkMode={darkMode}>
                    <InfoLabel darkMode={darkMode}><ConfirmationNumberIcon fontSize="small" /> Session ID</InfoLabel>
                    <InfoValue darkMode={darkMode}>{error.SESSION_ID || 'N/A'}</InfoValue>
                  </InfoCard>
                </Grid>
              </Grid>

              <ErrorMessageContainer darkMode={darkMode}>
                <Tooltip title="Copy Error Message">
                  <IconButton
                    size="small" 
                    onClick={() => handleCopyError(error.ERROR_MESSAGE || '')}
                    sx={{ 
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      zIndex: 1,
                      color: darkMode ? '#94a3b8' : '#64748b',
                      backgroundColor: darkMode ? alpha('#0f172a', 0.5) : alpha('#f8fafc', 0.5),
                      '&:hover': { 
                        color: darkMode ? '#cbd5e1' : '#475569',
                        backgroundColor: darkMode ? alpha('#0f172a', 0.8) : alpha('#f8fafc', 0.8),
                      }
                    }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              <ErrorMessagePaper darkMode={darkMode}>
                  {error.ERROR_MESSAGE && error.ERROR_MESSAGE.trim() !== '' && error.ERROR_MESSAGE.trim() !== '\n'
                    ? error.ERROR_MESSAGE
                    : 'No specific error message was recorded.'}
              </ErrorMessagePaper>
              </ErrorMessageContainer>
            </motion.div>
        )}
      </DialogContent>
      
        <DialogActions sx={{ p: 2, justifyContent: 'center', bgcolor: darkMode ? '#1e293b' : '#f8fafc' }}>
        <Button 
          onClick={onClose} 
          variant="contained"
            size="large"
          sx={{
              minWidth: '150px',
            borderRadius: '8px',
              fontWeight: 600,
              color: '#fff',
              backgroundColor: '#3b82f6', // blue-500
            '&:hover': {
                backgroundColor: '#2563eb', // blue-600
            }
          }}
        >
          Close
        </Button>
      </DialogActions>
      </StyledDialog>
      
      <Snackbar
        open={copySuccess}
        autoHideDuration={2500}
        onClose={() => setCopySuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setCopySuccess(false)} 
          severity="success" 
          variant="filled"
          icon={<ContentCopyIcon fontSize="inherit" />}
        >
          Error message copied to clipboard!
        </Alert>
      </Snackbar>
    </>
  );
};

export default ErrorDetailsDialog; 