'use client';

import { useEffect } from 'react';
import axios from 'axios';

/**
 * Check if a reference is locked by another user
 * @param {string} reference - The reference to check
 * @returns {Promise<{isLocked: boolean, lockedBy: string|null, lockedAt: string|null}>}
 */
export const checkReferenceLock = async (reference) => {
  try {
    // Get the current user from localStorage
    const userStr = localStorage.getItem('user');
    const currentUser = userStr ? JSON.parse(userStr) : null;
    
    if (!currentUser || !reference) {
      return { isLocked: false, lockedBy: null, lockedAt: null };
    }

    console.log(`Checking lock for reference: ${reference}, current user: ${currentUser.id}`);
    
    // First check if we have a lock in localStorage (we might be the owner)
    const lockKey = `mapper_lock_${reference}`;
    const localLockStr = localStorage.getItem(lockKey);
    
    if (localLockStr) {
      try {
        const localLock = JSON.parse(localLockStr);
        
        // If it's our own lock, then it's not locked for us
        if (localLock.userId === currentUser.id) {
          console.log(`Found our own lock in localStorage for ${reference}`);
          return { isLocked: false, lockedBy: null, lockedAt: null };
        }
      } catch (e) {
        console.error('Error parsing local lock:', e);
        // Remove invalid lock data
        localStorage.removeItem(lockKey);
      }
    }

    // Call the API to check if the reference is locked
    const response = await axios.get(`/api/mapper/locks?reference=${reference}`, {
      headers: {
        'x-skip-rewrite': '1'
      }
    });
    
    if (!response.data.success) {
      console.error('API error:', response.data.error);
      return { isLocked: false, lockedBy: null, lockedAt: null };
    }
    
    const lock = response.data.lock;
    
    if (!lock) {
      console.log(`No lock found on server for ${reference}`);
      return { isLocked: false, lockedBy: null, lockedAt: null };
    }
    
    console.log(`Found lock on server for ${reference}: owner=${lock.userId}, current=${currentUser.id}`);
    
    // Check if the lock is by the current user
    if (lock.userId === currentUser.id) {
      console.log(`Lock is owned by us, not locked for us`);
      return { isLocked: false, lockedBy: null, lockedAt: null };
    }
    
    // Check if the lock is expired (24 hours)
    const lockTime = new Date(lock.lockedAt);
    const now = new Date();
    const diffHours = (now - lockTime) / (1000 * 60 * 60);
    
    if (diffHours > 24) {
      // Lock is expired
      console.log(`Lock for ${reference} is expired (${diffHours.toFixed(2)} hours), considering released`);
      return { isLocked: false, lockedBy: null, lockedAt: null };
    }
    
    console.log(`Reference ${reference} is locked by ${lock.username} since ${lock.lockedAt}`);
    return {
      isLocked: true,
      lockedBy: lock.username,
      lockedAt: lock.lockedAt,
    };
  } catch (error) {
    console.error('Error checking reference lock', error);
    return { isLocked: false, lockedBy: null, lockedAt: null };
  }
};

/**
 * Acquire a lock on a reference
 * @param {string} reference - The reference to lock
 * @returns {Promise<boolean>} - Whether the lock was acquired
 */
export const acquireReferenceLock = async (reference) => {
  try {
    if (!reference) return false;
    
    // Get the current user from localStorage
    const userStr = localStorage.getItem('user');
    const currentUser = userStr ? JSON.parse(userStr) : null;
    
    if (!currentUser) {
      console.error('No user found in localStorage');
      return false;
    }
    
    // First check if the reference is already locked
    const lockStatus = await checkReferenceLock(reference);
    
    if (lockStatus.isLocked) {
      return false;
    }
    
    // Call the API to acquire the lock
    const response = await axios.post('/api/mapper/locks', {
      reference,
      userId: currentUser.id,
      username: currentUser.username,
    }, {
      headers: {
        'x-skip-rewrite': '1'
      }
    });
    
    if (!response.data.success) {
      console.error('API error:', response.data.error);
      return false;
    }
    
    // Save the lock to localStorage as a fallback
    saveLockToLocalStorage(reference, currentUser);
    
    // Set up heartbeat to keep the lock alive
    setupLockHeartbeat(reference);
    
    return true;
  } catch (error) {
    // Handle conflict (HTTP 409) - reference is locked by another user
    if (error.response && error.response.status === 409) {
      return false;
    }
    
    console.error('Error acquiring reference lock', error);
    return false;
  }
};

