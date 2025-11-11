'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Autocomplete,
  Snackbar,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Divider,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Container,
  Stack,
  List,
  ListItem,
  ListItemText,
  ListItemButton
} from '@mui/material';
import {
  Search,
  CheckCircle,
  Save,
  Refresh,
  PlayArrow,
  Edit,
  Close,
  Add,
  Code,
  DataObject,
  History,
  ContentCopy
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import Editor from '@monaco-editor/react';

const ManageSQLPage = () => {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';

  // All state variables
  const [sqlCodes, setSqlCodes] = useState([]);
  const [selectedSqlCode, setSelectedSqlCode] = useState(null);
  const [newSqlCode, setNewSqlCode] = useState('');
  const [sqlContent, setSqlContent] = useState('');
  const [originalSqlContent, setOriginalSqlContent] = useState('');
  const [validating, setValidating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [fetchingCodes, setFetchingCodes] = useState(false);
  const [fetchingLogic, setFetchingLogic] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [validationStatus, setValidationStatus] = useState(null);

  // SQL History states
  const [sqlHistory, setSqlHistory] = useState([]);
  const [historyDialog, setHistoryDialog] = useState(false);
  const [fetchingHistory, setFetchingHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [historyPreviewDialog, setHistoryPreviewDialog] = useState(false);

  // State for Autocomplete input to allow clearing it
  const [inputValue, setInputValue] = useState('');
  
  // Dialog states
  const [previewDialog, setPreviewDialog] = useState(false);

  useEffect(() => {
    fetchAllSqlCodes();
  }, []);

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const fetchAllSqlCodes = async () => {
    setFetchingCodes(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-all-sql-codes`);
      const result = await response.json();
      
      if (result.success) {
        setSqlCodes(result.data || []);
        showSnackbar(`Successfully loaded ${result.count} SQL codes`, 'success');
      } else {
        showSnackbar(result.message || 'Failed to fetch SQL codes', 'error');
      }
    } catch (error) {
      console.error('Error fetching SQL codes:', error);
      showSnackbar('Network error while fetching SQL codes', 'error');
    } finally {
      setFetchingCodes(false);
    }
  };

  const fetchSqlLogic = async (sqlCode) => {
    if (!sqlCode) return;
    
    setFetchingLogic(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-sql-logic?sql_code=${encodeURIComponent(sqlCode)}`);
      const result = await response.json();
      
      if (result.success) {
        setSqlContent(result.data.sql_content || '');
        setOriginalSqlContent(result.data.sql_content || '');
        setValidationStatus(null);
        showSnackbar(`Successfully loaded SQL logic for ${sqlCode}`, 'success');
      } else {
        showSnackbar(result.message || 'Failed to fetch SQL logic', 'error');
        setSqlContent('');
        setOriginalSqlContent('');
      }
    } catch (error) {
      console.error('Error fetching SQL logic:', error);
      showSnackbar('Network error while fetching SQL logic', 'error');
      setSqlContent('');
      setOriginalSqlContent('');
    } finally {
      setFetchingLogic(false);
    }
  };

  // Function to fetch SQL history
  const fetchSqlHistory = async (sqlCode) => {
    if (!sqlCode) return;
    
    setFetchingHistory(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/fetch-sql-history?sql_code=${encodeURIComponent(sqlCode)}`);
      const result = await response.json();
      
      if (result.success && result.data && result.data.history_items) {
        // Process history data from the updated API response
        setSqlHistory(result.data.history_items);
        setHistoryDialog(true);
        showSnackbar(`Successfully loaded ${result.data.history_items.length} historical versions for ${sqlCode}`, 'success');
      } else {
        showSnackbar(result.message || 'No history found for this SQL code', 'info');
        setSqlHistory([]);
      }
    } catch (error) {
      console.error('Error fetching SQL history:', error);
      showSnackbar('Network error while fetching SQL history', 'error');
      setSqlHistory([]);
    } finally {
      setFetchingHistory(false);
    }
  };

  const validateSql = async () => {
    if (!sqlContent.trim()) {
      showSnackbar('Please enter SQL content to validate', 'warning');
      return;
    }

    setValidating(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/validate-sql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sql_content: sqlContent
        })
      });
      
      const result = await response.json();
      
      if (result.success && result.is_valid) {
        setValidationStatus('valid');
        showSnackbar('SQL validation passed successfully!', 'success');
      } else {
        setValidationStatus('invalid');
        showSnackbar(result.message || 'SQL validation failed', 'error');
      }
    } catch (error) {
      console.error('Error validating SQL:', error);
      setValidationStatus('invalid');
      showSnackbar('Network error during validation', 'error');
    } finally {
      setValidating(false);
    }
  };
  
  const saveSql = async () => {
    const codeToSave = isCreating ? newSqlCode.trim() : selectedSqlCode;
    
    if (!codeToSave) {
      showSnackbar('SQL code name is required.', 'error');
      return;
    }
    if (codeToSave.includes(' ')) {
        showSnackbar('Spaces are not allowed in SQL code name.', 'error');
        return;
    }

    setSaving(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/manage-sql/save-sql`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql_code: codeToSave, sql_content: sqlContent }),
      });
      const result = await response.json();
      
      if (result.success) {
        setOriginalSqlContent(sqlContent);
        showSnackbar(`SQL saved successfully for ${codeToSave}!`, 'success');
        if (isCreating) {
          setSqlCodes(prev => [...prev, codeToSave].sort());
          setSelectedSqlCode(codeToSave);
          setIsCreating(false);
        }
      } else {
        showSnackbar(result.message || 'Failed to save SQL.', 'error');
      }
    } catch (error) {
      showSnackbar('Network error while saving SQL.', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSelectCode = (event, newValue) => {
    setSelectedSqlCode(newValue);
    if (newValue) {
      fetchSqlLogic(newValue);
    } else {
      setSqlContent('');
      setOriginalSqlContent('');
      setValidationStatus(null);
    }
  };
  
  const handleContentChange = (value) => {
    setSqlContent(value || '');
    setValidationStatus(null); // Invalidate on change
  };

  const handleCreateNew = () => {
    setIsCreating(true);
    setSelectedSqlCode(null);
    setNewSqlCode('');
    setSqlContent('');
    setOriginalSqlContent('');
    setValidationStatus(null);
  };
  
  const handleCancelCreate = () => {
    setIsCreating(false);
    setNewSqlCode('');
  };

  const handleViewHistory = () => {
    if (selectedSqlCode) {
      fetchSqlHistory(selectedSqlCode);
    } else {
      showSnackbar('Please select an SQL code first', 'warning');
    }
  };

  const handleHistoryItemClick = (historyItem) => {
    setSelectedHistoryItem(historyItem);
    setHistoryPreviewDialog(true);
  };

  const handleCopyHistoryContent = () => {
    if (selectedHistoryItem) {
      navigator.clipboard.writeText(selectedHistoryItem.sql_content)
        .then(() => {
          showSnackbar('SQL content copied to clipboard', 'success');
        })
        .catch(err => {
          console.error('Failed to copy content: ', err);
          showSnackbar('Failed to copy content', 'error');
        });
    }
  };

  const handleUseHistoryVersion = () => {
    if (selectedHistoryItem) {
      setSqlContent(selectedHistoryItem.sql_content);
      setHistoryPreviewDialog(false);
      setHistoryDialog(false);
      setValidationStatus(null);
      showSnackbar('Historical SQL version loaded into editor', 'success');
    }
  };

  const isSaveEnabled = () => {
    const hasCode = isCreating ? newSqlCode.trim() !== '' : selectedSqlCode !== null;
    return hasCode && validationStatus === 'valid' && !saving;
  };

  // Add function to handle copying SQL content to clipboard
  const handleCopySqlContent = () => {
    if (sqlContent) {
      navigator.clipboard.writeText(sqlContent)
        .then(() => {
          showSnackbar('SQL content copied to clipboard', 'success');
        })
        .catch(err => {
          console.error('Failed to copy content: ', err);
          showSnackbar('Failed to copy content', 'error');
        });
    } else {
      showSnackbar('No SQL content to copy', 'warning');
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      backgroundColor: 'background.default', // Use theme background
      color: 'text.primary' // Use theme text color
    }}>
      <Container maxWidth={false} sx={{ py: 2, px: 3, mb: 4 }}>
        {/* Top Control Bar - Removed the box container */}
        <Grid container spacing={2} alignItems="center" sx={{ mb: 2 }}>
          {isCreating ? (
            <>
              <Grid item xs>
                <TextField
                  label="New SQL Code Name"
                  variant="outlined"
                  size="small"
                  fullWidth
                  value={newSqlCode}
                  onChange={(e) => setNewSqlCode(e.target.value.replace(/\s/g, ''))}
                  helperText="No spaces allowed"
                />
              </Grid>
              <Grid item>
                <Button onClick={handleCancelCreate} size="small">Cancel</Button>
              </Grid>
            </>
          ) : (
            <>
              <Grid item xs={6} md={4}>
                <Autocomplete
                  value={selectedSqlCode}
                  onChange={handleSelectCode}
                  options={sqlCodes}
                  loading={fetchingCodes}
                  size="small"
                  renderInput={(params) => <TextField {...params} label="Select SQL Code" />}
                />
              </Grid>
              <Grid item>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button 
                    onClick={handleViewHistory} 
                    disabled={!selectedSqlCode || fetchingHistory}
                    size="small"
                    variant="outlined"
                    startIcon={<History />}
                    sx={{ 
                      minWidth: '100px',
                      height: '36px'
                    }}
                  >
                    History
                  </Button>
                  <Button 
                    onClick={handleCreateNew} 
                    size="small"
                    variant="outlined"
                    startIcon={<Add />}
                    sx={{ 
                      minWidth: '100px',
                      height: '36px'
                    }}
                  >
                    New
                  </Button>
                  <Button 
                    onClick={fetchAllSqlCodes} 
                    disabled={fetchingCodes} 
                    size="small"
                    variant="outlined"
                    startIcon={<Refresh />}
                    sx={{ 
                      minWidth: '100px',
                      height: '36px'
                    }}
                  >
                    Refresh
                  </Button>
                </Box>
              </Grid>
            </>
          )}
        </Grid>

        {/* Editor Card */}
        <Card sx={{ borderRadius: 2, bgcolor: 'background.paper' }}>
          <CardContent sx={{ p: 0 }}>
            <Box sx={{ 
              p: 2, 
              borderBottom: '1px solid', 
              borderColor: 'divider',
              bgcolor: validationStatus === 'valid' ? 'rgba(76, 175, 80, 0.2)' : // Light green
                       validationStatus === 'invalid' ? 'rgba(244, 67, 54, 0.2)' : // Light red
                       'inherit',
              transition: 'background-color 0.3s ease',
              color: 'text.primary' // Keep text color consistent
            }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Code color={validationStatus === 'valid' ? "success" : 
                           validationStatus === 'invalid' ? "error" : "primary"} />
                    <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
                      {isCreating ? (newSqlCode || 'New SQL Code') : (selectedSqlCode || 'SQL Editor')}
                    </Typography>
                  </Stack>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button variant="contained" 
                      onClick={validateSql} 
                      disabled={!sqlContent || validating} 
                      size="small"
                      color={validationStatus === 'valid' ? 'success' : 
                             validationStatus === 'invalid' ? 'error' : 'primary'}
                    >
                      Validate
                    </Button>
                    <Button 
                      variant="outlined" 
                      onClick={handleCopySqlContent}
                      disabled={!sqlContent}
                      size="small"
                      startIcon={<ContentCopy />}
                    >
                      Copy
                    </Button>
                    <Button variant="contained" onClick={saveSql} disabled={!isSaveEnabled()} color="success" size="small">
                      {isCreating ? 'Create' : 'Save'}
                    </Button>
                  </Stack>
                </Grid>
              </Grid>
            </Box>
            <Box sx={{ height: '60vh' }}>
              <Editor
                height="100%"
                language="sql"
                value={sqlContent}
                onChange={handleContentChange}
                theme={isDarkMode ? 'vs-dark' : 'vs-light'} // This is the crucial fix
                options={{ minimap: { enabled: false }, automaticLayout: true }}
              />
            </Box>
          </CardContent>
        </Card>
      </Container>

      {/* SQL History Dialog */}
      <Dialog 
        open={historyDialog} 
        onClose={() => setHistoryDialog(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle sx={{ 
          bgcolor: theme.palette.primary.main, 
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          py: 1.5
        }}>
          <Typography variant="h6">SQL History for {selectedSqlCode}</Typography>
          <IconButton onClick={() => setHistoryDialog(false)} sx={{ color: 'white' }}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ maxHeight: '300px' }}>
          {fetchingHistory ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : sqlHistory.length > 0 ? (
            <List dense>
              {sqlHistory.map((item, index) => (
                <ListItem key={index} disablePadding divider>
                  <ListItemButton 
                    onClick={() => handleHistoryItemClick(item)}
                    sx={{
                      '&:hover': {
                        bgcolor: theme.palette.action.hover,
                      },
                      py: 1
                    }}
                  >
                    <ListItemText 
                      primary={
                        <Typography variant="subtitle2" fontWeight="medium">
                          {item.date}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="body2" color="text.secondary">
                          Click to view
                        </Typography>
                      }
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          ) : (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body1" color="text.secondary">
                No history records found for this SQL code.
              </Typography>
            </Box>
          )}
        </DialogContent>
      </Dialog>

      {/* History Preview Dialog */}
      <Dialog
        open={historyPreviewDialog}
        onClose={() => setHistoryPreviewDialog(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle sx={{ 
          bgcolor: theme.palette.primary.main, 
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          py: 1.5
        }}>
          <Typography variant="h6">
            SQL Version: {selectedHistoryItem ? selectedHistoryItem.date : ''}
          </Typography>
          <IconButton onClick={() => setHistoryPreviewDialog(false)} sx={{ color: 'white' }}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ height: '35vh' }}>
            <Editor
              height="100%"
              language="sql"
              value={selectedHistoryItem?.sql_content || ''}
              theme={isDarkMode ? 'vs-dark' : 'vs-light'}
              options={{ readOnly: true, minimap: { enabled: false }, automaticLayout: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 1.5, justifyContent: 'space-between' }}>
          <Button onClick={() => setHistoryPreviewDialog(false)} variant="outlined">
            Cancel
          </Button>
          <Box>
            <Button 
              onClick={handleCopyHistoryContent} 
              startIcon={<ContentCopy />}
              variant="outlined"
              sx={{ mr: 1 }}
            >
              Copy
            </Button>
            <Button 
              onClick={handleUseHistoryVersion} 
              variant="contained" 
              color="primary"
            >
              Use This Version
            </Button>
          </Box>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={1000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ManageSQLPage;
