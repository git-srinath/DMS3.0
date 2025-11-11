'use client';

import ProtectedRoute from '../components/ProtectedRoute';

export default function HomeLayout({ children }) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  );
} 