import React, { useState } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
  IconButton,
  Tooltip,
  Chip,
  TextField,
  Button,
  Stack,
  Avatar,
  useTheme,
  alpha,
  Badge,
  Menu,
  MenuItem,
  Checkbox,
  ListItemText,
  Divider
} from '@mui/material';
import { motion } from 'framer-motion';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import FilterListIcon from '@mui/icons-material/FilterList';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import CheckIcon from '@mui/icons-material/Check';
import BlockIcon from '@mui/icons-material/Block';
import CloseIcon from '@mui/icons-material/Close';

const UserTableRow = ({ user, index, onEdit, onDelete, onResetPassword, onApprove, onReject }) => {
  const theme = useTheme();
  
  const tableRowVariants = {
    hidden: { opacity: 0, x: -5 },
    visible: i => ({
      opacity: 1,
      x: 0,
      transition: {
        delay: i * 0.03, // stagger effect
        duration: 0.2,
        ease: 'easeInOut'
      }
    }),
    hover: { 
      backgroundColor: theme.palette.action.hover,
      transition: { duration: 0.1 }
    },
    tap: { scale: 0.99 }
  };
  
  const isPending = user.account_status === 'PENDING';

  return (
    <TableRow
      component={motion.tr}
      variants={tableRowVariants}
      initial="hidden"
      animate="visible"
      custom={index}
      whileHover="hover"
      sx={{ 
        height: '40px',
        '&:last-child td, &:last-child th': { border: 0 },
        borderRadius: '8px',
        '& td': { borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`, py: 0.5 },
        '&:nth-of-type(odd)': {
          backgroundColor: alpha(theme.palette.action.hover, 0.04),
        },
      }}
    >
      <TableCell component="th" scope="row" sx={{ py: 0.5 }}>
        <Box display="flex" alignItems="center" gap={1.2}>
          {isPending ? (
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: theme.palette.warning.main,
                    border: `2px solid ${theme.palette.background.paper}`,
                  }}
                />
              }
            >
              <Avatar
                sx={{
                  width: 28,
                  height: 28,
                  backgroundColor: alpha(theme.palette.warning.main, 0.1),
                  color: theme.palette.warning.main,
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  boxShadow: `0 0 0 1px ${alpha(theme.palette.warning.main, 0.3)}`
                }}
              >
                {user.first_name ? user.first_name[0] : user.username ? user.username[0].toUpperCase() : '?'}
              </Avatar>
            </Badge>
          ) : (
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: user.is_active ? theme.palette.success.main : theme.palette.error.main,
                    border: `2px solid ${theme.palette.background.paper}`,
                  }}
                />
              }
            >
              <Avatar
                sx={{
                  width: 28,
                  height: 28,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${alpha(theme.palette.primary.light, 0.8)} 100%)`,
                  fontWeight: 600,
                  fontSize: '0.8rem',
                }}
              >
                {user.first_name ? user.first_name[0] : user.username ? user.username[0].toUpperCase() : '?'}
              </Avatar>
            </Badge>
          )}

          <Box>
            <Typography variant="subtitle2" fontWeight={600} noWrap sx={{ fontSize: '0.825rem' }}>
              {user.first_name} {user.last_name}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap sx={{ fontSize: '0.7rem' }}>
              {user.username}
            </Typography>
          </Box>
        </Box>
      </TableCell>
      
      <TableCell sx={{ py: 0.5 }}>
        <Typography variant="body2" noWrap sx={{ fontSize: '0.8rem' }}>
          {user.email}
        </Typography>
      </TableCell>
      
      <TableCell sx={{ py: 0.5 }}>
        <Chip
          label={user.role_name || 'No role'}
          size="small"
          sx={{
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            color: theme.palette.primary.main,
            fontWeight: 500,
            fontSize: '0.7rem',
            height: 20,
            borderRadius: '4px',
          }}
        />
      </TableCell>
      
      <TableCell sx={{ py: 0.5 }}>
        {isPending ? (
          <Chip
            label="Pending"
            size="small"
            color="warning"
            sx={{
              fontWeight: 500,
              fontSize: '0.7rem',
              height: 20,
              borderRadius: '4px',
            }}
          />
        ) : (
          <Chip
            label={user.is_active ? 'Active' : 'Inactive'}
            size="small"
            color={user.is_active ? 'success' : 'error'}
            sx={{
              fontWeight: 500,
              fontSize: '0.7rem',
              height: 20,
              borderRadius: '4px',
            }}
          />
        )}
      </TableCell>
      
      <TableCell align="right" sx={{ py: 0.5 }}>
        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
          {isPending ? (
            <>
              <Tooltip title="Approve">
                <IconButton
                  component={motion.button}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  color="success"
                  size="small"
                  onClick={() => onApprove(user.user_id)}
                  sx={{
                    p: 0.5,
                    backgroundColor: alpha(theme.palette.success.main, 0.1),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.success.main, 0.2),
                    }
                  }}
                >
                  <CheckIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
              <Tooltip title="Reject">
                <IconButton
                  component={motion.button}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  color="error"
                  size="small"
                  onClick={() => onReject(user.user_id)}
                  sx={{
                    p: 0.5,
                    backgroundColor: alpha(theme.palette.error.main, 0.1),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.error.main, 0.2),
                    }
                  }}
                >
                  <BlockIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
            </>
          ) : (
            <>
              <Tooltip title="Edit User">
                <IconButton
                  component={motion.button}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  color="primary"
                  size="small"
                  onClick={() => onEdit(user)}
                  sx={{
                    p: 0.5,
                    backgroundColor: alpha(theme.palette.primary.main, 0.1),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.primary.main, 0.2),
                    }
                  }}
                >
                  <EditIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete User">
                <IconButton
                  component={motion.button}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  color="error"
                  size="small"
                  onClick={() => onDelete(user.user_id)}
                  sx={{
                    p: 0.5,
                    backgroundColor: alpha(theme.palette.error.main, 0.1),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.error.main, 0.2),
                    }
                  }}
                >
                  <DeleteIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
              <Tooltip title="Reset Password">
                <IconButton
                  component={motion.button}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  color="info"
                  size="small"
                  onClick={() => onResetPassword(user)}
                  sx={{
                    p: 0.5,
                    backgroundColor: alpha(theme.palette.info.main, 0.1),
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.info.main, 0.2),
                    }
                  }}
                >
                  <RestartAltIcon sx={{ fontSize: 16 }} />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Stack>
      </TableCell>
    </TableRow>
  );
};

