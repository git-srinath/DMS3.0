import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Typography, 
  Box, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  CircularProgress,
  Tooltip,
  useMediaQuery,
  Chip,
  Fade,
  Alert,
  Divider
} from '@mui/material';
import { styled, useTheme as useMuiTheme } from '@mui/material/styles';
import { 
  VisibilityOutlined, 
  Close, 
  KeyOutlined,
  DescriptionOutlined,
  ErrorOutline,
  CheckCircleOutline as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
  ArrowDownward as ArrowDownwardIcon,
  ArrowUpward as ArrowUpwardIcon,
  AccountTree as TreeIcon
} from '@mui/icons-material';
import { useTheme } from '@/context/ThemeContext';

// Styled components for better UI
const StyledTableContainer = styled(TableContainer)(({ theme, darkMode }) => ({
  borderRadius: '12px',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  boxShadow: darkMode ? '0 4px 20px rgba(0, 0, 0, 0.2)' : '0 4px 20px rgba(0, 0, 0, 0.08)',
  backgroundColor: darkMode ? 'rgba(26, 32, 44, 0.5)' : 'rgba(255, 255, 255, 0.8)',
  backdropFilter: 'blur(8px)',
  transition: 'all 0.3s ease',
  maxHeight: 'calc(100% - 64px)',
  '& .MuiTableCell-head': {
    backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.8)' : 'rgba(249, 250, 251, 0.8)',
    color: darkMode ? '#E2E8F0' : '#2D3748',
    fontWeight: 600,
    fontSize: '0.875rem',
    padding: '14px 16px',
    whiteSpace: 'nowrap',
    borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
    position: 'sticky',
    top: 0,
    zIndex: 1,
  },
  '& .MuiTableCell-body': {
    color: darkMode ? '#E2E8F0' : '#2D3748',
    padding: '10px 16px',
    fontSize: '0.875rem',
    borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  },
  '& .MuiTableRow-root:hover': {
    backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.01)',
    transition: 'background-color 0.2s ease',
  },
}));

const StatusChip = styled(Chip)(({ theme, darkMode, status }) => ({
  height: '24px',
  fontWeight: 600,
  fontSize: '0.75rem',
  borderRadius: '6px',
  backgroundColor: 
    status === 'Scheduled' ? (darkMode ? 'rgba(34, 197, 94, 0.2)' : 'rgba(34, 197, 94, 0.1)') :
    (darkMode ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)'),
  color: 
    status === 'Scheduled' ? (darkMode ? '#4ADE80' : '#22C55E') :
    (darkMode ? '#FBBF24' : '#D97706'),
  border: '1px solid',
  borderColor: 
    status === 'Scheduled' ? (darkMode ? 'rgba(34, 197, 94, 0.3)' : 'rgba(34, 197, 94, 0.2)') :
    (darkMode ? 'rgba(245, 158, 11, 0.3)' : 'rgba(245, 158, 11, 0.2)'),
  '& .MuiChip-label': {
    padding: '0 8px',
  }
}));

const RelationChip = styled(Chip)(({ theme, darkMode, type }) => ({
  height: '24px',
  fontWeight: 600,
  fontSize: '0.75rem',
  borderRadius: '6px',
  backgroundColor: type === 'parent' 
    ? (darkMode ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)') 
    : (darkMode ? 'rgba(14, 165, 233, 0.2)' : 'rgba(14, 165, 233, 0.1)'),
  color: type === 'parent'
    ? (darkMode ? '#818CF8' : '#6366F1')
    : (darkMode ? '#38BDF8' : '#0EA5E9'),
  border: '1px solid',
  borderColor: type === 'parent'
    ? (darkMode ? 'rgba(99, 102, 241, 0.3)' : 'rgba(99, 102, 241, 0.2)')
    : (darkMode ? 'rgba(14, 165, 233, 0.3)' : 'rgba(14, 165, 233, 0.2)'),
  '& .MuiChip-label': {
    padding: '0 8px',
  }
}));

const InfoSection = styled(Box)(({ theme, darkMode }) => ({
  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.4)' : 'rgba(249, 250, 251, 0.6)',
  borderRadius: '10px',
  padding: '16px',
  margin: '0 0 20px 0',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  backdropFilter: 'blur(8px)',
  transition: 'all 0.3s ease',
  '&:hover': {
    backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.5)' : 'rgba(249, 250, 251, 0.8)',
    boxShadow: darkMode ? '0 4px 12px rgba(0, 0, 0, 0.15)' : '0 4px 12px rgba(0, 0, 0, 0.05)',
  }
}));

