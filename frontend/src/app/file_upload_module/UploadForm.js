'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Box,
  Button,
  Paper,
  Typography,
  TextField,
  useTheme as useMuiTheme,
  alpha,
  Grid,
  FormControlLabel,
  Checkbox,
  MenuItem,
  Divider,
  CircularProgress,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  CloudUpload as CloudUploadIcon,
  Add as AddIcon,
  Clear as ClearIcon,
  AutoAwesome as AutoAwesomeIcon,
  Description as DescriptionIcon,
  Storage as StorageIcon,
  Settings as SettingsIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon,
  FolderOpen as FolderOpenIcon,
  UploadFile as UploadFileIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material'
import axios from 'axios'
import { message } from 'antd'
import { useTheme } from '@/context/ThemeContext'
import { API_BASE_URL } from '@/app/config'
import ColumnMappingTable from './ColumnMappingTable'
import { useSaveContext } from '@/context/SaveContext'
import FileDataTypeDialog from './FileDataTypeDialog'

// Frequency code options with descriptions
const FREQUENCY_OPTIONS = [
  { value: 'DL', label: 'Daily (DL)' },
  { value: 'WK', label: 'Weekly (WK)' },
  { value: 'MN', label: 'Monthly (MN)' },
  { value: 'HY', label: 'Half-Yearly (HY)' },
  { value: 'YR', label: 'Yearly (YR)' },
]

// Helper function to generate file reference from filename
const generateFileReference = (filename) => {
  if (!filename) return ''
  // Remove extension, convert to uppercase, replace spaces/special chars with underscores
  const nameWithoutExt = filename.replace(/\.[^/.]+$/, '')
  return nameWithoutExt
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
}

// Helper function to suggest target table name
const suggestTargetTable = (reference) => {
  if (!reference) return ''
  return reference
}

// Helper function to generate description
const generateDescription = (fileInfo, rowCount, colCount) => {
  if (!fileInfo) return ''
  const parts = []
  if (fileInfo.file_type) {
    parts.push(fileInfo.file_type.toUpperCase())
  }
  if (rowCount !== undefined && rowCount !== null) {
    parts.push(`${rowCount} rows`)
  }
  if (colCount !== undefined && colCount !== null) {
    parts.push(`${colCount} columns`)
  }
  return parts.length > 0 ? parts.join(', ') : ''
}

// Helper function to format bytes
const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

