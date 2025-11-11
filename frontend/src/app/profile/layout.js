'use client';

import ProtectedRoute from '../components/ProtectedRoute';

export default function ProfileLayout({ children }) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  );
} 