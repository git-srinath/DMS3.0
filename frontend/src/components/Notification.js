import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Typography, 
  Box, 
  Button, 
  IconButton, 
  Divider, 
  Paper, 
  useTheme, 
  alpha,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import CloseIcon from '@mui/icons-material/Close';
import NotificationsIcon from '@mui/icons-material/Notifications';
import { useAuth } from '../app/context/AuthContext';
import axios from 'axios';
import { API_BASE_URL } from '../app/config';
import ReactMarkdown from 'react-markdown';

const Notification = () => {
  const [open, setOpen] = useState(false);
  const [notification, setNotification] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, updateUser } = useAuth();
  const theme = useTheme();

  useEffect(() => {
    // Check if user has notifications to show
    if (user && user.show_notification) {
      fetchNotifications();
    }
  }, [user]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/admin/notifications`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.data && response.data.length > 0) {
        // Get the latest notification (assuming they're sorted by creation date)
        const latestNotification = response.data[response.data.length - 1];
        setNotification(latestNotification);
        setOpen(true);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = async () => {
    // Mark notification as dismissed
    try {
      await axios.post(`${API_BASE_URL}/admin/notifications/dismiss`, {}, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
    setOpen(false);

    // Update user context and local storage to not show notification again
    if (user) {
      const updatedUser = { ...user, show_notification: false };
      updateUser(updatedUser);
    }
  };

  // If no user or no notifications to show, don't render anything
  if (!user || !user.show_notification || !notification) {
    return null;
  }

  const markdownComponents = {
    h1: ({node, children, ...props}) => (
      <Typography 
        variant="subtitle1" 
        sx={{
          fontSize: '1.25rem',
          fontWeight: 600,
          mt: 1.5,
          mb: 0.75,
          color: theme.palette.mode === 'dark' ? theme.palette.primary.light : theme.palette.primary.main
        }}
        {...props}
      >
        {children}
      </Typography>
    ),
    h2: ({node, children, ...props}) => (
      <Typography 
        variant="subtitle2" 
        sx={{
          fontSize: '1.1rem',
          fontWeight: 600,
          mt: 1.25,
          mb: 0.5,
          color: theme.palette.mode === 'dark' ? theme.palette.primary.light : theme.palette.primary.main
        }}
        {...props}
      >
        {children}
      </Typography>
    ),
    h3: ({node, children, ...props}) => (
      <Typography 
        variant="body2" 
        sx={{
          fontSize: '1rem',
          fontWeight: 600,
          mt: 1,
          mb: 0.25,
          color: theme.palette.mode === 'dark' ? alpha(theme.palette.primary.light, 0.9) : theme.palette.primary.dark
        }}
        {...props}
      >
        {children}
      </Typography>
    ),
    p: ({node, children, ...props}) => (
      <Typography 
        variant="body2" 
        sx={{
          my: 0.5,
          lineHeight: 1.4,
          color: theme.palette.mode === 'dark' ? theme.palette.text.primary : theme.palette.text.secondary
        }}
        {...props}
      >
        {children}
      </Typography>
    ),
    ul: ({node, children, ...props}) => (
      <Box 
        component="ul" 
        sx={{
          pl: 2,
          my: 0.5,
          listStyleType: 'disc'
        }}
        {...props}
      >
        {children}
      </Box>
    ),
    li: ({node, children, ...props}) => (
      <Box 
        component="li" 
        sx={{
          mb: 0.5,
          lineHeight: 1.2,
          fontSize: '0.875rem',
          color: theme.palette.mode === 'dark' ? theme.palette.text.primary : theme.palette.text.secondary,
          '& > a': {
            display: 'inline-block',
            mb: 0.25
          }
        }}
        {...props}
      >
        {children}
      </Box>
    ),
    a: ({node, children, ...props}) => (
      <Box 
        component="a" 
        target="_blank" 
        rel="noopener"
        sx={{
          color: theme.palette.primary.main,
          textDecoration: 'underline',
          fontWeight: 500,
          display: 'inline-block',
          transition: 'color 0.2s',
          '&:hover': {
            color: theme.palette.primary.dark
          }
        }}
        {...props}
      >
        {children}
      </Box>
    )
  };

  return (
    <Dialog
      open={open}
      onClose={(e, reason) => {
        // Prevent closing on backdrop click or escape key
        if (reason === 'backdropClick' || reason === 'escapeKeyDown') {
          return;
        }
        handleClose();
      }}
      maxWidth="sm"
      fullWidth
      PaperComponent={motion.div}
      PaperProps={{
        style: {
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 10px 40px rgba(0, 0, 0, 0.15)',
          backgroundColor: theme.palette.mode === 'dark' ? alpha(theme.palette.background.paper, 0.95) : theme.palette.background.paper,
        },
        initial: { opacity: 0, y: 20, scale: 0.95 },
        animate: { opacity: 1, y: 0, scale: 1 },
        transition: { duration: 0.3 }
      }}
    >
      <DialogTitle 
        sx={{ 
          background: theme.palette.mode === 'dark' 
            ? `linear-gradient(90deg, ${alpha(theme.palette.primary.dark, 0.85)} 0%, ${alpha(theme.palette.primary.main, 0.65)} 100%)`
            : `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          py: 1.75,
          px: 2.5,
          borderBottom: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
        }}
      >
        <NotificationsIcon sx={{ fontSize: 22 }} />
        <Typography variant="h6" component="div" sx={{ fontWeight: 600, flex: 1, fontSize: '1.1rem' }}>
          New Features Available
        </Typography>
        <IconButton
          edge="end"
          color="inherit"
          aria-label="close"
          size="small"
          sx={{ 
            visibility: 'visible', // Show the close icon
            color: '#fff',
            opacity: 0.8,
            '&:hover': { 
              opacity: 1,
              backgroundColor: alpha('#fff', 0.15) 
            }
          }}
          onClick={handleClose}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      
      <DialogContent 
        sx={{ 
          p: 0,
          maxHeight: '55vh',
          backgroundColor: theme.palette.mode === 'dark' 
            ? alpha(theme.palette.background.default, 0.8) 
            : theme.palette.background.default,
          overflowX: 'hidden'
        }}
      >
        <Box 
          sx={{ 
            p: 2.5,
            backgroundImage: theme.palette.mode === 'dark'
              ? `radial-gradient(${alpha(theme.palette.primary.dark, 0.12)} 1px, transparent 1px)`
              : `radial-gradient(${alpha(theme.palette.primary.light, 0.12)} 1px, transparent 1px)`,
            backgroundSize: '20px 20px',
          }}
        >
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: 2.5,
              border: `1px solid ${theme.palette.mode === 'dark' 
                ? alpha(theme.palette.primary.dark, 0.2) 
                : alpha(theme.palette.primary.main, 0.15)}`,
              backgroundColor: theme.palette.mode === 'dark' 
                ? alpha(theme.palette.background.paper, 0.7) 
                : alpha(theme.palette.background.paper, 0.9),
              backdropFilter: 'blur(8px)',
              boxShadow: theme.palette.mode === 'dark'
                ? `0 4px 20px ${alpha(theme.palette.common.black, 0.2)}`
                : `0 4px 20px ${alpha(theme.palette.common.black, 0.05)}`
            }}
          >
            <Typography
              variant="h6"
              sx={{
                fontWeight: 600,
                fontSize: '1.15rem',
                color: theme.palette.mode === 'dark' 
                  ? theme.palette.primary.light 
                  : theme.palette.primary.main,
                mb: 1.25,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              {notification.title}
            </Typography>
            <Divider sx={{ mb: 1.5 }} />
            
            <Box sx={{ color: theme.palette.text.primary }}>
              <ReactMarkdown components={markdownComponents}>
                {notification.description}
              </ReactMarkdown>
            </Box>
            
            <Box
              sx={{
                mt: 1.5,
                pt: 1,
                borderTop: `1px dashed ${alpha(theme.palette.divider, 0.5)}`,
                display: 'flex',
                justifyContent: 'flex-end'
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  fontSize: '0.7rem',
                  color: theme.palette.text.disabled,
                  fontStyle: 'italic'
                }}
              >
                {new Date(notification.created_at).toLocaleDateString()}
              </Typography>
            </Box>
          </Paper>
        </Box>
      </DialogContent>
      
      <DialogActions 
        sx={{ 
          px: 2.5, 
          py: 2, 
          background: theme.palette.mode === 'dark'
            ? alpha(theme.palette.background.paper, 0.7)
            : alpha(theme.palette.background.paper, 0.9),
          borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}
      >
        <Button 
          onClick={handleClose}
          variant="contained"
          fullWidth
          sx={{
            py: 1,
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '0.9rem',
            fontWeight: 500,
            boxShadow: theme.palette.mode === 'dark'
              ? `0 4px 12px ${alpha(theme.palette.primary.dark, 0.4)}`
              : `0 4px 12px ${alpha(theme.palette.primary.main, 0.25)}`,
            background: theme.palette.mode === 'dark'
              ? `linear-gradient(90deg, ${alpha(theme.palette.primary.dark, 0.95)} 0%, ${alpha(theme.palette.primary.main, 0.75)} 100%)`
              : `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
            letterSpacing: '0.25px',
            '&:hover': {
              boxShadow: theme.palette.mode === 'dark'
                ? `0 6px 16px ${alpha(theme.palette.primary.dark, 0.6)}`
                : `0 6px 16px ${alpha(theme.palette.primary.main, 0.4)}`,
              background: theme.palette.mode === 'dark'
                ? `linear-gradient(90deg, ${alpha(theme.palette.primary.dark, 1)} 0%, ${alpha(theme.palette.primary.main, 0.85)} 100%)`
                : `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${alpha(theme.palette.primary.dark, 0.9)} 100%)`
            }
          }}
        >
          Got it
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default Notification; 