/**
 * Release a lock on a reference
 * @param {string} reference - The reference to unlock
 * @returns {Promise<boolean>} - Whether the lock was released
 */
export const releaseReferenceLock = async (reference) => {
  try {
    if (!reference) return false;
    
    // Get the current user from localStorage
    const userStr = localStorage.getItem('user');
    const currentUser = userStr ? JSON.parse(userStr) : null;
    
    if (!currentUser) {
      console.error('No user found in localStorage');
      // Clean up local state anyway
      removeLockFromLocalStorage(reference);
      clearLockHeartbeat(reference);
      return false;
    }
    
    console.log(`Releasing lock for reference: ${reference}, user: ${currentUser.id}`);
    
    // Always clean up the local state first
    removeLockFromLocalStorage(reference);
    clearLockHeartbeat(reference);
    
    // Call the API to release the lock
    try {
      const response = await axios.delete(`/api/mapper/locks?reference=${reference}&userId=${currentUser.id}`, {
        headers: {
          'x-skip-rewrite': '1'
        }
      });
      
      return response.data.success;
    } catch (apiError) {
      console.error('API error releasing reference lock', apiError);
      // We've already cleaned up locally, so return success even if API call fails
      return true;
    }
  } catch (error) {
    console.error('Error in releaseReferenceLock:', error);
    
    // Still clean up local state
    removeLockFromLocalStorage(reference);
    clearLockHeartbeat(reference);
    
    // Return true since we've cleaned up locally
    return true;
  }
};

/**
 * Override an existing lock on a reference
 * @param {string} reference - The reference to lock
 * @returns {Promise<boolean>} - Whether the lock was acquired
 */
export const overrideReferenceLock = async (reference) => {
  try {
    if (!reference) return false;
    
    // Get the current user from localStorage
    const userStr = localStorage.getItem('user');
    const currentUser = userStr ? JSON.parse(userStr) : null;
    
    if (!currentUser) {
      console.error('No user found in localStorage');
      return false;
    }
    
    // Call the API to override the lock
    const response = await axios.patch('/api/mapper/locks', {
      reference,
      userId: currentUser.id,
      username: currentUser.username,
    }, {
      headers: {
        'x-skip-rewrite': '1'
      }
    });
    
    if (!response.data.success) {
      console.error('API error:', response.data.error);
      return false;
    }
    
    // Save the lock to localStorage as a fallback
    saveLockToLocalStorage(reference, currentUser);
    
    // Set up heartbeat
    setupLockHeartbeat(reference);
    
    return true;
  } catch (error) {
    console.error('Error overriding reference lock', error);
    return false;
  }
};

// Helper functions for localStorage
const saveLockToLocalStorage = (reference, user) => {
  try {
    const lockKey = `mapper_lock_${reference}`;
    const lockData = {
      reference,
      userId: user.id,
      username: user.username,
      lockedAt: new Date().toISOString(),
    };
    localStorage.setItem(lockKey, JSON.stringify(lockData));
  } catch (error) {
    console.error('Error saving lock to localStorage', error);
  }
};

const removeLockFromLocalStorage = (reference) => {
  try {
    const lockKey = `mapper_lock_${reference}`;
    localStorage.removeItem(lockKey);
  } catch (error) {
    console.error('Error removing lock from localStorage', error);
  }
};

