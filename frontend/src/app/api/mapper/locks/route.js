import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const LOCK_FILE_PATH = path.join(process.cwd(), 'public', 'mapper_module', 'reference_locks.json');

// Ensure the directory exists
const ensureDirectoryExists = () => {
  const dir = path.dirname(LOCK_FILE_PATH);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
};

// Read locks from file
const readLocks = () => {
  ensureDirectoryExists();
  
  try {
    if (!fs.existsSync(LOCK_FILE_PATH)) {
      fs.writeFileSync(LOCK_FILE_PATH, '[]', 'utf8');
      return [];
    }
    
    const data = fs.readFileSync(LOCK_FILE_PATH, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading lock file:', error);
    return [];
  }
};

// Write locks to file
const writeLocks = (locks) => {
  ensureDirectoryExists();
  
  try {
    fs.writeFileSync(LOCK_FILE_PATH, JSON.stringify(locks, null, 2), 'utf8');
    return true;
  } catch (error) {
    console.error('Error writing lock file:', error);
    return false;
  }
};

// Function to clean up expired locks
const cleanupExpiredLocks = () => {
  console.log('API: Cleaning up expired locks');
  try {
    const locks = readLocks();
    const now = new Date();
    
    // Filter out locks older than 24 hours
    const validLocks = locks.filter(lock => {
      const lockTime = new Date(lock.lockedAt);
      const diffHours = (now - lockTime) / (1000 * 60 * 60);
      const isValid = diffHours <= 24;
      
      if (!isValid) {
        console.log(`API: Removing expired lock for reference ${lock.reference}, was locked by ${lock.username} for ${diffHours.toFixed(2)} hours`);
      }
      
      return isValid;
    });
    
    // If we removed any locks, write the updated locks back to the file
    if (validLocks.length < locks.length) {
      console.log(`API: Removed ${locks.length - validLocks.length} expired locks`);
      writeLocks(validLocks);
    }
  } catch (error) {
    console.error('API: Error cleaning up expired locks:', error);
  }
};

// GET endpoint to check locks
export async function GET(request) {
  try {
    // Clean up expired locks on every check
    cleanupExpiredLocks();
    
    const { searchParams } = new URL(request.url);
    const reference = searchParams.get('reference');
    
    const locks = readLocks();
    
    if (reference) {
      const lock = locks.find(lock => lock.reference === reference);
      return NextResponse.json({ 
        success: true, 
        lock: lock || null 
      });
    }
    
    return NextResponse.json({ 
      success: true, 
      locks 
    });
  } catch (error) {
    console.error('Error getting locks:', error);
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to get locks' 
    }, { status: 500 });
  }
}

// POST endpoint to acquire a lock
export async function POST(request) {
  try {
    const body = await request.json();
    const { reference, userId, username } = body;
    
    if (!reference || !userId || !username) {
      return NextResponse.json({ 
        success: false, 
        error: 'Missing required fields' 
      }, { status: 400 });
    }
    
    const locks = readLocks();
    
    // Check if the reference is already locked by someone else
    const existingLock = locks.find(lock => lock.reference === reference);
    if (existingLock && existingLock.userId !== userId) {
      // Check if the lock is expired (24 hours)
      const lockTime = new Date(existingLock.lockedAt);
      const now = new Date();
      const diffHours = (now - lockTime) / (1000 * 60 * 60);
      
      if (diffHours <= 24) {
        return NextResponse.json({ 
          success: false, 
          error: 'Reference is locked by another user',
          lock: existingLock
        }, { status: 409 });
      }
    }
    
    // Remove any existing lock for this reference
    const updatedLocks = locks.filter(lock => lock.reference !== reference);
    
    // Add the new lock
    updatedLocks.push({
      reference,
      userId,
      username,
      lockedAt: new Date().toISOString(),
    });
    
    const writeSuccess = writeLocks(updatedLocks);
    
    if (!writeSuccess) {
      return NextResponse.json({ 
        success: false, 
        error: 'Failed to write locks to file' 
      }, { status: 500 });
    }
    
    return NextResponse.json({ 
      success: true, 
      message: 'Lock acquired successfully' 
    });
  } catch (error) {
    console.error('Error acquiring lock:', error);
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to acquire lock' 
    }, { status: 500 });
  }
}

// DELETE endpoint to release a lock
export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const reference = searchParams.get('reference');
    const userId = searchParams.get('userId');
    
    console.log(`API: Received lock release request for reference ${reference}, userId ${userId}`);
    
    if (!reference) {
      return NextResponse.json({ 
        success: false, 
        error: 'Missing reference parameter' 
      }, { status: 400 });
    }
    
    const locks = readLocks();
    
    // Get the current lock for this reference, if any
    const existingLock = locks.find(lock => lock.reference === reference);
    
    // If no lock found, consider it already released (idempotent)
    if (!existingLock) {
      console.log(`API: No lock found for reference ${reference}, considering already released`);
      return NextResponse.json({ 
        success: true, 
        message: 'No lock found, already released' 
      });
    }
    
    // If userId is provided, check if the lock is owned by this user
    if (userId && existingLock.userId !== userId) {
      console.log(`API: Lock for reference ${reference} is owned by ${existingLock.userId}, not ${userId}`);
      
      // Check if the lock is expired (24 hours)
      const lockTime = new Date(existingLock.lockedAt);
      const now = new Date();
      const diffHours = (now - lockTime) / (1000 * 60 * 60);
      
      if (diffHours <= 24) {
        // If not expired, only warn but proceed with deletion anyway
        console.log(`API: Lock not expired but proceeding with release anyway`);
      }
    }
    
    // Remove the lock regardless of ownership
    const updatedLocks = locks.filter(lock => lock.reference !== reference);
    
    const writeSuccess = writeLocks(updatedLocks);
    
    if (!writeSuccess) {
      console.error(`API: Failed to write updated locks to file`);
      return NextResponse.json({ 
        success: false, 
        error: 'Failed to write locks to file' 
      }, { status: 500 });
    }
    
    console.log(`API: Successfully released lock for reference ${reference}`);
    return NextResponse.json({ 
      success: true, 
      message: 'Lock released successfully' 
    });
  } catch (error) {
    console.error('API Error releasing lock:', error);
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to release lock' 
    }, { status: 500 });
  }
}

// PATCH endpoint to override a lock
export async function PATCH(request) {
  try {
    const body = await request.json();
    const { reference, userId, username } = body;
    
    if (!reference || !userId || !username) {
      return NextResponse.json({ 
        success: false, 
        error: 'Missing required fields' 
      }, { status: 400 });
    }
    
    const locks = readLocks();
    
    // Remove any existing lock for this reference
    const updatedLocks = locks.filter(lock => lock.reference !== reference);
    
    // Add the new lock
    updatedLocks.push({
      reference,
      userId,
      username,
      lockedAt: new Date().toISOString(),
    });
    
    const writeSuccess = writeLocks(updatedLocks);
    
    if (!writeSuccess) {
      return NextResponse.json({ 
        success: false, 
        error: 'Failed to write locks to file' 
      }, { status: 500 });
    }
    
    return NextResponse.json({ 
      success: true, 
      message: 'Lock overridden successfully' 
    });
  } catch (error) {
    console.error('Error overriding lock:', error);
    return NextResponse.json({ 
      success: false, 
      error: 'Failed to override lock' 
    }, { status: 500 });
  }
} 