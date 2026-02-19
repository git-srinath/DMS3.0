/**
 * DatatypeForm Component
 * Form for adding/editing datatypes with validation
 * Phase 2B: Datatypes Management
 */

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
} from '@mui/material'
import { useDatatypeAPI } from '../../hooks/useDatatypeAPI'

export default function DatatypeForm({
  open,
  onClose,
  onSubmit,
  initialData = null,
  selectedDatabase = null,
  existingDatatypes = [],
}) {
  const { updateDatatype, addDatatype, getImpactAnalysis, loading } = useDatatypeAPI()
  const [formData, setFormData] = useState({
    PRCD: '',
    DBTYP: '',
    PRDESC: '',
    NEW_PRVAL: '',
    REASON: '',
  })
  const [errors, setErrors] = useState({})
  const [showImpact, setShowImpact] = useState(false)
  const [impactData, setImpactData] = useState(null)
  const [confirmUpdate, setConfirmUpdate] = useState(false)

  useEffect(() => {
    if (initialData) {
      setFormData({
        PRCD: initialData.PRCD || '',
        DBTYP: initialData.DBTYP || selectedDatabase || '',
        PRDESC: initialData.PRDESC || '',
        NEW_PRVAL: initialData.NEW_PRVAL || initialData.PRVAL || '',
        REASON: '',
      })
    } else {
      setFormData({
        PRCD: '',
        DBTYP: selectedDatabase || '',
        PRDESC: '',
        NEW_PRVAL: '',
        REASON: '',
      })
    }
    setErrors({})
    setShowImpact(false)
    setConfirmUpdate(false)
  }, [open, initialData, selectedDatabase])

  const validateForm = () => {
    const newErrors = {}
    if (!formData.PRCD?.trim()) newErrors.PRCD = 'Parameter code is required'
    if (!formData.DBTYP?.trim()) newErrors.DBTYP = 'Database type is required'
    if (!formData.NEW_PRVAL?.trim()) newErrors.NEW_PRVAL = 'Datatype value is required'

    if (!initialData) {
      const prcdUpper = formData.PRCD?.trim().toUpperCase()
      const dbtypUpper = formData.DBTYP?.trim().toUpperCase()
      const exists = (existingDatatypes || []).some(
        (dt) =>
          (dt.PRCD || '').trim().toUpperCase() === prcdUpper &&
          (dt.DBTYP || '').trim().toUpperCase() === dbtypUpper
      )

      if (exists) {
        newErrors.PRCD = `Datatype ${formData.PRCD} already exists for ${formData.DBTYP}`
      }
    }

    return newErrors
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: '',
      }))
    }
  }

  const handleShowImpact = async () => {
    const newErrors = validateForm()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    try {
      const impact = await getImpactAnalysis(
        formData.PRCD,
        formData.NEW_PRVAL,
        formData.DBTYP
      )
      setImpactData(impact)
      setShowImpact(true)
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        submit: err.message || 'Failed to analyze impact',
      }))
    }
  }

  const handleSubmit = async () => {
    const newErrors = validateForm()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    try {
      const result = initialData
        ? await updateDatatype(
            formData.PRCD,
            formData.DBTYP,
            formData.NEW_PRVAL,
            formData.REASON
          )
        : await addDatatype(
            formData.PRCD,
            formData.DBTYP,
            formData.NEW_PRVAL,
            formData.PRDESC,
            formData.REASON
          )

      if (result.status === 'success' || result.status === 'warning') {
        onSubmit(result)
        onClose()
      } else {
        setErrors((prev) => ({
          ...prev,
          submit: result.detail || 'Failed to save datatype',
        }))
      }
    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        submit: err.message || 'Failed to update datatype',
      }))
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {initialData ? 'Edit Datatype' : 'Add New Datatype'}
      </DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        {errors.submit && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errors.submit}
          </Alert>
        )}

        {showImpact && impactData && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
              Impact Analysis:
            </Typography>
            <Typography variant="body2">
              This change affects {impactData.impact?.affected_mappings || 0} mappings,{' '}
              {impactData.impact?.affected_jobs || 0} jobs, and{' '}
              {impactData.impact?.affected_reports || 0} reports.
            </Typography>
            {impactData.recommendations && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {impactData.recommendations}
              </Typography>
            )}
            <FormControlLabel
              control={<Checkbox checked={confirmUpdate} onChange={(e) => setConfirmUpdate(e.target.checked)} />}
              label="I understand the impact and want to proceed"
              sx={{ mt: 1 }}
            />
          </Alert>
        )}

        <TextField
          fullWidth
          label="Parameter Code"
          name="PRCD"
          value={formData.PRCD}
          onChange={handleInputChange}
          error={!!errors.PRCD}
          helperText={errors.PRCD}
          disabled={!!initialData}
          margin="normal"
        />

        <TextField
          fullWidth
          label="Database Type"
          name="DBTYP"
          value={formData.DBTYP}
          onChange={handleInputChange}
          disabled
          helperText={errors.DBTYP || 'Datatype will be created for selected database'}
          error={!!errors.DBTYP}
          margin="normal"
        />

        {!initialData && (
          <TextField
            fullWidth
            label="Description (optional)"
            name="PRDESC"
            value={formData.PRDESC}
            onChange={handleInputChange}
            margin="normal"
          />
        )}

        <TextField
          fullWidth
          label="Datatype Value"
          name="NEW_PRVAL"
          value={formData.NEW_PRVAL}
          onChange={handleInputChange}
          error={!!errors.NEW_PRVAL}
          helperText={errors.NEW_PRVAL}
          margin="normal"
        />

        <TextField
          fullWidth
          label="Reason for Change (optional)"
          name="REASON"
          value={formData.REASON}
          onChange={handleInputChange}
          multiline
          rows={3}
          margin="normal"
        />

        {initialData && !showImpact && (
          <Button
            fullWidth
            variant="outlined"
            sx={{ mt: 2 }}
            onClick={handleShowImpact}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Show Impact'}
          </Button>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={
            loading ||
            (showImpact && impactData && !confirmUpdate) ||
            Object.keys(errors).length > 0
          }
        >
          {loading ? <CircularProgress size={24} /> : 'Save'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