// Heartbeat mechanism to keep locks alive
const HEARTBEAT_INTERVAL = 60000; // 1 minute
const heartbeatTimers = {};

const setupLockHeartbeat = (reference) => {
  // Clear any existing heartbeat
  clearLockHeartbeat(reference);
  
  // Set up a new heartbeat
  heartbeatTimers[reference] = setInterval(async () => {
    // Get the current user from localStorage
    const userStr = localStorage.getItem('user');
    const currentUser = userStr ? JSON.parse(userStr) : null;
    
    if (currentUser) {
      try {
        // Update the lock on the server
        await axios.post('/api/mapper/locks', {
          reference,
          userId: currentUser.id,
          username: currentUser.username,
        }, {
          headers: {
            'x-skip-rewrite': '1'
          }
        });
        
        // Also update the timestamp in localStorage
        saveLockToLocalStorage(reference, currentUser);
      } catch (error) {
        console.error('Error in lock heartbeat:', error);
      }
    } else {
      // If no user is found, clear the heartbeat
      clearLockHeartbeat(reference);
    }
  }, HEARTBEAT_INTERVAL);
};

const clearLockHeartbeat = (reference) => {
  if (heartbeatTimers[reference]) {
    clearInterval(heartbeatTimers[reference]);
    delete heartbeatTimers[reference];
  }
};

/**
 * Hook to automatically acquire and release locks
 * @param {string} reference - The reference to lock
 * @param {function} onLockFailed - Callback when lock acquisition fails
 */
export const useReferenceLock = (reference, onLockFailed) => {
  useEffect(() => {
    // Skip if no reference
    if (!reference) return;
    
    let isLocked = false;
    
    const acquireLock = async () => {
      const lockResult = await acquireReferenceLock(reference);
      isLocked = lockResult;
      
      if (!lockResult && typeof onLockFailed === 'function') {
        // Get lock details
        const lockStatus = await checkReferenceLock(reference);
        onLockFailed(lockStatus);
      }
    };
    
    acquireLock();
    
    // Cleanup: release the lock when the component unmounts
    return () => {
      if (reference) {
        // Always attempt to release the lock on unmount, even if isLocked is false
        // This ensures we clean up in all scenarios
        console.log(`Cleanup: releasing lock for ${reference}`);
        releaseReferenceLock(reference)
          .then(result => {
            console.log(`Lock release result for ${reference}:`, result);
          })
          .catch(error => {
            console.error(`Error releasing lock for ${reference}:`, error);
          });
      }
    };
  }, [reference, onLockFailed]);
};

// Handle browser close/refresh events
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', (event) => {
    // Get all lock keys from localStorage
    const lockKeys = Object.keys(localStorage).filter(key => key.startsWith('mapper_lock_'));
    
    // For each lock, extract the reference and release it
    lockKeys.forEach(key => {
      try {
        const reference = key.replace('mapper_lock_', '');
        const lockData = JSON.parse(localStorage.getItem(key));
        
        // Get the current user from localStorage
        const userStr = localStorage.getItem('user');
        const currentUser = userStr ? JSON.parse(userStr) : null;
        
        // Only release locks owned by the current user
        if (currentUser && lockData && lockData.userId === currentUser.id) {
          console.log(`Releasing lock for ${reference} on page unload`);
          
          // Use synchronous XHR for beforeunload
          const xhr = new XMLHttpRequest();
          xhr.open('DELETE', `/api/mapper/locks?reference=${reference}&userId=${lockData.userId}`, false);
          xhr.setRequestHeader('Content-Type', 'application/json');
          xhr.send();
          
          // Remove from localStorage
          localStorage.removeItem(key);
        }
      } catch (error) {
        console.error('Error releasing lock on beforeunload:', error);
      }
    });
    
    // Standard practice for beforeunload - show confirmation dialog in some browsers
    event.preventDefault();
    event.returnValue = '';
  });
} 