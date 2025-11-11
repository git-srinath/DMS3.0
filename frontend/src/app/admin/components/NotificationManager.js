import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Paper, 
  Divider, 
  useTheme, 
  alpha, 
  Alert,
  CircularProgress,
  Tab,
  Tabs
} from '@mui/material';
import { motion } from 'framer-motion';
import axios from 'axios';
import { API_BASE_URL } from '../../../app/config';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SendIcon from '@mui/icons-material/Send';
import MarkdownIcon from '@mui/icons-material/Code';
import PreviewIcon from '@mui/icons-material/Visibility';
import ReactMarkdown from 'react-markdown';

const NotificationManager = () => {
  const theme = useTheme();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccess(false);
    setError('');

    try {
      if (!title || !description) {
        throw new Error('Title and description are required');
      }

      await axios.post(
        `${API_BASE_URL}/admin/notifications`,
        { title, description },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      setSuccess(true);
      setTitle('');
      setDescription('');
      setTabValue(0);
    } catch (err) {
      console.error('Error creating notification:', err);
      setError(err.response?.data?.error || err.message || 'Failed to create notification');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Helper function to insert markdown syntax at cursor position
  const insertMarkdown = (syntax, placeholder) => {
    const textarea = document.getElementById('markdown-editor');
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = textarea.value;
    const selectedText = text.substring(start, end) || placeholder;
    
    const beforeText = text.substring(0, start);
    const afterText = text.substring(end);
    
    // Create the new text with markdown syntax
    const newText = beforeText + syntax.replace('$1', selectedText) + afterText;
    
    // Update the textarea value
    setDescription(newText);
    
    // Focus the textarea and set the selection
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + syntax.indexOf('$1') + selectedText.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  // Custom styles for markdown content in preview
  const markdownStyles = {
    h1: {
      fontSize: '1.5rem',
      fontWeight: 600,
      marginTop: '1rem',
      marginBottom: '0.5rem',
      color: theme.palette.mode === 'dark' ? theme.palette.primary.light : theme.palette.primary.main
    },
    h2: {
      fontSize: '1.25rem',
      fontWeight: 600,
      marginTop: '0.75rem',
      marginBottom: '0.5rem',
      color: theme.palette.mode === 'dark' ? theme.palette.primary.light : theme.palette.primary.main
    },
    h3: {
      fontSize: '1.1rem',
      fontWeight: 600,
      marginTop: '0.75rem',
      marginBottom: '0.5rem',
      color: theme.palette.mode === 'dark' ? alpha(theme.palette.primary.light, 0.9) : theme.palette.primary.dark
    },
    p: {
      marginBottom: '0.5rem',
      color: theme.palette.mode === 'dark' ? theme.palette.text.primary : theme.palette.text.secondary
    },
    ul: {
      marginLeft: '1.5rem',
      marginBottom: '0.5rem',
    },
    li: {
      marginBottom: '0.25rem',
      color: theme.palette.mode === 'dark' ? theme.palette.text.primary : theme.palette.text.secondary
    },
    a: {
      color: theme.palette.primary.main,
      textDecoration: 'underline'
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Notification Form */}
        <Paper
          elevation={0}
          sx={{
            p: 2,
            borderRadius: 2,
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            background: alpha(theme.palette.background.paper, 0.8),
            backdropFilter: 'blur(10px)',
            boxShadow: `0 8px 32px 0 ${alpha(theme.palette.common.black, 0.1)}`,
            overflow: 'hidden',
            mb: 3,
            width: '100%'
          }}
        >
          <form onSubmit={handleSubmit}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              Notification Details
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {success && (
              <Alert 
                severity="success" 
                sx={{ mb: 2, borderRadius: 2 }}
              >
                Notification created successfully! All users will see it on their next login.
              </Alert>
            )}

            {error && (
              <Alert 
                severity="error" 
                sx={{ mb: 2, borderRadius: 2 }}
              >
                {error}
              </Alert>
            )}

            <TextField
              label="Notification Title"
              variant="outlined"
              fullWidth
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="E.g., New Dashboard Features Released"
              required
              sx={{ mb: 2 }}
              size="small"
            />

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 1 }}>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange}
                aria-label="markdown editor tabs"
                sx={{
                  '& .MuiTab-root': {
                    textTransform: 'none',
                    minHeight: 40,
                    fontSize: '0.875rem'
                  }
                }}
              >
                <Tab 
                  icon={<MarkdownIcon fontSize="small" />} 
                  iconPosition="start" 
                  label="Write" 
                />
                <Tab 
                  icon={<PreviewIcon fontSize="small" />} 
                  iconPosition="start" 
                  label="Preview" 
                />
              </Tabs>
            </Box>

            {/* Markdown toolbar */}
            {tabValue === 0 && (
              <Box
                sx={{
                  display: 'flex',
                  gap: 0.5,
                  flexWrap: 'wrap',
                  mb: 1,
                  p: 0.5,
                  backgroundColor: alpha(theme.palette.background.default, 0.5),
                  borderRadius: 1
                }}
              >
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('# $1', 'Heading 1')}
                  sx={{ textTransform: 'none', minWidth: 'auto', py: 0.5, px: 1 }}
                >
                  H1
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('## $1', 'Heading 2')}
                  sx={{ textTransform: 'none', minWidth: 'auto', py: 0.5, px: 1 }}
                >
                  H2
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('### $1', 'Heading 3')}
                  sx={{ textTransform: 'none', minWidth: 'auto', py: 0.5, px: 1 }}
                >
                  H3
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('**$1**', 'bold text')}
                  sx={{ textTransform: 'none', fontWeight: 'bold', py: 0.5, px: 1 }}
                >
                  B
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('*$1*', 'italic text')}
                  sx={{ textTransform: 'none', fontStyle: 'italic', py: 0.5, px: 1 }}
                >
                  I
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('- $1', 'List item')}
                  sx={{ textTransform: 'none', py: 0.5, px: 1 }}
                >
                  • List
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('[$1](https://example.com)', 'link text')}
                  sx={{ textTransform: 'none', py: 0.5, px: 1 }}
                >
                  Link
                </Button>
                <Button 
                  size="small" 
                  variant="outlined"
                  onClick={() => insertMarkdown('```\n$1\n```', 'code block')}
                  sx={{ textTransform: 'none', fontFamily: 'monospace', py: 0.5, px: 1 }}
                >
                  Code
                </Button>
              </Box>
            )}

            <Box sx={{ display: tabValue === 0 ? 'block' : 'none' }}>
              <TextField
                id="markdown-editor"
                label="Notification Description (Supports Markdown)"
                variant="outlined"
                fullWidth
                multiline
                rows={8}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="## What's New\n\n- Added new dashboard widgets\n- Improved performance\n- Fixed bugs\n\n### How to Use\n\nClick on the **dashboard** to explore the new features."
                required
                sx={{ mb: 2, fontFamily: 'monospace' }}
                size="small"
              />
            </Box>

            {tabValue === 1 && (
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  mb: 2,
                  minHeight: '200px',
                  maxHeight: '350px',
                  overflow: 'auto',
                  borderRadius: 2,
                  border: `1px solid ${alpha(theme.palette.divider, 0.2)}`,
                  backgroundColor: alpha(theme.palette.background.default, 0.5),
                }}
              >
                {description ? (
                  <Box
                    sx={{
                      '& a': {
                        color: theme.palette.primary.main
                      },
                      '& ul': {
                        pl: 2,
                        m: 0
                      }
                    }}
                  >
                    <ReactMarkdown
                      components={{
                        h1: ({node, ...props}) => <Typography variant="h6" gutterBottom style={markdownStyles.h1} {...props} />,
                        h2: ({node, ...props}) => <Typography variant="subtitle1" gutterBottom style={markdownStyles.h2} {...props} />,
                        h3: ({node, ...props}) => <Typography variant="subtitle2" gutterBottom style={markdownStyles.h3} {...props} />,
                        p: ({node, ...props}) => <Typography variant="body2" paragraph style={{...markdownStyles.p, marginBottom: '0.3rem'}} {...props} />,
                        ul: ({node, ...props}) => <Box component="ul" sx={{...markdownStyles.ul, marginBottom: '0.3rem'}} {...props} />,
                        li: ({node, ...props}) => <Box component="li" sx={{...markdownStyles.li, marginBottom: '0.1rem'}} {...props} />,
                        a: ({node, ...props}) => <Box component="a" sx={markdownStyles.a} target="_blank" rel="noopener" {...props} />
                      }}
                    >
                      {description}
                    </ReactMarkdown>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    Preview will appear here
                  </Typography>
                )}
              </Paper>
            )}

            <Button
              type="submit"
              variant="contained"
              size="medium"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={16} /> : <SendIcon />}
              sx={{
                py: 1,
                px: 3,
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 600,
                background: `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.3)}`,
                '&:hover': {
                  boxShadow: `0 6px 16px ${alpha(theme.palette.primary.main, 0.4)}`,
                }
              }}
            >
              {loading ? 'Creating...' : 'Create Notification'}
            </Button>
          </form>
        </Paper>
      </motion.div>
    </Box>
  );
};

export default NotificationManager; 