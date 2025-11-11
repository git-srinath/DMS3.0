'use client';

import { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  TextField, 
  Button, 
  InputAdornment, 
  IconButton, 
  Alert,
  CircularProgress,
  useTheme,
  Paper,
  Avatar,
  Grid,
  Divider,
  Chip
} from '@mui/material';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LockResetIcon from '@mui/icons-material/LockReset';
import PasswordIcon from '@mui/icons-material/Password';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import SecurityIcon from '@mui/icons-material/Security';
import ShieldIcon from '@mui/icons-material/Shield';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import WavingHandIcon from '@mui/icons-material/WavingHand';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';

// Floating particles animation component
const FloatingParticles = () => {
  const [particles, setParticles] = useState([]);
  
  useEffect(() => {
    const particleCount = 12;
    const newParticles = [];
    
    for (let i = 0; i < particleCount; i++) {
      newParticles.push({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 3 + 2,
        delay: Math.random() * 5,
        duration: Math.random() * 8 + 12,
        opacity: Math.random() * 0.2 + 0.1,
      });
    }
    
    setParticles(newParticles);
  }, []);
  
  return (
    <Box 
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        overflow: 'hidden',
      }}
    >
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          initial={{ 
            x: `${particle.x}%`,
            y: `${particle.y}%`,
            opacity: 0,
          }}
          animate={{ 
            x: [`${particle.x}%`, `${particle.x + 15}%`, `${particle.x}%`],
            y: [`${particle.y}%`, `${particle.y - 20}%`, `${particle.y}%`],
            opacity: [0, particle.opacity, 0],
          }}
          transition={{ 
            duration: particle.duration,
            delay: particle.delay,
            ease: "easeInOut",
            repeat: Infinity,
          }}
          style={{
            position: 'absolute',
            width: particle.size,
            height: particle.size,
            borderRadius: '50%',
            background: 'linear-gradient(45deg, #667eea, #764ba2)',
            filter: 'blur(1px)',
          }}
        />
      ))}
    </Box>
  );
};

// Welcome section component
const WelcomeSection = ({ user }) => {
  const firstName = user?.first_name || user?.username?.split(' ')[0] || 'User';
  
  return (
    <Box
      sx={{
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden',
        color: 'white',
        px: { xs: 2, sm: 3, md: 4 },
      }}
    >
      <FloatingParticles />
      
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        style={{ textAlign: 'center', zIndex: 1 }}
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', damping: 10, stiffness: 100, delay: 0.2 }}
        >
          <Avatar
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.2)',
              width: { xs: 80, md: 100, lg: 120 },
              height: { xs: 80, md: 100, lg: 120 },
              mb: { xs: 2, md: 3, lg: 4 },
              mx: 'auto',
              backdropFilter: 'blur(10px)',
              border: '3px solid rgba(255, 255, 255, 0.3)',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)',
            }}
          >
            <WavingHandIcon sx={{ fontSize: { xs: 40, md: 50, lg: 60 } }} />
          </Avatar>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <Typography 
            variant="h2" 
            sx={{ 
              fontWeight: 800,
              mb: 2,
              fontSize: { xs: '1.8rem', sm: '2.2rem', md: '2.8rem', lg: '3.2rem' },
              background: 'linear-gradient(45deg, #ffffff, #f0f0f0)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-1px',
            }}
          >
            Welcome Back,
          </Typography>
          
          <Typography 
            variant="h3" 
            sx={{ 
              fontWeight: 600,
              mb: 3,
              fontSize: { xs: '1.5rem', sm: '1.8rem', md: '2.2rem', lg: '2.5rem' },
              color: '#FFD700',
              textShadow: '0 2px 10px rgba(255, 215, 0, 0.3)',
            }}
          >
            {firstName}!
          </Typography>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
        >
          <Typography 
            variant="h6" 
            sx={{ 
              mb: 4,
              opacity: 0.9,
              maxWidth: { xs: 300, md: 400 },
              mx: 'auto',
              lineHeight: 1.6,
              fontSize: { xs: '1rem', md: '1.1rem', lg: '1.2rem' },
            }}
          >
            Let's secure your account with a strong new password
          </Typography>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8, duration: 0.5 }}
        >
          <Box sx={{ display: 'flex', gap: { xs: 1, md: 2 }, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Chip
              icon={<SecurityIcon />}
              label="Secure"
              size="small"
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                '& .MuiChip-icon': { color: '#FFD700' }
              }}
            />
            <Chip
              icon={<ShieldIcon />}
              label="Protected"
              size="small"
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                '& .MuiChip-icon': { color: '#FFD700' }
              }}
            />
            <Chip
              icon={<VerifiedUserIcon />}
              label="Verified"
              size="small"
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                '& .MuiChip-icon': { color: '#FFD700' }
              }}
            />
          </Box>
        </motion.div>
      </motion.div>
      
      {/* Decorative elements - hidden on small screens */}
      <Box sx={{ display: { xs: 'none', lg: 'block' } }}>
        <motion.div
          animate={{ 
            rotate: 360,
          }}
          transition={{ 
            duration: 20,
            repeat: Infinity,
            ease: "linear"
          }}
          style={{
            position: 'absolute',
            top: '10%',
            right: '10%',
            width: 80,
            height: 80,
            opacity: 0.1,
          }}
        >
          <AutoAwesomeIcon sx={{ fontSize: 80 }} />
        </motion.div>
        
        <motion.div
          animate={{ 
            rotate: -360,
          }}
          transition={{ 
            duration: 25,
            repeat: Infinity,
            ease: "linear"
          }}
          style={{
            position: 'absolute',
            bottom: '15%',
            left: '5%',
            width: 60,
            height: 60,
            opacity: 0.1,
          }}
        >
          <SecurityIcon sx={{ fontSize: 60 }} />
        </motion.div>
      </Box>
    </Box>
  );
};

