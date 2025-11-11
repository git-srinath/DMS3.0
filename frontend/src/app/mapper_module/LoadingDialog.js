'use client'

import React from 'react'
import { Dialog, Typography } from '@mui/material'
import { useTheme } from '@/context/ThemeContext'
import { motion } from 'framer-motion'

const LoadingDialog = ({ open, title, message }) => {
  const { darkMode } = useTheme()

  return (
    <Dialog
      open={open}
      PaperProps={{
        style: {
          backgroundColor: 'transparent',
          boxShadow: 'none',
          overflow: 'hidden',
        },
      }}
      BackdropProps={{
        style: {
          backgroundColor: darkMode
            ? 'rgba(17, 24, 39, 0.6)'
            : 'rgba(243, 244, 246, 0.6)',
          backdropFilter: 'blur(4px)',
        },
      }}
    >
      <div className="flex flex-col items-center justify-center text-center p-6">
        {/* Bouncing dots animation */}
        <div className="flex space-x-2">
          <motion.div
            className="w-4 h-4 rounded-full"
            style={{ backgroundColor: darkMode ? '#60A5FA' : '#3B82F6' }}
            animate={{
              y: [0, -16, 0],
            }}
            transition={{
              duration: 0.8,
              ease: 'easeInOut',
              repeat: Infinity,
              repeatType: 'loop',
            }}
          />
          <motion.div
            className="w-4 h-4 rounded-full"
            style={{ backgroundColor: darkMode ? '#60A5FA' : '#3B82F6' }}
            animate={{
              y: [0, -16, 0],
            }}
            transition={{
              duration: 0.8,
              ease: 'easeInOut',
              repeat: Infinity,
              repeatType: 'loop',
              delay: 0.2,
            }}
          />
          <motion.div
            className="w-4 h-4 rounded-full"
            style={{ backgroundColor: darkMode ? '#60A5FA' : '#3B82F6' }}
            animate={{
              y: [0, -16, 0],
            }}
            transition={{
              duration: 0.8,
              ease: 'easeInOut',
              repeat: Infinity,
              repeatType: 'loop',
              delay: 0.4,
            }}
          />
        </div>

        <Typography
          variant="h6"
          className="mt-6 font-semibold"
          style={{
            color: darkMode ? '#F9FAFB' : '#111827',
            textShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          {title}
        </Typography>
        <Typography
          variant="body1"
          className="mt-1"
          style={{
            color: darkMode ? '#D1D5DB' : '#4B5563',
            textShadow: '0 1px 2px rgba(0,0,0,0.1)',
          }}
        >
          {message}
        </Typography>
      </div>
    </Dialog>
  )
}

export default LoadingDialog 