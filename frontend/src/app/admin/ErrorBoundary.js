'use client';

import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { ErrorOutline } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '200px',
            p: 4,
            textAlign: 'center',
            border: '1px solid #e0e0e0',
            borderRadius: 2,
            bgcolor: '#f8f8f8',
            my: 2,
          }}
        >
          <ErrorOutline sx={{ fontSize: 48, color: 'error.main', mb: 2 }} />
          <Typography variant="h5" gutterBottom fontWeight="medium">
            Something went wrong
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            There was an error loading this component. Please try refreshing the page.
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => window.location.reload()}
            sx={{ borderRadius: 1.5 }}
          >
            Refresh Page
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

// Usage example:
// import ErrorBoundary from './ErrorBoundary';
//
// <ErrorBoundary>
//   <AdminDashboard />
// </ErrorBoundary> 