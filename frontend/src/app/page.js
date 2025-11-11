"use client"

import React, { useEffect } from 'react';
import { redirect } from 'next/navigation';
import { useAuth } from './context/AuthContext';

const Dashboard = () => {
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (isAuthenticated) {
        redirect('/home');
      } else {
        redirect('/auth/login');
      }
    }
  }, [isAuthenticated, loading]);

  // Show loading state while checking authentication
  if (loading) {
    return <div>Loading...</div>;
  }

  return null; // This won't render because we'll be redirected
};

// Helper Components

export default Dashboard;