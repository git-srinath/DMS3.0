/**
 * UsageDashboard Component
 * Display datatype usage statistics and analytics
 * Phase 2B: Datatypes Management
 */

import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material'
import { useDatatypeAPI } from '../../hooks/useDatatypeAPI'

export default function UsageDashboard({ selectedDatabase = null }) {
  const { getDatatypeUsageStats, loading, error } = useDatatypeAPI()
  const [stats, setStats] = useState(null)

  useEffect(() => {
    loadStats()
  }, [selectedDatabase])

  const loadStats = async () => {
    try {
      const data = await getDatatypeUsageStats(selectedDatabase)
      setStats(data)
    } catch (err) {
      // Error is handled by the hook
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  if (!stats) {
    return <Alert severity="info">No statistics available</Alert>
  }

  return (
    <Box>
      {/* Key Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Datatypes
              </Typography>
              <Typography variant="h5">
                {stats.total_datatypes || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Databases Supported
              </Typography>
              <Typography variant="h5">
                {stats.by_database ? Object.keys(stats.by_database).length : 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Most Used Type
              </Typography>
              <Typography variant="h6">
                {stats.most_used ? stats.most_used[0]?.type : 'N/A'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {stats.most_used ? stats.most_used[0]?.count : 0} uses
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Unused Datatypes
              </Typography>
              <Typography variant="h5">
                {stats.unused_datatypes ? stats.unused_datatypes.length : 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* By Database Breakdown */}
      {stats.by_database && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Datatypes by Database
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.entries(stats.by_database).map(([dbtype, count]) => (
                <Chip
                  key={dbtype}
                  label={`${dbtype}: ${count}`}
                  color="primary"
                  variant="outlined"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Datatype Distribution */}
      {stats.by_type && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Datatype Distribution
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow
                    sx={{
                      backgroundColor: (theme) =>
                        theme.palette.mode === 'dark'
                          ? theme.palette.grey[800]
                          : theme.palette.grey[100],
                    }}
                  >
                    <TableCell sx={{ fontWeight: 'bold' }}>Datatype</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      Count
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                      Percentage
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(stats.by_type)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 10)
                    .map(([type, count]) => (
                      <TableRow key={type}>
                        <TableCell>{type}</TableCell>
                        <TableCell align="right">{count}</TableCell>
                        <TableCell align="right">
                          {stats.total_datatypes > 0
                            ? (
                                ((count / stats.total_datatypes) * 100).toFixed(
                                  1
                                )
                              ) + '%'
                            : 'N/A'}
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
            {stats.by_type && Object.keys(stats.by_type).length > 10 && (
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
                Showing top 10 of {Object.keys(stats.by_type).length} types
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Unused Datatypes */}
      {stats.unused_datatypes && stats.unused_datatypes.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Unused Datatypes ({stats.unused_datatypes.length})
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              These datatypes are defined but not used in any mappings. Consider
              removing them to reduce complexity.
            </Alert>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {stats.unused_datatypes.map((dtype) => (
                <Chip
                  key={`${dtype.PRCD}-${dtype.DBTYP}`}
                  label={`${dtype.PRCD} (${dtype.DBTYP})`}
                  onDelete={() => {}}
                  variant="outlined"
                  color="warning"
                />
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
