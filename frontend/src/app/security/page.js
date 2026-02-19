'use client';

import React, { useEffect, useMemo, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../config';
import axios from 'axios';
import {
  Alert,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  InputAdornment,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

const groupLabels = {
  data_management: 'Data Management',
  report_management: 'Report Management',
};

const groupHelpText = {
  data_management: 'Core operational modules for managing and processing data assets.',
  report_management: 'Analytics and reporting modules that surface performance insights.',
};

const formatUserLabel = (user) => {
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
  return fullName || user.username || 'Unknown User';
};

const defaultFeedback = { type: null, message: '' };

const SecurityPage = () => {
  const { user, loading, refreshModuleAccess } = useAuth();
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [modules, setModules] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingModules, setLoadingModules] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [feedback, setFeedback] = useState(defaultFeedback);

  const isAdmin = user?.role === 'ADMIN';

  const fetchUsers = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setFeedback({ type: 'error', message: 'Authentication is required to load users.' });
      setLoadingUsers(false);
      return;
    }

    try {
      setLoadingUsers(true);
      const response = await axios.get(`${API_BASE_URL}/admin/users`, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        withCredentials: true,
      });

      const retrievedUsers = Array.isArray(response.data) ? response.data : [];
      setUsers(retrievedUsers);
      setFilteredUsers(retrievedUsers);

      if (!selectedUserId && retrievedUsers.length > 0) {
        setSelectedUserId(Number(retrievedUsers[0].user_id));
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
      setFeedback({
        type: 'error',
        message: error.response?.data?.error || 'Unable to load users. Please try again.',
      });
    } finally {
      setLoadingUsers(false);
    }
  }, [selectedUserId]);

  const fetchUserModules = useCallback(
    async (userId) => {
      const token = localStorage.getItem('token');
      if (!token || !userId) {
        setModules([]);
        return;
      }

      try {
        setLoadingModules(true);
        setHasChanges(false);
        setFeedback(defaultFeedback);

        const response = await axios.get(`${API_BASE_URL}/security/user-access/${userId}`, {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          withCredentials: true,
        });

        const retrievedModules = Array.isArray(response.data?.modules)
          ? response.data.modules
          : [];
        setModules(retrievedModules);
      } catch (error) {
        console.error('Failed to fetch module access:', error);
        setModules([]);
        setFeedback({
          type: 'error',
          message:
            error.response?.data?.error ||
            'Unable to load module access for the selected user.',
        });
      } finally {
        setLoadingModules(false);
      }
    },
    [],
  );

  useEffect(() => {
    if (!loading && isAdmin) {
      fetchUsers();
    }
  }, [fetchUsers, isAdmin, loading]);

  useEffect(() => {
    if (selectedUserId) {
      fetchUserModules(selectedUserId);
    }
  }, [fetchUserModules, selectedUserId]);

  useEffect(() => {
    if (!search.trim()) {
      setFilteredUsers(users);
      return;
    }

    const query = search.toLowerCase();
    const results = users.filter((item) => {
      const values = [
        item.username,
        item.email,
        item.first_name,
        item.last_name,
        item.department,
      ]
        .filter(Boolean)
        .map((value) => value.toString().toLowerCase());
      return values.some((value) => value.includes(query));
    });
    setFilteredUsers(results);
  }, [search, users]);

  const groupedModules = useMemo(() => {
    return modules.reduce(
      (acc, module) => {
        if (!module?.group) return acc;
        if (!acc[module.group]) {
          acc[module.group] = [];
        }
        acc[module.group].push(module);
        return acc;
      },
      { data_management: [], report_management: [] },
    );
  }, [modules]);

  const handleToggle = (key) => {
    setModules((prev) =>
      prev.map((module) =>
        module.key === key ? { ...module, enabled: !module.enabled } : module,
      ),
    );
    setHasChanges(true);
  };

  const handleSave = async () => {
    const token = localStorage.getItem('token');
    if (!selectedUserId || !token) return;

    try {
      setSaving(true);
      setFeedback(defaultFeedback);
      const payload = {
        modules: modules.map((module) => ({
          key: module.key,
          enabled: !!module.enabled,
        })),
      };

      const response = await axios.post(
        `${API_BASE_URL}/security/user-access/${selectedUserId}`,
        payload,
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          withCredentials: true,
        },
      );

      const updatedModules = Array.isArray(response.data?.modules)
        ? response.data.modules
        : modules;
      setModules(updatedModules);
      setHasChanges(false);

      // Refresh current user's module access if they updated themselves
      if (user?.id && Number(user.id) === Number(selectedUserId)) {
        await refreshModuleAccess();
      }

      setFeedback({
        type: 'success',
        message: response.data?.message || 'User access updated successfully.',
      });
    } catch (error) {
      console.error('Failed to update user modules:', error);
      setFeedback({
        type: 'error',
        message: error.response?.data?.error || 'Failed to update module access.',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!isAdmin) {
    return (
      <Box sx={{ minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center', px: 2 }}>
        <Paper
          elevation={0}
          sx={{
            maxWidth: 480,
            width: '100%',
            p: 4,
            borderRadius: 4,
            textAlign: 'center',
            border: '1px solid rgba(148, 163, 184, 0.25)',
          }}
        >
          <ShieldOutlinedIcon sx={{ fontSize: 48, color: '#64748b', mb: 2 }} />
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Admin Access Required
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Only administrators can manage module security. Please contact your administrator if you need access.
          </Typography>
        </Paper>
      </Box>
    );
  }

  const activeUser = users.find((item) => Number(item.user_id) === Number(selectedUserId));

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: { xs: 3, md: 4 }, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Enable or disable access to specific application modules for each user. Essentials and Admin tools remain available for everyone.
      </Typography>

      {feedback.type && (
        <Alert
          severity={feedback.type}
          onClose={() => setFeedback(defaultFeedback)}
          sx={{ mb: 2 }}
        >
          {feedback.message}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper
            elevation={0}
            sx={{
              borderRadius: 3,
              p: 2.5,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              height: '100%',
            }}
          >
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Users
            </Typography>

            <TextField
              size="small"
              placeholder="Search by name, email, or department"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />

            <Box sx={{ maxHeight: 420, overflowY: 'auto' }}>
              {loadingUsers ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : filteredUsers.length === 0 ? (
                <Typography variant="body2" color="text.secondary" textAlign="center" py={4}>
                  No users match your search.
                </Typography>
              ) : (
                <List dense disablePadding>
                  {filteredUsers.map((item) => {
                    const userId = Number(item.user_id);
                    const isSelected = Number(selectedUserId) === userId;
                    const initials =
                      item.first_name?.[0] ||
                      item.username?.[0]?.toUpperCase() ||
                      '?';

                    return (
                      <ListItemButton
                        key={userId}
                        selected={isSelected}
                        onClick={() => setSelectedUserId(userId)}
                        sx={{
                          borderRadius: 2,
                          mb: 0.5,
                        }}
                      >
                        <Avatar
                          sx={{
                            width: 32,
                            height: 32,
                            mr: 1.5,
                            bgcolor: isSelected ? 'primary.main' : 'grey.200',
                            color: isSelected ? '#fff' : 'text.primary',
                            fontSize: '0.85rem',
                            fontWeight: 600,
                          }}
                        >
                          {initials}
                        </Avatar>
                        <ListItemText
                          primary={
                            <Typography variant="body2" fontWeight={600}>
                              {formatUserLabel(item)}
                            </Typography>
                          }
                          secondary={
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="caption" color="text.secondary">
                                {item.email}
                              </Typography>
                              {item.role_name && (
                                <Chip
                                  size="small"
                                  label={item.role_name}
                                  sx={{ fontSize: '0.65rem', height: 18 }}
                                />
                              )}
                            </Stack>
                          }
                        />
                      </ListItemButton>
                    );
                  })}
                </List>
              )}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper
            elevation={0}
            sx={{
              borderRadius: 3,
              p: { xs: 2.5, md: 3 },
              border: '1px solid rgba(148, 163, 184, 0.2)',
              minHeight: 420,
            }}
          >
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} mb={2}>
              <Box>
                <Typography variant="subtitle1" fontWeight={600}>
                  {activeUser ? formatUserLabel(activeUser) : 'Select a user'}
                </Typography>
                {activeUser?.username && (
                  <Typography variant="caption" color="text.secondary">
                    Username: {activeUser.username}
                  </Typography>
                )}
              </Box>

              <Chip
                icon={<InfoOutlinedIcon />}
                variant="outlined"
                label="Essentials and Admin cards remain enabled for all users"
                sx={{ fontSize: '0.7rem', height: 28 }}
              />
            </Stack>

            <Divider sx={{ mb: 3 }} />

            {loadingModules ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 240 }}>
                <CircularProgress size={28} />
              </Box>
            ) : modules.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <Typography variant="body2" color="text.secondary">
                  Select a user to view their module access.
                </Typography>
              </Box>
            ) : (
              <Stack spacing={3}>
                {['data_management', 'report_management'].map((groupKey) => {
                  const items = groupedModules[groupKey] || [];
                  if (!items.length) return null;

                  return (
                    <Box key={groupKey}>
                      <Stack direction="row" alignItems="center" spacing={1} mb={1}>
                        <Typography variant="subtitle2" fontWeight={700}>
                          {groupLabels[groupKey]}
                        </Typography>
                        <Tooltip title={groupHelpText[groupKey]}>
                          <InfoOutlinedIcon fontSize="small" color="action" />
                        </Tooltip>
                      </Stack>
                      <Stack spacing={1.2}>
                        {items.map((module) => (
                          <Paper
                            key={module.key}
                            variant="outlined"
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              p: 1.5,
                              borderRadius: 2,
                            }}
                          >
                            <Box>
                              <Typography variant="body2" fontWeight={600}>
                                {module.title}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {module.description}
                              </Typography>
                            </Box>
                            <Stack direction="row" spacing={1} alignItems="center">
                              <Typography variant="caption" color="text.secondary">
                                {module.enabled ? 'Enabled' : 'Disabled'}
                              </Typography>
                              <Switch
                                color="primary"
                                checked={!!module.enabled}
                                onChange={() => handleToggle(module.key)}
                                inputProps={{ 'aria-label': `Toggle ${module.title}` }}
                              />
                              {module.enabled ? (
                                <CheckIcon fontSize="small" color="success" />
                              ) : (
                                <CloseIcon fontSize="small" color="error" />
                              )}
                            </Stack>
                          </Paper>
                        ))}
                      </Stack>
                    </Box>
                  );
                })}
              </Stack>
            )}

            <Divider sx={{ my: 3 }} />

            <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="flex-end" spacing={1.5}>
              <Button
                variant="outlined"
                onClick={() => selectedUserId && fetchUserModules(selectedUserId)}
                disabled={loadingModules || saving}
              >
                Reset
              </Button>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={!hasChanges || saving || loadingModules}
              >
                {saving ? <CircularProgress size={20} sx={{ color: '#fff' }} /> : 'Save Changes'}
              </Button>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SecurityPage;