const UploadForm = ({ handleReturnToUploadTable, upload }) => {
  const { darkMode } = useTheme()
  const muiTheme = useMuiTheme()
  const fileInputRef = useRef(null)
  const createRowId = () => crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`

  const [formData, setFormData] = useState({
    flupldref: '',
    fluplddesc: '',
    flnm: '',
    flpth: '',
    fltyp: '',
    trgconid: null,
    trgschm: '',
    trgtblnm: '',
    trnctflg: 'N',
    hdrrwcnt: 0,
    ftrrwcnt: 0,
    hdrrwpttrn: '',
    ftrrwpttrn: '',
    frqcd: '',
    stflg: 'N',
    batch_size: 1000, // Batch size for data loading
    flupldid: null, // Store the ID when editing to ensure updates work correctly
  })
  const [fileInfo, setFileInfo] = useState(null)
  const [columns, setColumns] = useState([])
  const [preview, setPreview] = useState([])
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [columnMappings, setColumnMappings] = useState([])
  const [dataTypes, setDataTypes] = useState([])
  const [connections, setConnections] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadSpeed, setUploadSpeed] = useState(null)
  const [uploadedBytes, setUploadedBytes] = useState(0)
  const [fileSize, setFileSize] = useState(0)
  const [tableExists, setTableExists] = useState(false)
  const [showDataTypeDialog, setShowDataTypeDialog] = useState(false)
  const saveContext = useSaveContext()

  // For editing, we prefer to load the latest values from the backend (see loadExistingConfigurationDetails below),
  // so we only use `upload` here to seed the filename chip quickly.
  useEffect(() => {
    if (upload?.flnm) {
      setSelectedFile({ name: upload.flnm })
    }
  }, [upload])

  // Fetch data types from mapper parameter endpoint
  useEffect(() => {
    const fetchDataTypes = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(`${API_BASE_URL}/mapper/get-parameter-mapping-datatype`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setDataTypes(response.data || [])
      } catch (error) {
        console.error('Error fetching data types:', error)
      }
    }
    fetchDataTypes()
  }, [])

  // Fetch available target connections for this upload
  useEffect(() => {
    const fetchConnections = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get(`${API_BASE_URL}/file-upload/get-connections`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setConnections(response.data?.data || [])
      } catch (error) {
        console.error('Error fetching file upload connections:', error)
      }
    }
    fetchConnections()
  }, [])

  // When editing an existing configuration, load saved columns, file info, and preview
  useEffect(() => {
    const loadExistingConfigurationDetails = async () => {
      if (!upload?.flupldref) {
        return
      }

      try {
        const token = localStorage.getItem('token')

        // 0) Refresh core configuration and file information from backend
        // This ensures we always show the latest saved values when editing.
        let effectiveFilePath = upload.flpth
        try {
          const configResponse = await axios.get(
            `${API_BASE_URL}/file-upload/get-by-reference/${upload.flupldref}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          )

          const cfg = configResponse.data?.data || configResponse.data
          if (cfg) {
            effectiveFilePath = cfg.flpth || effectiveFilePath
            // Completely replace formData with backend data to ensure all saved values are shown
            const newFormData = {
              flupldref: cfg.flupldref ?? '',
              fluplddesc: cfg.fluplddesc ?? '',
              flnm: cfg.flnm ?? '',
              flpth: cfg.flpth ?? '',
              fltyp: cfg.fltyp ?? '',
              trgconid: cfg.trgconid ?? null,
              trgschm: cfg.trgschm ?? '',
              trgtblnm: cfg.trgtblnm ?? '',
              trnctflg: cfg.trnctflg ?? 'N',
              hdrrwcnt: cfg.hdrrwcnt ?? 0,
              ftrrwcnt: cfg.ftrrwcnt ?? 0,
              batch_size: cfg.batch_size ?? 1000,
              hdrrwpttrn: cfg.hdrrwpttrn ?? '',
              ftrrwpttrn: cfg.ftrrwpttrn ?? '',
              frqcd: cfg.frqcd ?? '',
              stflg: cfg.stflg ?? 'N',
              flupldid: cfg.flupldid ?? null, // Store the ID for updates
            }
            // Log for debugging (removed object logging to prevent React errors)
            console.log('Loading saved config for:', upload.flupldref)
            setFormData(newFormData)

            if (cfg.flnm) {
              setSelectedFile({ name: cfg.flnm })
            }
          } else {
            console.warn('No configuration data found in response:', configResponse.data)
          }
        } catch (err) {
          console.error('Error loading full upload configuration:', err)
        }

        // 1) Load saved column mappings
        try {
          const columnsResponse = await axios.get(
            `${API_BASE_URL}/file-upload/get-columns/${upload.flupldref}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          )

          const data = columnsResponse.data?.data || []
          if (Array.isArray(data) && data.length > 0) {
            const restoredMappings = data.map((c, idx) => ({
              id: createRowId(),
              fluplddtlid: c.fluplddtlid,
              srcclnm: c.srcclnm || '',
              trgclnm: c.trgclnm || '',
              trgcldtyp: c.trgcldtyp || '',
              trgkyflg: c.trgkyflg === 'Y' ? 'Y' : 'N',
              trgkyseq: c.trgkyseq,
              trgcldesc: c.trgcldesc || '',
              drvlgc: c.drvlgc || '',
              drvlgcflg: c.drvlgcflg === 'Y' ? 'Y' : 'N',
              excseq: c.excseq || idx + 1,
              isaudit: c.isaudit === 'Y' ? 'Y' : 'N',
              audttyp: c.audttyp || '',
              dfltval: c.dfltval || '',
              isrqrd: c.isrqrd === 'Y' || c.isrqrd === true ? 'Y' : 'N', // Keep as 'Y'/'N' string for consistency
            }))

            // Ensure audit columns are present
            const defaultAuditColumns = [
              { trgclnm: 'CRTDBY', audttyp: 'CREATED_BY', trgcldtyp: 'String100', isrqrd: 'N', isaudit: 'Y' },
              { trgclnm: 'CRTDDT', audttyp: 'CREATED_DATE', trgcldtyp: 'Timestamp', isrqrd: 'Y', isaudit: 'Y' },
              { trgclnm: 'UPDTBY', audttyp: 'UPDATED_BY', trgcldtyp: 'String100', isrqrd: 'N', isaudit: 'Y' },
              { trgclnm: 'UPDTDT', audttyp: 'UPDATED_DATE', trgcldtyp: 'Timestamp', isrqrd: 'Y', isaudit: 'Y' },
            ]
            
            // Check for existing audit columns by name (not just by audttyp)
            const auditColumnNames = ['CRTDBY', 'CRTDDT', 'UPDTBY', 'UPDTDT']
            const existingAuditColNames = new Set(
              restoredMappings
                .filter(c => {
                  const isAudit = c.isaudit === 'Y' || c.isaudit === true
                  const isDefaultAudit = auditColumnNames.includes((c.trgclnm || '').toUpperCase())
                  return isAudit || isDefaultAudit
                })
                .map(c => (c.trgclnm || '').toUpperCase())
            )
            
            const maxExcseq = Math.max(...restoredMappings.map(c => c.excseq || 0), 0)
            const missingAuditCols = defaultAuditColumns
              .filter(audit => !existingAuditColNames.has(audit.trgclnm.toUpperCase()))
              .map((audit, idx) => ({
                id: createRowId(),
                srcclnm: '',
                trgclnm: audit.trgclnm,
                trgcldtyp: audit.trgcldtyp,
                excseq: maxExcseq + idx + 1,
                trgkyflg: 'N',
                isrqrd: audit.isrqrd,
                drvlgc: '',
                drvlgcflg: 'N',
                isaudit: 'Y',
                audttyp: audit.audttyp,
              }))
            
            // Sort to ensure audit columns are last
            const allMappings = [...restoredMappings, ...missingAuditCols]
            const sortedMappings = allMappings.sort((a, b) => {
              const aIsAudit = (a.isaudit === 'Y' || a.isaudit === true) || auditColumnNames.includes((a.trgclnm || '').toUpperCase())
              const bIsAudit = (b.isaudit === 'Y' || b.isaudit === true) || auditColumnNames.includes((b.trgclnm || '').toUpperCase())
              
              if (aIsAudit && !bIsAudit) return 1
              if (!aIsAudit && bIsAudit) return -1
              
              const aSeq = a.excseq || 0
              const bSeq = b.excseq || 0
              return aSeq - bSeq
            })
            
            setColumnMappings(sortedMappings)

            // Set simple columns list for preview header / chips
            const simpleColumns = data.map((c) => c.srcclnm || c.trgclnm).filter(Boolean)
            setColumns(simpleColumns)
          }
        } catch (err) {
          console.error('Error loading saved column mappings:', err)
        }

        // 1.5) Check if target table exists
        try {
          const tableCheckResponse = await axios.get(
            `${API_BASE_URL}/file-upload/check-table-exists/${upload.flupldref}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          )
          if (tableCheckResponse.data?.success) {
            setTableExists(tableCheckResponse.data.table_exists || false)
          }
        } catch (err) {
          console.error('Error checking table existence:', err)
          // If check fails, assume table doesn't exist (safer default)
          setTableExists(false)
        }

        // 2) Load preview from saved file path, if available
        if (effectiveFilePath) {
          try {
            const previewResponse = await axios.get(
              `${API_BASE_URL}/file-upload/preview-file`,
              {
                params: {
                  file_path: effectiveFilePath,
                  rows: 10,
                },
                headers: {
                  Authorization: `Bearer ${token}`,
                },
              }
            )

            const previewData = previewResponse.data?.data || []
            if (Array.isArray(previewData) && previewData.length > 0) {
              setPreview(previewData)
            }
          } catch (err) {
            console.error('Error loading file preview:', err)
          }
        }
      } catch (error) {
        console.error('Error loading existing configuration details:', error)
      }
    }

    loadExistingConfigurationDetails()
  }, [upload])

  const handleInputChange = React.useCallback((field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    
    // Auto-fill target schema when connection is selected
    if (field === 'trgconid' && value) {
      const selectedConnection = connections.find(conn => conn.conid === value || conn.conid === String(value))
      if (selectedConnection && selectedConnection.usrnm) {
        setFormData(prev => ({
          ...prev,
          trgschm: selectedConnection.usrnm,
        }))
      }
    } else if (field === 'trgconid' && !value) {
      // Clear schema when connection is cleared
      setFormData(prev => ({
        ...prev,
        trgschm: '',
      }))
    }
  }, [connections])


  const handleFileSelect = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      // Auto-update file name in form
      setFormData(prev => ({
        ...prev,
        flnm: file.name,
      }))
    }
  }

  const inferColumnTypes = (previewRows, columnNames) => {
    const types = {}
    if (!previewRows || previewRows.length === 0 || !columnNames) return types

    columnNames.forEach((col) => {
      const values = previewRows
        .map((row) => row[col])
        .filter((v) => v !== null && v !== undefined && v !== '')

      if (values.length === 0) {
        types[col] = ''
        return
      }

      const looksNumeric = values.every((v) => !isNaN(Number(v)))
      const looksDate = values.every((v) =>
        typeof v === 'string' && /^\d{4}-\d{2}-\d{2}/.test(v)
      )

      if (looksDate) {
        types[col] = 'DATE'
      } else if (looksNumeric) {
        types[col] = 'NUMBER'
      } else {
        types[col] = 'TEXT'
      }
    })

    return types
  }

  const handlePrefillDetails = async () => {
    // When editing, selectedFile might be just { name: ... } from saved config, not an actual File
    // In that case, we can't upload it again - user needs to browse a new file
    if (!selectedFile) {
      message.error('Please select a file first')
      return
    }

    // Check if selectedFile is an actual File object
    if (!(selectedFile instanceof File)) {
      message.error('Please browse and select a file to upload. Saved file paths cannot be re-uploaded.')
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setUploadSpeed(null)
    setUploadedBytes(0)
    setFileSize(selectedFile.size || 0)
    
    // Track upload start time for speed calculation
    const uploadStartTime = Date.now()
    let lastUpdateTime = uploadStartTime
    let lastUploadedBytes = 0
    
    try {
      const token = localStorage.getItem('token')
      const formDataObj = new FormData()
      formDataObj.append('file', selectedFile)
      formDataObj.append('preview_rows', '200')  // Read first 200 rows for column detection

      const response = await axios.post(`${API_BASE_URL}/file-upload/upload-file`, formDataObj, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`,
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const currentTime = Date.now()
            const currentUploaded = progressEvent.loaded
            const total = progressEvent.total
            
            // Calculate progress percentage
            const percentCompleted = Math.round((currentUploaded / total) * 100)
            setUploadProgress(percentCompleted)
            setUploadedBytes(currentUploaded)
            
            // Calculate upload speed (bytes per second)
            const timeElapsed = (currentTime - lastUpdateTime) / 1000 // seconds
            if (timeElapsed > 0.5) { // Update speed every 500ms
              const bytesUploaded = currentUploaded - lastUploadedBytes
              const speed = bytesUploaded / timeElapsed // bytes per second
              
              // Format speed (B/s, KB/s, MB/s)
              let speedFormatted
              if (speed < 1024) {
                speedFormatted = `${Math.round(speed)} B/s`
              } else if (speed < 1024 * 1024) {
                speedFormatted = `${(speed / 1024).toFixed(1)} KB/s`
              } else {
                speedFormatted = `${(speed / (1024 * 1024)).toFixed(1)} MB/s`
              }
              
              setUploadSpeed(speedFormatted)
              lastUpdateTime = currentTime
              lastUploadedBytes = currentUploaded
            }
          }
        },
      })

      if (response.data?.success) {
        const data = response.data
        const fileInfoData = data.file_info || {}
        const detectedColumns = data.columns || []
        const previewData = data.preview || []

        // Generate auto-filled values
        const generatedRef = generateFileReference(selectedFile.name)
        const suggestedTable = suggestTargetTable(generatedRef)
        const rowCount = previewData.length
        const colCount = detectedColumns.length
        const generatedDesc = generateDescription(fileInfoData, rowCount, colCount)
        const inferredTypes = inferColumnTypes(previewData, detectedColumns)

        // Update form data with auto-filled values
        setFormData(prev => ({
          ...prev,
          flupldref: prev.flupldref || generatedRef,
          fluplddesc: prev.fluplddesc || generatedDesc,
          trgtblnm: prev.trgtblnm || suggestedTable,
          flnm: fileInfoData.original_filename || selectedFile.name,
          flpth: fileInfoData.saved_path || prev.flpth,
          fltyp: fileInfoData.file_type || prev.fltyp,
        }))

        setFileInfo(fileInfoData)
        setColumns(detectedColumns)
        setPreview(previewData)

        // Auto-detect column mappings
        const mappedColumns = detectedColumns.map((c, idx) => ({
          id: createRowId(),
          srcclnm: c,
          trgclnm: c,
          trgcldtyp: inferredTypes[c] || '',
          excseq: idx + 1,
          trgkyflg: 'N',
          isrqrd: 'N',
          drvlgc: '', // Initialize derive logic
          drvlgcflg: 'N', // Initialize derive logic flag
        }))
        
        // Add default audit columns (using standard naming: CRTDBY, CRTDDT, UPDTBY, UPDTDT)
        const auditColumns = [
          { trgclnm: 'CRTDBY', audttyp: 'CREATED_BY', trgcldtyp: 'String100', isrqrd: 'N', isaudit: 'Y' },
          { trgclnm: 'CRTDDT', audttyp: 'CREATED_DATE', trgcldtyp: 'Timestamp', isrqrd: 'Y', isaudit: 'Y' },
          { trgclnm: 'UPDTBY', audttyp: 'UPDATED_BY', trgcldtyp: 'String100', isrqrd: 'N', isaudit: 'Y' },
          { trgclnm: 'UPDTDT', audttyp: 'UPDATED_DATE', trgcldtyp: 'Timestamp', isrqrd: 'Y', isaudit: 'Y' },
        ]
        
        const auditMappings = auditColumns.map((audit, idx) => ({
          id: createRowId(),
          srcclnm: '',
          trgclnm: audit.trgclnm,
          trgcldtyp: audit.trgcldtyp,
          excseq: mappedColumns.length + idx + 1,
          trgkyflg: 'N',
          isrqrd: audit.isrqrd,
          drvlgc: '',
          drvlgcflg: 'N',
          isaudit: 'Y',
          audttyp: audit.audttyp,
        }))
        
        // Sort to ensure audit columns are last
        const allMappings = [...mappedColumns, ...auditMappings]
        const sortedMappings = allMappings.sort((a, b) => {
          const auditColumnNames = ['CRTDBY', 'CRTDDT', 'UPDTBY', 'UPDTDT']
          const aIsAudit = (a.isaudit === 'Y' || a.isaudit === true) || auditColumnNames.includes((a.trgclnm || '').toUpperCase())
          const bIsAudit = (b.isaudit === 'Y' || b.isaudit === true) || auditColumnNames.includes((b.trgclnm || '').toUpperCase())
          
          if (aIsAudit && !bIsAudit) return 1
          if (!aIsAudit && bIsAudit) return -1
          
          const aSeq = a.excseq || 0
          const bSeq = b.excseq || 0
          return aSeq - bSeq
        })
        
        setColumnMappings(sortedMappings)

        message.success('File uploaded and details pre-filled successfully')
      } else {
        message.error('Upload failed')
      }
    } catch (error) {
      console.error('Upload error:', error?.message || error?.toString() || 'Unknown error')

      const detail = error.response?.data?.detail
      let serverMessage =
        error.response?.data?.message ||
        error?.message ||
        'Failed to upload file'

      // Normalise FastAPI 422 detail (arrays / objects) into a readable string
      if (detail) {
        if (Array.isArray(detail)) {
          serverMessage = detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        } else if (typeof detail === 'object') {
          serverMessage = detail.msg || JSON.stringify(detail)
        } else if (typeof detail === 'string') {
          serverMessage = detail
        }
      }

      message.error(serverMessage)
    } finally {
      setUploading(false)
      setUploadProgress(0)
      setUploadSpeed(null)
      setUploadedBytes(0)
      setFileSize(0)
    }
  }

  const handleSave = useCallback(async () => {
    if (!formData.flupldref.trim()) {
      message.error('Reference is required')
      return
    }
    if (columnMappings.length === 0) {
      message.warning('Add at least one column mapping before saving')
      return
    }
    
    // Sort column mappings to ensure audit columns are last before saving
    const auditColumnNames = ['CRTDBY', 'CRTDDT', 'UPDTBY', 'UPDTDT']
    const sortedMappings = [...columnMappings].sort((a, b) => {
      const aIsAudit = (a.isaudit === 'Y' || a.isaudit === true) || auditColumnNames.includes((a.trgclnm || '').toUpperCase())
      const bIsAudit = (b.isaudit === 'Y' || b.isaudit === true) || auditColumnNames.includes((b.trgclnm || '').toUpperCase())
      
      // Regular columns first, audit columns last
      if (aIsAudit && !bIsAudit) return 1
      if (!aIsAudit && bIsAudit) return -1
      
      // Within same type, sort by excseq
      const aSeq = a.excseq || 0
      const bSeq = b.excseq || 0
      return aSeq - bSeq
    })
    
    const mappedColumns =
      sortedMappings.length > 0
        ? sortedMappings.map((c, idx) => ({
            trgclnm: c.trgclnm || c.srcclnm || '',
            srcclnm: c.srcclnm || c.trgclnm || '',
            trgcldtyp: c.trgcldtyp || '',
            trgkyflg: c.trgkyflg === 'Y' || c.trgkyflg === true ? 'Y' : 'N',
            trgkyseq: c.trgkyseq || null,
            trgcldesc: c.trgcldesc || '',
            drvlgc: c.drvlgc || '',
            drvlgcflg: c.drvlgcflg || 'N',
            excseq: c.excseq || idx + 1,
            isaudit: c.isaudit === 'Y' || c.isaudit === true ? 'Y' : 'N',
            audttyp: c.audttyp || '',
            dfltval: c.dfltval || '',
            isrqrd: c.isrqrd === 'Y' || c.isrqrd === true ? 'Y' : 'N',
          }))
        : []
    setSaving(true)
    try {
      const token = localStorage.getItem('token')
      const payload = {
        formData: {
          ...formData,
          crtdby: formData.crtdby || 'SYSTEM',
          // Include flupldid when editing to ensure update instead of create
          flupldid: formData.flupldid || null,
        },
        columns: mappedColumns,
      }
      await axios.post(`${API_BASE_URL}/file-upload/save`, payload, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      })
      message.success('Upload configuration saved')
      handleReturnToUploadTable()
    } catch (error) {
      console.error('Error saving upload config:', error)

      const detail = error.response?.data?.detail
      let serverMessage =
        error.response?.data?.message ||
        error?.message ||
        'Failed to save configuration'

      if (detail) {
        if (Array.isArray(detail)) {
          serverMessage = detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        } else if (typeof detail === 'object') {
          serverMessage = detail.msg || JSON.stringify(detail)
        } else if (typeof detail === 'string') {
          serverMessage = detail
        }
      }

      message.error(serverMessage)
    } finally {
      setSaving(false)
    }
  }, [formData, columnMappings, handleReturnToUploadTable])
  // Register global Save/Back handlers in NavBar when this form is active
  useEffect(() => {
    if (!saveContext || !saveContext.registerHandlers) return

    saveContext.registerHandlers({
      moduleId: 'file_upload_module',
      onSave: handleSave,
      onBack: handleReturnToUploadTable,
      canSave: !saving,
      canBack: true,
      label: upload ? 'Update' : 'Save',
    })

    return () => {
      if (saveContext && saveContext.clearHandlers) {
        saveContext.clearHandlers('file_upload_module')
      }
    }
  }, [saveContext, handleSave, handleReturnToUploadTable, saving, upload])



  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        elevation={3}
        sx={{
          p: 3,
          backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.8) : muiTheme.palette.background.paper,
          borderRadius: 2,
        }}
      >
        {/* Header with sticky action bar */}
        <Box
          sx={{
            position: 'sticky',
            top: 0,
            zIndex: 2,
            backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.92) : alpha('#fff', 0.96),
            mb: 2,
            borderBottom: `1px solid ${darkMode ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'}`,
            pb: 1,
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="subtitle1"
              component="h1"
              sx={{ fontWeight: 600, letterSpacing: 0.2 }}
            >
              Upload Configuration
            </Typography>
            {/* Back and Save actions are provided in the global NavBar via SaveContext */}
          </Box>
        </Box>

        {/* File Specification Section */}
        <Card
          sx={{
            mb: 3,
            backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.6) : alpha('#f8fafc', 0.8),
            border: `1px solid ${darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'}`,
            borderRadius: 2,
          }}
        >
          <CardContent>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                flexWrap: 'wrap',
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 'fit-content' }}>
                <UploadFileIcon color="primary" />
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  File:
                </Typography>
              </Box>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.5,
                  flexWrap: 'wrap',
                  flexGrow: 1,
                }}
              >
                  <Box
                    sx={{
                      flexGrow: 1,
                      minWidth: 220,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                      px: 1.5,
                      py: 1,
                      borderRadius: 1,
                      border: `1px dashed ${darkMode ? 'rgba(148,163,184,0.6)' : 'rgba(148,163,184,0.8)'}`,
                      backgroundColor: darkMode ? 'rgba(15,23,42,0.6)' : 'rgba(248,250,252,0.9)',
                    }}
                  >
                    {formData.flnm || selectedFile ? (
                      <>
                        <FolderOpenIcon
                          sx={{ fontSize: 18, color: darkMode ? 'rgba(148,163,184,0.9)' : 'rgba(30,64,175,0.9)' }}
                        />
                        <Box sx={{ overflow: 'hidden' }}>
                          <Typography
                            variant="body2"
                            sx={{
                              whiteSpace: 'nowrap',
                              textOverflow: 'ellipsis',
                              overflow: 'hidden',
                              maxWidth: '100%',
                            }}
                          >
                            {selectedFile?.name || formData.flnm}
                          </Typography>
                          {formData.flpth && (
                            <Typography
                              variant="caption"
                              sx={{
                                display: 'block',
                                whiteSpace: 'nowrap',
                                textOverflow: 'ellipsis',
                                overflow: 'hidden',
                                maxWidth: '100%',
                                color: 'text.secondary',
                              }}
                            >
                              {formData.flpth}
                            </Typography>
                          )}
                        </Box>
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No file selected
                      </Typography>
                    )}
                  </Box>
                  <Button
                    variant="outlined"
                    component="label"
                    startIcon={<CloudUploadIcon />}
                    sx={{ textTransform: 'none', whiteSpace: 'nowrap' }}
                  >
                    Browse
                    <input
                      ref={fileInputRef}
                      type="file"
                      hidden
                      onChange={handleFileSelect}
                      accept=".csv,.xlsx,.xls,.json,.parquet,.parq"
                    />
                  </Button>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={uploading ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />}
                    onClick={handlePrefillDetails}
                    disabled={!selectedFile || uploading || !(selectedFile instanceof File)}
                    sx={{ textTransform: 'none', whiteSpace: 'nowrap' }}
                  >
                    {uploading ? `Uploading... ${uploadProgress}%` : 'Prefill Details'}
                  </Button>
                </Box>
            </Box>
            {/* Upload Progress Indicator */}
            {uploading && (
              <Box sx={{ mt: 2, px: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Uploading file...
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {uploadProgress}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={uploadProgress} 
                  sx={{ 
                    height: 6, 
                    borderRadius: 3,
                    backgroundColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                  }} 
                />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {formatBytes(uploadedBytes)} / {formatBytes(fileSize)}
                  </Typography>
                  {uploadSpeed && (
                    <Typography variant="caption" color="primary.main" sx={{ fontWeight: 600 }}>
                      {uploadSpeed}
                    </Typography>
                  )}
                </Box>
              </Box>
            )}
            {(selectedFile || formData.flnm) && (
              <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  icon={<InfoIcon />}
                  label={`File: ${selectedFile?.name || formData.flnm}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                {formData.flpth && (
                  <Chip
                    label={`Path: ${formData.flpth}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )}
                {formData.fltyp && (
                  <Chip
                    label={`Type: ${formData.fltyp.toUpperCase()}`}
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                )}
                {columns.length > 0 && (
                  <Chip
                    label={`${columns.length} columns detected`}
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                )}
                {preview.length > 0 && (
                  <Chip
                    label={`${preview.length} preview rows`}
                    size="small"
                    color="info"
                    variant="outlined"
                  />
                )}
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Details Panel */}
        <Card
          sx={{
            mb: 3,
            backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.6) : alpha('#ffffff', 0.8),
            border: `1px solid ${darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)'}`,
            borderRadius: 2,
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <DescriptionIcon color="primary" />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Configuration Details
              </Typography>
            </Box>
            <Grid container spacing={2}>
              {/* Line 1: Reference, Description, Target Connection, Target Table */}
              <Grid item xs={12} md={3}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  label="Reference"
                  value={formData.flupldref || ''}
                  onChange={(e) => handleInputChange('flupldref', e.target.value)}
                  required
                  disabled={!!upload} // Disable when editing existing configuration
                  helperText={upload ? 'Reference cannot be changed for saved configurations' : ''}
                  sx={{
                    '& .MuiInputBase-input.Mui-disabled': {
                      WebkitTextFillColor: darkMode 
                        ? 'rgba(255, 255, 255, 0.5)' // Light grey text in dark mode
                        : 'rgba(0, 0, 0, 0.6)', // Dark grey text in light mode
                      backgroundColor: darkMode 
                        ? 'rgba(255, 255, 255, 0.05)' // Dark grey background in dark mode
                        : 'rgba(0, 0, 0, 0.04)', // Light grey background in light mode
                    },
                    '& .MuiInputBase-root.Mui-disabled': {
                      backgroundColor: darkMode 
                        ? 'rgba(255, 255, 255, 0.05)' 
                        : 'rgba(0, 0, 0, 0.04)',
                    },
                  }}
                />
              </Grid>

              <Grid item xs={12} md={3}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  label="Description"
                  value={formData.fluplddesc || ''}
                  onChange={(e) => handleInputChange('fluplddesc', e.target.value)}
                />
              </Grid>

              <Grid item xs={12} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Target Connection</InputLabel>
                  <Select
                    label="Target Connection"
                    value={formData.trgconid || ''}
                    onChange={(e) => handleInputChange('trgconid', e.target.value || null)}
                  >
                    <MenuItem value="">None (Metadata Connection)</MenuItem>
                    {connections.map((conn) => (
                      <MenuItem key={conn.conid} value={conn.conid}>
                        {conn.connm}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={3}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  label="Target Table"
                  value={formData.trgtblnm || ''}
                  onChange={(e) => handleInputChange('trgtblnm', e.target.value)}
                />
              </Grid>

              {/* Line 2: Truncate, Batch size, Header/Footer rows, Status & Frequency on same row */}
              <Grid item xs={12} md={2.5}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.trnctflg === 'Y'}
                      onChange={(e) => handleInputChange('trnctflg', e.target.checked ? 'Y' : 'N')}
                    />
                  }
                  label="Truncate before load"
                />
              </Grid>

              <Grid item xs={12} md={2.5}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  type="number"
                  label="Batch Size"
                  value={formData.batch_size || 1000}
                  onChange={(e) => {
                    const value = parseInt(e.target.value) || 1000
                    const clampedValue = Math.max(100, Math.min(100000, value))
                    handleInputChange('batch_size', clampedValue)
                  }}
                  inputProps={{ min: 100, max: 100000 }}
                  helperText="Rows per batch (100-100000). Recommended: 1000-5000"
                />
              </Grid>

              <Grid item xs={12} md={2}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  type="number"
                  label="Header Rows"
                  value={formData.hdrrwcnt || 0}
                  onChange={(e) => handleInputChange('hdrrwcnt', parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0 }}
                />
              </Grid>

              <Grid item xs={12} md={2}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  type="number"
                  label="Footer Rows"
                  value={formData.ftrrwcnt || 0}
                  onChange={(e) => handleInputChange('ftrrwcnt', parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0 }}
                />
              </Grid>

              <Grid item xs={12} md={1.5}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    label="Status"
                    value={formData.stflg || 'N'}
                    onChange={(e) => handleInputChange('stflg', e.target.value)}
                  >
                    <MenuItem value="N">Inactive</MenuItem>
                    <MenuItem value="A">Active</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={1.5}>
                <FormControl fullWidth size="small">
                  <InputLabel>Frequency</InputLabel>
                  <Select
                    label="Frequency"
                    value={formData.frqcd || ''}
                    onChange={(e) => handleInputChange('frqcd', e.target.value || '')}
                  >
                    <MenuItem value="">None</MenuItem>
                    {FREQUENCY_OPTIONS.map((freq) => (
                      <MenuItem key={freq.value} value={freq.value}>
                        {freq.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Line 3: Header pattern, Footer pattern */}
              <Grid item xs={12} md={4}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  label="Header Row Pattern"
                  value={formData.hdrrwpttrn || ''}
                  onChange={(e) => handleInputChange('hdrrwpttrn', e.target.value)}
                  placeholder="e.g., ^HEADER|^#"
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <TextField
                  size="small"
                  fullWidth
                  variant="outlined"
                  label="Footer Row Pattern"
                  value={formData.ftrrwpttrn || ''}
                  onChange={(e) => handleInputChange('ftrrwpttrn', e.target.value)}
                  placeholder="e.g., ^FOOTER|^TOTAL"
                />
              </Grid>

              {/* Frequency moved up next to Status */}
            </Grid>
          </CardContent>
        </Card>

        {/* Column Mapping Section */}
        {columns.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 1,
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                Column Mapping
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Button
                  size="small"
                  variant="text"
                  color="secondary"
                  startIcon={<ClearIcon />}
                  onClick={() => setColumnMappings([])}
                  sx={{ textTransform: 'none' }}
                >
                  Clear All
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() =>
                    setColumnMappings((prev) => [
                      ...prev,
                      {
                        id: createRowId(),
                        srcclnm: '',
                        trgclnm: '',
                        excseq: (prev?.length || 0) + 1,
                        trgkyflg: 'N',
                        isrqrd: 'N',
                        drvlgc: '', // Initialize derive logic
                        drvlgcflg: 'N', // Initialize derive logic flag
                      },
                    ])
                  }
                  sx={{ textTransform: 'none' }}
                >
                  Add Column
                </Button>
                <Button
                  size="small"
                  variant="text"
                  startIcon={<VisibilityIcon />}
                  onClick={() => setPreviewDialogOpen(true)}
                  disabled={preview.length === 0}
                  sx={{ textTransform: 'none' }}
                >
                  Preview Data
                </Button>
              </Box>
            </Box>
            <ColumnMappingTable
              columnMappings={columnMappings}
              setColumnMappings={setColumnMappings}
              dataTypes={dataTypes}
              darkMode={darkMode}
              tableExists={tableExists}
              onDeleteRow={(idx) => {
                const col = columnMappings[idx]
                const isAuditColumn = col?.isaudit === 'Y' || col?.isaudit === true
                const auditColumnNames = ['CRTDBY', 'CRTDDT', 'UPDTBY', 'UPDTDT']
                const isDefaultAudit = isAuditColumn && auditColumnNames.includes((col?.trgclnm || '').toUpperCase())
                
                if (isDefaultAudit) {
                  message.warning('Audit columns cannot be removed')
                  return
                }
                setColumnMappings((prev) => prev.filter((_, i) => i !== idx))
              }}
            />
            {columnMappings.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                No columns yet. Upload a file to auto-detect columns or add them manually.
              </Typography>
            )}
          </Box>
        )}
      </Paper>

      {/* Data preview dialog */}
      <Dialog
        open={previewDialogOpen && preview.length > 0}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Data Preview</DialogTitle>
        <DialogContent dividers>
          {preview.length > 0 && (
            <Box
              sx={{
                overflowX: 'auto',
                border: `1px solid ${darkMode ? '#1f2937' : '#e2e8f0'}`,
                borderRadius: 1,
              }}
            >
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    {Object.keys(preview[0]).map((col) => (
                      <th
                        key={col}
                        style={{
                          borderBottom: `1px solid ${darkMode ? '#1f2937' : '#e2e8f0'}`,
                          padding: '6px 8px',
                          textAlign: 'left',
                          background: darkMode ? '#111827' : '#f8fafc',
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
                            borderBottom: `1px solid ${darkMode ? '#0f172a' : '#eef2f7'}`,
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
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Data Type Review Dialog */}
      <FileDataTypeDialog
        open={showDataTypeDialog}
        onClose={() => setShowDataTypeDialog(false)}
        onApply={({ columnMappings: newMappings }) => {
          // Merge with existing mappings, preserving audit columns
          const auditColumns = columnMappings.filter(
            (m) => m.isaudit === 'Y' || m.isaudit === true
          )
          
          // Update existing mappings or add new ones
          const updatedMappings = newMappings.map((newMapping) => {
            const existing = columnMappings.find(
              (m) => m.srcclnm === newMapping.srcclnm || m.trgclnm === newMapping.trgclnm
            )
            if (existing) {
              return {
                ...existing,
                trgcldtyp: newMapping.trgcldtyp,
              }
            }
            return newMapping
          })
          
          setColumnMappings([...updatedMappings, ...auditColumns])
          setShowDataTypeDialog(false)
          message.success('Data types applied to column mappings')
        }}
        darkMode={darkMode}
        columns={columns}
        previewData={preview}
        existingMappings={columnMappings}
      />
    </Box>
  )
}

export default UploadForm
