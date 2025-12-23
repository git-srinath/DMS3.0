'use client'

import React, { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  LinearProgress,
} from '@mui/material'
import { Upload as UploadIcon, Close as CloseIcon } from '@mui/icons-material'
import axios from 'axios'
import { message } from 'antd'
import { API_BASE_URL } from '@/app/config'

const FileUploadDialog = ({ open, onClose, onUploaded }) => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState([])
  const [columns, setColumns] = useState([])

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files?.[0] || null)
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      message.error('Please select a file to upload')
      return
    }
    setUploading(true)
    try {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('preview_rows', '10')

      const response = await axios.post(`${API_BASE_URL}/file-upload/upload-file`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.data?.success) {
        const data = response.data
        setPreview(data.preview || [])
        setColumns(data.columns || [])
        if (onUploaded) {
          onUploaded(data)
        }
        message.success('File uploaded and parsed successfully')
      } else {
        message.error('Upload failed')
      }
    } catch (error) {
      console.error('Upload error:', error)
      const serverMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        'Failed to upload file'
      message.error(serverMessage)
    } finally {
      setUploading(false)
    }
  }

  const hasPreview = preview && preview.length > 0

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <UploadIcon fontSize="small" />
        Upload File & Preview
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 2 }}>
          <Button variant="contained" component="label" startIcon={<UploadIcon />} sx={{ textTransform: 'none' }}>
            Choose File
            <input type="file" hidden onChange={handleFileChange} />
          </Button>
          <Typography variant="body2" color="text.secondary">
            {selectedFile ? selectedFile.name : 'No file selected'}
          </Typography>
        </Box>

        {uploading && <LinearProgress sx={{ mb: 2 }} />}

        {hasPreview && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Preview (first {preview.length} rows)
            </Typography>
            <Box sx={{ overflowX: 'auto', border: '1px solid #e2e8f0', borderRadius: 1 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {Object.keys(preview[0]).map((col) => (
                      <th
                        key={col}
                        style={{
                          borderBottom: '1px solid #e2e8f0',
                          padding: '6px 8px',
                          textAlign: 'left',
                          background: '#f8fafc',
                        }}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, idx) => (
                    <tr key={idx}>
                      {Object.keys(row).map((col) => (
                        <td
                          key={col}
                          style={{
                            borderBottom: '1px solid #eef2f7',
                            padding: '6px 8px',
                            fontSize: '0.85rem',
                          }}
                        >
                          {row[col] === null ? '' : row[col]}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </Box>
          </Box>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} startIcon={<CloseIcon />} sx={{ textTransform: 'none' }}>
          Close
        </Button>
        <Button
          variant="contained"
          onClick={handleUpload}
          disabled={uploading}
          startIcon={<UploadIcon />}
          sx={{ textTransform: 'none' }}
        >
          {uploading ? 'Uploading...' : 'Upload & Preview'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default FileUploadDialog

