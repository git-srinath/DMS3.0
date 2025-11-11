import React, { useEffect, useRef, useState } from 'react';
import { 
  Box, 
  Typography, 
  Divider, 
  Avatar, 
  useTheme, 
  Link, 
  Stack, 
  IconButton, 
  Grid, 
  Paper, 
  Tooltip, 
  Container 
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import LanguageIcon from '@mui/icons-material/Language';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import TwitterIcon from '@mui/icons-material/Twitter';
import GitHubIcon from '@mui/icons-material/GitHub';
import EmailIcon from '@mui/icons-material/Email';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import BusinessIcon from '@mui/icons-material/Business';
import VerifiedIcon from '@mui/icons-material/Verified';
import ConnectWithoutContactIcon from '@mui/icons-material/ConnectWithoutContact';

const AboutTabContent = () => {
  const theme = useTheme();
  
  // Define the developer name here - easy to modify
  const developerName = "Ahana Dev Team";
  // App version - for consistency
  const appVersion = "v2.0.0";
  
  // State for typing animation
  const [displayText, setDisplayText] = useState('');
  const [showCursor, setShowCursor] = useState(true);
  const [isTypingComplete, setIsTypingComplete] = useState(false);
  const [animationStarted, setAnimationStarted] = useState(false);
  const typingIndex = useRef(0);
  
  // Start animation after component mounts
  useEffect(() => {
    const startDelay = setTimeout(() => {
      setAnimationStarted(true);
    }, 500); // Delay before animation starts
    
    return () => clearTimeout(startDelay);
  }, []);
  
  // Typing animation effect - enhanced smooth implementation
  useEffect(() => {
    if (!animationStarted) return;
    
    if (typingIndex.current < developerName.length) {
      // Variable typing speed based on character for more natural look
      let typingSpeed = 70; // Base typing speed (faster)
      
      // Adjust speed for certain characters
      const char = developerName[typingIndex.current];
      if ([' ', '-', '_'].includes(char)) {
        typingSpeed = 100; // Slower for spaces and special characters
      } else if (['.', ',', '!', '?'].includes(char)) {
        typingSpeed = 180; // Even slower for punctuation
      }
      
      // Randomize speed slightly for more natural effect
      typingSpeed += Math.floor(Math.random() * 30) - 15;
      
      const timer = setTimeout(() => {
        setDisplayText(developerName.substring(0, typingIndex.current + 1));
        typingIndex.current += 1;
      }, typingSpeed);
      
      return () => clearTimeout(timer);
    } else if (!isTypingComplete) {
      // When typing is complete, set flag and keep cursor for a moment
      setIsTypingComplete(true);
      
      // Hide cursor after a short delay when typing completes
      const finalTimer = setTimeout(() => {
        setShowCursor(false);
      }, 800);
      
      return () => clearTimeout(finalTimer);
    }
  }, [developerName, typingIndex.current, isTypingComplete, animationStarted]);
  
  // Blinking cursor effect - only active during typing
  useEffect(() => {
    if (isTypingComplete || !animationStarted) return; // Don't blink before animation starts or after typing is done
    
    const cursorInterval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 450); // Faster blink rate
    
    return () => clearInterval(cursorInterval);
  }, [isTypingComplete, animationStarted]);
  
  // Reset animation when developer name changes
  useEffect(() => {
    setDisplayText('');
    typingIndex.current = 0;
    setIsTypingComplete(false);
    setShowCursor(true);
    setAnimationStarted(false);
    
    // Restart animation with a delay
    const restartDelay = setTimeout(() => {
      setAnimationStarted(true);
    }, 300);
    
    return () => clearTimeout(restartDelay);
  }, [developerName]);

  return (
    <Box sx={{
      width: '100%',
      bgcolor: theme.palette.background.default,
      py: 1,
    }}>
      {/* Hero Section */}
      <Paper
        elevation={0}
        sx={{
          borderRadius: 0,
          background: `linear-gradient(120deg, ${alpha(theme.palette.primary.main, 0.08)} 0%, ${alpha(theme.palette.primary.dark, 0.12)} 100%)`,
          py: 2,
          px: { xs: 2, sm: 3, md: 4 },
          mb: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 2,
        }}
      >
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar
            sx={{
              bgcolor: theme.palette.primary.main,
              width: { xs: 40, sm: 50 },
              height: { xs: 40, sm: 50 },
              boxShadow: theme.shadows[2],
              fontSize: '1.5rem',
            }}
          >
            A
          </Avatar>
          <Stack>
            <Typography 
              variant="h5"
              component="h1" 
              fontWeight="700" 
              color="primary.dark"
              sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
            >
              Ahana DW Tool
            </Typography>
            <Typography 
              variant="subtitle2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              Data Warehouse Management System
            </Typography>
          </Stack>
        </Stack>
        
        <Box sx={{ 
          bgcolor: alpha(theme.palette.success.main, 0.1),
          color: theme.palette.success.dark,
          borderRadius: 2,
          px: 1.5,
          py: 0.5,
          display: 'flex',
          alignItems: 'center',
        }}>
          <VerifiedIcon fontSize="small" sx={{ mr: 0.5 }} />
          <Typography variant="caption" fontWeight="medium">{appVersion} • Up to date</Typography>
        </Box>
      </Paper>

      {/* Main Content Grid */}
      <Grid container spacing={2} sx={{ px: { xs: 1, sm: 2 } }}>
        {/* Company Card */}
        <Grid item xs={12} md={6} lg={4}>
          <Paper 
            elevation={0} 
            sx={{ 
              borderRadius: 2,
              height: '100%',
              border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
              p: { xs: 1.5, sm: 2 },
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                boxShadow: theme.shadows[2],
                borderColor: theme.palette.primary.light,
              }
            }}
          >
            <Stack spacing={1.5} height="100%">
              <Stack direction="row" spacing={1} alignItems="center">
                <Box sx={{ 
                  p: 0.75,
                  borderRadius: '50%', 
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  <BusinessIcon color="primary" fontSize="small" />
                </Box>
                <Typography variant="subtitle1" fontWeight="600" color="primary.main">
                  About the Company
                </Typography>
              </Stack>
              
              <Box sx={{ py: 0.5 }}>
                <Typography variant="body2" fontWeight="medium" gutterBottom>
                  Ahana Systems & Solutions Pvt Ltd
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  "Creating Possibilities"
                </Typography>
              </Box>

              <Divider sx={{ my: 0.5 }} />
              
              <Stack spacing={1} sx={{ mt: 'auto' }}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <LanguageIcon fontSize="small" color="action" />
                  <Link
                    href="https://www.ahanait.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="caption"
                    underline="hover"
                  >
                    www.ahanait.com
                  </Link>
                </Stack>
                <Stack direction="row" spacing={1} alignItems="center">
                  <EmailIcon fontSize="small" color="action" />
                  <Link
                    href="mailto:info@ahanait.co.in"
                    variant="caption"
                    underline="hover"
                  >
                    info@ahanait.co.in
                  </Link>
                </Stack>
              </Stack>
            </Stack>
          </Paper>
        </Grid>

        {/* Application Info Card */}
        <Grid item xs={12} md={6} lg={4}>
          <Paper 
            elevation={0} 
            sx={{ 
              borderRadius: 2,
              height: '100%',
              border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
              p: { xs: 1.5, sm: 2 },
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                boxShadow: theme.shadows[2],
                borderColor: theme.palette.primary.light,
              }
            }}
          >
            <Stack spacing={1.5} height="100%">
              <Stack direction="row" spacing={1} alignItems="center">
                <Box sx={{ 
                  p: 0.75,
                  borderRadius: '50%', 
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  <InfoOutlinedIcon color="primary" fontSize="small" />
                </Box>
                <Typography variant="subtitle1" fontWeight="600" color="primary.main">
                  Application Info
                </Typography>
              </Stack>
              
              <Box sx={{ py: 0.5 }}>
                <Grid container spacing={1}>
                  <Grid item xs={4}>
                    <Typography variant="caption" color="text.secondary">Version</Typography>
                    <Typography variant="body2" fontWeight="500">{appVersion.replace('v', '')}</Typography>
                  </Grid>
                  <Grid item xs={8}>
                    <Typography variant="caption" color="text.secondary">Status</Typography>
                    <Typography variant="body2" fontWeight="500" color="success.main" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <VerifiedIcon fontSize="small" /> Up to date
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">Last Checked</Typography>
                    <Typography variant="body2">{new Date().toLocaleDateString()}</Typography>
                  </Grid>
                </Grid>
              </Box>

              <Box sx={{ mt: 'auto', pt: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  © {new Date().getFullYear()} Ahana Systems & Solutions Pvt Ltd
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Grid>

        {/* Connect With Us Card */}
        <Grid item xs={12} md={12} lg={4}>
          <Paper 
            elevation={0} 
            sx={{ 
              borderRadius: 2,
              height: '100%',
              border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
              p: { xs: 1.5, sm: 2 },
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                boxShadow: theme.shadows[2],
                borderColor: theme.palette.primary.light,
              }
            }}
          >
            <Stack spacing={1.5} height="100%">
              <Stack direction="row" spacing={1} alignItems="center">
                <Box sx={{ 
                  p: 0.75,
                  borderRadius: '50%', 
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center'
                }}>
                  <ConnectWithoutContactIcon color="primary" fontSize="small" />
                </Box>
                <Typography variant="subtitle1" fontWeight="600" color="primary.main">
                  Connect With Us
                </Typography>
              </Stack>
              
              <Typography variant="caption" color="text.secondary">
                Follow us on our social channels for updates and news.
              </Typography>

              <Box sx={{ 
                display: 'flex', 
                gap: 1,
                flexWrap: 'wrap', 
                justifyContent: 'center',
                mt: 1
              }}>
                <Tooltip title="Website">
                  <IconButton
                    component={Link}
                    href="https://www.ahanait.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Visit Ahana Website"
                    size="small"
                    sx={{
                      color: theme.palette.primary.main,
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      '&:hover': { 
                        bgcolor: alpha(theme.palette.primary.main, 0.2),
                        transform: 'translateY(-2px)'
                      },
                      transition: 'all 0.2s',
                    }}
                  >
                    <LanguageIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Email">
                  <IconButton
                    component={Link}
                    href="mailto:info@ahanait.co.in"
                    aria-label="Send Email to Ahana"
                    size="small"
                    sx={{
                      color: '#EA4335',
                      bgcolor: alpha('#EA4335', 0.1),
                      '&:hover': { 
                        bgcolor: alpha('#EA4335', 0.2),
                        transform: 'translateY(-2px)'
                      },
                      transition: 'all 0.2s',
                    }}
                  >
                    <EmailIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="LinkedIn">
                  <IconButton
                    component={Link}
                    href="https://www.linkedin.com/company/ahana-systems-solutions/"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Ahana on LinkedIn"
                    size="small"
                    sx={{
                      color: '#0077B5',
                      bgcolor: alpha('#0077B5', 0.1),
                      '&:hover': { 
                        bgcolor: alpha('#0077B5', 0.2),
                        transform: 'translateY(-2px)'
                      },
                      transition: 'all 0.2s',
                    }}
                  >
                    <LinkedInIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Twitter">
                  <IconButton
                    component={Link}
                    href="https://twitter.com/ahana_it"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Ahana on Twitter"
                    size="small"
                    sx={{
                      color: '#1DA1F2',
                      bgcolor: alpha('#1DA1F2', 0.1),
                      '&:hover': { 
                        bgcolor: alpha('#1DA1F2', 0.2),
                        transform: 'translateY(-2px)'
                      },
                      transition: 'all 0.2s',
                    }}
                  >
                    <TwitterIcon fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="GitHub">
                  <IconButton
                    component={Link}
                    href="https://github.com/ahana-systems"
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label="Ahana on GitHub"
                    size="small"
                    sx={{
                      color: theme.palette.mode === 'dark' ? '#fff' : '#24292e',
                      bgcolor: alpha(theme.palette.mode === 'dark' ? '#fff' : '#24292e', 0.1),
                      '&:hover': { 
                        bgcolor: alpha(theme.palette.mode === 'dark' ? '#fff' : '#24292e', 0.2),
                        transform: 'translateY(-2px)'
                      },
                      transition: 'all 0.2s',
                    }}
                  >
                    <GitHubIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              
              <Typography variant="caption" color="text.secondary" align="center" sx={{ mt: 'auto', pt: 1 }}>
                All rights reserved • Ahana DW Tool {appVersion}
              </Typography>
            </Stack>
          </Paper>
        </Grid>
      </Grid>

      {/* Developer Signature - Typing Animation */}
      <Box
        sx={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          mt: 3,
          mb: 2,
          position: 'relative',
        }}
      >
        <Box
          sx={{
            position: 'relative',
            textAlign: 'center',
            minHeight: '60px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: animationStarted ? 1 : 0,
            transform: animationStarted ? 'translateY(0)' : 'translateY(10px)',
            transition: 'all 0.5s ease',
          }}
        >
          {/* Typewriter Effect Container */}
          <Box
            sx={{
              display: 'flex',
              position: 'relative',
              justifyContent: 'center',
              minHeight: '40px',
              p: 1,
              borderRadius: 1,
              background: alpha(theme.palette.primary.main, 0.05),
              boxShadow: isTypingComplete ? `0 2px 8px ${alpha(theme.palette.primary.main, 0.2)}` : 'none',
              transition: 'all 0.5s ease',
              overflow: 'hidden',
              '&::before': isTypingComplete ? {
                content: '""',
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: `linear-gradient(90deg, 
                  ${alpha(theme.palette.primary.main, 0)} 0%, 
                  ${alpha(theme.palette.primary.main, 0.1)} 50%, 
                  ${alpha(theme.palette.primary.main, 0)} 100%)`,
                backgroundSize: '200% 100%',
                animation: 'shimmer 2s infinite',
                '@keyframes shimmer': {
                  '0%': { backgroundPosition: '200% 0' },
                  '100%': { backgroundPosition: '-200% 0' },
                },
              } : {},
            }}
          >
            {/* The typing text */}
            <Typography
              sx={{
                fontFamily: "'Dancing Script', cursive",
                fontSize: { xs: '1.6rem', sm: '2rem' },
                color: theme.palette.mode === 'dark' 
                  ? theme.palette.primary.light 
                  : theme.palette.primary.main,
                textShadow: `1px 1px 2px ${alpha(theme.palette.common.black, 0.2)}`,
                position: 'relative',
                whiteSpace: 'nowrap',
                paddingRight: showCursor ? '4px' : '0',
                zIndex: 1,
              }}
            >
              {displayText}
              {/* Blinking cursor - only shown during typing */}
              {showCursor && (
                <Box
                  component="span"
                  sx={{
                    display: 'inline-block',
                    width: '2px',
                    height: '1.4em',
                    backgroundColor: theme.palette.mode === 'dark' 
                      ? theme.palette.primary.light 
                      : theme.palette.primary.main,
                    position: 'absolute',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    right: '-4px',
                    animation: 'blink 0.7s step-end infinite',
                    '@keyframes blink': {
                      '0%, 100%': { opacity: 1 },
                      '50%': { opacity: 0 },
                    },
                  }}
                />
              )}
            </Typography>
          </Box>

          {/* Animated underline that appears when typing is complete */}
          {isTypingComplete && (
            <Box
              sx={{
                height: '2px',
                background: theme.palette.mode === 'dark' 
                  ? `linear-gradient(90deg, transparent, ${theme.palette.primary.light}, transparent)`
                  : `linear-gradient(90deg, transparent, ${theme.palette.primary.main}, transparent)`,
                width: '0%',
                animation: 'expandWidth 0.8s ease-out forwards',
                mt: 0.5,
                boxShadow: `0 0 4px ${alpha(theme.palette.primary.main, 0.5)}`,
                '@keyframes expandWidth': {
                  '0%': { width: '0%' },
                  '100%': { width: '100%' },
                },
              }}
            />
          )}

          {/* "developed with ❤️" text */}
          <Typography
            variant="caption"
            sx={{
              mt: 2,
              color: 'text.secondary',
              opacity: isTypingComplete ? 0.8 : 0,
              transform: isTypingComplete ? 'translateY(0)' : 'translateY(10px)',
              transition: 'all 0.5s ease',
              fontStyle: 'italic',
              fontSize: '0.7rem',
            }}
          >
            Developed with ❤️
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default AboutTabContent;