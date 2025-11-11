'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { Container, Paper, Typography, Alert, Box } from '@mui/material';
import { motion } from 'framer-motion';
import { styled } from '@mui/material/styles';
import Link from 'next/link';
import Input from '../../components/shared/Input';
import Button from '../../components/shared/Button';
import { useAuth } from '../../context/AuthContext';

const StyledContainer = styled(Container)`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #1a237e; /* fallback */

  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 60%),
                linear-gradient(135deg, #1a237e 0%, #283593 50%, #3f51b5 100%);
    animation: rotate 20s linear infinite;
  }

  @keyframes rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;

const StyledPaper = styled(Paper)`
  padding: 40px;
  width: 100%;
  max-width: 420px;
  text-align: center;
  border-radius: 20px;
  z-index: 1;
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
`;

const LogoWrapper = styled(motion.div)`
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
`;

const ResetPasswordPage = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });
  const router = useRouter();
  const searchParams = useSearchParams();
  const { resetPassword } = useAuth();

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      router.push('/auth/login');
    }
  }, [token, router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: '', message: '' });

    if (password !== confirmPassword) {
      setStatus({
        type: 'error',
        message: 'Passwords do not match'
      });
      return;
    }

    if (password.length < 8) {
        setStatus({
            type: 'error',
            message: 'Password must be at least 8 characters long.'
        });
        return;
    }

    const result = await resetPassword(token, password);
    if (result.success) {
      setStatus({
        type: 'success',
        message: 'Password has been reset successfully. Redirecting to login...'
      });
      setTimeout(() => {
        router.push('/auth/login');
      }, 3000);
    } else {
      setStatus({
        type: 'error',
        message: result.error || 'Failed to reset password. Please try again.'
      });
    }
  };

  if (!token) {
    return null; // Or a loading spinner
  }

  return (
    <StyledContainer>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
      >
        <StyledPaper elevation={12}>
          <LogoWrapper
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 120, damping: 12, delay: 0.2 }}
          >
            <Image src="/ahana-logo.svg" alt="Ahana" width={40} height={40} />
             <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', color: '#FFF' }}>
                Set New Password
            </Typography>
          </LogoWrapper>

          <Typography variant="body1" sx={{ mb: 3, color: 'rgba(255,255,255,0.8)' }}>
            Your new password must be secure and at least 8 characters long.
          </Typography>

          <form onSubmit={handleSubmit}>
            {status.message && (
              <Alert 
                severity={status.type} 
                sx={{ 
                  mb: 2, 
                  borderRadius: '8px',
                  '.MuiAlert-message': {
                    color: status.type === 'error' ? '#ffcdd2' : '#c8e6c9'
                  },
                  backgroundColor: status.type === 'error' ? 'rgba(211, 47, 47, 0.3)' : 'rgba(67, 160, 71, 0.3)',
                  border: `1px solid ${status.type === 'error' ? 'rgba(211, 47, 47, 0.5)' : 'rgba(67, 160, 71, 0.5)'}`
                }}
              >
                {status.message}
              </Alert>
            )}

            <Input
              label="New Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              InputLabelProps={{ style: { color: '#FFF' } }}
              sx={{ 
                '.MuiOutlinedInput-root': { 
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.7)' },
                  '&.Mui-focused fieldset': { borderColor: '#FFF' },
                  '& input': { color: '#FFF' }
                } 
              }}
            />

            <Input
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              InputLabelProps={{ style: { color: '#FFF' } }}
              sx={{ 
                '.MuiOutlinedInput-root': { 
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.3)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.7)' },
                  '&.Mui-focused fieldset': { borderColor: '#FFF' },
                  '& input': { color: '#FFF' }
                }
              }}
            />
            <Box sx={{ mt: 3, mb: 2 }}>
              <Button
                type="submit"
                fullWidth
                size="large"
              >
                Reset Password
              </Button>
            </Box>

            <Typography variant="body2" sx={{ mt: 2 }}>
              <Link href="/auth/login" style={{ color: '#bbdefb', textDecoration: 'none' }}>
                Back to Login
              </Link>
            </Typography>
          </form>
        </StyledPaper>
      </motion.div>
    </StyledContainer>
  );
};

export default ResetPasswordPage; 