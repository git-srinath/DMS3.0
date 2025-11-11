'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { API_BASE_URL } from '../../config';
import axios from 'axios';

const useAccessControl = (moduleName) => {
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasAccess, setHasAccess] = useState(false);
  const { user } = useAuth();

  const fetchPermissions = useCallback(async () => {
    if (!user?.id || !moduleName) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentication required');
        setLoading(false);
        return;
      }

      const response = await axios.get(`${API_BASE_URL}/access-control/get-permissions`, {
        params: {
          user_id: user.id,
          module_name: moduleName
        },
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        withCredentials: true
      });

      if (response.data && response.data.permissions) {
        setPermissions(response.data.permissions);
        
        // Check if user has SUPER_ADMIN role for admin module access
        const hasSuperAdminRole = response.data.permissions.some(
          permission => permission.role_name === 'ADMIN'
        );
        
        setHasAccess(hasSuperAdminRole);
      } else {
        setPermissions([]);
        setHasAccess(false);
      }
    } catch (err) {
      console.error('Error fetching permissions:', err);
      setError(err.response?.data?.error || 'Failed to fetch permissions');
      setPermissions([]);
      setHasAccess(false);
    } finally {
      setLoading(false);
    }
  }, [user?.id, moduleName]);

  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  // Helper function to check specific permissions
  const checkPermission = useCallback((permissionType) => {
    if (!permissions || permissions.length === 0) return false;
    
    return permissions.some(permission => {
      switch (permissionType) {
        case 'view':
          return permission.can_view === 'Yes';
        case 'create':
          return permission.can_create === 'Yes';
        case 'edit':
          return permission.can_edit === 'Yes';
        case 'delete':
          return permission.can_delete === 'Yes';
        default:
          return false;
      }
    });
  }, [permissions]);

  // Helper function to get user roles for the module
  const getUserRoles = useCallback(() => {
    if (!permissions || permissions.length === 0) return [];
    
    return permissions.map(permission => permission.role_name);
  }, [permissions]);

  return {
    permissions,
    loading,
    error,
    hasAccess,
    checkPermission,
    getUserRoles,
    refetch: fetchPermissions
  };
};

export default useAccessControl; 