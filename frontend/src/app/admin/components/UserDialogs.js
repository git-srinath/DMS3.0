import React, { useState, useEffect } from 'react';
import {  Dialog,  DialogTitle,  DialogContent,  DialogActions,  TextField,  Button,  FormControl,  InputLabel,  Select,  MenuItem,  Grid,  IconButton,  Box,  Typography,  useTheme,  alpha,  FormHelperText,  Divider,  Alert,  Switch,  FormControlLabel,  InputAdornment,  CircularProgress} from '@mui/material';
import { motion } from 'framer-motion';
import CloseIcon from '@mui/icons-material/Close';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import axios from 'axios';
import { API_BASE_URL } from '../../config';
import { message } from 'antd';

// Log API URL for debugging
console.log('API Base URL:', API_BASE_URL);

// Password strength validation
const isValidPassword = (password) => {
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const isLongEnough = password.length >= 8;
  
  return hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar && isLongEnough;
};

// Password requirements helper text
const getPasswordRequirementsText = () => {
  return 'Password must have at least 8 characters and include uppercase, lowercase, numbers, and special characters.';
};

export const UserDialog = ({ 
  open, 
  onClose, 
  dialogType, 
  selectedUser, 
  roles = [], 
  onSuccess 
}) => {
  const theme = useTheme();
  const isNewUser = dialogType === 'newUser';
  const isEditUser = dialogType === 'editUser';
  const isResetPassword = dialogType === 'resetPassword';

  // User form state
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    department: '',
    position: '',
    role_id: '',
    is_active: true,
    change_password: false
  });

  // Password state for reset
  const [passwordData, setPasswordData] = useState({
    new_password: '',
    confirm_password: ''
  });

  // Form validation
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resetPasswordSuccess, setResetPasswordSuccess] = useState(false);

  // Init form data when dialog opens
  useEffect(() => {
    if (isEditUser && selectedUser) {
      console.log("Edit User - selectedUser:", selectedUser);
      setFormData({
        username: selectedUser.username || '',
        email: selectedUser.email || '',
        password: '',
        confirmPassword: '',
        first_name: selectedUser.first_name || '',
        last_name: selectedUser.last_name || '',
        department: selectedUser.department || '',
        position: selectedUser.position || '',
        role_id: selectedUser.role_id || '',
        is_active: selectedUser.is_active,
        change_password: selectedUser.change_password || false
      });
    } else if (isResetPassword && selectedUser) {
      console.log("Reset Password - selectedUser:", selectedUser);
      console.log("User ID from selectedUser:", selectedUser.user_id || selectedUser.id || "No ID found");
      setPasswordData({
        new_password: '',
        confirm_password: ''
      });
      setResetPasswordSuccess(false);
    } else if (isNewUser) {
      setFormData({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        first_name: '',
        last_name: '',
        department: '',
        position: '',
        role_id: '',
        is_active: true,
        change_password: false
      });
    }
  }, [open, dialogType, selectedUser, isEditUser, isNewUser, isResetPassword]);

  const validateForm = () => {
    const newErrors = {};
    
    if (isNewUser || isEditUser) {
      if (!formData.username.trim()) newErrors.username = 'Username is required';
      if (!formData.email.trim()) newErrors.email = 'Email is required';
      if (!formData.first_name.trim()) newErrors.first_name = 'First name is required';
      if (!formData.last_name.trim()) newErrors.last_name = 'Last name is required';
      if (!formData.role_id) newErrors.role_id = 'Role is required';
      
      if (isNewUser) {
        if (!formData.password) {
          newErrors.password = 'Password is required';
        } else if (!isValidPassword(formData.password)) {
          newErrors.password = getPasswordRequirementsText();
        }
        
        if (!formData.confirmPassword) {
          newErrors.confirmPassword = 'Please confirm your password';
        } else if (formData.password !== formData.confirmPassword) {
          newErrors.confirmPassword = 'Passwords do not match';
        }
      }
    } else if (isResetPassword) {
      if (!passwordData.new_password) {
        newErrors.new_password = 'New password is required';
      } else if (!isValidPassword(passwordData.new_password)) {
        newErrors.new_password = getPasswordRequirementsText();
      }
      
      if (!passwordData.confirm_password) {
        newErrors.confirm_password = 'Please confirm the new password';
      } else if (passwordData.new_password !== passwordData.confirm_password) {
        newErrors.confirm_password = 'Passwords do not match';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value, checked } = e.target;
    if (name === 'is_active') {
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (name === 'change_password') {
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const handleToggleConfirmPasswordVisibility = () => {
    setShowConfirmPassword(!showConfirmPassword);
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    // Prevent multiple submissions
    if (loading) return;
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        setLoading(false);
        return;
      }

      if (isResetPassword && selectedUser) {
        // Reset user password
        await axios.post(
          `${API_BASE_URL}/admin/users/${selectedUser.user_id}/reset-password`,
          { new_password: passwordData.new_password },
          {
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        message.success('Password reset successfully');
        
        if (onSuccess) {
          onSuccess();
        }
        
        onClose();
      } else if (isNewUser) {
        // Create new user
        const response = await axios.post(
          `${API_BASE_URL}/admin/users`,
          {
            username: formData.username,
            email: formData.email,
            password: formData.password,
            first_name: formData.first_name,
            last_name: formData.last_name,
            department: formData.department,
            position: formData.position,
            role_id: formData.role_id,
            is_active: formData.is_active,
            change_password: formData.change_password
          },
          {
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );
        message.success('User created successfully');
        
        if (onSuccess) {
          onSuccess();
        }
        
        onClose();
      } else if (isEditUser && selectedUser) {
        // Update existing user
        const response = await axios.put(
          `${API_BASE_URL}/admin/users/${selectedUser.user_id}`,
          {
            username: formData.username,
            email: formData.email,
            first_name: formData.first_name,
            last_name: formData.last_name,
            department: formData.department,
            position: formData.position,
            role_id: formData.role_id,
            is_active: formData.is_active,
            change_password: formData.change_password
          },
          {
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );
        message.success('User updated successfully');
        
        if (onSuccess) {
          onSuccess();
        }
        
        onClose();
      }
    } catch (err) {
      console.error("Error in handleSubmit:", err);
      message.error(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Separate function specifically for password reset
  const handleResetPassword = async (e) => {
    e.preventDefault(); // Prevent form submission
    
    console.log("Reset password form submitted");
    
    // Extract user ID safely
    const userId = selectedUser?.user_id || selectedUser?.id;
    
    if (!userId) {
      console.error("No user ID found:", selectedUser);
      message.error("Cannot reset password: User ID is missing");
      return;
    }
    
    console.log("Resetting password for user ID:", userId);
    
    // Validate password fields
    const resetErrors = {};
    if (!passwordData.new_password) {
      resetErrors.new_password = 'New password is required';
    } else if (!isValidPassword(passwordData.new_password)) {
      resetErrors.new_password = getPasswordRequirementsText();
    }
    
    if (!passwordData.confirm_password) {
      resetErrors.confirm_password = 'Please confirm the new password';
    } else if (passwordData.new_password !== passwordData.confirm_password) {
      resetErrors.confirm_password = 'Passwords do not match';
    }
    
    setErrors(resetErrors);
    if (Object.keys(resetErrors).length > 0) {
      return;
    }
    
    // Prevent multiple submissions
    if (loading) return;
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        setLoading(false);
        return;
      }
      
      // Create the API endpoint URL
      const resetPasswordUrl = `${API_BASE_URL}/admin/users/${userId}/reset-password`;
      
      console.log("Making API request to:", resetPasswordUrl);
      
      // Create the request payload
      const requestData = {
        new_password: passwordData.new_password
      };
      
      // Make direct XMLHttpRequest for maximum compatibility
      const xhr = new XMLHttpRequest();
      xhr.open('POST', resetPasswordUrl, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.withCredentials = true;
      
      xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
          console.log("Password reset successful!");
          message.success('Password reset successfully');
          setResetPasswordSuccess(true);
          
          if (onSuccess) {
            onSuccess();
          }
          
          // Don't close immediately on success to show feedback
          setTimeout(() => {
            onClose();
          }, 1500);
        } else {
          console.error("Error response:", xhr.status, xhr.statusText);
          let errorMessage = 'Failed to reset password';
          
          try {
            const errorData = JSON.parse(xhr.responseText);
            if (errorData && errorData.error) {
              errorMessage = errorData.error;
            }
          } catch (e) {
            // Parse error, use default message
          }
          
          message.error(errorMessage);
        }
        setLoading(false);
      };
      
      xhr.onerror = function() {
        console.error("Network error occurred");
        message.error('Network error occurred. Please check your connection.');
        setLoading(false);
      };
      
      xhr.send(JSON.stringify(requestData));
      
    } catch (error) {
      console.error('Reset password error:', error);
      message.error(error.message || 'Failed to reset password');
      setLoading(false);
    }
  };

  const renderTitle = () => {
    if (isNewUser) return 'Add New User';
    if (isEditUser) return 'Edit User';
    if (isResetPassword) return 'Reset Password';
    return '';
  };

  const renderUserForm = () => (
    <Grid container spacing={1.5}>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Username"
          name="username"
          value={formData.username}
          onChange={handleChange}
          error={!!errors.username}
          helperText={errors.username}
          variant="outlined"
          margin="dense"
          size="small"
          disabled={isEditUser && selectedUser?.is_system_user}
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Email"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          error={!!errors.email}
          helperText={errors.email}
          variant="outlined"
          margin="dense"
          size="small"
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="First Name"
          name="first_name"
          value={formData.first_name}
          onChange={handleChange}
          error={!!errors.first_name}
          helperText={errors.first_name}
          variant="outlined"
          margin="dense"
          size="small"
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Last Name"
          name="last_name"
          value={formData.last_name}
          onChange={handleChange}
          error={!!errors.last_name}
          helperText={errors.last_name}
          variant="outlined"
          margin="dense"
          size="small"
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Department"
          name="department"
          value={formData.department}
          onChange={handleChange}
          variant="outlined"
          margin="dense"
          size="small"
        />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          fullWidth
          label="Position"
          name="position"
          value={formData.position}
          onChange={handleChange}
          variant="outlined"
          margin="dense"
          size="small"
        />
      </Grid>
      <Grid item xs={12}>
        <FormControl fullWidth margin="dense" error={!!errors.role_id} size="small">
          <InputLabel id="role-select-label">Role</InputLabel>
          <Select
            labelId="role-select-label"
            id="role-select"
            name="role_id"
            value={formData.role_id}
            onChange={handleChange}
            label="Role"
          >
            {roles.map(role => (
              <MenuItem key={role.role_id} value={role.role_id}>
                {role.role_name}
              </MenuItem>
            ))}
          </Select>
          {errors.role_id && <FormHelperText>{errors.role_id}</FormHelperText>}
        </FormControl>
      </Grid>
      {isNewUser && (
        <>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Password"
              name="password"
              type={showPassword ? "text" : "password"}
              value={formData.password}
              onChange={handleChange}
              error={!!errors.password}
              helperText={errors.password}
              variant="outlined"
              margin="dense"
              size="small"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleTogglePasswordVisibility}
                      edge="end"
                      size="small"
                    >
                      {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Confirm Password"
              name="confirmPassword"
              type={showConfirmPassword ? "text" : "password"}
              value={formData.confirmPassword}
              onChange={handleChange}
              error={!!errors.confirmPassword}
              helperText={errors.confirmPassword}
              variant="outlined"
              margin="dense"
              size="small"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleToggleConfirmPasswordVisibility}
                      edge="end"
                      size="small"
                    >
                      {showConfirmPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Grid>
        </>
      )}
      <Grid item xs={12}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', mt: 0.5 }}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={handleChange}
                name="is_active"
                color="primary"
                size="small"
              />
            }
            label={<Typography variant="body2">Active</Typography>}
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.change_password}
                onChange={handleChange}
                name="change_password"
                color="primary"
                size="small"
              />
            }
            label={<Typography variant="body2">Require Password Change On Next Login</Typography>}
            sx={{ ml: 2 }}
          />
        </Box>
      </Grid>
    </Grid>
  );

  const renderPasswordResetForm = () => {
    // Safely determine the user ID from the selectedUser object
    let userId = null;
    let username = 'Unknown User';
    
    if (selectedUser) {
      // Try different possible property names
      userId = selectedUser.user_id || selectedUser.id;
      username = selectedUser.username || selectedUser.name || 'Unknown User';
    }
    
    return (
      <form onSubmit={handleResetPassword}>
        <Grid container spacing={1.5}>
          <Grid item xs={12}>
            <Alert severity="info" sx={{ mb: 1, py: 0.5, fontSize: '0.85rem' }}>
              Reset password for user: <strong>{username}</strong>
              {userId ? <Box mt={0.5} fontSize="0.75rem">User ID: {userId}</Box> : <Box mt={0.5} color="error.main" fontSize="0.75rem">Error: No user ID found!</Box>}
            </Alert>
          </Grid>
          {resetPasswordSuccess && (
            <Grid item xs={12}>
              <Alert severity="success" sx={{ mb: 1, py: 0.5, fontSize: '0.85rem' }}>
                Password has been reset successfully!
              </Alert>
            </Grid>
          )}
          <Grid item xs={12}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              {getPasswordRequirementsText()}
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="New Password"
              name="new_password"
              type={showPassword ? "text" : "password"}
              value={passwordData.new_password}
              onChange={handlePasswordChange}
              error={!!errors.new_password}
              helperText={errors.new_password}
              variant="outlined"
              margin="dense"
              size="small"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleTogglePasswordVisibility}
                      edge="end"
                      size="small"
                    >
                      {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Confirm New Password"
              name="confirm_password"
              type={showConfirmPassword ? "text" : "password"}
              value={passwordData.confirm_password}
              onChange={handlePasswordChange}
              error={!!errors.confirm_password}
              helperText={errors.confirm_password}
              variant="outlined"
              margin="dense"
              size="small"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={handleToggleConfirmPasswordVisibility}
                      edge="end"
                      size="small"
                    >
                      {showConfirmPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sx={{ mt: 1 }}>
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={loading || resetPasswordSuccess || !userId}
              size="small"
              sx={{
                borderRadius: 1.5,
                py: 0.75,
                background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${alpha(theme.palette.primary.dark, 0.9)})`,
                boxShadow: `0 3px 6px ${alpha(theme.palette.primary.main, 0.3)}`,
                '&:hover': {
                  boxShadow: `0 4px 10px ${alpha(theme.palette.primary.main, 0.5)}`,
                }
              }}
            >
              {loading ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={14} color="inherit" sx={{ mr: 1 }} />
                  Processing...
                </Box>
              ) : resetPasswordSuccess ? 'Password Reset' : 'Reset Password'}
            </Button>
          </Grid>
        </Grid>
      </form>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        component: motion.div,
        initial: { y: 20, opacity: 0 },
        animate: { y: 0, opacity: 1 },
        transition: { duration: 0.3 },
        sx: {
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: `0 8px 32px 0 ${alpha(theme.palette.primary.main, 0.2)}`,
        }
      }}
    >
      <DialogTitle sx={{ 
        py: 1.5, 
        px: 2,
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        backgroundColor: alpha(theme.palette.primary.main, 0.05),
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
      }}>
        <Typography variant="subtitle1" component="div" fontWeight={600}>
          {renderTitle()}
        </Typography>
        <IconButton
          edge="end"
          onClick={onClose}
          size="small"
          sx={{
            color: theme.palette.text.secondary,
            backgroundColor: alpha(theme.palette.text.secondary, 0.05),
            '&:hover': {
              backgroundColor: alpha(theme.palette.text.secondary, 0.1),
            }
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ p: 2 }}>
        {(isNewUser || isEditUser) && renderUserForm()}
        {isResetPassword && renderPasswordResetForm()}
      </DialogContent>
      {(isNewUser || isEditUser) && (
        <DialogActions sx={{ p: 2, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
          <Button 
            onClick={onClose}
            variant="outlined"
            size="small"
            sx={{
              borderRadius: 1.5,
              px: 1.5,
              py: 0.6,
              fontSize: '0.8rem',
              borderColor: alpha(theme.palette.divider, 0.5),
              color: theme.palette.text.secondary,
              '&:hover': {
                backgroundColor: alpha(theme.palette.text.secondary, 0.05),
                borderColor: alpha(theme.palette.divider, 0.8),
              }
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            variant="contained"
            disabled={loading}
            size="small"
            sx={{
              borderRadius: 1.5,
              px: 1.5,
              py: 0.6,
              fontSize: '0.8rem',
              background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${alpha(theme.palette.primary.dark, 0.9)})`,
              boxShadow: `0 3px 6px ${alpha(theme.palette.primary.main, 0.3)}`,
              '&:hover': {
                boxShadow: `0 4px 10px ${alpha(theme.palette.primary.main, 0.5)}`,
              },
              '&.Mui-disabled': {
                opacity: 0.7,
                background: `linear-gradient(90deg, ${alpha(theme.palette.primary.main, 0.8)}, ${alpha(theme.palette.primary.dark, 0.7)})`
              }
            }}
            startIcon={loading ? <CircularProgress size={14} color="inherit" /> : null}
          >
            {loading ? 'Processing...' : isNewUser ? 'Create User' : 'Update User'}
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
};

export default UserDialog; 