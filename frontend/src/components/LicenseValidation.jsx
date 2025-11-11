import React, { useState } from 'react';
import { Modal, Input, Button, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '@/app/context/AuthContext';

// Create an axios instance for authenticated requests
const authAxios = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
});

// Add auth token to authenticated requests
authAxios.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

const LicenseValidation = ({ children }) => {
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [licenseKey, setLicenseKey] = useState('');
    const [activating, setActivating] = useState(false);
    const { user, licenseStatus, checkLicenseStatus } = useAuth();

    const handleActivate = async () => {
        if (!licenseKey.trim()) {
            message.error('Please enter a license key');
            return;
        }

        setActivating(true);
        try {
            const response = await authAxios.post('/api/admin/license/activate', {
                license_key: licenseKey
            });

            if (response.data.success) {
                message.success('License activated successfully');
                await checkLicenseStatus();
                setLicenseKey('');
                setIsModalVisible(false);
            } else {
                message.error(response.data.message);
            }
        } catch (error) {
            console.error('Error activating license:', error);
            if (error.response?.status === 401) {
                message.error('Please log in as an administrator to activate the license');
            } else {
                message.error(error.response?.data?.message || 'Failed to activate license');
            }
        } finally {
            setActivating(false);
        }
    };
    
    // If no user or license is valid, just render children
    if (!user || (licenseStatus && licenseStatus.data.valid)) {
        return children;
    }

    // If license is invalid, show the license required UI
    return (
        <div className="relative">
            <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-40" />
            <div className="fixed top-0 left-0 right-0 z-50">
                <div className="max-w-4xl mx-auto px-4 py-3 mt-4">
                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                        <div className="p-6">
                            <div className="flex items-center mb-4">
                                <LockOutlined className="text-2xl text-yellow-500 mr-3" />
                                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                                    License Required
                                </h2>
                            </div>
                            <div className="space-y-2 text-gray-600 dark:text-gray-300">
                                <p className="text-lg">
                                    This application requires a valid license to operate.
                                </p>
                                <p>
                                    All features are locked until a valid license is applied.
                                </p>
                                {licenseStatus?.message && (
                                    <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-2">
                                        Status: {licenseStatus.message}
                                    </p>
                                )}
                            </div>
                            <div className="mt-6">
                                <Button 
                                    type="primary"
                                    size="large"
                                    onClick={() => setIsModalVisible(true)}
                                    icon={<LockOutlined />}
                                >
                                    Activate License
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div className="pointer-events-none opacity-40 filter blur-[1px]">
                {children}
            </div>

            <Modal
                title="Activate License"
                open={isModalVisible}
                onCancel={() => {
                    setIsModalVisible(false);
                    setLicenseKey('');
                }}
                footer={[
                    <Button 
                        key="cancel" 
                        onClick={() => {
                            setIsModalVisible(false);
                            setLicenseKey('');
                        }}
                    >
                        Cancel
                    </Button>,
                    <Button
                        key="activate"
                        type="primary"
                        loading={activating}
                        onClick={handleActivate}
                        disabled={!licenseKey.trim()}
                    >
                        Activate
                    </Button>
                ]}
            >
                <div className="space-y-4">
                    <p>Enter your license key to activate the application:</p>
                    <Input.TextArea
                        value={licenseKey}
                        onChange={(e) => setLicenseKey(e.target.value)}
                        placeholder="Enter license key"
                        rows={3}
                        className="mb-2"
                    />
                    <p className="text-sm text-gray-500">
                        Note: You must be logged in as an administrator to activate the license.
                    </p>
                </div>
            </Modal>
        </div>
    );
};

export default LicenseValidation; 