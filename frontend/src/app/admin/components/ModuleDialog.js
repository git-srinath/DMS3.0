import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  IconButton,
  Box,
  Typography,
  useTheme,
  alpha,
  FormHelperText,
  Divider,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip
} from '@mui/material';
import { motion } from 'framer-motion';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import axios from 'axios';
import { API_BASE_URL } from '../../config';
import { message } from 'antd';

const ModuleDialog = ({
  open,
  onClose,
  dialogType,
  selectedModule,
  onSuccess,
  modules,
  setModules
}) => {
  const theme = useTheme();
  const isNewModule = dialogType === 'newModule';
  const isEditModule = dialogType === 'editModule';
  const isManageModules = dialogType === 'manageModules';

  // Module form state
  const [formData, setFormData] = useState({
    module_name: '',
    display_name: '',
    description: ''
  });

  // For managing modules
  const [editingModuleId, setEditingModuleId] = useState(null);
  const [newModuleName, setNewModuleName] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');
  const [newDescription, setNewDescription] = useState('');

  // Form validation
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [isModulesLoading, setIsModulesLoading] = useState(false);

  // Fetch modules from backend
  const fetchModules = async () => {
    try {
      setIsModulesLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        return;
      }

      const response = await axios.get(`${API_BASE_URL}/admin/modules`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data) {
        setModules(response.data);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to fetch modules';
      message.error(errorMessage);
    } finally {
      setIsModulesLoading(false);
    }
  };

  // Initialize form data when dialog opens
  useEffect(() => {
    if (open) {
      if (isManageModules) {
        fetchModules();
      }

      if (isEditModule && selectedModule) {
        setFormData({
          module_id: selectedModule.module_id,
          module_name: selectedModule.module_name || '',
          display_name: selectedModule.display_name || '',
          description: selectedModule.description || ''
        });
      } else if (isNewModule) {
        setFormData({
          module_name: '',
          display_name: '',
          description: ''
        });
      }
    }
  }, [open, dialogType, selectedModule, isEditModule, isNewModule, isManageModules]);

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.module_name.trim()) {
      newErrors.module_name = 'Module name is required';
    } else if (!/^[a-z0-9_]+$/.test(formData.module_name)) {
      newErrors.module_name = 'Module name should contain only lowercase letters, numbers, and underscores';
    }
    
    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Display name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
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

      if (isNewModule) {
        // Create new module via API
        const response = await axios.post(
          `${API_BASE_URL}/admin/modules`,
          formData,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        message.success('Module created successfully');
        fetchModules(); // Refresh modules
      } else if (isEditModule && selectedModule) {
        // Update module via API
        const response = await axios.put(
          `${API_BASE_URL}/admin/modules/${selectedModule.module_id}`,
          formData,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            }
          }
        );
        
        message.success('Module updated successfully');
        fetchModules(); // Refresh modules
      }
      
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'An error occurred. Please try again.';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAddModule = async () => {
    if (!newModuleName.trim() || !newDisplayName.trim()) {
      message.error('Module name and display name are required');
      return;
    }
    
    if (!/^[a-z0-9_]+$/.test(newModuleName)) {
      message.error('Module name should contain only lowercase letters, numbers, and underscores');
      return;
    }

    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        return;
      }

      // Create new module via API
      const response = await axios.post(
        `${API_BASE_URL}/admin/modules`,
        {
          module_name: newModuleName,
          display_name: newDisplayName,
          description: newDescription
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      message.success('Module added successfully');
      setNewModuleName('');
      setNewDisplayName('');
      setNewDescription('');
      fetchModules(); // Refresh modules
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to add module';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteModule = async (moduleId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('Authentication required');
        return;
      }

      // Delete module via API
      const response = await axios.delete(
        `${API_BASE_URL}/admin/modules/${moduleId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );
      
      message.success('Module deleted successfully');
      fetchModules(); // Refresh modules
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'Failed to delete module';
      message.error(errorMessage);
    }
  };

  const handleEditModule = (module) => {
    // We can't directly use setDialogType and setSelectedModule here
    // So we'll close this dialog and open a new one via parent component
    onClose();
    setTimeout(() => {
      if (onSuccess) onSuccess('editModule', module);
    }, 100);
  };

  const renderTitle = () => {
    if (isManageModules) return "Manage Modules";
    return isNewModule ? "Create New Module" : "Edit Module";
  };

  // Render the form for creating/editing a single module
  const renderModuleForm = () => (
    <Box>
      <Grid container spacing={1}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Module Name"
            name="module_name"
            value={formData.module_name}
            onChange={handleChange}
            error={!!errors.module_name}
            size="small"
            required
            disabled={isEditModule} // Don't allow changing the module name once created
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Display Name"
            name="display_name"
            value={formData.display_name}
            onChange={handleChange}
            error={!!errors.display_name}
            helperText={errors.display_name}
            size="small"
            required
          />
        </Grid>
        
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            multiline
            rows={1}
            size="small"
            margin="dense"
          />
        </Grid>
      </Grid>
    </Box>
  );

  // Render the module management interface
  const renderModuleManagement = () => (
    <Box>
      <Alert severity="info" sx={{ mb: 1.5, py: 0.5, fontSize: '0.85rem' }}>
        Modules define the functional areas that permissions can be assigned to in roles.
      </Alert>
      
      <Paper 
        elevation={0} 
        sx={{ 
          p: 1.5, 
          mb: 2,
          bgcolor: alpha(theme.palette.background.paper, 0.5),
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          borderRadius: 1
        }}
      >
        <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
          Add New Module
        </Typography>
        
        <Grid container spacing={1} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Module Name"
              value={newModuleName}
              onChange={(e) => setNewModuleName(e.target.value)}
              placeholder="e.g. analytics"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Display Name"
              value={newDisplayName}
              onChange={(e) => setNewDisplayName(e.target.value)}
              placeholder="e.g. Analytics"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Description"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              placeholder="Module description"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={handleAddModule}
              disabled={loading}
              size="small"
              sx={{ 
                borderRadius: 1,
                textTransform: 'none',
                px: 2
              }}
            >
              {loading ? <CircularProgress size={20} /> : 'Add Module'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      <Typography variant="subtitle2" sx={{ mb: 0.5, fontWeight: 600 }}>
        Existing Modules
      </Typography>
      
      {isModulesLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress size={24} />
        </Box>
      ) : (
        <List sx={{ 
          bgcolor: alpha(theme.palette.background.paper, 0.5),
          border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
          borderRadius: 1,
          py: 0
        }}>
          {modules.length > 0 ? (
            modules.map((module, index) => (
              <React.Fragment key={module.module_id || index}>
                <ListItem 
                  sx={{ 
                    py: 0.75,
                    backgroundColor: index % 2 === 0 ? alpha(theme.palette.background.paper, 0.3) : 'transparent',
                  }}
                >
                  <ListItemText 
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {module.display_name}
                        </Typography>
                        <Chip 
                          label={module.module_name} 
                          size="small"
                          sx={{ 
                            height: 18, 
                            fontSize: '0.65rem',
                            backgroundColor: alpha(theme.palette.info.main, 0.1),
                            color: theme.palette.info.main
                          }}
                        />
                      </Box>
                    }
                    secondary={
                      <Typography variant="caption">
                        {module.description || 'No description provided'}
                      </Typography>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton 
                      edge="end" 
                      aria-label="edit"
                      size="small"
                      onClick={() => handleEditModule(module)}
                      sx={{
                        mr: 1,
                        backgroundColor: alpha(theme.palette.primary.main, 0.1),
                        '&:hover': { backgroundColor: alpha(theme.palette.primary.main, 0.2) }
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton 
                      edge="end" 
                      aria-label="delete"
                      size="small"
                      onClick={() => {
                        if (window.confirm(`Are you sure you want to delete the "${module.display_name}" module?`)) {
                          handleDeleteModule(module.module_id);
                        }
                      }}
                      sx={{
                        backgroundColor: alpha(theme.palette.error.main, 0.1),
                        '&:hover': { backgroundColor: alpha(theme.palette.error.main, 0.2) }
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < modules.length - 1 && <Divider />}
              </React.Fragment>
            ))
          ) : (
            <ListItem>
              <ListItemText primary="No modules defined yet" />
            </ListItem>
          )}
        </List>
      )}
    </Box>
  );

  return (
    <Dialog
      open={open}
      onClose={loading ? null : onClose}
      maxWidth={isManageModules ? "sm" : "xs"}
      fullWidth
      PaperProps={{
        elevation: 6,
        sx: {
          borderRadius: 2,
          backgroundColor: theme.palette.background.paper,
          backgroundImage: `linear-gradient(${alpha(theme.palette.background.paper, 0.9)}, ${alpha(theme.palette.background.paper, 0.95)})`,
          backdropFilter: 'blur(10px)',
        }
      }}
    >
      <DialogTitle sx={{ 
        py: 1,
        px: 2,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Typography variant="subtitle1" component="div" sx={{ fontWeight: 600 }}>
          {renderTitle()}
        </Typography>
        <IconButton
          edge="end"
          color="inherit"
          onClick={onClose}
          disabled={loading}
          aria-label="close"
          size="small"
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      
      <Divider />
      
      <DialogContent sx={{ py: 1.5, px: 2 }}>
        {isManageModules 
          ? renderModuleManagement()
          : renderModuleForm()
        }
      </DialogContent>
      
      <DialogActions sx={{ px: 2, py: 1 }}>
        <Button 
          onClick={onClose} 
          disabled={loading}
          variant="outlined"
          size="small"
          sx={{ 
            borderRadius: 1,
            textTransform: 'none',
            px: 2
          }}
        >
          Close
        </Button>
        
        {!isManageModules && (
          <Button
            onClick={handleSubmit}
            variant="contained"
            size="small"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
            sx={{ 
              borderRadius: 1,
              textTransform: 'none',
              px: 2
            }}
          >
            {isNewModule ? 'Create Module' : 'Update Module'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ModuleDialog; 