import React from 'react';
import { 
  Box, 
  Typography, 
  useTheme, 
  alpha, 
  Card, 
  Divider,
  Chip,
  Grid
} from '@mui/material';
import { motion } from 'framer-motion';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import CategoryIcon from '@mui/icons-material/Category';
import VerifiedIcon from '@mui/icons-material/Verified';

const LicenseManager = () => {
  const theme = useTheme();
  
  // Demo license data (would come from API in real application)
  const licenseInfo = {
    status: 'active',
    type: 'Enterprise',
    validUntil: '2025-12-31',
    features: ['Advanced Analytics', 'User Management', 'API Access', 'Custom Branding', 'Email Support', 'Data Export', 'Integrations', 'Role Management'],
    lastVerified: '2024-04-15T10:30:00Z'
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 3 }}>
        <Typography 
          variant="h6" 
          component="h2" 
          gutterBottom
          sx={{ 
            fontWeight: 600, 
            mb: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5
          }}
        >
          <Box 
            sx={{ 
              p: 0.8, 
              borderRadius: 1.5, 
              bgcolor: alpha(theme.palette.primary.main, 0.1),
              color: theme.palette.primary.main,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <VpnKeyIcon sx={{ fontSize: '1.2rem' }} />
          </Box>
          License Information
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          View your current software license details
        </Typography>
      </Box>

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Card
          elevation={0}
          sx={{
            borderRadius: 3,
            border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
            background: `linear-gradient(145deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.background.paper, 0.85)} 100%)`,
            backdropFilter: 'blur(10px)',
            boxShadow: `0 10px 30px -5px ${alpha(theme.palette.common.black, 0.05)}`,
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <Box 
            sx={{ 
              position: 'absolute', 
              top: 0, 
              left: 0, 
              right: 0, 
              height: 4, 
              background: licenseInfo.status === 'active' 
                ? `linear-gradient(90deg, ${theme.palette.success.main}, ${alpha(theme.palette.success.light, 0.8)})` 
                : `linear-gradient(90deg, ${theme.palette.error.main}, ${alpha(theme.palette.error.light, 0.8)})`,
              boxShadow: licenseInfo.status === 'active' 
                ? `0 1px 3px ${alpha(theme.palette.success.main, 0.3)}` 
                : `0 1px 3px ${alpha(theme.palette.error.main, 0.3)}`,
            }}
          />
          
          <Box sx={{ p: 2.5, pt: 3 }}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  sx={{
                    width: 48,
                    height: 48,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${alpha(theme.palette.primary.light, 0.8)})`,
                    boxShadow: `0 4px 8px ${alpha(theme.palette.primary.main, 0.25)}`,
                  }}
                >
                  <VpnKeyIcon sx={{ color: 'white', fontSize: '1.5rem' }} />
                </Box>
                <Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom sx={{ lineHeight: 1.2, mb: 0.5 }}>
                    {licenseInfo.type} License
                  </Typography>
                  <Chip
                    size="small"
                    icon={<CheckCircleIcon fontSize="small" />}
                    label="Active"
                    color="success"
                    sx={{ 
                      height: 22, 
                      fontWeight: 500,
                      fontSize: '0.7rem',
                      '& .MuiChip-icon': { fontSize: '0.85rem' }
                    }}
                  />
                </Box>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  Last verified
                </Typography>
                <Typography variant="body2" fontWeight={500}>
                  {new Date(licenseInfo.lastVerified).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
            
            <Divider sx={{ my: 2, opacity: 0.6 }} />
            
            <Grid container spacing={3} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box
                    sx={{
                      p: 0.8,
                      borderRadius: 1.5,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: alpha(theme.palette.info.main, 0.1),
                      color: theme.palette.info.main,
                    }}
                  >
                    <CalendarTodayIcon sx={{ fontSize: '1rem' }} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Valid Until
                    </Typography>
                    <Typography variant="body1" fontWeight={600}>
                      {new Date(licenseInfo.validUntil).toLocaleDateString()}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box
                    sx={{
                      p: 0.8,
                      borderRadius: 1.5,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: alpha(theme.palette.warning.main, 0.1),
                      color: theme.palette.warning.main,
                    }}
                  >
                    <CategoryIcon sx={{ fontSize: '1rem' }} />
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      License Type
                    </Typography>
                    <Typography variant="body1" fontWeight={600}>
                      {licenseInfo.type}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 2, opacity: 0.6 }} />
            
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                <VerifiedIcon sx={{ color: theme.palette.primary.main, fontSize: '1.1rem' }} />
                <Typography variant="subtitle2">Included Features</Typography>
              </Box>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {licenseInfo.features.map((feature, index) => (
                  <Chip
                    key={index}
                    label={feature}
                    size="small"
                    sx={{
                      height: '24px',
                      backgroundColor: alpha(theme.palette.primary.main, 0.08),
                      color: theme.palette.primary.main,
                      fontWeight: 500,
                      fontSize: '0.75rem',
                      borderRadius: 1,
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Box>
        </Card>
      </motion.div>
    </Box>
  );
};

export default LicenseManager; 