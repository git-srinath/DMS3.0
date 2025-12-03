"use client"

import React, { useEffect, useState } from 'react';
import { LogOut } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { useTheme } from '@/context/ThemeContext';
import { useClickOutside } from '@/hooks/useClickOutside';
import { useAuth } from '@/app/context/AuthContext';
import { 
  LightModeOutlined,
  DarkModeOutlined,
  PersonOutlineOutlined,
  KeyboardArrowDownOutlined,
  SpeedOutlined,
  HomeOutlined,
  SettingsOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  DescriptionOutlined,
  EventNoteOutlined,
  HistoryOutlined
} from '@mui/icons-material';

const getPageTitle = (pathname) => {
  switch (pathname) {
    case '/mapper_module':
      return 'Mapper Module';
    case '/home':
      return 'Data Management Solution';
    case '/jobs':
      return 'Jobs';
    case '/type_mapper':
      return 'Parameters';
    case '/admin':
      return 'Admin';
    case '/profile':
      return 'User Profile';
    case '/settings':
      return 'Settings';
    case '/dashboard':
      return 'Dashboard';
    case '/job_status_and_logs':
        return 'Logs & Status';
    case '/manage_sql':
        return 'Manage SQL';
    case '/security':
        return 'Security';
    case '/register_db_connections':
        return 'DB Connections';
    case '/reports':
        return 'Reports';
    case '/report_scheduler':
        return 'Report Scheduler';
    case '/report_runs':
        return 'Report Runs';
    default:
      return 'Menu';
  }
};

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 18) return 'Good Afternoon';
  return 'Good Evening';
};

const getIcon = (pathname) => {
  switch (pathname) {
    case '/mapper_module':
    case '/type_mapper':
      return <SpeedOutlined className="w-4 h-4" />;
    case '/home':
      return <HomeOutlined className="w-4 h-4" />;
    case '/settings':
      return <SettingsOutlined className="w-4 h-4" />;
    case '/reports':
      return <DescriptionOutlined className="w-4 h-4" />;
    case '/report_scheduler':
      return <EventNoteOutlined className="w-4 h-4" />;
    case '/report_runs':
      return <HistoryOutlined className="w-4 h-4" />;
    default:
      return null;
  }
};