const StyledPaper = styled(Paper)(({ theme, darkMode }) => ({
  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.6)' : 'rgba(255, 255, 255, 0.8)',
  borderRadius: '12px',
  padding: '16px',
  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
  backdropFilter: 'blur(8px)',
  boxShadow: darkMode ? '0 4px 12px rgba(0, 0, 0, 0.2)' : '0 4px 12px rgba(0, 0, 0, 0.08)',
  margin: '0 0 16px 0',
  transition: 'all 0.3s ease',
}));

const StyledButton = styled(Button)(({ theme, darkMode }) => ({
  textTransform: 'none',
  fontWeight: 600,
  borderRadius: '8px',
  padding: '8px 16px',
  transition: 'all 0.2s ease',
  boxShadow: 'none',
  '&:hover': {
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
    transform: 'translateY(-1px)',
  },
  '&:active': {
    transform: 'translateY(0)',
  }
}));

const StyledDialogTitle = styled(DialogTitle)(({ theme, darkMode }) => ({
  display: 'flex', 
  justifyContent: 'space-between', 
  alignItems: 'center', 
  borderBottom: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
  padding: '16px 24px',
  backgroundColor: darkMode ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
  backdropFilter: 'blur(12px)',
}));

const JobDetailsDialog = ({ open, onClose, job, allJobs = [] }) => {
  const [jobDetails, setJobDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState(null);
  
  const { darkMode } = useTheme();
  const muiTheme = useMuiTheme();
  const fullScreen = useMediaQuery(muiTheme.breakpoints.down('md'));

  // Find parent and child jobs based on dependencies
  const parentJob = allJobs.find(j => job?.DPND_JOBSCHID === j.JOBSCHID);
  const childJobs = allJobs.filter(j => j.DPND_JOBSCHID === job?.JOBSCHID && j.JOB_SCHEDULE_STATUS === 'Scheduled');

  // Function to fetch job details
  const fetchJobDetails = async (mapref) => {
    setLoadingDetails(true);
    try {
      const response = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/job/get_job_details/${mapref}`);
      
      if (response.data && response.data.job_details) {
        const details = response.data.job_details;
        // Format job details to object format for each row in the array
        if (Array.isArray(details) && details.length > 0) {
          const formattedDetails = details.map(detail => ({
            TRGCLNM: detail[0],
            TRGCLDTYP: detail[1],
            TRGKEYFLG: detail[2],
            TRGKEYSEQ: detail[3],
            TRGCLDESC: detail[4],
            MAPLOGIC: detail[5],
            KEYCLNM: detail[6],
            VALCLNM: detail[7],
            SCDTYP: detail[8]
          }));
          setJobDetails(formattedDetails);
        } else {
          setJobDetails([]);
        }
      } else {
        setJobDetails([]);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching job details:', err);
      setError('Failed to fetch job details. Please try again later.');
    } finally {
      setLoadingDetails(false);
    }
  };

  // Fetch job details when the dialog opens with a job
  useEffect(() => {
    if (open && job) {
      fetchJobDetails(job.MAPREF);
    } else {
      // Reset state when dialog closes
      setJobDetails(null);
      setLoadingDetails(false);
    }
  }, [open, job]);

  return (
    <Dialog
      open={open}
      onClose={(event, reason) => {
        // Only close when the close button is clicked, not on backdrop click or escape key
        if (reason !== 'backdropClick' && reason !== 'escapeKeyDown') {
          onClose();
        }
      }}
      fullScreen={fullScreen}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          backgroundColor: darkMode ? '#1A202C' : '#FFFFFF',
          color: darkMode ? 'white' : 'inherit',
          height: '95vh',
          maxHeight: '95vh',
          borderRadius: { xs: 0, sm: 2 },
          m: { xs: 0, sm: 2 },
          overflow: 'hidden',
          backgroundImage: darkMode ? 
            'linear-gradient(to bottom right, rgba(17, 24, 39, 0.8), rgba(30, 41, 59, 0.8))' : 
            'linear-gradient(to bottom right, rgba(249, 250, 251, 0.8), rgba(255, 255, 255, 0.8))',
          backdropFilter: 'blur(12px)',
          border: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
          boxShadow: darkMode ? 
            '0 25px 50px -12px rgba(0, 0, 0, 0.7)' : 
            '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }
      }}
    >
      <StyledDialogTitle darkMode={darkMode}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <VisibilityOutlined 
            sx={{ 
              mr: 1.5, 
              color: darkMode ? 'primary.main' : 'secondary.main',
              fontSize: 28
            }} 
          />
          <Typography variant="h5" fontWeight="600" sx={{ textShadow: darkMode ? '0 2px 4px rgba(0,0,0,0.5)' : 'none' }}>
            Job Details: <Box component="span" sx={{ 
              color: darkMode ? 'primary.light' : 'secondary.main',
              backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.1)' : 'rgba(124, 58, 237, 0.1)',
              px: 1.5,
              py: 0.5,
              borderRadius: 1,
              ml: 1
            }}>{job?.MAPREF}</Box>
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <StatusChip 
            label={
              job?.JOB_SCHEDULE_STATUS === 'Scheduled' ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircleIcon sx={{ fontSize: 14, mr: 0.5 }} />
                  Scheduled
                </Box>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <AccessTimeIcon sx={{ fontSize: 14, mr: 0.5 }} />
                  Not Scheduled
                </Box>
              )
            }
            darkMode={darkMode}
            status={job?.JOB_SCHEDULE_STATUS}
          />
          
          <IconButton 
            onClick={onClose}
            sx={{ 
              color: darkMode ? 'gray.400' : 'gray.600',
              '&:hover': {
                backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
                color: darkMode ? 'white' : 'black',
              },
              transition: 'all 0.2s ease',
            }}
          >
            <Close />
          </IconButton>
        </Box>
      </StyledDialogTitle>
      
      <DialogContent 
        sx={{ 
          p: 3, 
          height: 'calc(100% - 64px - 64px)',
          overflow: 'auto',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: darkMode ? 'rgba(15, 23, 42, 0.3)' : 'rgba(243, 244, 246, 0.5)',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.5)' : 'rgba(59, 130, 246, 0.3)',
            borderRadius: '4px',
            '&:hover': {
              backgroundColor: darkMode ? 'rgba(59, 130, 246, 0.7)' : 'rgba(59, 130, 246, 0.5)',
            }
          }
        }}
      >
        {error && (
          <Alert 
            severity="error" 
            sx={{ 
              mb: 3,
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
            }}
          >
            {error}
          </Alert>
        )}
        
        {/* Job information section */}
        <InfoSection darkMode={darkMode}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <DescriptionOutlined sx={{ mr: 1, color: darkMode ? 'primary.light' : 'secondary.main' }} />
            Job Information
          </Typography>
          
          <Box sx={{ display: 'grid', gap: 3, gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr' } }}>
            <Box>
              <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5 }}>Target Schema</Typography>
              <Typography variant="body1" fontWeight={500}>{job?.TRGSCHM || 'N/A'}</Typography>
            </Box>
            
            <Box>
              <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5 }}>Target Table</Typography>
              <Typography variant="body1" fontWeight={500}>{job?.TRGTBNM || 'N/A'}</Typography>
            </Box>
            
            <Box>
              <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5 }}>Table Type</Typography>
              <Typography variant="body1" fontWeight={500}>{job?.TRGTBTYP || 'N/A'}</Typography>
            </Box>
            
            <Box>
              <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5 }}>Source Schema</Typography>
              <Typography variant="body1" fontWeight={500}>{job?.SRCSCHM || 'N/A'}</Typography>
            </Box>
            
            <Box>
              <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5 }}>Source Table</Typography>
              <Typography variant="body1" fontWeight={500}>{job?.SRCTBNM || 'N/A'}</Typography>
            </Box>
            
            <Box>
              <Typography color="text.secondary" variant="body2" sx={{ mb: 0.5 }}>Job ID</Typography>
              <Typography variant="body1" fontWeight={500}>{job?.JOBID || 'N/A'}</Typography>
            </Box>
          </Box>
        </InfoSection>
        
        {/* Job dependency section */}
        {(parentJob || childJobs.length > 0) && (
          <InfoSection darkMode={darkMode}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center' }}>
              <TreeIcon sx={{ mr: 1, color: darkMode ? 'primary.light' : 'secondary.main' }} />
              Job Dependencies
            </Typography>
            
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {parentJob && (
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  gap: 2,
                  p: 2,
                  borderRadius: '8px',
                  backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.3)' : 'rgba(249, 250, 251, 0.5)',
                  border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
                }}>
                  <ArrowUpwardIcon sx={{ color: darkMode ? 'primary.light' : 'primary.main' }} />
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                      <RelationChip 
                        label="Parent Job" 
                        size="small" 
                        darkMode={darkMode} 
                        type="parent"
                      />
                    </Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {parentJob.MAPREF} - {parentJob.TRGSCHM}.{parentJob.TRGTBNM} ({parentJob.TRGTBTYP})
                    </Typography>
                  </Box>
                </Box>
              )}
              
              {childJobs.length > 0 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Child Jobs ({childJobs.length}):
                  </Typography>
                  
                  {childJobs.map((childJob) => (
                    <Box key={childJob.JOBID} sx={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      gap: 2,
                      p: 2,
                      borderRadius: '8px',
                      backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.3)' : 'rgba(249, 250, 251, 0.5)',
                      border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
                    }}>
                      <ArrowDownwardIcon sx={{ color: darkMode ? 'info.light' : 'info.main' }} />
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                          <RelationChip 
                            label="Child Job" 
                            size="small" 
                            darkMode={darkMode} 
                            type="child"
                          />
                        </Box>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {childJob.MAPREF} - {childJob.TRGSCHM}.{childJob.TRGTBNM} ({childJob.TRGTBTYP})
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </InfoSection>
        )}
        
        {/* Job Column Details Table */}
        <StyledPaper elevation={0} darkMode={darkMode}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600, display: 'flex', alignItems: 'center' }}>
            <KeyOutlined sx={{ mr: 1, color: darkMode ? 'primary.light' : 'secondary.main' }} />
            Column Details
          </Typography>
          
          {loadingDetails ? (
            <Box display="flex" justifyContent="center" alignItems="center" py={4}>
              <CircularProgress size={40} thickness={4} />
            </Box>
          ) : jobDetails && jobDetails.length > 0 ? (
            <StyledTableContainer darkMode={darkMode}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Column Name</TableCell>
                    <TableCell>Data Type</TableCell>
                    <TableCell align="center">Primary Key</TableCell>
                    <TableCell align="center">Key Sequence</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>SCD Type</TableCell>
                    <TableCell>Key Column</TableCell>
                    <TableCell>Value Column</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {jobDetails.map((detail, index) => (
                    <TableRow key={index} hover>
                      <TableCell sx={{ fontWeight: detail.TRGKEYFLG === 'Y' ? 600 : 400 }}>
                        {detail.TRGCLNM}
                      </TableCell>
                      <TableCell>{detail.TRGCLDTYP}</TableCell>
                      <TableCell align="center">
                        {detail.TRGKEYFLG === 'Y' ? (
                          <Chip 
                            label="Primary Key" 
                            size="small"
                            sx={{ 
                              height: '20px',
                              fontSize: '0.7rem',
                              backgroundColor: darkMode ? 'rgba(239, 68, 68, 0.2)' : 'rgba(239, 68, 68, 0.1)',
                              color: darkMode ? '#F87171' : '#EF4444',
                              fontWeight: 600
                            }}
                          />
                        ) : '—'}
                      </TableCell>
                      <TableCell align="center">{detail.TRGKEYSEQ || '—'}</TableCell>
                      <TableCell>{detail.TRGCLDESC || '—'}</TableCell>
                      <TableCell>{detail.SCDTYP || '—'}</TableCell>
                      <TableCell>{detail.KEYCLNM || '—'}</TableCell>
                      <TableCell>{detail.VALCLNM || '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </StyledTableContainer>
          ) : (
            <Box sx={{ 
              p: 3, 
              textAlign: 'center',
              backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.3)' : 'rgba(249, 250, 251, 0.5)',
              borderRadius: '8px',
              border: darkMode ? '1px solid rgba(255, 255, 255, 0.05)' : '1px solid rgba(0, 0, 0, 0.05)',
            }}>
              <ErrorOutline sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              <Typography>No column details available for this job</Typography>
            </Box>
          )}
        </StyledPaper>
      </DialogContent>
      
      <DialogActions sx={{ 
        p: 2, 
        borderTop: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)',
        backgroundColor: darkMode ? 'rgba(15, 23, 42, 0.6)' : 'rgba(249, 250, 251, 0.6)',
        backdropFilter: 'blur(8px)',
      }}>
        <StyledButton 
          onClick={onClose} 
          variant="contained" 
          color="primary"
          darkMode={darkMode}
        >
          Close
        </StyledButton>
      </DialogActions>
    </Dialog>
  );
};

export default JobDetailsDialog; 