"use client"

import React from 'react';
import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Sidebar from './Sidebar';
import NavBar from './NavBar';
import { useTheme } from '@/context/ThemeContext';
import LicenseValidation from './LicenseValidation';
import Notification from './Notification';
import { motion, AnimatePresence } from 'framer-motion';

export default function LayoutWrapper({ children }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [showProfile, setShowProfile] = useState(false);
    const { darkMode } = useTheme();
    const pathname = usePathname();

    // For auth routes, render only the children without the layout
    if (pathname?.startsWith('/auth')) {
        return <>{children}</>;
    }

    // For non-auth routes, render with the full layout (sidebar and navbar)
    return (
        <LicenseValidation>
            <div className={`min-h-screen flex ${darkMode ? 'bg-[#111111]' : 'bg-gray-50'}`}>
                <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
                <motion.div 
                    className="flex-1 flex flex-col min-h-screen"
                    animate={{ 
                        marginLeft: sidebarOpen ? '15rem' : '3.5rem'
                    }}
                    transition={{ 
                        type: "spring",
                        stiffness: 400,
                        damping: 30,
                        mass: 0.8
                    }}
                >
                    <NavBar 
                        sidebarOpen={sidebarOpen} 
                        setSidebarOpen={setSidebarOpen} 
                        showProfile={showProfile}
                        setShowProfile={setShowProfile}
                    />
                    <main className="flex-1 p-1">
                        {children}
                    </main>
                    <Notification />
                </motion.div>
            </div>
        </LicenseValidation>
    );
} 