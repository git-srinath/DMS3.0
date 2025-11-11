"use client";

import React, { useEffect } from 'react';
import Link from 'next/link';
import { 
  Container, 
  Box, 
  Typography, 
  Button, 
  Paper,
  useMediaQuery
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { 
  SentimentVeryDissatisfied, 
  Home as HomeIcon, 
  Search as SearchIcon,
  ArrowBack
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useTheme } from '@/context/ThemeContext';

const GradientText = styled(Typography)(({ theme, darkMode }) => ({
  background: darkMode 
    ? 'linear-gradient(90deg, #60A5FA 0%, #8B5CF6 50%, #EC4899 100%)' 
    : 'linear-gradient(90deg, #3B82F6 0%, #7C3AED 50%, #DB2777 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
  textFillColor: 'transparent',
  fontWeight: 800
}));

const StyledButton = styled(Button)(({ theme, darkMode }) => ({
  borderRadius: '12px',
  textTransform: 'none',
  padding: '10px 20px',
  fontWeight: 600,
  boxShadow: darkMode 
    ? '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.3)' 
    : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: darkMode 
      ? '0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.4)'
      : '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
    transition: 'all 0.3s ease-in-out'
  }
}));

// SVG Background Component
const BackgroundSVG = ({ darkMode }) => (
  <Box sx={{
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    zIndex: -1,
    opacity: 0.5
  }}>
    <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="smallGrid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" 
            stroke={darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)'} 
            strokeWidth="1"/>
        </pattern>
        <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
          <rect width="80" height="80" fill="url(#smallGrid)"/>
          <path d="M 80 0 L 0 0 0 80" fill="none" 
            stroke={darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'} 
            strokeWidth="1"/>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
    </svg>
  </Box>
);

export default function NotFound() {
  const { darkMode } = useTheme();
  const isMobile = useMediaQuery('(max-width:600px)');
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        when: "beforeChildren",
        staggerChildren: 0.2,
        duration: 0.5
      }
    }
  };
  
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: { 
        type: "spring", 
        stiffness: 100,
        damping: 15
      }
    }
  };
  
  const iconVariants = {
    hidden: { rotate: -180, opacity: 0 },
    visible: { 
      rotate: 0, 
      opacity: 1,
      transition: { 
        type: "spring", 
        stiffness: 200,
        damping: 20
      }
    },
    hover: {
      rotate: [0, -10, 10, -10, 10, 0],
      transition: { duration: 1.5, repeat: Infinity, repeatType: "loop" }
    }
  };
  
  const buttonVariants = {
    hover: { 
      scale: 1.05,
      transition: { 
        type: "spring", 
        stiffness: 400,
        damping: 10
      }
    },
    tap: { scale: 0.95 }
  };

  return (
    <Container maxWidth="lg" sx={{ 
      minHeight: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      justifyContent: 'center', 
      alignItems: 'center',
      position: 'relative',
      py: 4
    }}>
      <BackgroundSVG darkMode={darkMode} />
      
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{ width: '100%', display: 'flex', justifyContent: 'center' }}
      >
        <Paper elevation={darkMode ? 6 : 3} sx={{
          py: { xs: 4, md: 6 },
          px: { xs: 3, md: 8 },
          width: '100%',
          maxWidth: 800,
          textAlign: 'center',
          borderRadius: 4,
          position: 'relative',
          overflow: 'hidden',
          backgroundColor: darkMode ? 'rgba(17, 24, 39, 0.7)' : 'rgba(255, 255, 255, 0.7)',
          backdropFilter: 'blur(10px)',
          border: darkMode ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.05)'
        }}>
          <motion.div variants={iconVariants} whileHover="hover">
            <SentimentVeryDissatisfied 
              sx={{ 
                fontSize: { xs: 80, md: 120 }, 
                color: darkMode ? 'primary.light' : 'secondary.main',
                mb: 2
              }} 
            />
          </motion.div>
          
          <motion.div variants={itemVariants}>
            <Typography variant="h3" component="h1" sx={{ mb: 1, fontWeight: 700 }}>
              <Box component="span" sx={{ display: { xs: 'block', sm: 'inline' } }}>
                404
              </Box>
              {!isMobile && <Box component="span" sx={{ mx: 1 }}>|</Box>}
              <Box component="span" sx={{ display: { xs: 'block', sm: 'inline' } }}>
                Page Not Found
              </Box>
            </Typography>
          </motion.div>
          
          <motion.div variants={itemVariants}>
            <GradientText variant="h4" component="h2" darkMode={darkMode} gutterBottom sx={{ mb: 3 }}>
              Oops! We&apos;ve hit a dead end.
            </GradientText>
          </motion.div>
          
          <motion.div variants={itemVariants}>
            <Typography variant="body1" sx={{ mb: 4, maxWidth: 600, mx: 'auto', color: darkMode ? 'gray.300' : 'text.secondary' }}>
              The page you're looking for doesn't exist or has been moved.
              It might have been renamed, deleted, or the URL might be incorrect.
            </Typography>
          </motion.div>
          
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' }, 
            justifyContent: 'center',
            gap: 2,
            mt: 4
          }}>
            <motion.div variants={buttonVariants} whileHover="hover" whileTap="tap">
              <StyledButton 
                component={Link} 
                href="/"
                variant="contained" 
                color={darkMode ? 'primary' : 'secondary'} 
                startIcon={<HomeIcon />}
                darkMode={darkMode}
                fullWidth={isMobile}
                size="large"
              >
                Back to Home
              </StyledButton>
            </motion.div>
            
            <motion.div variants={buttonVariants} whileHover="hover" whileTap="tap">
              <StyledButton 
                component={Link} 
                href="javascript:history.back()"
                variant="outlined" 
                color={darkMode ? 'primary' : 'secondary'}
                startIcon={<ArrowBack />}
                darkMode={darkMode}
                fullWidth={isMobile}
                size="large"
              >
                Go Back
              </StyledButton>
            </motion.div>
          </Box>
          
          <Box sx={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            height: 6, 
            background: darkMode 
              ? 'linear-gradient(90deg, #60A5FA 0%, #8B5CF6 50%, #EC4899 100%)' 
              : 'linear-gradient(90deg, #3B82F6 0%, #7C3AED 50%, #DB2777 100%)'
          }}/>
        </Paper>
      </motion.div>
    </Container>
  );
} 