const ChangePasswordPage = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const { user, changePasswordAfterLogin } = useAuth();
  const router = useRouter();

  // Password validation criteria
  const criteria = [
    { id: 'length', label: 'At least 8 characters', valid: newPassword.length >= 8 },
    { id: 'uppercase', label: 'One uppercase letter', valid: /[A-Z]/.test(newPassword) },
    { id: 'lowercase', label: 'One lowercase letter', valid: /[a-z]/.test(newPassword) },
    { id: 'number', label: 'One number', valid: /[0-9]/.test(newPassword) },
    { id: 'special', label: 'One special character', valid: /[!@#$%^&*(),.?":{}|<>]/.test(newPassword) },
    { id: 'match', label: 'Passwords match', valid: confirmPassword && newPassword === confirmPassword }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    setErrors({});
    
    const newErrors = {};
    if (!newPassword) {
      newErrors.newPassword = 'Password is required';
    } else if (newPassword.length < 8) {
      newErrors.newPassword = 'Password must be at least 8 characters long';
    } else if (!/[A-Z]/.test(newPassword)) {
      newErrors.newPassword = 'Password must contain at least one uppercase letter';
    } else if (!/[a-z]/.test(newPassword)) {
      newErrors.newPassword = 'Password must contain at least one lowercase letter';
    } else if (!/[0-9]/.test(newPassword)) {
      newErrors.newPassword = 'Password must contain at least one number';
    } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(newPassword)) {
      newErrors.newPassword = 'Password must contain at least one special character';
    }
    
    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (newPassword !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setLoading(true);
    
    try {
      const result = await changePasswordAfterLogin(newPassword);
      
      if (result.success) {
        setSuccess(true);
        setTimeout(() => {
          router.push('/home');
        }, 2000);
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: error.message || 'An error occurred' });
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
        }}
      >
        <CircularProgress size={60} sx={{ color: '#667eea' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', flexDirection: { xs: 'column', md: 'row' } }}>
      {/* Left Side - Welcome Section */}
      <Box sx={{ 
        flex: { md: 1 }, 
        display: { xs: 'none', md: 'block' },
        minHeight: { md: '100vh' }
      }}>
        <WelcomeSection user={user} />
      </Box>
      
      {/* Right Side - Password Form */}
      <Box 
        sx={{ 
          flex: { xs: 1, md: 1 },
          background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: { xs: 2, sm: 3, md: 4 },
          position: 'relative',
          overflow: 'hidden',
          minHeight: { xs: '100vh', md: 'auto' }
        }}
      >
        {/* Background decoration */}
        <Box
          sx={{
            position: 'absolute',
            top: -50,
            right: -50,
            width: { xs: 150, md: 200 },
            height: { xs: 150, md: 200 },
            borderRadius: '50%',
            background: 'linear-gradient(45deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08))',
            filter: 'blur(40px)',
          }}
        />
        
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          style={{ width: '100%', maxWidth: 480, zIndex: 1 }}
        >
          {/* Mobile welcome header */}
          <Box sx={{ display: { xs: 'block', md: 'none' }, mb: 3, textAlign: 'center' }}>
            <Avatar
              sx={{
                bgcolor: '#667eea',
                width: 64,
                height: 64,
                mb: 2,
                mx: 'auto',
                boxShadow: '0 8px 24px rgba(102, 126, 234, 0.3)',
              }}
            >
              <WavingHandIcon sx={{ fontSize: 32, color: '#FFD700' }} />
            </Avatar>
            <Typography variant="h5" sx={{ fontWeight: 700, color: '#667eea', mb: 0.5 }}>
              Welcome Back!
            </Typography>
            <Typography variant="body1" sx={{ color: '#64748b', fontSize: '0.95rem' }}>
              {user?.first_name || user?.username?.split(' ')[0] || 'User'}
            </Typography>
          </Box>

          <Paper 
            elevation={0}
            sx={{ 
              borderRadius: { xs: 3, md: 4 },
              overflow: 'hidden',
              bgcolor: 'white',
              boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08)',
              border: '1px solid rgba(226, 232, 240, 0.8)',
            }}
          >
            <Box 
              sx={{ 
                p: { xs: 2.5, sm: 3 },
                background: 'linear-gradient(135deg, #667eea, #764ba2)',
                color: 'white',
                textAlign: 'center',
              }}
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', damping: 10, stiffness: 100, delay: 0.2 }}
              >
                <LockResetIcon sx={{ fontSize: { xs: 32, md: 36 }, mb: 1 }} />
              </motion.div>
              <Typography variant="h5" fontWeight={700} sx={{ mb: 0.5, fontSize: { xs: '1.3rem', md: '1.5rem' } }}>
                Create New Password
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9, fontSize: { xs: '0.85rem', md: '0.9rem' } }}>
                Choose a strong password to keep your account secure
              </Typography>
            </Box>

            <Box sx={{ p: { xs: 2.5, sm: 3, md: 4 } }}>
              <AnimatePresence>
                {errors.general && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                  >
                    <Alert 
                      severity="error" 
                      sx={{ mb: 3, borderRadius: 2 }}
                    >
                      {errors.general}
                    </Alert>
                  </motion.div>
                )}

                {success && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                  >
                    <Alert 
                      severity="success" 
                      icon={<CheckCircleOutlineIcon fontSize="inherit" />}
                      sx={{ mb: 3, borderRadius: 2 }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Password changed successfully! Redirecting...
                      </Typography>
                    </Alert>
                  </motion.div>
                )}
              </AnimatePresence>

              <Box component="form" onSubmit={handleSubmit}>
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.5 }}
                >
                  <TextField
                    required
                    fullWidth
                    size="medium"
                    name="newPassword"
                    label="New Password"
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    error={!!errors.newPassword}
                    helperText={errors.newPassword}
                    sx={{ 
                      mb: 2.5,
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        bgcolor: 'white',
                        border: '2px solid #e2e8f0',
                        '&:hover': {
                          borderColor: '#cbd5e1',
                          bgcolor: 'white',
                        },
                        '&.Mui-focused': {
                          bgcolor: 'white',
                          borderColor: '#667eea',
                          boxShadow: '0 0 0 3px rgba(102, 126, 234, 0.1)',
                        },
                        '&.Mui-error': {
                          borderColor: '#ef4444',
                        },
                        '& fieldset': {
                          border: 'none',
                        },
                        '& input': {
                          color: '#1f2937',
                          fontSize: '1rem',
                          fontWeight: 500,
                          '&::placeholder': {
                            color: '#9ca3af',
                            opacity: 1,
                          }
                        }
                      },
                      '& .MuiInputLabel-root': {
                        color: '#6b7280',
                        fontSize: '0.95rem',
                        fontWeight: 500,
                        backgroundColor: 'white',
                        padding: '0 8px',
                        '&.Mui-focused': {
                          color: '#667eea',
                        },
                        '&.Mui-error': {
                          color: '#ef4444',
                        }
                      },
                      '& .MuiFormHelperText-root': {
                        color: '#ef4444',
                        fontSize: '0.85rem',
                        marginLeft: 0,
                        marginTop: '6px'
                      }
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <PasswordIcon sx={{ color: '#667eea', fontSize: '1.2rem' }} />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                            sx={{ 
                              color: '#6b7280',
                              '&:hover': {
                                color: '#667eea',
                                bgcolor: 'rgba(102, 126, 234, 0.1)'
                              }
                            }}
                          >
                            {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </motion.div>
                
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.5 }}
                >
                  <TextField
                    required
                    fullWidth
                    size="medium"
                    name="confirmPassword"
                    label="Confirm Password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    error={!!errors.confirmPassword}
                    helperText={errors.confirmPassword}
                    sx={{ 
                      mb: 3,
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        bgcolor: 'white',
                        border: '2px solid #e2e8f0',
                        '&:hover': {
                          borderColor: '#cbd5e1',
                          bgcolor: 'white',
                        },
                        '&.Mui-focused': {
                          bgcolor: 'white',
                          borderColor: '#667eea',
                          boxShadow: '0 0 0 3px rgba(102, 126, 234, 0.1)',
                        },
                        '&.Mui-error': {
                          borderColor: '#ef4444',
                        },
                        '& fieldset': {
                          border: 'none',
                        },
                        '& input': {
                          color: '#1f2937',
                          fontSize: '1rem',
                          fontWeight: 500,
                          '&::placeholder': {
                            color: '#9ca3af',
                            opacity: 1,
                          }
                        }
                      },
                      '& .MuiInputLabel-root': {
                        color: '#6b7280',
                        fontSize: '0.95rem',
                        fontWeight: 500,
                        backgroundColor: 'white',
                        padding: '0 8px',
                        '&.Mui-focused': {
                          color: '#667eea',
                        },
                        '&.Mui-error': {
                          color: '#ef4444',
                        }
                      },
                      '& .MuiFormHelperText-root': {
                        color: '#ef4444',
                        fontSize: '0.85rem',
                        marginLeft: 0,
                        marginTop: '6px'
                      }
                    }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <LockResetIcon sx={{ color: '#667eea', fontSize: '1.2rem' }} />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            edge="end"
                            sx={{ 
                              color: '#6b7280',
                              '&:hover': {
                                color: '#667eea',
                                bgcolor: 'rgba(102, 126, 234, 0.1)'
                              }
                            }}
                          >
                            {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </motion.div>

                {/* Password requirements */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                >
                  <Paper 
                    variant="outlined" 
                    sx={{ 
                      p: { xs: 2, sm: 2.5 }, 
                      mb: 3, 
                      borderRadius: 2,
                      bgcolor: '#f8fafc',
                      borderColor: '#e2e8f0',
                      boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.05)'
                    }}
                  >
                    <Typography 
                      variant="subtitle2" 
                      sx={{ 
                        mb: 1.5, 
                        fontWeight: 600, 
                        color: '#374151',
                        display: 'flex',
                        alignItems: 'center',
                        fontSize: { xs: '0.85rem', md: '0.9rem' }
                      }}
                    >
                      <SecurityIcon sx={{ mr: 1, fontSize: '1.1rem', color: '#667eea' }} />
                      Password Requirements
                    </Typography>
                    
                    <Grid container spacing={1}>
                      {criteria.map((item, index) => (
                        <Grid item xs={12} sm={6} key={item.id}>
                          <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.6 + index * 0.1, duration: 0.3 }}
                          >
                            <Box 
                              sx={{ 
                                display: 'flex', 
                                alignItems: 'center',
                                py: 0.75,
                                px: 1,
                                borderRadius: 1.5,
                                bgcolor: item.valid ? 'rgba(34, 197, 94, 0.1)' : 'transparent',
                                transition: 'all 0.3s ease',
                                border: '1px solid',
                                borderColor: item.valid ? 'rgba(34, 197, 94, 0.2)' : 'transparent',
                              }}
                            >
                              <motion.div
                                animate={{ scale: item.valid ? [1, 1.2, 1] : 1 }}
                                transition={{ duration: 0.3 }}
                              >
                                {item.valid ? (
                                  <CheckCircleOutlineIcon 
                                    sx={{ mr: 1, color: '#22c55e', fontSize: '1rem' }} 
                                  />
                                ) : (
                                  <CancelOutlinedIcon 
                                    sx={{ mr: 1, color: '#94a3b8', fontSize: '1rem' }} 
                                  />
                                )}
                              </motion.div>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  color: item.valid ? '#22c55e' : '#64748b',
                                  fontWeight: item.valid ? 600 : 400,
                                  fontSize: { xs: '0.8rem', md: '0.85rem' }
                                }}
                              >
                                {item.label}
                              </Typography>
                            </Box>
                          </motion.div>
                        </Grid>
                      ))}
                    </Grid>
                  </Paper>
                </motion.div>
                
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7, duration: 0.5 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    size="large"
                    disabled={loading || success}
                    sx={{ 
                      py: { xs: 1.2, md: 1.4 }, 
                      borderRadius: 2,
                      textTransform: 'none',
                      fontWeight: 600,
                      fontSize: { xs: '1rem', md: '1.1rem' },
                      background: 'linear-gradient(135deg, #667eea, #764ba2)',
                      boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #5a6fd8, #6a4190)',
                        boxShadow: '0 12px 35px rgba(102, 126, 234, 0.4)',
                        transform: 'translateY(-1px)',
                      },
                      '&:disabled': {
                        background: 'linear-gradient(135deg, #cbd5e1, #94a3b8)',
                      },
                      transition: 'all 0.3s ease',
                    }}
                    endIcon={!loading && !success && <ArrowForwardIcon />}
                  >
                    {loading ? (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CircularProgress size={20} sx={{ mr: 1, color: 'inherit' }} />
                        Updating Password...
                      </Box>
                    ) : success ? (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CheckCircleOutlineIcon sx={{ mr: 1 }} />
                        Password Changed!
                      </Box>
                    ) : (
                      'Set New Password'
                    )}
                  </Button>
                </motion.div>
              </Box>
            </Box>
          </Paper>
        </motion.div>
      </Box>
    </Box>
  );
};

export default ChangePasswordPage;