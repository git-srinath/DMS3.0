'use client';

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  CircularProgress,
  Paper,
} from '@mui/material';
import { overrideReferenceLock } from './lockUtils';
import { useTheme } from '@/context/ThemeContext';

/**
 * Dialog component shown when a reference is locked by another user
 */
const LockDialog = ({ 
  open, 
  onClose, 
  lockInfo, 
  onOverrideLock,
  isOverriding = false
}) => {
  const { darkMode } = useTheme();

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleOverrideLock = async () => {
    if (typeof onOverrideLock === 'function') {
      onOverrideLock();
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          bgcolor: darkMode ? '#1F2937' : 'background.paper',
          borderRadius: 2,
          boxShadow: darkMode ? '0 10px 25px -5px rgba(0, 0, 0, 0.8)' : undefined,
        }
      }}
    >
      <DialogTitle sx={{ 
        bgcolor: darkMode ? 'rgba(220, 38, 38, 0.9)' : 'error.main', 
        color: 'white',
        fontWeight: 'bold',
        py: 2
      }}>
        Reference Locked
      </DialogTitle>
      <DialogContent sx={{ py: 3 }}>
        <Typography 
          variant="body1" 
          sx={{ 
            mb: 2,
            color: darkMode ? 'rgba(255, 255, 255, 0.9)' : 'text.primary' 
          }}
        >
          This reference is currently being edited by another user.
        </Typography>
        
        <Box sx={{ 
          bgcolor: darkMode ? 'rgba(17, 24, 39, 0.7)' : 'grey.100', 
          p: 2, 
          borderRadius: 1,
          mb: 2,
          border: '1px solid',
          borderColor: darkMode ? 'rgba(75, 85, 99, 0.4)' : 'rgba(0, 0, 0, 0.05)'
        }}>
          <Typography 
            variant="body2" 
            sx={{ 
              mb: 1,
              color: darkMode ? 'rgba(255, 255, 255, 0.9)' : 'text.primary' 
            }}
          >
            <strong>Locked by:</strong> {lockInfo?.lockedBy || 'Unknown user'}
          </Typography>
          <Typography 
            variant="body2"
            sx={{ 
              color: darkMode ? 'rgba(255, 255, 255, 0.9)' : 'text.primary' 
            }}
          >
            <strong>Locked since:</strong> {formatDate(lockInfo?.lockedAt)}
          </Typography>
        </Box>
        
        <Typography 
          variant="body2" 
          sx={{ 
            color: darkMode ? 'rgba(255, 255, 255, 0.7)' : 'text.secondary'
          }}
        >
          You can wait until the other user finishes editing, or override the lock if you believe it's stale.
          Overriding the lock might cause the other user to lose their changes.
        </Typography>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button 
          onClick={onClose} 
          sx={{
            textTransform: 'none',
            color: darkMode ? 'rgba(255, 255, 255, 0.7)' : 'text.primary',
          }}
          disabled={isOverriding}
        >
          Cancel
        </Button>
        <Button 
          onClick={handleOverrideLock} 
          variant="contained"
          disabled={isOverriding}
          startIcon={isOverriding ? <CircularProgress size={20} color="inherit" /> : null}
          sx={{
            textTransform: 'none',
            bgcolor: darkMode ? 'rgba(220, 38, 38, 0.8)' : 'error.main',
            '&:hover': {
              bgcolor: darkMode ? 'rgba(220, 38, 38, 0.9)' : 'error.dark',
            },
            '&.Mui-disabled': {
              bgcolor: darkMode ? 'rgba(220, 38, 38, 0.3)' : undefined,
            }
          }}
        >
          {isOverriding ? 'Overriding...' : 'Override Lock'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default LockDialog; 