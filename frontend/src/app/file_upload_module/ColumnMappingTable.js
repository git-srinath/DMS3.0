'use client'

import React from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Paper,
  Select,
  MenuItem,
  Box,
  IconButton,
  Checkbox,
  Tooltip,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import { alpha, useTheme as useMuiTheme } from '@mui/material/styles'
import { Delete as DeleteIcon, MoreVert as MoreVertIcon, Info as InfoIcon } from '@mui/icons-material'

const ColumnMappingTable = ({
  columnMappings,
  setColumnMappings,
  dataTypes,
  darkMode,
  tableExists = false,
  onDeleteRow,
}) => {
  const muiTheme = useMuiTheme()
  const [formulaHelpOpen, setFormulaHelpOpen] = React.useState(false)

  const handleChange = (index, field, value) => {
    setColumnMappings((prev) => {
      const copy = [...prev]
      copy[index] = { ...copy[index], [field]: value }
      return copy
    })
  }

  return (
    <Box sx={{ mt: 2 }}>
      {tableExists && (
        <Box
          sx={{
            mb: 2,
            p: 1.5,
            borderRadius: 1,
            backgroundColor: darkMode
              ? alpha(muiTheme.palette.warning.main, 0.15)
              : alpha(muiTheme.palette.warning.main, 0.1),
            border: `1px solid ${alpha(muiTheme.palette.warning.main, 0.3)}`,
          }}
        >
          <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon fontSize="small" color="warning" />
            <strong>Table Already Exists:</strong> Column structure fields (Target Column, Data Type, Primary Key, Required, Sequence) are disabled to prevent changes to the existing table structure.
          </Typography>
        </Box>
      )}
      <TableContainer
        component={Paper}
        sx={{
          backgroundColor: darkMode ? alpha(muiTheme.palette.background.paper, 0.6) : '#fff',
        }}
      >
        <Table size="small">
          <TableHead>
              <TableRow>
                <TableCell>Seq</TableCell>
                <TableCell>Source Column</TableCell>
                <TableCell>Target Column</TableCell>
                <TableCell>Data Type</TableCell>
                <TableCell>Primary Key</TableCell>
                <TableCell>Required</TableCell>
                <TableCell>Default Value</TableCell>
                <TableCell>Use Formula</TableCell>
                <TableCell>Formula</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
          </TableHead>
          <TableBody>
            {columnMappings.map((col, idx) => {
              const isAuditColumn = col.isaudit === 'Y' || col.isaudit === true
              const auditColumnNames = ['CRTDBY', 'CRTDDT', 'UPDTBY', 'UPDTDT']
              const isDefaultAudit = isAuditColumn && auditColumnNames.includes((col.trgclnm || '').toUpperCase())
              
              return (
              <TableRow key={col.id || `${col.trgclnm || col.srcclnm || idx}-${idx}`}>
                <TableCell width={50}>
                  <TextField
                    size="small"
                    type="number"
                    value={col.excseq ?? (idx + 1)}
                    onChange={(e) => handleChange(idx, 'excseq', Number(e.target.value) || idx + 1)}
                    inputProps={{ min: 1, step: 1 }}
                    sx={{ width: 70 }}
                    disabled={isDefaultAudit || tableExists}
                  />
                </TableCell>
                <TableCell width={180}>
                  <TextField
                    size="small"
                    value={col.srcclnm || col.trgclnm || ''}
                    onChange={(e) => handleChange(idx, 'srcclnm', e.target.value)}
                    placeholder="Source column"
                    disabled={isDefaultAudit}
                  />
                </TableCell>
                <TableCell width={180}>
                  <TextField
                    size="small"
                    value={col.trgclnm || col.srcclnm || ''}
                    onChange={(e) => handleChange(idx, 'trgclnm', e.target.value)}
                    placeholder="Target column"
                    disabled={isDefaultAudit || tableExists}
                    sx={{
                      ...((isDefaultAudit || tableExists) && {
                        backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                      }),
                    }}
                  />
                </TableCell>
                <TableCell width={160}>
                  <Select
                    size="small"
                    fullWidth
                    value={col.trgcldtyp || ''}
                    onChange={(e) => handleChange(idx, 'trgcldtyp', e.target.value)}
                    displayEmpty
                    disabled={isDefaultAudit || tableExists}
                    sx={{
                      ...((isDefaultAudit || tableExists) && {
                        backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                      }),
                    }}
                  >
                    <MenuItem value="">
                      <em>Select type</em>
                    </MenuItem>
                    {dataTypes.map((dt) => (
                      <MenuItem key={dt.prcd || dt.PRCD} value={dt.prcd || dt.PRCD}>
                        {dt.prcd || dt.PRCD}
                      </MenuItem>
                    ))}
                  </Select>
                </TableCell>
                <TableCell width={120}>
                  <IconButton
                    size="small"
                    onClick={() =>
                      handleChange(
                        idx,
                        'trgkyflg',
                        col.trgkyflg === 'Y' || col.trgkyflg === true ? 'N' : 'Y'
                      )
                    }
                    disabled={isDefaultAudit || tableExists}
                    sx={{
                      ...((isDefaultAudit || tableExists) && {
                        opacity: 0.5,
                        cursor: 'not-allowed',
                      }),
                    }}
                  >
                    {col.trgkyflg === 'Y' || col.trgkyflg === true ? '✓' : '○'}
                  </IconButton>
                </TableCell>
                <TableCell width={120}>
                  <IconButton
                    size="small"
                    onClick={() =>
                      handleChange(
                        idx,
                        'isrqrd',
                        col.isrqrd === 'Y' || col.isrqrd === true ? 'N' : 'Y'
                      )
                    }
                    disabled={isDefaultAudit || tableExists}
                    sx={{
                      ...((isDefaultAudit || tableExists) && {
                        opacity: 0.5,
                        cursor: 'not-allowed',
                      }),
                    }}
                  >
                    {col.isrqrd === 'Y' || col.isrqrd === true ? '✓' : '○'}
                  </IconButton>
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    value={col.dfltval || ''}
                    onChange={(e) => handleChange(idx, 'dfltval', e.target.value)}
                    placeholder="Default value"
                    disabled={isDefaultAudit}
                    sx={{
                      ...(isDefaultAudit && {
                        backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                      }),
                    }}
                  />
                </TableCell>
                <TableCell width={100}>
                  <Tooltip title="Enable formula/derivation logic for this column">
                    <Checkbox
                      size="small"
                      checked={col.drvlgcflg === 'Y' || col.drvlgcflg === true}
                      onChange={(e) => handleChange(idx, 'drvlgcflg', e.target.checked ? 'Y' : 'N')}
                      disabled={isDefaultAudit}
                    />
                  </Tooltip>
                </TableCell>
                <TableCell width={300}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
                    <TextField
                      size="small"
                      fullWidth
                      multiline
                      maxRows={3}
                      value={col.drvlgc || ''}
                      onChange={(e) => handleChange(idx, 'drvlgc', e.target.value)}
                      placeholder="e.g., COL1 + COL2, CONCAT(COL1, '-', COL2)"
                      disabled={isDefaultAudit || !(col.drvlgcflg === 'Y' || col.drvlgcflg === true)}
                      sx={{
                        flex: 1,
                        ...(isDefaultAudit && {
                          backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                        }),
                        '& .MuiInputBase-input.Mui-disabled': {
                          WebkitTextFillColor: darkMode 
                            ? 'rgba(255, 255, 255, 0.3)' 
                            : 'rgba(0, 0, 0, 0.3)',
                          backgroundColor: darkMode 
                            ? 'rgba(255, 255, 255, 0.02)' 
                            : 'rgba(0, 0, 0, 0.02)',
                        },
                      }}
                    />
                    <Tooltip title="Formula syntax help">
                      <IconButton
                        size="small"
                        onClick={() => setFormulaHelpOpen(true)}
                        sx={{ mt: 0.5 }}
                        disabled={!(col.drvlgcflg === 'Y' || col.drvlgcflg === true)}
                      >
                        <MoreVertIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
                <TableCell align="right">
                  {isDefaultAudit ? (
                    <Tooltip title="Audit columns cannot be removed">
                      <IconButton
                        size="small"
                        disabled
                        sx={{ opacity: 0.3 }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  ) : (
                    <Tooltip title={tableExists ? "Cannot delete columns when table exists" : "Delete row"}>
                      <IconButton
                        size="small"
                        onClick={() => onDeleteRow ? onDeleteRow(idx) : setColumnMappings((prev) => prev.filter((_, i) => i !== idx))}
                        color="error"
                        disabled={tableExists}
                        sx={{
                          ...(tableExists && {
                            opacity: 0.5,
                            cursor: 'not-allowed',
                          }),
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            )})}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Formula Help Dialog */}
      <Dialog
        open={formulaHelpOpen}
        onClose={() => setFormulaHelpOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            backgroundColor: darkMode ? muiTheme.palette.background.paper : '#fff',
          },
        }}
      >
        <DialogTitle>
          <Typography variant="h6" component="div">
            Formula Syntax Guide
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            Python-based syntax that works with all databases
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
              📊 Arithmetic Operations
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Addition" 
                  secondary="COL1 + COL2"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Subtraction" 
                  secondary="COL1 - COL2"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Multiplication" 
                  secondary="COL1 * COL2"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Division" 
                  secondary="COL1 / COL2"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Complex Expression" 
                  secondary="COL1 * COL2 - COL3 / 2"
                />
              </ListItem>
            </List>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
              🔢 Number Functions
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Round" 
                  secondary="ROUND(COL1, 2) - Round to 2 decimal places"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Absolute Value" 
                  secondary="ABS(COL1)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Coalesce (First Non-Null)" 
                  secondary="COALESCE(COL1, COL2, 0) - Returns first non-null value"
                />
              </ListItem>
            </List>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
              📝 String Functions
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Concatenate" 
                  secondary="CONCAT(COL1, '-', COL2) - Join strings"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Upper Case" 
                  secondary="UPPER(COL1)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Lower Case" 
                  secondary="LOWER(COL1)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Length" 
                  secondary="LEN(COL1) - Get string length"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Split" 
                  secondary="SPLIT(COL1, '-', 0) - Split by delimiter, get index"
                />
              </ListItem>
            </List>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
              📅 Date Functions (Coming Soon)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              Date formatting and arithmetic functions will be available in future updates.
            </Typography>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
              💡 Usage Tips
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Column References" 
                  secondary="Use column names directly (e.g., COL1, COL2, AMOUNT, DATE)"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Nested Functions" 
                  secondary="ROUND(COL1 * 1.1, 2) - Functions can be nested"
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Null Handling" 
                  secondary="Use COALESCE to handle null values: COALESCE(COL1, 0)"
                />
              </ListItem>
            </List>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFormulaHelpOpen(false)} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ColumnMappingTable

