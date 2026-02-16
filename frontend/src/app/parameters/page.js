'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { format } from 'date-fns'
// Import Material UI components
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  MenuItem,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  IconButton,
  CircularProgress,
  Chip,
  useTheme,
  Tooltip,
  Fade,
  alpha,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  InputAdornment,
} from '@mui/material'
import {
  Add as AddIcon,
  Cancel as CancelIcon,
  FilterList as FilterListIcon,
  Close as CloseIcon,
  Save as SaveIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from '@mui/icons-material'

export default function ParameterPage() {
  const theme = useTheme()
  const [parameters, setParameters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [types, setTypes] = useState([])

  // Form state
  const [newParameter, setNewParameter] = useState({
    PRTYP: '',
    PRCD: '',
    PRDESC: '',
    PRVAL: '',
  })

  useEffect(() => {
    fetchParameters()
  }, [])

  const fetchParameters = async () => {
    try {
      setLoading(true)
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/mapping/parameter_mapping`
      )
      const sortedData = response.data.sort(
        (a, b) => new Date(b.PRRECCRDT) - new Date(a.PRRECCRDT)
      )
      setParameters(sortedData)

      const uniqueTypes = [
        ...new Set(sortedData.map((param) => param.PRTYP)),
      ]
      setTypes(uniqueTypes)

      setLoading(false)
    } catch (err) {
      setError('Failed to load parameters. Please try again later.')
      setLoading(false)
    }
  }

  const handleAddParameter = async (e) => {
    e.preventDefault()
    if (loading) return
    try {
      setLoading(true)
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/mapping/parameter_add`,
        newParameter
      )

      setNewParameter({ PRTYP: '', PRCD: '', PRDESC: '', PRVAL: '' })
      setShowAddForm(false)
      // Refresh data and handle loading state
      fetchParameters()
    } catch (err) {
      setError('Failed to add parameter. Please try again.')
      setLoading(false) // Keep loading false on error
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setNewParameter((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
    } catch (err) {
      return String(dateString)
    }
  }

  const filteredParameters = parameters.filter((param) => {
    const lowercasedQuery = searchQuery.toLowerCase()

    const typeMatch = !filterType || param.PRTYP === filterType

    const searchMatch =
      !searchQuery ||
      param.PRTYP.toLowerCase().includes(lowercasedQuery) ||
      param.PRCD.toLowerCase().includes(lowercasedQuery) ||
      param.PRDESC.toLowerCase().includes(lowercasedQuery) ||
      param.PRVAL.toLowerCase().includes(lowercasedQuery)

    return typeMatch && searchMatch
  })

  return (
    <Box
      sx={{
        height: 'calc(100vh - 64px)', // Adjust based on your nav/header height
        display: 'flex',
        flexDirection: 'column',
        p: 2.5,
        backgroundColor:
          theme.palette.mode === 'dark'
            ? alpha(theme.palette.background.default, 0.5)
            : theme.palette.grey[50],
        gap: 2,
      }}
    >
      {/* --- Top Controls --- */}
      <Box
        sx={{
          flexShrink: 0,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1.5,
        }}
      >
        <Typography variant="h5" fontWeight={700}>
          System Parameters
        </Typography>
        <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
          <TextField
            size="small"
            variant="outlined"
            label="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search..."
            sx={{
              width: 250,
              backgroundColor: theme.palette.background.paper,
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            size="small"
            label="Filter by Type"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            sx={{
              minWidth: 180,
              backgroundColor: theme.palette.background.paper,
            }}
          >
            <MenuItem value="">
              <em>All Types</em>
            </MenuItem>
            {types.map((type) => (
              <MenuItem key={type} value={type}>
                {type}
              </MenuItem>
            ))}
          </TextField>
          <Tooltip title={loading ? 'Refreshing...' : 'Refresh Data'} arrow>
            <span>
              <IconButton
                color="primary"
                onClick={fetchParameters}
                disabled={loading}
              >
                <RefreshIcon />
              </IconButton>
            </span>
          </Tooltip>
          <Button
            variant={showAddForm ? 'outlined' : 'contained'}
            startIcon={showAddForm ? <CancelIcon /> : <AddIcon />}
            onClick={() => setShowAddForm(!showAddForm)}
            color={'primary'}
          >
            {'Add Parameter'}
          </Button>
        </Box>
      </Box>

      {/* --- Add Parameter Dialog --- */}
      <Dialog
        open={showAddForm}
        onClose={() => setShowAddForm(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ component: 'form', onSubmit: handleAddParameter }}
      >
        <DialogTitle sx={{ fontWeight: 'bold' }}>
          Add New System Parameter
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                autoFocus
                margin="dense"
                name="PRTYP"
                label="Type"
                type="text"
                fullWidth
                variant="outlined"
                value={newParameter.PRTYP}
                onChange={handleChange}
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                margin="dense"
                name="PRCD"
                label="Code"
                type="text"
                fullWidth
                variant="outlined"
                value={newParameter.PRCD}
                onChange={handleChange}
                required
                size="small"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                margin="dense"
                name="PRDESC"
                label="Description"
                type="text"
                fullWidth
                variant="outlined"
                value={newParameter.PRDESC}
                onChange={handleChange}
                required
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                margin="dense"
                name="PRVAL"
                label="Value"
                type="text"
                fullWidth
                variant="outlined"
                value={newParameter.PRVAL}
                onChange={handleChange}
                required
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: '16px 24px' }}>
          <Button onClick={() => setShowAddForm(false)} color="inherit">
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading}
            startIcon={
              loading ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />
            }
          >
            Save Parameter
          </Button>
        </DialogActions>
      </Dialog>

      {error && (
        <Alert
          severity="error"
          onClose={() => setError(null)}
          sx={{ flexShrink: 0 }}
        >
          {error}
        </Alert>
      )}

      {/* --- Main Table --- */}
      <Paper
        elevation={0}
        sx={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          border: '1px solid',
          borderColor: theme.palette.divider,
          borderRadius: 2,
        }}
      >
        {loading && !parameters.length ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer sx={{ flex: 1, overflow: 'auto' }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Type</TableCell>
                  <TableCell>Code</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Value</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Updated</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredParameters.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                      <InfoIcon color="action" sx={{ mb: 1 }} />
                      <Typography color="text.secondary">
                        {parameters.length === 0
                          ? 'No parameters found.'
                          : 'No parameters match the filter or search.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredParameters.map((param, index) => (
                    <TableRow
                      key={index}
                      hover
                      sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                    >
                      <TableCell>
                        <Chip
                          label={param.PRTYP}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>
                        {param.PRCD}
                      </TableCell>
                      <TableCell>{param.PRDESC}</TableCell>
                      <TableCell>
                        <Box
                          component="span"
                          sx={{
                            fontFamily: 'monospace',
                            backgroundColor: alpha(
                              theme.palette.action.hover,
                              0.5
                            ),
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                          }}
                        >
                          {param.PRVAL}
                        </Box>
                      </TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>
                        {formatDate(param.PRRECCRDT)}
                      </TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>
                        {formatDate(param.PRRECUPDT)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  )
}

