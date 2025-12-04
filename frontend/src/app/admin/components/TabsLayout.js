import React from 'react';
import { Box, Tab, Tabs, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import StorageIcon from '@mui/icons-material/Storage';
import { useRouter, usePathname } from 'next/navigation';

const tabRoutes = [
  { label: 'Database Connection', path: '/register_db_connections', icon: <StorageIcon sx={{ fontSize: '1rem', mr: 0.5 }} /> },
];

const TabsLayout = ({ isMobile }) => {
  const theme = useTheme();
  const router = useRouter();
  const pathname = usePathname();

  const activeTab = tabRoutes.findIndex(tab => {
    if(tab.path === '/register_db_connections') {
      return pathname.startsWith('/register_db_connections');
    }
    return pathname.startsWith(tab.path);
  });

  const handleTabChange = (_e, newIndex) => {
    const targetPath = tabRoutes[newIndex]?.path;
    if (targetPath) router.push(targetPath);
  };

  return (
    <Box sx={{ width: '100%', mb: 1, position: 'sticky', top: 0, zIndex: 10, backdropFilter: 'blur(10px)', background: alpha(theme.palette.background.default, 0.8), borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        variant={isMobile ? 'scrollable' : 'standard'}
        scrollButtons={isMobile ? 'auto' : false}
        sx={{
          minHeight: 40,
          '& .MuiTabs-indicator': {
            height: 2,
            borderTopLeftRadius: 2,
            borderTopRightRadius: 2,
            background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${alpha(theme.palette.primary.light, 0.8)})`,
            boxShadow: `0 0 6px ${alpha(theme.palette.primary.main, 0.5)}`,
          },
          '& .MuiTabs-flexContainer': {
            gap: 0.5,
          },
          '& .MuiTab-root': {
            py: 0.5,
            px: 1.5,
            minHeight: 40,
            textTransform: 'none',
            color: theme.palette.text.secondary,
            borderRadius: '8px 8px 0 0',
            transition: 'all 0.3s ease',
            opacity: 0.7,
            fontSize: '0.85rem',
            '&::after': {
              content: '""',
              position: 'absolute',
              bottom: 0,
              left: '20%',
              right: '20%',
              height: '2px',
              backgroundColor: theme.palette.primary.main,
              transform: 'scaleX(0)',
              transition: 'transform 0.3s ease',
            },
            '&.Mui-selected': {
              color: theme.palette.primary.main,
              fontWeight: 600,
              opacity: 1,
              backgroundColor: alpha(theme.palette.primary.main, 0.05),
            },
            '&:hover': {
              color: theme.palette.primary.main,
              opacity: 1,
              backgroundColor: alpha(theme.palette.primary.main, 0.03),
              '&::after': {
                transform: 'scaleX(1)',
              },
              '&.Mui-selected::after': {
                transform: 'scaleX(0)',
              }
            }
          },
        }}
      >
        {tabRoutes.map((tab, i) => (
          <Tab
            key={tab.path}
            icon={<motion.div whileHover={{ scale: 1.1, rotate: 5 }} whileTap={{ scale: 0.9 }}>{tab.icon}</motion.div>}
            iconPosition="start"
            label={tab.label}
          />
        ))}
      </Tabs>
    </Box>
  );
};

export default TabsLayout; 