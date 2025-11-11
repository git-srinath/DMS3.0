import React, { useState, useEffect, createContext, useContext } from 'react';
import { Alert, Spin, Modal, Input, Button, message } from 'antd';
import axios from 'axios';
import { usePathname } from 'next/navigation';
import { LockOutlined } from '@ant-design/icons';

// Create a context to share license status
export const LicenseContext = createContext({
    licenseStatus: null,
    refreshLicenseStatus: () => {},
});

export const useLicenseStatus = () => useContext(LicenseContext);

// Create an axios instance for license status checks
const licenseAxios = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
});

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

const LicenseCheck = ({ children }) => {
    const [licenseStatus, setLicenseStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [licenseKey, setLicenseKey] = useState('');
    const [activating, setActivating] = useState(false);

    const fetchLicenseStatus = async () => {
        try {
            const response = await licenseAxios.get('/api/license/status');
            console.log('License status response:', response.data);
            setLicenseStatus(response.data);
            return response.data;
        } catch (error) {
            console.error('Error checking license:', error);
            const status = { valid: false, message: 'Failed to check license status' };
            setLicenseStatus(status);
            return status;
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLicenseStatus();
        // Poll for license status every 30 seconds
        const interval = setInterval(fetchLicenseStatus, 30000);
        return () => clearInterval(interval);
    }, []);

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
                const newStatus = await fetchLicenseStatus();
                if (!newStatus.valid) {
                    message.error('License validation failed after activation');
                }
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

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <Spin size="large" tip="Checking license status..." />
            </div>
        );
    }

    // If license is invalid, show warning and disable ALL content
    if (!licenseStatus?.valid) {
        return (
            <LicenseContext.Provider value={{ licenseStatus, refreshLicenseStatus: fetchLicenseStatus }}>
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
                            {licenseStatus?.system_id && (
                                <div className="text-sm bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border border-blue-200 dark:border-blue-800 mt-2">
                                    <p className="font-medium mb-1 text-blue-700 dark:text-blue-300">System Information</p>
                                    <p className="text-gray-600 dark:text-gray-300">
                                        System ID: <span className="font-mono font-medium">{licenseStatus.system_id}</span>
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                        This system identifier is required when generating a license key.
                                    </p>
                                </div>
                            )}
                            <p className="text-sm text-gray-500">
                                Note: You must be logged in as an administrator to activate the license.
                            </p>
                        </div>
                    </Modal>
                </div>
            </LicenseContext.Provider>
        );
    }

    return (
        <LicenseContext.Provider value={{ licenseStatus, refreshLicenseStatus: fetchLicenseStatus }}>
            {children}
        </LicenseContext.Provider>
    );
};

export default LicenseCheck; 