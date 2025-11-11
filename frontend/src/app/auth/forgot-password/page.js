'use client';

import { useState } from 'react';
import { Box, Typography, Alert } from '@mui/material';
import { motion } from 'framer-motion';
import { styled } from '@mui/material/styles';
import Link from 'next/link';
import Input from '../../components/shared/Input';
import Button from '../../components/shared/Button';
import { useAuth } from '../../context/AuthContext';
import EmailOutlinedIcon from '@mui/icons-material/EmailOutlined';

const StyledContainer = styled(Box)`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background-color: #1a202c;
  background-image:
    radial-gradient(at 47% 33%, hsl(200, 70%, 55%) 0, transparent 59%),
    radial-gradient(at 82% 65%, hsl(215, 70%, 65%) 0, transparent 55%);
`;

const GlassmorphicPaper = styled(motion.div)`
  padding: 40px;
  width: 100%;
  max-width: 450px;
  text-align: center;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  color: #fff;
`;

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState({ type: '', message: '' });
  const { forgotPassword } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus({ type: '', message: '' });

    const result = await forgotPassword(email);
    if (result.success) {
      setStatus({
        type: 'success',
        message: 'If an account exists with this email, you will receive password reset instructions.'
      });
      setEmail('');
    } else {
      setStatus({
        type: 'error',
        message: result.error || 'An unexpected error occurred. Please try again.'
      });
    }
  };

  return (
    <StyledContainer>
      <GlassmorphicPaper
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 120, delay: 0.2 }}
            style={{ marginBottom: '2rem' }}
        >
            <Typography variant="h4" component="h1" fontWeight="bold">
                Reset Password
            </Typography>
        </motion.div>

        <Typography variant="body1" sx={{ mb: 3, color: 'rgba(255, 255, 255, 0.7)' }}>
          Enter your email and we'll send a link to reset your password.
        </Typography>

        <form onSubmit={handleSubmit}>
          {status.message && (
            <Alert 
              severity={status.type} 
              sx={{ 
                mb: 2,
                borderRadius: '8px',
                '.MuiAlert-message': {
                  color: status.type === 'success' ? '#2e7d32' : '#d32f2f'
                }
              }}
            >
              {status.message}
            </Alert>
          )}
          
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            icon={<EmailOutlinedIcon />}
          />

          <Button
            type="submit"
            fullWidth
            size="large"
            sx={{ 
                mt: 2, 
                py: 1.5,
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                '&:hover': {
                    boxShadow: '0 0 20px #2196F3',
                }
            }}
          >
            Send Reset Link
          </Button>

          <Typography variant="body2" sx={{ mt: 3 }}>
            <Link href="/auth/login" style={{ color: '#2196F3', textDecoration: 'none', fontWeight: 'bold' }}>
              Remember your password? Login
            </Link>
          </Typography>
        </form>
      </GlassmorphicPaper>
    </StyledContainer>
  );
};

export default ForgotPasswordPage; 