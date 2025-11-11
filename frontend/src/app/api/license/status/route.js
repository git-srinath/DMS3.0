"use server";

import { NextResponse } from 'next/server';
import axios from 'axios';

export async function GET() {
    // During build time, return a placeholder response
    if (process.env.NODE_ENV === 'production' && process.env.NEXT_PHASE === 'phase-production-build') {
        return NextResponse.json({
            valid: true,
            status: 'placeholder',
            message: 'Placeholder response during build'
        });
    }

    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        const response = await axios.get(`${apiUrl}/api/license/status`);
        return NextResponse.json(response.data);
    } catch (error) {
        console.error('Error fetching license status:', error);
        return NextResponse.json(
            { 
                valid: false, 
                status: 'error',
                message: 'Failed to check license status' 
            },
            { status: 500 }
        );
    }
} 