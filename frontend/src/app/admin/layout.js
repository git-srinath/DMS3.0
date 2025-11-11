'use client';
import { Box } from '@mui/material';

export default function AdminLayout({ children, about, license, 'manage-users': manageUsers }) {
    return (
        <Box sx={{ 
            width: '100%', 
            maxWidth: '100%',
            overflowX: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            minHeight: 'calc(100vh - 14rem)'
        }}>
            <Box 
                sx={{ 
                    width: '100%',
                    px: { xs: 1, sm: 2, md: 3 }, 
                    py: 2,
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column'
                }}
            >
                {children}
                {about}
                {license}
                {manageUsers}
            </Box>
        </Box>
    );
} 