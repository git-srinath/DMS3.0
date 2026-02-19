/**
 * DatabaseWizard Component
 * 4-step wizard for adding new database types with suggestions
 * Phase 2B: Datatypes Management
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  TextField,
  Alert,
  CircularProgress,
  Box,
  Typography,
  Checkbox,
  FormControlLabel,
  useTheme,
  Table,
  TableHead,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
} from '@mui/material'
import { useDatatypeAPI } from '../../hooks/useDatatypeAPI'

const steps = [
  'Database Details',
  'Get Suggestions',
  'Review Suggestions',
  'Confirm & Create',
]

export default function DatabaseWizard({ open, onClose, onSuccess }) {
  const {
    addSupportedDatabase,
    getDatatypeSuggestions,
    cloneDatatypes,
    loading,
  } = useDatatypeAPI()
  const theme = useTheme()

  const [activeStep, setActiveStep] = useState(0)
  const [dbType, setDbType] = useState('')
  const [dbDesc, setDbDesc] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [selectedSuggestions, setSelectedSuggestions] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState(false)

  // Automatically fetch suggestions when entering Step 1
  useEffect(() => {
    if (activeStep === 1 && dbType && !suggestions.length && !isFetchingSuggestions) {
      const fetchSuggestions = async () => {
        setIsFetchingSuggestions(true)
        setError('')
        try {
          const data = await getDatatypeSuggestions(dbType, true)
          if (data.suggestions && data.suggestions.length > 0) {
            setSuggestions(data.suggestions)
            setSelectedSuggestions(data.suggestions.map((_, idx) => idx))
            // Automatically advance to Step 2
            setActiveStep(2)
          } else {
            setError('No suggestions found for this database type')
          }
        } catch (err) {
          setError(err.message || 'Failed to get suggestions. Please try again.')
        } finally {
          setIsFetchingSuggestions(false)
        }
      }
      fetchSuggestions()
    }
  }, [activeStep, dbType, getDatatypeSuggestions, isFetchingSuggestions, suggestions.length])

  const handleReset = () => {
    setActiveStep(0)
    setDbType('')
    setDbDesc('')
    setSuggestions([])
    setSelectedSuggestions([])
    setError('')
    setSuccess(false)
  }

  const handleClose = () => {
    handleReset()
    onClose()
  }

  const handleNextStep = async () => {
    setError('')

    if (activeStep === 0) {
      // Validate database details and move to Step 1 (which will auto-fetch suggestions)
      if (!dbType.trim()) {
        setError('Database type is required')
        return
      }
      if (!/^[A-Z0-9_]+$/.test(dbType.toUpperCase())) {
        setError('Database type must contain only letters, numbers, and underscores')
        return
      }
      if (dbType.length < 2) {
        setError('Database type must be at least 2 characters long')
        return
      }
      if (dbType.length > 30) {
        setError('Database type must not exceed 30 characters')
        return
      }
      if (!dbDesc.trim()) {
        setError('Database description is required')
        return
      }
      setActiveStep((prev) => prev + 1)
    } else if (activeStep === 1) {
      // This step is now handled by useEffect, but keep as fallback
      try {
        const data = await getDatatypeSuggestions(dbType, true)
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestions(data.suggestions)
          setSelectedSuggestions(data.suggestions.map((_, idx) => idx))
          setActiveStep((prev) => prev + 1)
        } else {
          setError('No suggestions found for this database type')
        }
      } catch (err) {
        setError(err.message || 'Failed to get suggestions. Please try again.')
      }
    } else if (activeStep === 2) {
      // Review suggestions - just move to next
      setActiveStep((prev) => prev + 1)
    } else if (activeStep === 3) {
      // Confirm and create
      await handleCreateDatabase()
    }
  }

  const handleCreateDatabase = async () => {
    try {
      // Step 1: Add database
      console.log(`[DatabaseWizard] Adding database: ${dbType}`)
      const dbResult = await addSupportedDatabase(dbType, dbDesc)
      console.log(`[DatabaseWizard] Add database response:`, dbResult)
      
      if (dbResult.status !== 'success') {
        const errorMsg = dbResult.detail || dbResult.message || 'Failed to create database'
        console.error(`[DatabaseWizard] Add database failed:`, errorMsg)
        setError(errorMsg)
        return
      }

      // Step 2: Clone datatypes
      console.log(`[DatabaseWizard] Cloning datatypes for: ${dbType}`)
      const cloneResult = await cloneDatatypes(dbType)
      console.log(`[DatabaseWizard] Clone datatypes response:`, cloneResult)
      
      if (cloneResult.status !== 'success') {
        const errorMsg = cloneResult.detail || cloneResult.message || 'Database created but failed to clone datatypes'
        console.error(`[DatabaseWizard] Clone datatypes failed:`, errorMsg)
        setError(errorMsg)
        return
      }

      console.log(`[DatabaseWizard] Success! Database created and datatypes cloned.`)
      setSuccess(true)
      setActiveStep((prev) => prev + 1)
      onSuccess()
    } catch (err) {
      console.error(`[DatabaseWizard] Exception in handleCreateDatabase:`, err)
      // Error message is already extracted and set by the hook
      // But if it comes through catch, display it again for clarity
      if (!error) {
        const errorMsg = err.message || 'Failed to create database. Please check the database name and try again.'
        console.error(`[DatabaseWizard] Setting error:`, errorMsg)
        setError(errorMsg)
      }
    }
  }

  const handleSuggestionToggle = (index) => {
    setSelectedSuggestions((prev) => {
      if (prev.includes(index)) {
        return prev.filter((i) => i !== index)
      } else {
        return [...prev, index]
      }
    })
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Database Setup Wizard</DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Step 1: Database Details */}
        {activeStep === 0 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>
              Enter the details for the new database type
            </Typography>
            <TextField
              fullWidth
              label="Database Type"
              placeholder="e.g., SNOWFLAKE, BIGQUERY, REDSHIFT"
              value={dbType}
              onChange={(e) => {
                setDbType(e.target.value.toUpperCase())
                setError('')
              }}
              margin="normal"
              required
              helperText="2-30 characters, letters/numbers/underscores only"
            />
            <TextField
              fullWidth
              label="Description"
              placeholder="Brief description of the database (required)"
              value={dbDesc}
              onChange={(e) => {
                setDbDesc(e.target.value)
                setError('')
              }}
              multiline
              rows={3}
              margin="normal"
              required
            />
          </Box>
        )}

        {/* Step 2: Getting Suggestions */}
        {activeStep === 1 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>
              Fetching suggestions for {dbType}...
            </Typography>
            <CircularProgress />
          </Box>
        )}

        {/* Step 3: Review Suggestions */}
        {activeStep === 2 && (
          <Box>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>
              Review suggested datatypes ({selectedSuggestions.length} selected)
            </Typography>
            <TableContainer
              component={Paper}
              sx={{
                maxHeight: 400,
                backgroundColor: theme.palette.mode === 'dark'
                  ? theme.palette.grey[900]
                  : theme.palette.background.paper,
              }}
            >
              <Table stickyHeader>
                <TableHead>
                  <TableRow sx={{ backgroundColor: theme.palette.action.hover }}>
                    <TableCell sx={{ width: '50px', textAlign: 'center' }}>
                      <strong>Select</strong>
                    </TableCell>
                    <TableCell sx={{ width: '120px' }}>
                      <strong>Type</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Code</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Description</strong>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {suggestions.map((suggestion, idx) => (
                    <TableRow
                      key={idx}
                      sx={{
                        backgroundColor: selectedSuggestions.includes(idx)
                          ? theme.palette.action.selected
                          : 'transparent',
                        '&:hover': {
                          backgroundColor: theme.palette.action.hover,
                        },
                        cursor: 'pointer',
                      }}
                      onClick={() => handleSuggestionToggle(idx)}
                    >
                      <TableCell sx={{ textAlign: 'center' }}>
                        <Checkbox
                          checked={selectedSuggestions.includes(idx)}
                          onChange={() => handleSuggestionToggle(idx)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Datatype</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {suggestion.PRCD}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                          {suggestion.PRDESC || suggestion.REASON || suggestion.PRVAL || '-'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Step 4: Confirm & Create */}
        {activeStep === 3 && (
          <Box>
            {success ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                Database "{dbType}" created successfully with{' '}
                {suggestions.length} datatypes cloned!
              </Alert>
            ) : (
              <>
                <Typography variant="subtitle1" sx={{ mb: 2 }}>
                  Ready to create database
                </Typography>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Database Type: <strong>{dbType}</strong>
                  </Typography>
                  <Typography variant="body2">
                    Selected Datatypes: <strong>{selectedSuggestions.length}</strong>
                  </Typography>
                </Alert>
              </>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          {success ? 'Close' : 'Cancel'}
        </Button>
        {!success && (
          <>
            {activeStep > 0 && (
              <Button onClick={() => setActiveStep((prev) => prev - 1)}>
                Back
              </Button>
            )}
            <Button
              onClick={handleNextStep}
              variant="contained"
              disabled={loading || (activeStep === 0 && !dbType.trim())}
            >
              {loading ? (
                <CircularProgress size={24} />
              ) : activeStep === 3 ? (
                'Create'
              ) : (
                'Next'
              )}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  )
}
