'use client'
import React, { useState, useEffect, useMemo } from 'react'
import {
  Typography,
  Grid,
  Box,
  Container,
  Paper,
  useMediaQuery,
  Divider,
} from '@mui/material'
import { useRouter } from 'next/navigation'
import { useTheme as useMuiTheme } from '@mui/material/styles'
import { useTheme } from '@/context/ThemeContext'
import { useAuth } from '../context/AuthContext'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AdminPanelSettings,
  Storage,
  Timeline,
  AutoFixHigh,
  Shield,
  BarChart,
  TaskAlt,
  AccountCircle,
  Dashboard,
} from '@mui/icons-material'

const Page = () => {
  const router = useRouter()
  const { darkMode } = useTheme()
  const { user, needsPasswordChange, moduleAccess } = useAuth()
  const muiTheme = useMuiTheme()
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(muiTheme.breakpoints.down('md'))
  const [hoveredCard, setHoveredCard] = useState(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const isAdmin = user?.role === 'ADMIN'
  const moduleAccessLoading = moduleAccess?.loading ?? true
  const accessibleModuleKeys = moduleAccess?.enabledKeys
  const accessibleModuleKeysSet = useMemo(() => {
    if (!Array.isArray(accessibleModuleKeys)) {
      return null
    }
    return new Set(accessibleModuleKeys)
  }, [accessibleModuleKeys])
  const isCardVisible = (card) => {
    if (!card) return false
    if (card.requiresAdmin && !isAdmin) return false
    if (!card.accessKey) return true
    if (moduleAccessLoading) return true
    if (!accessibleModuleKeysSet) return true
    return accessibleModuleKeysSet.has(card.accessKey)
  }

  useEffect(() => {
    setIsLoaded(true)
    
    // Redirect if user needs to change password
    if (needsPasswordChange()) {
      router.push('/auth/change-password')
    }
  }, [needsPasswordChange, router])

  const cards = [
    {
      title: 'Manage SQL',
      accessKey: 'manage_sql',
      path: '/manage_sql',
      gradient: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
      description: 'Create and Edit SQL queries.',
      icon: <BarChart sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.1,
    },
    {
      title: 'Data Mapper',
      accessKey: 'data_mapper',
      path: '/mapper_module',
      gradient: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)',
      description: 'Map and Transform Data Elements.',
      icon: <Storage sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.2,
    },
    {
      title: 'Register DB Connections',
      path: '/register_db_connections',
      gradient: 'linear-gradient(135deg, #06B6D4 0%, #0E7490 100%)',
      description: 'Register, Edit, and Manage DB Connections.',
      icon: <Storage sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.15,
    },
    {
      title: 'Jobs',
      accessKey: 'jobs',
      path: '/jobs',
      gradient: 'linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%)',
      description: 'Schedule, Manage and Monitor Jobs.',
      icon: <Timeline sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.3,
    },
    {
      title: 'Parameters',
      path: '/type_mapper',
      gradient: 'linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%)',
      description: 'Create and Manage Parameters.',
      icon: <AutoFixHigh sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.4,
    },
    {
      title: 'Admin',
      requiresAdmin: true,
      path: '/admin',
      gradient: 'linear-gradient(135deg, #EC4899 0%, #DB2777 100%)',
      description: 'Create and Manage Application Users.',
      icon: <AdminPanelSettings sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.5,
    },
    {
      title: 'Jobs and Status',
      accessKey: 'job_status_and_logs',
      path: '/job_status_and_logs',
      gradient: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
      description: 'Track and Manage Jobs.',
      icon: <TaskAlt sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.6,
    },
    {
      title: 'User Profile',
      path: '/profile',
      gradient: 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
      description: 'Manage your account settings and preferences',
      icon: <AccountCircle sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.7,
    },
    {
      title: 'Dashboard',
      accessKey: 'dashboard',
      path: '/dashboard',
      gradient: 'linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)',
      description: 'Job Summary and Performance.',
      icon: <Dashboard sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.8,
    },
    {
      title: 'Security',
      path: '/security',
      gradient: 'linear-gradient(135deg, #64748B 0%, #475569 100%)',
      description: 'Manage User Access and Control.',
      icon: <Shield sx={{ fontSize: '2rem', color: '#fff' }} />,
      delay: 0.9,
      requiresAdmin: true,
    },
  ]

  // 1. Prepare group arrays from cards
  const dataManagementTitles = [
    'Manage SQL',
    'Data Mapper',
    'Jobs',
    'Jobs and Status',
  ];
  const essentialsTitles = [
    'Parameters',
    'Register DB Connections',
  ];
  const adminTitles = [
    'Admin',
    'Security',
    'User Profile', // Moved here
  ];
  const reportTitles = [
    'Dashboard',
  ];

  const mapCardsByTitles = (titles) =>
    titles
      .map((title) => cards.find((card) => card.title === title))
      .filter((card) => isCardVisible(card));

  const dataManagementCards = mapCardsByTitles(dataManagementTitles);
  const essentialsCards = mapCardsByTitles(essentialsTitles);
  const adminCards = mapCardsByTitles(adminTitles);
  const reportCards = mapCardsByTitles(reportTitles);

  // Animation variants
  const pageVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        when: 'beforeChildren',
      },
    },
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.3,
      },
    },
  }

  const cardVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: (i) => ({
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 80,
        damping: 12,
        delay: i * 0.05,
      },
    }),
  }

  const headerVariants = {
    hidden: { y: -40, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: 'spring',
        stiffness: 70,
        damping: 12,
        delay: 0.2,
      },
    },
  }

  return (
    <motion.div
      initial="hidden"
      animate={isLoaded ? 'visible' : 'hidden'}
      variants={pageVariants}
      className={`min-h-screen ${darkMode ? 'bg-[#0A101F]' : 'bg-[#F8FAFC]'}`}
    >
      <div className="absolute top-0 left-0 right-0 h-[32vh] overflow-hidden -z-10">
        <div
          className={`w-full h-full ${
            darkMode
              ? 'bg-gradient-to-b from-indigo-900/30 via-blue-900/20 to-transparent'
              : 'bg-gradient-to-b from-blue-50 via-indigo-50/50 to-transparent'
          }`}
        />
        {/* Animated background elements */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden">
          {[...Array(8)].map((_, i) => (
            <motion.div
              key={i}
              className={`absolute rounded-full ${
                darkMode ? 'bg-blue-500/10' : 'bg-indigo-400/10'
              }`}
              style={{
                width: `${Math.random() * 160 + 40}px`,
                height: `${Math.random() * 160 + 40}px`,
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
              }}
              animate={{
                y: [0, Math.random() * 25 - 12],
                x: [0, Math.random() * 25 - 12],
                scale: [1, Math.random() * 0.3 + 0.9],
              }}
              transition={{
                duration: Math.random() * 5 + 10,
                repeat: Infinity,
                repeatType: 'reverse',
              }}
            />
          ))}
        </div>
      </div>

      <Container maxWidth="lg" sx={{ py: { xs: 2.2, md: 3.5 }, position: 'relative' }}>
        {/* Header Section with centered title */}
        <motion.div variants={headerVariants} className="text-center mb-6">
          <Typography
            variant="h2"
            component="h1"
            sx={{
              fontWeight: 600,
              mb: 0.35,
              mt: 0,
              fontSize: { xs: '0.95rem', md: '1.08rem' },
              color: darkMode ? '#f3f8fa' : '#22243a',
              letterSpacing: '-0.01em',
              lineHeight: 1.05
            }}
          >
            Data Management Tool.
          </Typography>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Typography
              variant="subtitle1"
              sx={{
                color: darkMode
                  ? 'rgba(255,255,255,0.7)'
                  : 'rgba(71,85,105,0.9)',
                maxWidth: '650px',
                mx: 'auto',
                mt: 2,
                mb: 3,
                lineHeight: 1.5,
                fontWeight: 400,
                fontSize: '0.95rem',
              }}
            >
              Powerful tools to transform, manage, and analyze your data
              securely and efficiently
            </Typography>
          </motion.div>
        </motion.div>

        {/* Cards Section */}
        <Box sx={{ maxWidth: 1000, mx: 'auto', my: 0.6, width: '100%' }}>
          <Grid container spacing={{ xs: 1, md: 1.5 }}>
            {[{
              title: 'Essentials',
              color: darkMode ? '#fbbf24' : '#b45309',
              cards: essentialsCards,
              bg: darkMode ? 'rgba(55, 48, 163, 0.82)' : '#fef3c7',
              order: { xs: 0, md: 0 },
            }, {
              title: 'Data Management',
              color: darkMode ? '#38bdf8' : '#155fa0',
              cards: dataManagementCards,
              bg: darkMode ? 'rgba(23,39,59,0.87)' : '#f2f7fd',
              order: { xs: 1, md: 1 },
            }, {
              title: 'Report Management',
              color: darkMode ? '#7dd3fc' : '#2563eb',
              cards: reportCards,
              bg: darkMode ? 'rgba(26,38,45,0.90)' : '#e9f5fc',
              order: { xs: 2, md: 3 },
            }, {
              title: 'Admin',
              color: darkMode ? '#d946ef' : '#9d174d',
              cards: adminCards,
              bg: darkMode ? 'rgba(34,17,56,0.91)' : '#fff0fc',
              order: { xs: 3, md: 2 },
            }].filter((group) => group.cards.length > 0).map((group) => (
              <Grid
                item
                xs={12}
                md={6}
                key={group.title}
                sx={{ order: group.order, display: 'flex' }}
              >
                <Paper
                  elevation={0}
                  sx={{
                    p: { xs: 0.9, md: 1.05 },
                    mb: 0.85,
                    borderRadius: 2,
                    bgcolor: group.bg,
                    boxShadow: '0 2px 10px 0 rgba(0,0,0,0.022)',
                    border: darkMode ? '1px solid rgba(148, 163, 184, 0.18)' : '1px solid rgba(148, 163, 184, 0.28)',
                    width: '100%',
                  }}
                >
                  <Typography variant="subtitle2" sx={{ color: group.color, fontWeight: 700, mb: 0.3, fontSize: '0.88rem', letterSpacing: 0.15 }}>{group.title}</Typography>
                  <Grid container spacing={{ xs: 0.7, sm: 1.1, md: 1.35 }}>
                    {group.cards.map((card, idx) => (
                      <Grid
                        item
                        xs={12}
                        sm={6}
                        md={4}
                        key={card.title}
                        sx={{ display: 'flex', justifyContent: 'center' }}
                      >
                        <motion.div custom={idx} variants={cardVariants} style={{ width: '100%' }}>
                          <Paper
                            component={motion.div}
                            whileHover={{ scale: 1.015, y: -2, boxShadow: darkMode ? '0 6px 13px -7px #3336' : '0 7px 17px -8px #3332' }}
                            whileTap={{ scale: 0.96 }}
                            sx={{
                              minHeight: { xs: 78, md: 86 },
                              px: 0.65,
                              py: 0.7,
                              borderRadius: '6.5px',
                              backgroundColor: darkMode ? 'rgba(15, 22, 30, 0.72)' : '#fff',
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              justifyContent: 'center',
                              boxShadow: 'none',
                              position: 'relative',
                              cursor: 'pointer',
                              overflow: 'hidden',
                              transition: 'all 0.22s',
                              width: '100%',
                              maxWidth: { xs: '100%', md: 210 },
                              margin: '0 auto',
                            }}
                            onClick={() => router.push(card.path)}
                          >
                            <Box sx={{ position: 'absolute', inset: 0, background: card.gradient, opacity: 0.97, zIndex: 0, borderRadius: '7px' }}></Box>
                            <Box sx={{ position: 'relative', zIndex: 2, width: '100%' }}>
                              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 0.45 }}>
                                {React.cloneElement(card.icon, { sx: { fontSize: '1.04rem', color: '#fff' } })}
                              </Box>
                              <Typography
                                variant="body2"
                                sx={{
                                  color: '#fff',
                                  fontWeight: 700,
                                  fontSize: '0.62rem',
                                  mb: 0.22,
                                  textAlign: 'center',
                                  whiteSpace: 'normal',
                                  overflowWrap: 'anywhere',
                                  lineHeight: 1.05,
                                  letterSpacing: '0.01em',
                                  textShadow: '0 0.5px 2px rgba(0,0,0,0.08)',
                                }}
                              >
                                {card.title}
                              </Typography>
                              <Typography
                                variant="caption"
                                sx={{
                                  color: 'rgba(255,255,255,0.93)',
                                  fontSize: '0.51rem',
                                  fontWeight: 400,
                                  textAlign: 'center',
                                  whiteSpace: 'normal',
                                  overflowWrap: 'break-word',
                                  lineHeight: 1.08,
                                  letterSpacing: '0.002em',
                                }}
                              >
                                {card.description}
                              </Typography>
                            </Box>
                          </Paper>
                        </motion.div>
                      </Grid>
                    ))}
                  </Grid>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>

        {/* Footer Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          <Box sx={{ mt: 6, textAlign: 'center' }}>
            <Divider
              sx={{
                mb: 3,
                opacity: darkMode ? 0.1 : 0.2,
                maxWidth: '400px',
                mx: 'auto',
              }}
            />
            <Typography
              variant="caption"
              sx={{
                color: darkMode ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)',
                fontSize: '0.75rem',
                mt: 1.5,
              }}
            >
              © 2025 Ahana Systems & Solutions Pvt Ltd | All Rights Reserved
            </Typography>
          </Box>
        </motion.div>
      </Container>
    </motion.div>
  )
}

export default Page
