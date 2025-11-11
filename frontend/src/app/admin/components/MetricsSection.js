import React from 'react';
import { Box, Typography, useTheme, alpha, Grid } from '@mui/material';
import { motion } from 'framer-motion';
import AssignmentIcon from '@mui/icons-material/Assignment';
import PersonIcon from '@mui/icons-material/Person';
import SecurityIcon from '@mui/icons-material/Security';
import HistoryIcon from '@mui/icons-material/History';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

const MetricCard = ({ icon, title, value, color, trend, delay }) => {
  const theme = useTheme();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: delay * 0.1 }}
      whileHover={{ 
        y: -2,
        transition: { duration: 0.2 } 
      }}
      style={{ height: '100%' }}
    >
      <Box
        sx={{
          py: 1.2,
          px: 1.5,
          borderRadius: 2,
          height: '100%',
          background: `linear-gradient(145deg, ${alpha(color, 0.08)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
          backdropFilter: 'blur(8px)',
          boxShadow: `0 3px 8px -2px ${alpha(color, 0.1)}`,
          border: `1px solid ${alpha(color, 0.1)}`,
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: `0 5px 12px -3px ${alpha(color, 0.15)}`,
            background: `linear-gradient(145deg, ${alpha(color, 0.1)} 0%, ${alpha(theme.palette.background.paper, 0.98)} 100%)`,
          }
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            zIndex: 1,
          }}
        >
          <Box
            sx={{
              p: 0.7,
              borderRadius: 1.5,
              background: `linear-gradient(135deg, ${color} 0%, ${alpha(color, 0.8)} 100%)`,
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: `0 2px 5px ${alpha(color, 0.25)}`,
              mr: 1.2,
            }}
          >
            {React.cloneElement(icon, { sx: { fontSize: '0.9rem' } })}
          </Box>
          <Box>
            <Typography
              variant="body2"
              component="div"
              sx={{
                fontWeight: 600,
                fontSize: '0.75rem',
                color: alpha(theme.palette.text.primary, 0.8),
                lineHeight: 1.2,
              }}
            >
              {title}
            </Typography>
            <Typography
              variant="h6"
              component="div"
              sx={{
                fontWeight: 700,
                lineHeight: 1.1,
                color: theme.palette.mode === 'dark' ? color : theme.palette.text.primary,
                fontSize: '1.25rem',
                mt: 0.3,
              }}
            >
              {value}
            </Typography>
          </Box>
        </Box>

        {trend && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: alpha(theme.palette.success.main, 0.1),
              color: theme.palette.success.main,
              borderRadius: 3,
              px: 0.7,
              py: 0.2,
              zIndex: 1,
              alignSelf: 'flex-start',
              mt: 0.5,
            }}
          >
            <TrendingUpIcon sx={{ fontSize: 11, mr: 0.3 }} />
            <Typography
              variant="caption"
              sx={{
                fontWeight: 600,
                fontSize: '0.65rem'
              }}
            >
              {trend}
            </Typography>
          </Box>
        )}
        
        <Box sx={{ 
          position: 'absolute', 
          right: -10, 
          top: -10, 
          width: 70, 
          height: 70, 
          borderRadius: '50%', 
          background: alpha(color, 0.04), 
          zIndex: 0 
        }} />
      </Box>
    </motion.div>
  );
};

const MetricsSection = ({ users, roles, pendingApprovals }) => {
  const theme = useTheme();

  return (
    <Grid container spacing={2} sx={{ mb: 2 }}>
      <Grid item xs={6} sm={6} md={3}>
        <MetricCard
          icon={<AssignmentIcon />}
          title="Total Users"
          value={users.length}
          color={theme.palette.primary.main}
          delay={0}
        />
      </Grid>
      <Grid item xs={6} sm={6} md={3}>
        <MetricCard
          icon={<PersonIcon />}
          title="Active Users"
          value={users.filter(user => user.is_active).length}
          color={theme.palette.success.main}
          delay={1}
        />
      </Grid>
      <Grid item xs={6} sm={6} md={3}>
        <MetricCard
          icon={<SecurityIcon />}
          title="Roles"
          value={roles.length}
          color={theme.palette.info.main}
          delay={2}
        />
      </Grid>
      <Grid item xs={6} sm={6} md={3}>
        <MetricCard
          icon={<HistoryIcon />}
          title="Pending Approvals"
          value={pendingApprovals.length}
          color={theme.palette.warning.main}
          trend="+2 today"
          delay={3}
        />
      </Grid>
    </Grid>
  );
};

export default MetricsSection; 