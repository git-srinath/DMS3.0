'use client';

import { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Avatar,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  useTheme,
  alpha,
  Stack,
  Alert,
  Snackbar,
  useMediaQuery,
  Link,
  Tooltip,
  IconButton,
  Divider,
  Fade
} from '@mui/material';
import {
  Edit as EditIcon,
  Security as SecurityIcon,
  Logout as LogoutIcon,
  EmailOutlined as EmailIcon,
  PhoneOutlined as PhoneIcon,
  WorkOutline as WorkIcon,
  AccountCircle as AccountIcon,
  Person as PersonIcon,
  SaveOutlined as SaveIcon,
  Language as LanguageIcon,
  LinkedIn as LinkedInIcon,
  Twitter as TwitterIcon,
  GitHub as GitHubIcon,
  Business as BusinessIcon,
  Code as CodeIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '../components/ProtectedRoute';

const ProfilePage = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, logout, updateUserProfile } = useAuth();
  const router = useRouter();
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openPasswordDialog, setOpenPasswordDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [editedData, setEditedData] = useState({
    first_name: '', last_name: '', email: '', phone: '', department: ''
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '', newPassword: '', confirmPassword: ''
  });

  const appVersion = "v2.0.0";

  useEffect(() => {
    if (!user) return;
    setProfileData({ ...user, is_active: true });
    setEditedData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      email: user.email || '',
      phone: user.phone || '',
      department: user.department || ''
    });
    setLoading(false);
  }, [user]);

  const handleLogout = async () => {
    await logout();
    router.push('/auth/login');
  };

  const handleEditDialogOpen = () => setOpenEditDialog(true);
  const handleEditDialogClose = () => setOpenEditDialog(false);
  const handlePasswordDialogOpen = () => setOpenPasswordDialog(true);
  const handlePasswordDialogClose = () => {
    setOpenPasswordDialog(false);
    setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
  };

  const handleEditChange = (e) => setEditedData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  const handlePasswordChange = (e) => setPasswordData(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSaveProfile = async () => {
    try {
      updateUserProfile(editedData);
      setProfileData(prev => ({ ...prev, ...editedData }));
      setNotification({ open: true, message: 'Profile updated successfully!', severity: 'success' });
      handleEditDialogClose();
    } catch (error) {
      setNotification({ open: true, message: 'Failed to update profile.', severity: 'error' });
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setNotification({ open: true, message: 'New passwords do not match.', severity: 'error' });
      return;
    }
    try {
      setNotification({ open: true, message: 'Password changed successfully!', severity: 'success' });
      handlePasswordDialogClose();
    } catch (error) {
      setNotification({ open: true, message: 'Failed to change password.', severity: 'error' });
    }
  };

  const handleCloseNotification = () => setNotification(prev => ({ ...prev, open: false }));

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh', 
        bgcolor: 'background.default' 
      }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
          <Avatar sx={{ width: 60, height: 60, bgcolor: 'primary.main' }}>
            <PersonIcon sx={{ fontSize: 30 }} />
          </Avatar>
        </motion.div>
      </Box>
    );
  }

  return (
    <ProtectedRoute>
      <Box sx={{ 
        minHeight: '100vh', 
        bgcolor: theme.palette.mode === 'dark' ? 'background.default' : 'grey.50',
      }}>
        <Container maxWidth="xl" sx={{ py: 2 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 3,
            }}
          >
            <Typography variant={isMobile ? "h6" : "h5"} fontWeight={700} color="text.primary">
              My Profile
            </Typography>
            <Stack direction="row" spacing={1.5}>
              <Button
                variant="outlined"
                startIcon={<SecurityIcon />}
                onClick={handlePasswordDialogOpen}
                sx={{
                  borderRadius: '12px',
                  textTransform: 'none',
                  fontWeight: 600,
                  borderColor: 'divider',
                  color: 'text.secondary',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: alpha(theme.palette.primary.main, 0.04),
                  },
                }}
              >
                Security
              </Button>
              <Button
                variant="contained"
                startIcon={<LogoutIcon />}
                onClick={handleLogout}
                color="error"
                sx={{
                  borderRadius: '12px',
                  textTransform: 'none',
                  fontWeight: 600,
                  boxShadow: 'none',
                  '&:hover': {
                    boxShadow: 'none',
                    backgroundColor: alpha(theme.palette.error.main, 0.9),
                  }
                }}
              >
                Logout
              </Button>
            </Stack>
          </Box>

          <Grid container spacing={2} sx={{ alignItems: 'stretch' }}>
            <Grid item xs={12} md={4} lg={3}>
              <Stack spacing={2} sx={{ height: '100%' }}>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
                  <Paper sx={{
                    p: 2,
                    borderRadius: 4,
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.05)',
                    border: '1px solid rgba(0,0,0,0.03)',
                  }}>
                    <Box sx={{ textAlign: 'center', mb: 2 }}>
                      <Avatar sx={{
                        width: 60,
                        height: 60,
                        mx: 'auto',
                        mb: 1.5,
                        bgcolor: 'primary.main',
                        fontSize: '2rem',
                        fontWeight: 600,
                        color: 'white'
                      }}>
                        {profileData?.first_name?.charAt(0) || profileData?.username?.charAt(0) || 'U'}
                      </Avatar>
                      <Typography variant="subtitle1" fontWeight={600} color="text.primary">
                        {`${profileData?.first_name || ''} ${profileData?.last_name || ''}`.trim() || profileData?.username}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                        {profileData?.role || 'User'}
                      </Typography>
                      <Box sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        px: 1.5,
                        py: 0.5,
                        bgcolor: profileData?.is_active ? alpha(theme.palette.success.main, 0.1) : alpha(theme.palette.error.main, 0.1),
                        color: profileData?.is_active ? 'success.dark' : 'error.dark',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        gap: 0.5,
                      }}>
                        <CheckCircleIcon sx={{ fontSize: '1rem' }} />
                        {profileData?.is_active ? 'Active' : 'Inactive'}
                      </Box>
                    </Box>
                    <Button
                      variant="contained"
                      fullWidth
                      startIcon={<EditIcon />}
                      onClick={handleEditDialogOpen}
                      sx={{
                        borderRadius: '12px',
                        textTransform: 'none',
                        py: 1,
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        boxShadow: 'none',
                      }}
                    >
                      Edit Profile
                    </Button>
                  </Paper>
                </motion.div>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }} style={{ flexGrow: 1 }}>
                   <Paper sx={{
                    p: 2,
                    borderRadius: 4,
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.05)',
                    border: '1px solid rgba(0,0,0,0.03)',
                    height: '100%',
                   }}>
                      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                        <Avatar sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.1), color: 'secondary.main', width: 32, height: 32 }}>
                          <CodeIcon />
                        </Avatar>
                        <Typography variant="subtitle1" fontWeight={600}>Application</Typography>
                      </Stack>
                      <Stack spacing={1.5}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                           <Typography variant="body2" color="text.secondary">Version</Typography>
                           <Typography variant="body2" fontWeight={600}>{appVersion}</Typography>
                        </Box>
                         <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                           <Typography variant="body2" color="text.secondary">Status</Typography>
                           <Box sx={{
                              px: 1, py: 0.25,
                              bgcolor: alpha(theme.palette.success.main, 0.1),
                              color: 'success.dark',
                              borderRadius: '8px',
                              fontSize: '0.75rem',
                              fontWeight: 600
                           }}>Active</Box>
                        </Box>
                      </Stack>
                   </Paper>
                </motion.div>
              </Stack>
            </Grid>

            <Grid item xs={12} md={8} lg={9}>
              <Stack spacing={2}>
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
                  <Paper sx={{
                    p: 2,
                    borderRadius: 4,
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.05)',
                    border: '1px solid rgba(0,0,0,0.03)',
                  }}>
                    <Typography variant="subtitle1" fontWeight={600} color="text.primary" sx={{ mb: 2 }}>
                      Account Information
                    </Typography>
                    <Grid container spacing={1.5}>
                      {[
                        { label: 'Username', value: profileData?.username, icon: <AccountIcon color="primary" /> },
                        { label: 'Email', value: profileData?.email, icon: <EmailIcon color="primary" /> },
                        { label: 'Phone', value: profileData?.phone || 'Not provided', icon: <PhoneIcon color="primary" /> },
                        { label: 'Department', value: profileData?.department || 'Not specified', icon: <WorkIcon color="primary" /> },
                        { label: 'First Name', value: profileData?.first_name || 'Not provided', icon: <PersonIcon color="primary" /> },
                        { label: 'Last Name', value: profileData?.last_name || 'Not provided', icon: <PersonIcon color="primary" /> }
                      ].map((item, index) => (
                        <Grid item xs={12} sm={6} lg={4} key={index}>
                          <Box sx={{
                            p: 1.5,
                            bgcolor: 'action.hover',
                            borderRadius: 3,
                            transition: 'all 0.3s ease',
                            height: '100%',
                            '&:hover': {
                              transform: 'translateY(-2px)',
                              boxShadow: '0 4px 12px 0 rgba(0,0,0,0.08)',
                            }
                          }}>
                            <Stack direction="row" spacing={1.5} alignItems="center">
                               {item.icon}
                              <Box>
                                <Typography variant="caption" color="text.secondary" fontWeight={500}>
                                  {item.label}
                                </Typography>
                                <Typography variant="body2" fontWeight={600} color="text.primary" sx={{ wordBreak: 'break-all' }}>
                                  {item.value}
                                </Typography>
                              </Box>
                            </Stack>
                          </Box>
                        </Grid>
                      ))}
                    </Grid>
                  </Paper>
                </motion.div>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
                  <Paper sx={{
                    p: 2,
                    borderRadius: 4,
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.05)',
                    border: '1px solid rgba(0,0,0,0.03)',
                  }}>
                    <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                      <Avatar sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), color: 'primary.main', width: 32, height: 32 }}>
                        <BusinessIcon />
                      </Avatar>
                      <Typography variant="subtitle1" fontWeight={600}>About Company</Typography>
                    </Stack>
                    <Stack spacing={1.5}>
                      <Typography variant="subtitle1" fontWeight={700} color="text.primary">
                        Ahana Systems & Solutions Pvt Ltd
                      </Typography>
                      <Typography variant="body1" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                        "Creating Possibilities"
                      </Typography>
                      <Divider />
                      <Stack spacing={1}>
                        <Stack direction="row" spacing={1.5} alignItems="center">
                          <LanguageIcon sx={{ color: 'text.secondary' }} />
                          <Link href="https://www.ahanait.com" target="_blank" sx={{ color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
                            www.ahanait.com
                          </Link>
                        </Stack>
                        <Stack direction="row" spacing={1.5} alignItems="center">
                          <EmailIcon sx={{ color: 'text.secondary' }} />
                          <Link href="mailto:info@ahanait.co.in" sx={{ color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
                            info@ahanait.co.in
                          </Link>
                        </Stack>
                      </Stack>
                      <Divider sx={{ my: 1 }}/>
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                        {[
                          { icon: <LanguageIcon />, href: "https://www.ahanait.com", name: 'Website' },
                          { icon: <LinkedInIcon />, href: "https://www.linkedin.com/company/ahana-systems-solutions/", name: 'LinkedIn' },
                          { icon: <TwitterIcon />, href: "https://twitter.com/ahana_it", name: 'Twitter' },
                          { icon: <GitHubIcon />, href: "https://github.com/ahana-systems", name: 'GitHub' }
                        ].map((social) => (
                          <Tooltip title={social.name} key={social.name}>
                            <IconButton
                              component={Link}
                              href={social.href}
                              target="_blank"
                              sx={{
                                color: 'text.secondary',
                                border: '1px solid',
                                borderColor: 'divider',
                                '&:hover': {
                                  bgcolor: 'action.hover'
                                }
                              }}
                            >
                              {social.icon}
                            </IconButton>
                          </Tooltip>
                        ))}
                      </Box>
                    </Stack>
                  </Paper>
                </motion.div>
              </Stack>
            </Grid>
          </Grid>
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              © {new Date().getFullYear()} Ahana Systems & Solutions. All Rights Reserved.
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Data Warehouse Management System
            </Typography>
          </Box>
        </Container>
      </Box>

      <Dialog
        open={openEditDialog}
        onClose={handleEditDialogClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 4,
            bgcolor: 'background.paper',
            boxShadow: theme.shadows[24]
          }
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={600}>
            Edit Your Profile
          </Typography>
        </DialogTitle>
        <DialogContent dividers sx={{ p: 3 }}>
          <Grid container spacing={2.5}>
            <Grid item xs={12} sm={6}>
              <TextField
                label="First Name"
                name="first_name"
                value={editedData.first_name}
                onChange={handleEditChange}
                fullWidth
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Last Name"
                name="last_name"
                value={editedData.last_name}
                onChange={handleEditChange}
                fullWidth
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Email"
                name="email"
                value={editedData.email}
                onChange={handleEditChange}
                fullWidth
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Phone"
                name="phone"
                value={editedData.phone}
                onChange={handleEditChange}
                fullWidth
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Department"
                name="department"
                value={editedData.department}
                onChange={handleEditChange}
                fullWidth
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button onClick={handleEditDialogClose} variant="outlined" color="secondary">Cancel</Button>
          <Button onClick={handleSaveProfile} variant="contained" startIcon={<SaveIcon />}>
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={openPasswordDialog}
        onClose={handlePasswordDialogClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 4,
            bgcolor: 'background.paper',
            boxShadow: theme.shadows[24]
          }
        }}
      >
        <DialogTitle>
          <Typography variant="h6" fontWeight={600}>
            Change Password
          </Typography>
        </DialogTitle>
        <DialogContent dividers sx={{ p: 3 }}>
          <Stack spacing={2.5}>
            <TextField
              label="Current Password"
              name="currentPassword"
              value={passwordData.currentPassword}
              onChange={handlePasswordChange}
              type="password"
              fullWidth
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
            />
            <TextField
              label="New Password"
              name="newPassword"
              value={passwordData.newPassword}
              onChange={handlePasswordChange}
              type="password"
              fullWidth
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
            />
            <TextField
              label="Confirm New Password"
              name="confirmPassword"
              value={passwordData.confirmPassword}
              onChange={handlePasswordChange}
              type="password"
              fullWidth
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 2 } }}
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Button onClick={handlePasswordDialogClose} variant="outlined" color="secondary">Cancel</Button>
          <Button onClick={handleChangePassword} variant="contained">
            Update Password
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={notification.open}
        onClose={handleCloseNotification}
        autoHideDuration={6000}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        TransitionComponent={Fade}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity} sx={{ width: '100%', borderRadius: 2, boxShadow: theme.shadows[3] }} variant="filled">
          {notification.message}
        </Alert>
      </Snackbar>
    </ProtectedRoute>
  );
};

export default ProfilePage; 