'use client'

import React, { useState, useRef } from 'react'
import { useTheme } from '@/context/ThemeContext'
import UploadTable from './UploadTable'
import UploadForm from './UploadForm'

const FileUploadModule = () => {
  const { darkMode } = useTheme()

  // State variables for the table view
  const [showUploadTable, setShowUploadTable] = useState(true)
  const [showUploadForm, setShowUploadForm] = useState(false)
  const [selectedUpload, setSelectedUpload] = useState(null)
  const refreshTableRef = useRef(null)

  // Function to handle creating a new upload configuration
  const handleCreateNewUpload = () => {
    // Reset form data
    setSelectedUpload(null)

    // Show the upload form and hide the table
    setShowUploadTable(false)
    setShowUploadForm(true)
  }

  // Function to handle editing an existing upload configuration
  const handleEditUpload = (upload) => {
    if (upload) {
      setSelectedUpload(upload)
      setShowUploadTable(false)
      setShowUploadForm(true)
    }
  }

  // Function to return to the upload table view
  const handleReturnToUploadTable = () => {
    setShowUploadForm(false)
    setShowUploadTable(true)
    setSelectedUpload(null)
    // Refresh the table when returning from form
    if (refreshTableRef.current) {
      refreshTableRef.current()
    }
  }

  return (
    <div style={{ padding: '20px', minHeight: '100vh' }}>
      {showUploadTable && (
        <UploadTable
          handleEditUpload={handleEditUpload}
          handleCreateNewUpload={handleCreateNewUpload}
          refreshTableRef={refreshTableRef}
        />
      )}
      {showUploadForm && (
        <UploadForm
          handleReturnToUploadTable={handleReturnToUploadTable}
          upload={selectedUpload}
        />
      )}
    </div>
  )
}

export default FileUploadModule