const UsersTable = ({ 
  users, 
  pendingApprovals = [], 
  onOpenNewUserDialog, 
  onEdit, 
  onDelete, 
  onResetPassword,
  onApprove,
  onReject
}) => {
  const theme = useTheme();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAnchorEl, setFilterAnchorEl] = useState(null);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [selectedStatuses, setSelectedStatuses] = useState([]);

  const handleFilterMenuOpen = (event) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterMenuClose = () => {
    setFilterAnchorEl(null);
  };

  const handleRoleToggle = (role) => {
    setSelectedRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    );
  };

  const handleStatusToggle = (status) => {
    setSelectedStatuses((prev) =>
      prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
    );
  };
  
  const clearFilters = () => {
    setSelectedRoles([]);
    setSelectedStatuses([]);
    handleFilterMenuClose();
  };

  // Combine users and pending approvals
  const allUsers = [...users, ...pendingApprovals];
  
  const uniqueRoles = [...new Set(allUsers.map((u) => u.role_name).filter(Boolean))];
  const allStatuses = ['Active', 'Inactive', 'Pending'];

  // Filter users based on search term
  const filteredUsers = allUsers.filter(user => {
    const searchMatch = searchTerm 
      ? user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.last_name?.toLowerCase().includes(searchTerm.toLowerCase())
      : true;

    const userStatus = user.account_status === 'PENDING' ? 'Pending' : (user.is_active ? 'Active' : 'Inactive');
    
    const statusMatch = selectedStatuses.length > 0 ? selectedStatuses.includes(userStatus) : true;
    const roleMatch = selectedRoles.length > 0 ? selectedRoles.includes(user.role_name) : true;

    return searchMatch && statusMatch && roleMatch;
  });

  const isFiltered = selectedRoles.length > 0 || selectedStatuses.length > 0;
  
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ mb: 2 }}>
        <Paper
          elevation={0}
          sx={{
            p: 1.5,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 1.5,
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            background: alpha(theme.palette.background.paper, 0.8),
            boxShadow: `0 6px 16px 0 ${alpha(theme.palette.primary.main, 0.1)}`,
          }}
        >
          <TextField
            placeholder="Search users..."
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary', fontSize: '1.1rem' }} />,
              sx: {
                borderRadius: 2,
                height: 36,
                backgroundColor: theme.palette.background.paper,
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: alpha(theme.palette.divider, 0.4),
                }
              }
            }}
            sx={{ flex: 1, minWidth: { xs: '100%', sm: 200 } }}
          />
          
          <Stack direction="row" spacing={1} sx={{ ml: { xs: 0, sm: 'auto' } }}>
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Badge color="primary" variant="dot" invisible={!isFiltered}>
                <Button
                  variant="outlined"
                  startIcon={<FilterListIcon />}
                  onClick={handleFilterMenuOpen}
                  sx={{
                    borderRadius: 2,
                    px: 1.5,
                    py: 0.6,
                    backgroundColor: alpha(theme.palette.background.paper, 0.6),
                    borderColor: isFiltered ? theme.palette.primary.main : alpha(theme.palette.divider, 0.4),
                    color: theme.palette.text.primary,
                    fontSize: '0.8rem',
                    '&:hover': {
                      backgroundColor: alpha(theme.palette.background.paper, 0.8),
                      borderColor: alpha(theme.palette.primary.main, 0.6),
                    },
                  }}
                >
                  Filters
                </Button>
              </Badge>
            </motion.div>
            
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={onOpenNewUserDialog}
                sx={{
                  borderRadius: 2,
                  px: 1.5,
                  py: 0.6,
                  fontSize: '0.8rem',
                  background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${alpha(theme.palette.primary.dark, 0.9)})`,
                  boxShadow: `0 3px 8px ${alpha(theme.palette.primary.main, 0.4)}`,
                  color: theme.palette.primary.contrastText,
                  '&:hover': {
                    boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.6)}`,
                  },
                }}
              >
                Add User
              </Button>
            </motion.div>
          </Stack>
        </Paper>
      </Box>
      
      <Menu
        anchorEl={filterAnchorEl}
        open={Boolean(filterAnchorEl)}
        onClose={handleFilterMenuClose}
        PaperProps={{
          elevation: 0,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.1))',
            mt: 1.5,
            borderRadius: 2.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
            '&:before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              top: 0,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: 'background.paper',
              transform: 'translateY(-50%) rotate(45deg)',
              zIndex: 0,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ pt:0, width: 240, display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p:1, pt: 1.5, pb: 0.5 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{px: 1}}>Filter Users</Typography>
                <IconButton size="small" onClick={handleFilterMenuClose}>
                    <CloseIcon fontSize="small" />
                </IconButton>
            </Box>
            <Divider sx={{ mb: 1 }} />

            <Typography variant="caption" fontWeight={600} sx={{ px: 2, py: 0.5, color: 'text.secondary', textTransform: 'uppercase' }}>Status</Typography>
            {allStatuses.map((status) => (
              <MenuItem key={status} onClick={() => handleStatusToggle(status)} sx={{ borderRadius: 1, mx: 1, py: 0.3 }}>
                <Checkbox checked={selectedStatuses.includes(status)} size="small" sx={{ p: 0.5, mr: 1 }} />
                <ListItemText primary={status} primaryTypographyProps={{ fontSize: '0.875rem' }} />
              </MenuItem>
            ))}
            
            <Divider sx={{ my: 1 }} />
            
            <Typography variant="caption" fontWeight={600} sx={{ px: 2, py: 0.5, color: 'text.secondary', textTransform: 'uppercase' }}>Role</Typography>
            {uniqueRoles.map((role) => (
              <MenuItem key={role} onClick={() => handleRoleToggle(role)} sx={{ borderRadius: 1, mx: 1, py: 0.3 }}>
                <Checkbox checked={selectedRoles.includes(role)} size="small" sx={{ p: 0.5, mr: 1 }} />
                <ListItemText primary={role} primaryTypographyProps={{ fontSize: '0.875rem', noWrap:true }} />
              </MenuItem>
            ))}

            {isFiltered && (
            <Box sx={{p:1.5, pt: 0.5}}>
                <Button
                    fullWidth
                    variant="outlined"
                    size="small"
                    onClick={clearFilters}
                    startIcon={<RestartAltIcon />}
                    sx={{ textTransform: 'none', fontSize: '0.8rem' }}
                >
                Clear Filters
                </Button>
            </Box>
            )}
        </Box>
      </Menu>

      <TableContainer
        component={motion.div}
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        sx={{
          borderRadius: 3,
          boxShadow: `0 6px 16px 0 ${alpha(theme.palette.common.black, 0.08)}`,
          backgroundColor: alpha(theme.palette.background.paper, 0.95),
          backdropFilter: 'blur(10px)',
          overflow: 'auto',
          maxHeight: '498px',
        }}
      >
        <Table stickyHeader size="small" sx={{ minWidth: 650 }}>
          <TableHead>
            <TableRow
              sx={{
                backgroundColor: alpha(theme.palette.primary.main, 0.03),
                '& th': {
                  borderBottom: `2px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  color: theme.palette.text.secondary,
                  fontWeight: 600,
                  fontSize: '0.7rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  py: 1,
                },
              }}
            >
              <TableCell>User</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers
              .map((user, index) => (
                <UserTableRow
                  key={user.user_id}
                  user={user}
                  index={index}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onResetPassword={onResetPassword}
                  onApprove={onApprove}
                  onReject={onReject}
                />
              ))}
            
            {filteredUsers.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 2 }}>
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      No users found
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                      {searchTerm ? 'Try adjusting your search criteria' : 'Add users to get started'}
                    </Typography>
                  </Box>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default UsersTable; 