const NavBar = ({ userProfile, showProfile, setShowProfile, sidebarOpen }) => {
  const { darkMode, setDarkMode } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const pageTitle = getPageTitle(pathname);
  const [greeting, setGreeting] = useState(getGreeting());
  const pageIcon = getIcon(pathname);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Update greeting every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setGreeting(getGreeting());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  // Check fullscreen status on mount and when it changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  const profileRef = useClickOutside(() => {
    if (showProfile) setShowProfile(false);
  });

  const handleLogout = () => {
    logout();
    setShowProfile(false);
  };

  const handleViewProfile = () => {
    router.push('/profile');
    setShowProfile(false);
  };

  return (
    <nav className={`
      sticky top-0 z-30 w-full
      transition-all duration-300 ease-in-out
      border-b backdrop-blur-md
      ${darkMode 
        ? 'bg-gray-900/90 border-gray-800 shadow-sm shadow-gray-900/10' 
        : 'bg-white/90 border-gray-100 shadow-sm shadow-gray-200/20'}
    `}>
      <div className="flex items-center justify-between h-12 px-5">
        {/* Left section - Page Title with icon */}
        <div className="flex items-center">
          <div className={`
            flex items-center justify-center w-6 h-6 mr-2 rounded-md
            ${darkMode 
              ? 'bg-blue-500/10 text-blue-400' 
              : 'bg-blue-500/10 text-blue-600'
            }
          `}>
            {pageIcon}
          </div>
          <h1 className={`
            text-sm font-semibold tracking-wide relative
            ${darkMode ? 'text-gray-100' : 'text-gray-800'}
          `}>
            {pageTitle}
            <span className="absolute -bottom-1 left-0 w-10 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"></span>
          </h1>
        </div>
        
        {/* Right section */}
        <div className="flex items-center space-x-2">
          {/* Fullscreen Toggle Button */}
          <button
            onClick={toggleFullscreen}
            className={`
              p-1 rounded-full transition-all duration-200 hover:scale-105
              ${darkMode 
                ? 'bg-gray-800 text-indigo-300 hover:bg-gray-700' 
                : 'bg-gray-100 text-indigo-600 hover:bg-gray-200'
              }
            `}
            aria-label="Toggle fullscreen"
          >
            {isFullscreen ? 
              <FullscreenExitOutlined className="w-4 h-4" /> : 
              <FullscreenOutlined className="w-4 h-4" />
            }
          </button>

          {/* Theme Toggle with improved styling */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`
              p-1 rounded-full transition-all duration-200 hover:scale-105
              ${darkMode 
                ? 'bg-gray-800 text-yellow-300 hover:bg-gray-700' 
                : 'bg-gray-100 text-blue-600 hover:bg-gray-200'
              }
            `}
            aria-label="Toggle theme"
          >
            {darkMode ? 
              <LightModeOutlined className="w-4 h-4" /> : 
              <DarkModeOutlined className="w-4 h-4" />
            }
          </button>

          {/* Enhanced Profile Section */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setShowProfile(!showProfile)}
              className={`
                flex items-center space-x-2 px-2 py-1 rounded-full transition-all duration-200
                ${darkMode 
                  ? 'bg-gray-800 hover:bg-gray-700 border border-gray-700' 
                  : 'bg-gray-100 hover:bg-gray-200 border border-gray-200'
                }
              `}
            >
              <div className={`
                w-6 h-6 rounded-full flex items-center justify-center
                bg-gradient-to-br from-blue-500 to-purple-600 text-white text-xs font-medium
                ring-1 ring-white/30
              `}>
                {user?.first_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
              </div>
              <div className="flex flex-col items-start">
                <span className={`text-xs font-medium leading-tight ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : (user?.email || 'User')}
                </span>
                <span className={`text-[10px] leading-tight ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  {user?.role || 'User'}
                </span>
              </div>
              <KeyboardArrowDownOutlined className={`
                w-4 h-4 transition-transform duration-200
                ${showProfile ? 'rotate-180' : 'rotate-0'}
                ${darkMode ? 'text-gray-400' : 'text-gray-500'}
              `} />
            </button>

            {/* Enhanced Profile Dropdown */}
            {showProfile && (
              <div className={`
                absolute right-0 mt-1.5 w-72 rounded-xl overflow-hidden shadow-2xl z-50
                transform transition-all duration-200 origin-top-right
                ${darkMode 
                  ? 'bg-gray-800 border border-gray-700' 
                  : 'bg-white border border-gray-200'
                }
              `}>
                <div className={`p-5 pb-4 relative ${darkMode ? 'bg-gradient-to-br from-blue-900/30 to-purple-900/30' : 'bg-gradient-to-br from-blue-50 to-purple-50'}`}>
                  <div className="flex items-start space-x-4">
                    <div className={`
                      w-12 h-12 rounded-full flex items-center justify-center
                      bg-gradient-to-br from-blue-500 to-purple-600 text-white text-lg font-semibold
                      ring-2 ${darkMode ? 'ring-gray-800' : 'ring-white'}
                    `}>
                      {user?.first_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                    </div>
                    <div>
                      <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'} mb-0.5`}>
                        {greeting}!
                      </div>
                      <h3 className={`text-base font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                        {user?.first_name ? `${user.first_name} ${user.last_name || ''}` : 'User'}
                      </h3>
                      <p className={`text-xs ${darkMode ? 'text-blue-400' : 'text-blue-600'} font-medium`}>
                        {user?.email || 'No email available'}
                      </p>
                      <div className={`mt-1 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
                        ${darkMode 
                          ? 'bg-blue-900/30 text-blue-300' 
                          : 'bg-blue-100 text-blue-800'
                        }`}>
                        {user?.role || 'User'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-3 space-y-2">
                  <button 
                    onClick={handleViewProfile}
                    className={`
                      w-full py-2 px-4 rounded-lg text-sm transition-colors flex items-center space-x-3
                      ${darkMode 
                        ? 'hover:bg-gray-700 text-gray-200' 
                        : 'hover:bg-gray-100 text-gray-700'
                      }
                    `}>
                    <div className={`
                      w-7 h-7 rounded-full flex items-center justify-center
                      ${darkMode 
                        ? 'bg-gray-700 text-blue-400' 
                        : 'bg-gray-100 text-blue-600'
                      }
                    `}>
                      <PersonOutlineOutlined className="w-4 h-4" />
                    </div>
                    <span>View Profile</span>
                  </button>
                  <button 
                    onClick={handleLogout}
                    className={`
                      w-full py-2 px-4 rounded-lg flex items-center space-x-3 text-sm transition-colors
                      ${darkMode 
                        ? 'hover:bg-gray-700 text-gray-200' 
                        : 'hover:bg-gray-100 text-gray-700'
                      }
                    `}>
                    <div className={`
                      w-7 h-7 rounded-full flex items-center justify-center
                      ${darkMode 
                        ? 'bg-red-900/30 text-red-400' 
                        : 'bg-red-100 text-red-600'
                      }
                    `}>
                      <LogOut className="w-4 h-4" />
                    </div>
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default NavBar; 