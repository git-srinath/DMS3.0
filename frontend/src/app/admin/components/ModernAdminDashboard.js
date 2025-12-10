import React, { useState, useEffect, useCallback } from 'react';
import { Box, useTheme, alpha, Typography, Container, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TablePagination, Paper, Chip, Stack, Avatar, IconButton, Tooltip, TextField, Button, InputAdornment, Divider } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { API_BASE_URL } from '../../config';
import { useRouter, usePathname } from 'next/navigation';
import axios from 'axios';
import { message } from 'antd';
// Import components
import MetricsSection from './MetricsSection';
import UsersTable from './UsersTable';
import LicenseManager from './LicenseManager';
import UserDialog from './UserDialogs';
import RoleDialog from './RoleDialogs';
import ModuleDialog from './ModuleDialog';
import { AboutTabContent } from './';
import NotificationManager from './NotificationManager';
import NotAuthorized from './NotAuthorized';
import useAccessControl from '../hooks/useAccessControl';
import RefreshIcon from '@mui/icons-material/Refresh';
import SecurityIcon from '@mui/icons-material/Security';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import FilterListIcon from '@mui/icons-material/FilterList';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import SettingsIcon from '@mui/icons-material/Settings';

// Page variants for animations
const pageVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 }
};

// Tab content variants
const tabContentVariants = {
  initial: { opacity: 0, y: 15 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -15 }
};

