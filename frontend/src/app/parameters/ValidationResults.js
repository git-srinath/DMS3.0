/**
 * ValidationResults Component
 * Display datatype validation results and remediation suggestions
 * Phase 2B: Datatypes Management
 */

import { useState } from 'react'
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Alert,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { useDatatypeAPI } from '../../hooks/useDatatypeAPI'

export default function ValidationResults({ selectedDatabase, onRefresh }) {
  const { validateAllMappings, loading } = useDatatypeAPI()
  const [validationResult, setValidationResult] = useState(null)
  const [showDetails, setShowDetails] = useState(false)

  const handleValidate = async () => {
    if (!selectedDatabase) {
      setValidationResult({
        status: 'error',
        detail: 'Please select a database to validate',
        database: 'None',
      })
      return
    }

    try {
      console.log(`[ValidationResults] Starting validation for: ${selectedDatabase}`)
      const result = await validateAllMappings(selectedDatabase)
      console.log(`[ValidationResults] Validation result:`, result)
      setValidationResult(result)
    } catch (err) {
      console.error(`[ValidationResults] Validation error:`, err)
      setValidationResult({
        status: 'error',
        detail: err.message || 'Validation failed',
        database: selectedDatabase,
        is404: err.originalError?.response?.status === 404,
      })
    }
  }

  if (!validationResult) {
    return (
      <Card>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            Validate all mappings for {selectedDatabase}
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
            Check that all datatype definitions are compatible with the selected
            database
          </Typography>
        </CardContent>
        <CardActions>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} /> : <CheckCircleIcon />}
            onClick={handleValidate}
            disabled={loading || !selectedDatabase}
            fullWidth
          >
            Run Validation
          </Button>
        </CardActions>
      </Card>
    )
  }

  const isValid = validationResult.status === 'success' && validationResult.valid_count > 0
  const hasErrors = validationResult.status === 'error' || validationResult.invalid_count > 0
  const hasWarnings = validationResult.warnings && validationResult.warnings.length > 0

  return (
    <>
      <Card>
        <CardContent>
          {/* Status Alert */}
          {isValid && (
            <Alert severity="success" sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon />
                <Typography>
                  All {validationResult.valid_count} mapping(s) are valid
                </Typography>
              </Box>
            </Alert>
          )}

          {hasErrors && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                <ErrorIcon />
                <Box sx={{ flex: 1 }}>
                  <Typography sx={{ fontWeight: 'bold', mb: 1 }}>
                    {validationResult.invalid_count
                      ? `${validationResult.invalid_count} mapping(s) have errors`
                      : 'Validation Error'}
                  </Typography>
                  {validationResult.detail && (
                    <Typography
                      variant="body2"
                      component="div"
                      sx={{ whiteSpace: 'pre-line' }}
                    >
                      {validationResult.detail}
                    </Typography>
                  )}
                  {validationResult.is404 && (
                    <Box
                      sx={{
                        mt: 2,
                        p: 1,
                        bgcolor: 'action.hover',
                        borderRadius: 1,
                      }}
                    >
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                        Troubleshooting Steps:
                      </Typography>
                      <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                        • Check that datatypes exist for {selectedDatabase}
                        <br />
                        • Verify backend server is running
                        <br />
                        • Try validating a different database
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            </Alert>
          )}

          {hasWarnings && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <WarningIcon />
                <Typography>
                  {validationResult.warnings.length} warning(s)
                </Typography>
              </Box>
              <Box sx={{ mt: 1 }}>
                {validationResult.warnings.map((warning, idx) => (
                  <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>
                    • {warning}
                  </Typography>
                ))}
              </Box>
            </Alert>
          )}

          {/* Summary Stats */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
              Validation Summary
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip
                icon={<CheckCircleIcon />}
                label={`Valid: ${validationResult.valid_count || 0}`}
                color="success"
                variant="outlined"
              />
              {validationResult.invalid_count > 0 && (
                <Chip
                  icon={<ErrorIcon />}
                  label={`Invalid: ${validationResult.invalid_count}`}
                  color="error"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>

          {/* Invalid Details */}
          {validationResult.invalid_details && validationResult.invalid_details.length > 0 && (
            <Box>
              <Button
                variant="text"
                onClick={() => setShowDetails(!showDetails)}
                sx={{ mb: 1 }}
              >
                {showDetails ? 'Hide' : 'Show'} Error Details
              </Button>
              {showDetails && (
                <TableContainer component={Paper} sx={{ mt: 1 }}>
                  <Table size="small">
                    <TableHead
                      sx={{
                        backgroundColor: (theme) =>
                          theme.palette.mode === 'dark'
                            ? 'rgba(239, 68, 68, 0.2)'
                            : '#fee',
                      }}
                    >
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold' }}>Component</TableCell>
                        <TableCell sx={{ fontWeight: 'bold' }}>Error</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {validationResult.invalid_details.map((detail, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{detail.component}</TableCell>
                          <TableCell>
                            <Typography variant="body2" color="error">
                              {detail.error}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          )}
        </CardContent>

        <CardActions>
          <Button
            startIcon={<RefreshIcon />}
            onClick={handleValidate}
            disabled={loading}
          >
            Re-validate
          </Button>
          {isValid && (
            <Button variant="contained" color="success">
              Ready to Deploy
            </Button>
          )}
        </CardActions>
      </Card>
    </>
  )
}
