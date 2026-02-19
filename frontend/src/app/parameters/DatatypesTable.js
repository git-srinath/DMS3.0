/**
 * DatatypesTable Component
 * Display datatypes in a table with edit/delete actions
 * Phase 2B: Datatypes Management
 */

import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  CircularProgress,
  Box,
  Typography,
  Chip,
  useTheme,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Check as CheckIcon,
} from '@mui/icons-material'
import { useDatatypeAPI } from '../../hooks/useDatatypeAPI'

export default function DatatypesTable({
  datatypes,
  selectedDatabase,
  onEdit,
  onDelete,
  onRefresh,
}) {
  const theme = useTheme()
  const { removeDatatype, loading: apiLoading } = useDatatypeAPI()
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState(null)

  // Filter out invalid datatypes and set status='active' for all valid ones
  const validDatatypes = (datatypes || [])
    .filter(dt => 
      dt && dt.PRCD && dt.DBTYP && 
      typeof dt.PRCD === 'string' && dt.PRCD.trim() !== '' &&
      typeof dt.DBTYP === 'string' && dt.DBTYP.trim() !== ''
    )
    .map(dt => ({
      ...dt,
      status: dt.status || 'active' // Default to 'active' if not set
    }))

  const handleDeleteClick = (datatype) => {
    setDeleteConfirm(datatype)
    setDeleteError(null)
  }

  const handleConfirmDelete = async () => {
    if (!deleteConfirm) return

    setDeleting(true)
    try {
      const result = await removeDatatype(deleteConfirm.PRCD, deleteConfirm.DBTYP)

      if (result.status === 'success') {
        onDelete(deleteConfirm)
        setDeleteConfirm(null)
      } else if (result.status === 'error') {
        // Show the detailed reason from backend validation
        setDeleteError(
          result.reason || `Cannot delete: This datatype is referenced by ${result.blocking_references} usage(s). Please remove those references first.`
        )
      } else {
        setDeleteError(result.detail || 'Failed to delete datatype')
      }
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete datatype')
    } finally {
      setDeleting(false)
    }
  }

  if (!validDatatypes || validDatatypes.length === 0) {
    return (
      <Paper 
        sx={{ 
          p: 3, 
          textAlign: 'center',
          backgroundColor: 'transparent',
          backgroundImage: 'none',
        }}
      >
        <Typography color="textSecondary">
          No datatypes found for {selectedDatabase}
        </Typography>
      </Paper>
    )
  }

  return (
    <>
      <TableContainer 
        component={Paper}
        sx={{
          backgroundColor: 'transparent',
          backgroundImage: 'none',
          boxShadow: 'none',
          overflow: 'auto'
        }}
      >
        <Table 
          sx={{
            backgroundColor: 'transparent'
          }}
        >
          <TableHead
            sx={{
              backgroundColor: theme.palette.mode === 'dark'
                ? theme.palette.grey[800]
                : theme.palette.grey[100],
            }}
          >
            <TableRow>
              <TableCell
                align="left"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Parameter Code
              </TableCell>
              <TableCell
                align="left"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Description
              </TableCell>
              <TableCell
                align="left"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Database Type
              </TableCell>
              <TableCell
                align="left"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Datatype Value
              </TableCell>
              <TableCell
                align="left"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Created Date
              </TableCell>
              <TableCell
                align="left"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Updated Date
              </TableCell>
              <TableCell
                align="center"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Status
              </TableCell>
              <TableCell
                align="center"
                sx={{
                  fontWeight: 'bold',
                  color: theme.palette.text.primary,
                  borderBottom: `2px solid ${theme.palette.divider}`,
                }}
              >
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody 
            sx={{
              backgroundColor: 'transparent'
            }}
          >
            {validDatatypes.map((datatype) => (
              <TableRow
                key={`${datatype.PRCD}-${datatype.DBTYP}`}
                sx={{
                  backgroundColor: 'transparent',
                  '&:hover': {
                    backgroundColor: theme.palette.mode === 'dark'
                      ? theme.palette.action.hover
                      : theme.palette.grey[50],
                  },
                  '&:last-child td, &:last-child th': { border: 0 },
                }}
              >
                <TableCell align="left">
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 500, color: theme.palette.text.primary }}
                  >
                    {datatype.PRCD}
                  </Typography>
                </TableCell>
                <TableCell align="left">
                  <Typography
                    variant="body2"
                    sx={{ color: theme.palette.text.secondary }}
                  >
                    {datatype.PRDESC || '-'}
                  </Typography>
                </TableCell>
                <TableCell align="left">
                  <Chip label={datatype.DBTYP} size="small" variant="outlined" />
                </TableCell>
                <TableCell align="left">
                  <code
                    style={{
                      backgroundColor: theme.palette.mode === 'dark'
                        ? theme.palette.grey[800]
                        : theme.palette.grey[100],
                      color: theme.palette.text.primary,
                      padding: '4px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    {datatype.PRVAL || datatype.NEW_PRVAL}
                  </code>
                </TableCell>
                <TableCell align="left">
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {datatype.PRRECCRDT ? new Date(datatype.PRRECCRDT).toLocaleString() : '-'}
                  </Typography>
                </TableCell>
                <TableCell align="left">
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {datatype.PRRECUPDT ? new Date(datatype.PRRECUPDT).toLocaleString() : '-'}
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  {datatype.status === 'active' ? (
                    <Tooltip title="Active - Datatype is validated and ready to use">
                      <CheckIcon sx={{ color: 'green' }} />
                    </Tooltip>
                  ) : (
                    <Tooltip title="Warning - Datatype may need validation or has pending updates">
                      <WarningIcon sx={{ color: 'orange' }} />
                    </Tooltip>
                  )}
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="Edit datatype">
                    <IconButton
                      size="small"
                      onClick={() => onEdit(datatype)}
                      color="primary"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={datatype.DBTYP === 'GENERIC' ? 'GENERIC datatypes cannot be deleted (reference records)' : 'Delete datatype'}>
                    <span>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(datatype)}
                        color="error"
                        disabled={datatype.DBTYP === 'GENERIC'}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          {!deleteError && (
            <Typography>
              Are you sure you want to delete the datatype{' '}
              <strong>{deleteConfirm?.PRCD}</strong> for{' '}
              <strong>{deleteConfirm?.DBTYP}</strong>?
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setDeleteConfirm(null)}
            disabled={deleting}
          >
            Cancel
          </Button>
          {!deleteError && (
            <Button
              onClick={handleConfirmDelete}
              variant="contained"
              color="error"
              disabled={deleting}
            >
              {deleting ? <CircularProgress size={24} /> : 'Delete'}
            </Button>
          )}
          {deleteError && (
            <Button onClick={() => setDeleteConfirm(null)} variant="contained">
              Close
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  )
}