const ModernAdminDashboard = ({ initialActiveTab = 0 }) => {
  const theme = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  
  // Sync activeTab with current route (matching TabsLayout tabRoutes order)
  const getActiveTabFromPath = () => {
    // Tab order matches TabsLayout: Users(0), DB Connections(1), Roles(2), Audit Logs(3), License(4), Notifications(5), About(6)
    if (pathname?.startsWith('/admin/users')) return 0;
    if (pathname?.startsWith('/register_db_connections')) return 1;
    if (pathname?.startsWith('/admin/roles')) return 2;
    if (pathname?.startsWith('/admin/audit-logs')) return 3;
    if (pathname?.startsWith('/admin/license')) return 4;
    if (pathname?.startsWith('/admin/notifications')) return 5;
    if (pathname?.startsWith('/admin/about')) return 6;
    // Default to Users tab if on /admin without specific path
    if (pathname?.startsWith('/admin')) return 0;
    return initialActiveTab;
  };
  
  const [activeTab, setActiveTab] = useState(getActiveTabFromPath());
  
  // Update activeTab when route changes
  useEffect(() => {
    const tab = getActiveTabFromPath();
    setActiveTab(tab);
  }, [pathname]);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [modules, setModules] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedModule, setSelectedModule] = useState(null);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isLoadingRoles, setIsLoadingRoles] = useState(false);
  const [isLoadingModules, setIsLoadingModules] = useState(false);
  const [auditLogsLoading, setAuditLogsLoading] = useState(false);
  const { user, loading, handleTokenExpiration } = useAuth();
  
  // Access control hook
  const { 
    hasAccess, 
    loading: accessLoading, 
    error: accessError,
    getUserRoles 
  } = useAccessControl('admin_module');
  
  const [roleSearchTerm, setRoleSearchTerm] = useState('');
  const [logSearchTerm, setLogSearchTerm] = useState('');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);

  const handleTabChange = useCallback((event, newValue) => {
    setActiveTab(newValue);
  }, []);

  const handleOpenDialog = (type, data = null) => {
    if (type === 'editUser') {
      console.log('Edit User - data:', data);
      setSelectedUser(data);
    } else if (type === 'editRole') {
      setSelectedRole(data);
    } else if (type === 'editModule') {
      setSelectedModule(data);
    } else if (type === 'resetPassword') {
      console.log('Reset Password - data:', data);
      console.log('User ID type:', typeof data.user_id);
      setSelectedUser(data);
    }
    setDialogType(type);
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedUser(null);
    setSelectedRole(null);
    setSelectedModule(null);
  };

  const loadUsers = async () => {
    if (isLoadingUsers) return;
    try {
      setIsLoadingUsers(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/admin/users`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = Array.isArray(response.data) ? response.data : [];
      setUsers(data);
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error loading users');
      }
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const loadRoles = async () => {
    if (isLoadingRoles) return;
    try {
      setIsLoadingRoles(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/admin/roles`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = Array.isArray(response.data) ? response.data : [];
      setRoles(data);
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error loading roles');
      }
    } finally {
      setIsLoadingRoles(false);
    }
  };

  const loadModules = async () => {
    try {
      setIsLoadingModules(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/admin/modules`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = Array.isArray(response.data) ? response.data : [];
      setModules(data);
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error loading modules');
      }
    } finally {
      setIsLoadingModules(false);
    }
  };

  const loadPendingApprovals = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/admin/pending-approvals`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = Array.isArray(response.data) ? response.data : [];
      setPendingApprovals(data);
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error loading pending approvals');
      }
    }
  };

  const loadAuditLogs = async () => {
    try {
      setAuditLogsLoading(true);
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(`${API_BASE_URL}/admin/audit-logs`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const data = Array.isArray(response.data) ? response.data : [];

      // Transform the data
      const transformedLogs = data.map(log => ({
        ...log,
        timestamp: log.login_timestamp,
        details: `${log.login_type} attempt from IP: ${log.ip_address}`,
        status: log.login_status.toLowerCase()
      }));

      setAuditLogs(transformedLogs);
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error loading audit logs');
      }
    } finally {
      setAuditLogsLoading(false);
    }
  };

  const deleteUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        router.push('/auth/login');
        return;
      }

      await axios.delete(`${API_BASE_URL}/admin/users/${userId}`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      message.success('User deleted successfully');
      loadUsers();
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error deleting user');
      }
    }
  };

  const deleteRole = async (roleId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        router.push('/auth/login');
        return;
      }

      await axios.delete(`${API_BASE_URL}/admin/roles/${roleId}`, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      message.success('Role deleted successfully');
      loadRoles();
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        message.error(err.response?.data?.error || 'Error deleting role');
      }
    }
  };

  const approveUser = async (userId, actionType) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        router.push('/auth/login');
        return;
      }

      const response = await axios.post(
        `${API_BASE_URL}/admin/approve-user/${userId}`,
        { action: actionType },
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.status === 200) {
        message.success(response.data.message);
        // Refresh both users and pending approvals lists
        await Promise.all([
          loadUsers(),
          loadPendingApprovals()
        ]);
      }
    } catch (err) {
      // Only show error message if it's not an access control issue
      if (err.response?.status !== 403) {
        const errorMessage = err.response?.data?.error || 'Error updating approval';
        message.error(errorMessage);
      }
    }
  };

  // Refresh all data based on active tab
  const refreshData = useCallback(() => {
    loadUsers();
    loadRoles();
    loadModules();
    loadPendingApprovals();
    if (activeTab === 2) loadAuditLogs();
  }, [activeTab]);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/auth/login');
      return;
    }

    // Only load data if user has access and access control is not loading
    if (!loading && !accessLoading && hasAccess) {
      refreshData();
    }
  }, [loading, user, activeTab, refreshData, accessLoading, hasAccess]);

  // Filter roles based on search term
  const filteredRoles = roleSearchTerm
    ? roles.filter(role =>
        role.role_name?.toLowerCase().includes(roleSearchTerm.toLowerCase()) ||
        role.description?.toLowerCase().includes(roleSearchTerm.toLowerCase())
      )
    : roles;

  // Filter audit logs based on search term and date range
  const filteredLogs = auditLogs.filter(log => {
    const logDate = new Date(log.timestamp);
    
    // Check if the log date is after the start date
    const isAfterStartDate = !startDate || logDate >= new Date(startDate);
    
    // Check if the log date is before the end date (end of day)
    const isBeforeEndDate = !endDate || logDate <= new Date(new Date(endDate).setHours(23, 59, 59, 999));

    // Check if the log matches the search term
    const matchesSearch = !logSearchTerm || (
        log.username?.toLowerCase().includes(logSearchTerm.toLowerCase()) ||
        log.login_type?.toLowerCase().includes(logSearchTerm.toLowerCase()) ||
        log.ip_address?.toLowerCase().includes(logSearchTerm.toLowerCase()) ||
        log.status?.toLowerCase().includes(logSearchTerm.toLowerCase())
    );
    
    return isAfterStartDate && isBeforeEndDate && matchesSearch;
  });

  const renderRolesTable = () => {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1, overflow: 'hidden' }}>
        <Box sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
          pb: 2,
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          flexShrink: 0,
        }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Role Management
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TextField
              placeholder="Search roles..."
              size="small"
              value={roleSearchTerm}
              onChange={(e) => setRoleSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
                sx: {
                  borderRadius: 2,
                  backgroundColor: alpha(theme.palette.background.paper, 0.5),
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.background.paper, 0.8),
                  }
                }
              }}
              sx={{ width: 200 }}
            />
            
            <Tooltip title="Refresh Roles">
              <IconButton 
                onClick={loadRoles}
                disabled={isLoadingRoles}
                sx={{
                  backgroundColor: alpha(theme.palette.background.paper, 0.5),
                  borderRadius: 2,
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.background.paper, 0.8),
                  }
                }}
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Manage Modules">
              <IconButton
                onClick={() => handleOpenDialog('manageModules')}
                sx={{
                  backgroundColor: alpha(theme.palette.warning.main, 0.1),
                  borderRadius: 2,
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.warning.main, 0.2),
                  }
                }}
              >
                <SettingsIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog('newRole')}
              sx={{
                borderRadius: 2,
                textTransform: 'none',
                boxShadow: 2,
                backgroundColor: theme.palette.success.main,
                '&:hover': {
                  backgroundColor: theme.palette.success.dark,
                }
              }}
            >
              New Role
            </Button>
          </Box>
        </Box>
      
        <TableContainer 
          component={motion.div}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          sx={{
            borderRadius: 3,
            boxShadow: `0 8px 32px 0 ${alpha(theme.palette.common.black, 0.1)}`,
            backgroundColor: alpha(theme.palette.background.paper, 0.95),
            backdropFilter: 'blur(10px)',
            overflow: 'auto',
            flexGrow: 1,
          }}
        >
          {isLoadingRoles ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
              <CircularProgress size={40} thickness={4} />
            </Box>
          ) : (
            <>
              <Table size="small">
                <TableHead>
                  <TableRow
                    sx={{
                      backgroundColor: alpha(theme.palette.primary.main, 0.03),
                      '& th': {
                        borderBottom: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                        color: theme.palette.text.secondary,
                        fontWeight: 600,
                        fontSize: '0.75rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        py: 1.5,
                      },
                    }}
                  >
                    <TableCell>Role Name</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>System Role</TableCell>
                    <TableCell>Permissions</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredRoles.length > 0 ? (
                    filteredRoles
                      .map((role) => (
                      <TableRow
                        key={role.role_id}
                        sx={{
                          height: '40px',
                          '&:hover': {
                            backgroundColor: alpha(theme.palette.primary.main, 0.04),
                          },
                          '& td': { borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`, py: 0.5 },
                        }}
                      >
                        <TableCell sx={{ py: 0.5 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {role.role_name}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ py: 0.5 }}>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {role.description || 'No description provided'}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ py: 0.5 }}>
                          <Chip
                            label={role.is_system_role ? 'Yes' : 'No'}
                            size="small"
                            color={role.is_system_role ? 'primary' : 'default'}
                            sx={{
                              height: '24px',
                              fontSize: '0.75rem',
                              borderRadius: '6px',
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ py: 0.5 }}>
                          <Stack direction="row" spacing={0.5} flexWrap="wrap">
                            {Object.keys(role.permissions || {}).map((module) => {
                              const permissions = role.permissions[module];
                              const permCount = Object.values(permissions).filter(Boolean).length;
                              return (
                                <Tooltip 
                                  key={module} 
                                  title={
                                    <Box>
                                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                        {module.charAt(0).toUpperCase() + module.slice(1)}
                                      </Typography>
                                      <Box component="ul" sx={{ m: 0, pl: 2 }}>
                                        {permissions.can_view && <li>View</li>}
                                        {permissions.can_create && <li>Create</li>}
                                        {permissions.can_edit && <li>Edit</li>}
                                        {permissions.can_delete && <li>Delete</li>}
                                      </Box>
                                    </Box>
                                  }
                                >
                                  <Chip
                                    label={`${module} (${permCount})`}
                                    size="small"
                                    sx={{
                                      height: '20px',
                                      fontSize: '0.7rem',
                                      backgroundColor: alpha(theme.palette.info.main, 0.1),
                                      color: theme.palette.info.main,
                                      borderRadius: '4px',
                                      mb: 0.5,
                                    }}
                                  />
                                </Tooltip>
                              );
                            })}
                          </Stack>
                        </TableCell>
                        <TableCell align="right" sx={{ py: 0.5 }}>
                          <Stack direction="row" spacing={1} justifyContent="flex-end">
                            <Tooltip title="Edit Role">
                              <IconButton
                                size="small"
                                color="primary"
                                disabled={role.is_system_role}
                                onClick={() => handleOpenDialog('editRole', role)}
                                sx={{
                                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                                  '&:hover': {
                                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                                  }
                                }}
                              >
                                <EditIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete Role">
                              <IconButton
                                size="small"
                                color="error"
                                disabled={role.is_system_role}
                                onClick={() => {
                                  if (window.confirm('Are you sure you want to delete this role?')) {
                                    deleteRole(role.role_id);
                                  }
                                }}
                                sx={{
                                  backgroundColor: alpha(theme.palette.error.main, 0.1),
                                  '&:hover': {
                                    backgroundColor: alpha(theme.palette.error.main, 0.2),
                                  }
                                }}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                        <Typography variant="body1">No roles found</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </>
          )}
        </TableContainer>
      </Box>
    );
  };

  const renderAuditLogsTable = () => {
    return (
      <TableContainer 
        component={motion.div}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        sx={{
          borderRadius: 3,
          boxShadow: `0 8px 32px 0 ${alpha(theme.palette.common.black, 0.1)}`,
          backgroundColor: alpha(theme.palette.background.paper, 0.95),
          backdropFilter: 'blur(10px)',
          overflow: 'auto',
          flexGrow: 1,
        }}
      >
        <Table size="small">
          <TableHead>
            <TableRow
              sx={{
                backgroundColor: alpha(theme.palette.primary.main, 0.03),
                '& th': {
                  borderBottom: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  color: theme.palette.text.secondary,
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  py: 1.5,
                },
              }}
            >
              <TableCell>Date & Time</TableCell>
              <TableCell>Username</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>IP Address</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredLogs.length > 0 ? (
              filteredLogs
                .map((log) => (
                <TableRow
                  key={log.log_id}
                  sx={{
                    height: '40px',
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.primary.main, 0.04),
                    },
                    '& td': { borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`, py: 0.5 },
                  }}
                >
                  <TableCell sx={{ py: 0.5 }}>
                    <Typography variant="body2">
                      {new Date(log.timestamp).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ py: 0.5 }}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Avatar
                        sx={{
                          width: 24,
                          height: 24,
                          fontSize: '0.8rem',
                          bgcolor: theme.palette.primary.main,
                        }}
                      >
                        {log.username ? log.username[0].toUpperCase() : '?'}
                      </Avatar>
                      <Typography variant="body2">{log.username}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell sx={{ py: 0.5 }}>
                    <Typography variant="body2">{log.login_type}</Typography>
                  </TableCell>
                  <TableCell sx={{ py: 0.5 }}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {log.ip_address}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ py: 0.5 }}>
                    <Chip
                      label={log.status.toUpperCase()}
                      size="small"
                      color={log.status === 'success' ? 'success' : 'error'}
                      sx={{
                        height: '24px',
                        fontSize: '0.75rem',
                        borderRadius: '6px',
                      }}
                    />
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                  <Typography variant="body1">
                    {auditLogsLoading ? 'Loading audit logs...' : 'No audit logs found'}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 0: // Users
        return (
          <motion.div
            key="users-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
            style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}
          >
            <MetricsSection 
              users={users} 
              roles={roles} 
              pendingApprovals={pendingApprovals} 
            />
            
            <UsersTable 
              users={users}
              pendingApprovals={pendingApprovals}
              onOpenNewUserDialog={() => handleOpenDialog('newUser')}
              onEdit={(user) => handleOpenDialog('editUser', user)}
              onDelete={(userId) => {
                if (window.confirm('Are you sure you want to delete this user?')) {
                  deleteUser(userId);
                }
              }}
              onResetPassword={(user) => handleOpenDialog('resetPassword', user)}
              onApprove={(userId) => approveUser(userId, 'approve')}
              onReject={(userId) => approveUser(userId, 'reject')}
            />
          </motion.div>
        );
      
      case 1: // Database Connection - navigates to separate page, so show nothing here
        return (
          <motion.div
            key="db-connection-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
            style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
              <Typography variant="body1" color="text.secondary">
                Database Connection management is available at the separate page.
              </Typography>
            </Box>
          </motion.div>
        );
      
      case 2: // Roles
        return (
          <motion.div
            key="roles-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
            style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}
          >
            {renderRolesTable()}
          </motion.div>
        );
      
      case 3: // Audit Logs
        return (
          <motion.div
            key="audit-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
            style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}
          >
            <Box sx={{ mb: 2, flexShrink: 0 }}>
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  mb: 2,
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  gap: 1.5,
                  borderRadius: 3,
                  backdropFilter: 'blur(10px)',
                  background: alpha(theme.palette.background.paper, 0.8),
                  boxShadow: `0 6px 16px 0 ${alpha(theme.palette.primary.main, 0.1)}`,
                }}
              >
                <TextField
                  placeholder="Search logs..."
                  variant="outlined"
                  size="small"
                  value={logSearchTerm}
                  onChange={(e) => setLogSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary', fontSize: '1.1rem' }} />,
                    sx: {
                      borderRadius: 2,
                      height: 36,
                      backgroundColor: theme.palette.background.paper,
                      '& .MuiOutlinedInput-notchedOutline': {
                        borderColor: alpha(theme.palette.divider, 0.4),
                      }
                    }
                  }}
                  sx={{ flex: 1, minWidth: { xs: '100%', sm: 200 } }}
                />
                
                <TextField
                  label="Start Date"
                  type="date"
                  size="small"
                  value={startDate || ''}
                  onChange={(e) => setStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  sx={{
                    width: { xs: 'calc(50% - 4px)', sm: 160 },
                    '& .MuiInputBase-root': {
                      borderRadius: 2,
                      height: 36,
                      backgroundColor: theme.palette.background.paper,
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: alpha(theme.palette.divider, 0.4),
                    }
                  }}
                />
                
                <TextField
                  label="End Date"
                  type="date"
                  size="small"
                  value={endDate || ''}
                  onChange={(e) => setEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  sx={{
                    width: { xs: 'calc(50% - 4px)', sm: 160 },
                    '& .MuiInputBase-root': {
                      borderRadius: 2,
                      height: 36,
                      backgroundColor: theme.palette.background.paper,
                    },
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: alpha(theme.palette.divider, 0.4),
                    }
                  }}
                />
                
                <Button
                  variant="outlined"
                  onClick={() => {
                    setLogSearchTerm('');
                    setStartDate(null);
                    setEndDate(null);
                  }}
                  sx={{
                    borderRadius: 2,
                    px: 1.5,
                    py: 0.6,
                    ml: { xs: 0, sm: 'auto' },
                    backgroundColor: alpha(theme.palette.background.paper, 0.6),
                    borderColor: alpha(theme.palette.divider, 0.4),
                    color: theme.palette.text.primary,
                    fontSize: '0.8rem',
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.background.paper, 0.8),
                      borderColor: alpha(theme.palette.primary.main, 0.6),
                    },
                  }}
                >
                  Clear Filters
                </Button>
                <Tooltip title="Refresh">
                  <IconButton
                    onClick={loadAuditLogs}
                    size="small"
                    sx={{
                      backgroundColor: alpha(theme.palette.primary.main, 0.1),
                      '&:hover': {
                        backgroundColor: alpha(theme.palette.primary.main, 0.2),
                      }
                    }}
                  >
                    <RefreshIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Paper>
            </Box>
            
            {auditLogsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress size={30} />
              </Box>
            ) : (
              renderAuditLogsTable()
            )}
          </motion.div>
        );
      
      case 4: // License
        return (
          <motion.div
            key="license-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <LicenseManager />
          </motion.div>
        );
      
      case 5: // Notifications
        return (
          <motion.div
            key="notifications-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <NotificationManager />
          </motion.div>
        );
      
      case 6: // About
        return (
          <motion.div
            key="about-tab"
            variants={tabContentVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.3 }}
          >
            <AboutTabContent />
          </motion.div>
        );
      
      default:
        return null;
    }
  };

  // Show loading state while checking access
  if (accessLoading || loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  // Show error state if there's an access error
  if (accessError) {
    return (
      <NotAuthorized 
        title="Error Loading Permissions"
        message={`Failed to load access permissions: ${accessError}`}
      />
    );
  }

  // Show not authorized if user doesn't have access
  if (!hasAccess) {
    const userRoles = getUserRoles();
    return (
      <NotAuthorized 
        title="Admin Access Required"
        message={`You need ADMIN role to access the Admin module. Your current role(s): ${userRoles.length > 0 ? userRoles.join(', ') : 'None'}`}
      />
    );
  }

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.3 }}
      style={{ width: '100%' }}
    >
      <Box
        sx={{
          width: '100%',
          height: '100%',
          overflow: 'auto',
          minHeight: 'calc(100vh - 64px)', // Adjust based on your layout
          background: theme.palette.mode === 'dark' 
            ? `linear-gradient(145deg, ${alpha(theme.palette.background.default, 0.9)}, ${alpha(theme.palette.background.paper, 0.7)})`
            : `linear-gradient(145deg, ${alpha(theme.palette.background.default, 0.7)}, ${alpha(theme.palette.background.paper, 0.9)})`,
          backdropFilter: 'blur(10px)',
        }}
      >
        {/* Main content area */}
        <Container maxWidth={false} sx={{ py: 1, px: { xs: 1, md: 2 } }}>
          <AnimatePresence mode="wait">
            {renderTabContent()}
          </AnimatePresence>
        </Container>
      </Box>
      
      {/* User Dialogs */}
      <UserDialog
        open={openDialog && ['newUser', 'editUser', 'resetPassword'].includes(dialogType)}
        onClose={handleCloseDialog}
        dialogType={dialogType}
        selectedUser={selectedUser}
        roles={roles}
        onSuccess={refreshData}
      />
      
      {/* Role Dialogs */}
      <RoleDialog
        open={openDialog && ['newRole', 'editRole'].includes(dialogType)}
        onClose={handleCloseDialog}
        dialogType={dialogType}
        selectedRole={selectedRole}
        onSuccess={loadRoles}
        modules={modules}
      />
      
      {/* Module Dialogs */}
      <ModuleDialog
        open={openDialog && ['newModule', 'editModule', 'manageModules'].includes(dialogType)}
        onClose={handleCloseDialog}
        dialogType={dialogType}
        selectedModule={selectedModule}
        onSuccess={(action, data) => {
          if (action === 'editModule' && data) {
            handleOpenDialog('editModule', data);
          } else {
            loadModules();
          }
        }} 
        modules={modules}
        setModules={setModules}
      />
    </motion.div>
  );
};

export default ModernAdminDashboard; 