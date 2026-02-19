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
  Tabs,
  Tab,
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
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  Check as CheckIcon,
} from '@mui/icons-material'
import { useDatatypeAPI } from '../../hooks/useDatatypeAPI'
import DatatypeForm from './DatatypeForm'
import DatatypesTable from './DatatypesTable'
import DatabaseWizard from './DatabaseWizard'
import UsageDashboard from './UsageDashboard'
import ValidationResults from './ValidationResults'

export default function ParameterPage() {
  const theme = useTheme()
  const { getSupportedDatabases, getDatatypesForDatabase } = useDatatypeAPI()
  
  // Tab state
  const [currentTab, setCurrentTab] = useState(0)
  
  // Parameters tab state
  const [parameters, setParameters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [types, setTypes] = useState([])

  // Datatypes tab state
  const [databases, setDatabases] = useState([])
  const [selectedDatabase, setSelectedDatabase] = useState('')
  const [datatypes, setDatatypes] = useState([])
  const [datatypesLoading, setDatatypesLoading] = useState(false)
  const [datatypesError, setDatatypesError] = useState('')
  const [showDatatypeForm, setShowDatatypeForm] = useState(false)
  const [editingDatatype, setEditingDatatype] = useState(null)
  const [showWizard, setShowWizard] = useState(false)

  // Form state
  const [newParameter, setNewParameter] = useState({
    PRTYP: '',
    PRCD: '',
    PRDESC: '',
    PRVAL: '',
  })

  useEffect(() => {
    fetchParameters()
    loadDatabases()
  }, [])

  // Load databases for datatypes tab
  const loadDatabases = async () => {
    try {
      const data = await getSupportedDatabases()
      // Deduplicate by DBTYP
      const uniqueDatabases = Object.values(
        (data.databases || []).reduce((acc, db) => {
          if (!acc[db.DBTYP]) {
            acc[db.DBTYP] = db
          }
          return acc
        }, {})
      )

      // Hide GENERIC in Datatypes Management UI
      const uiDatabases = uniqueDatabases.filter(
        (db) => (db.DBTYP || '').toUpperCase() !== 'GENERIC'
      )

      setDatabases(uiDatabases)
      if (uiDatabases.length > 0) {
        setSelectedDatabase(uiDatabases[0].DBTYP)
      } else {
        setSelectedDatabase('')
      }
    } catch (err) {
      console.error('Failed to load databases:', err)
    }
  }

  // Load datatypes for selected database
  const loadDatatypes = async (dbtype) => {
    if (!dbtype) return
    setDatatypesLoading(true)
    setDatatypesError('')
    try {
      const data = await getDatatypesForDatabase(dbtype)
      // Filter out any invalid/incomplete records as a safety measure
      const validDatatypes = (data.datatypes || []).filter(dt =>
        dt.PRCD && dt.PRCD.trim() !== '' &&
        dt.DBTYP && dt.DBTYP.trim() !== ''
      )

      // Show only database-specific records in Datatypes Management (hide GENERIC fallback rows)
      const selectedDbUpper = (dbtype || '').toUpperCase()
      const dbSpecificDatatypes = validDatatypes.filter(
        (dt) => (dt.DBTYP || '').toUpperCase() === selectedDbUpper
      )

      console.log(`[loadDatatypes] Loaded ${dbSpecificDatatypes.length} records for ${dbtype}`)
      if (dbSpecificDatatypes.length < validDatatypes.length) {
        console.info(`[loadDatatypes] Hidden ${validDatatypes.length - dbSpecificDatatypes.length} GENERIC fallback records`)
      }
      setDatatypes(dbSpecificDatatypes)
    } catch (err) {
      setDatatypesError(err.message || 'Failed to load datatypes')
    } finally {
      setDatatypesLoading(false)
    }
  }

  // Handle database selection change
  const handleDatabaseChange = (event) => {
    const dbtype = event.target.value
    setSelectedDatabase(dbtype)
    loadDatatypes(dbtype)
  }

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

  // Handle datatype form actions
  const handleEditDatatype = (datatype) => {
    setEditingDatatype(datatype)
    setShowDatatypeForm(true)
  }

  const handleDeleteDatatype = () => {
    loadDatatypes(selectedDatabase)
  }

  const handleDatatypeFormSubmit = () => {
    loadDatatypes(selectedDatabase)
  }

  const handleWizardSuccess = () => {
    loadDatabases()
    loadDatatypes(selectedDatabase)
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

    // Filter out ALL datatypes from System Parameters
    // Datatypes should only be shown in Datatypes Management tab
    const isNotDatatype = param.PRTYP !== 'Datatype'

    return typeMatch && searchMatch && isNotDatatype
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
      {/* Error Alert */}
      {error && (
        <Alert
          severity="error"
          onClose={() => setError(null)}
          sx={{ flexShrink: 0 }}
        >
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ borderRadius: 2 }}>
        <Tabs
          value={currentTab}
          onChange={(e, value) => setCurrentTab(value)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            label="System Parameters"
            icon={<StorageIcon />}
            iconPosition="start"
          />
          <Tab
            label="Datatypes Management"
            icon={<DashboardIcon />}
            iconPosition="start"
          />
          <Tab
            label="Validation"
            icon={<CheckIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab 1: System Parameters */}
      {currentTab === 0 && (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
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
      )}

      {/* Tab 2: Datatypes Management */}
      {currentTab === 1 && (
        <Box 
          sx={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column', 
            gap: 2,
            overflow: 'auto'
          }}
        >
          {/* Database Selector */}
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <TextField
              select
              label="Select Database"
              value={selectedDatabase}
              onChange={handleDatabaseChange}
              sx={{ minWidth: 250 }}
              disabled={databases.length === 0}
            >
              {databases.map((db) => (
                <MenuItem key={db.DBTYP} value={db.DBTYP}>
                  {db.DBTYP} - {db.DBDESC || 'No description'}
                </MenuItem>
              ))}
            </TextField>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowWizard(true)}
            >
              Add Database
            </Button>

            <Button
              variant="outlined"
              onClick={() => loadDatatypes(selectedDatabase)}
              disabled={datatypesLoading || !selectedDatabase}
            >
              {datatypesLoading ? <CircularProgress size={24} /> : 'Refresh'}
            </Button>

            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditingDatatype(null)
                setShowDatatypeForm(true)
              }}
              disabled={!selectedDatabase}
            >
              Add Datatype
            </Button>
          </Box>

          {datatypesError && (
            <Alert severity="error" onClose={() => setDatatypesError('')}>
              {datatypesError}
            </Alert>
          )}

          {/* Datatypes Table - No extra container, just the table */}
          {datatypesLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <DatatypesTable
              datatypes={datatypes}
              selectedDatabase={selectedDatabase}
              onEdit={handleEditDatatype}
              onDelete={handleDeleteDatatype}
              onRefresh={() => loadDatatypes(selectedDatabase)}
            />
          )}
        </Box>
      )}

      {/* Tab 3: Validation */}
      {currentTab === 2 && (
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            select
            label="Select Database to Validate"
            value={selectedDatabase}
            onChange={handleDatabaseChange}
            sx={{ maxWidth: 300 }}
          >
            {databases.map((db) => (
              <MenuItem key={db.DBTYP} value={db.DBTYP}>
                {db.DBTYP}
              </MenuItem>
            ))}
          </TextField>
          {selectedDatabase ? (
            <ValidationResults
              selectedDatabase={selectedDatabase}
              onRefresh={() => {}}
            />
          ) : (
            <Alert severity="info">No active non-GENERIC databases available for validation.</Alert>
          )}
        </Box>
      )}

      {/* Datatype Form Dialog */}
      <DatatypeForm
        open={showDatatypeForm}
        onClose={() => {
          setShowDatatypeForm(false)
          setEditingDatatype(null)
        }}
        onSubmit={handleDatatypeFormSubmit}
        initialData={editingDatatype}
        selectedDatabase={selectedDatabase}
        existingDatatypes={datatypes}
      />

      {/* Database Wizard Dialog */}
      <DatabaseWizard
        open={showWizard}
        onClose={() => setShowWizard(false)}
        onSuccess={handleWizardSuccess}
      />
    </Box>
  )
}

