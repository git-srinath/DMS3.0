"use server";

import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request) {
    try {
        const body = await request.json();
        const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/admin/license/activate`, body);
        return NextResponse.json(response.data);
    } catch (error) {
        console.error('Error activating license:', error);
        return NextResponse.json(
            { 
                success: false, 
                message: 'Failed to activate license' 
            },
            { status: error.response?.status || 500 }
        );
    }
} 