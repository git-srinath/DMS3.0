"use client";

import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Box,
  Typography,
  Paper,
  Stack,
  Button,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Snackbar,
  Alert,
  Tooltip,
  Grid,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  TableContainer,
  LinearProgress,
  alpha,
  useTheme as useMuiTheme,
} from "@mui/material";
import {
  Refresh,
  FilterList,
  Clear,
  CheckCircleOutline,
  ErrorOutline,
  ChangeCircle,
  AddCircleOutline,
  DeleteSweep,
  SyncAlt,
  HelpOutline,
} from "@mui/icons-material";
import { useTheme } from "@/context/ThemeContext";
import { API_BASE_URL } from "@/app/config";

const FileUploadHistoryPage = () => {
  const { darkMode } = useTheme();
  const muiTheme = useMuiTheme();

  const [runs, setRuns] = useState([]);
  const [uploads, setUploads] = useState([]);
  const [connections, setConnections] = useState([]);
  const [selectedFlupldref, setSelectedFlupldref] = useState("");
  const [status, setStatus] = useState("");
  const [targetConnectionId, setTargetConnectionId] = useState("");
  const [loadMode, setLoadMode] = useState("");
  const [fileType, setFileType] = useState("");
  const [fileName, setFileName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(true); // Default to visible
  const [notification, setNotification] = useState({ open: false, message: "", severity: "info" });
  
  // Sorting state
  const [orderBy, setOrderBy] = useState("strttm");
  const [order, setOrder] = useState("desc");

  // Error dialog state
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [errorRows, setErrorRows] = useState([]);
  const [loadingErrors, setLoadingErrors] = useState(false);
  const [errorFilterCode, setErrorFilterCode] = useState("");

  const fetchUploads = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await axios.get(`${API_BASE_URL}/file-upload/get-all-uploads`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      setUploads(res.data.data || []);
    } catch (err) {
      showNotification("Failed to load file upload configurations", "error");
    }
  };

  const fetchConnections = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await axios.get(`${API_BASE_URL}/file-upload/get-connections`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      setConnections(res.data.data || []);
    } catch (err) {
      showNotification("Failed to load database connections", "error");
    }
  };

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams({ limit: limit.toString() });
      if (selectedFlupldref) params.append("flupldref", selectedFlupldref);
      if (status) params.append("status", status);
      if (targetConnectionId) params.append("target_connection_id", targetConnectionId);
      if (loadMode) params.append("load_mode", loadMode);
      if (fileType) params.append("file_type", fileType);
      if (fileName) params.append("file_name", fileName);
      if (startDate) params.append("start_date", startDate);
      const res = await axios.get(`${API_BASE_URL}/file-upload/runs?${params.toString()}`, {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      setRuns(res.data.data || []);
    } catch (err) {
      showNotification("Failed to load file upload runs", "error");
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setSelectedFlupldref("");
    setStatus("");
    setTargetConnectionId("");
    setLoadMode("");
    setFileType("");
    setFileName("");
    setStartDate("");
  };

  const hasActiveFilters = () => {
    return !!(selectedFlupldref || status || targetConnectionId || loadMode || fileType || fileName || startDate);
  };

  const showNotification = (message, severity = "info") => {
    setNotification({ open: true, message, severity });
  };

  const closeNotification = () => setNotification((prev) => ({ ...prev, open: false }));

  const getUploadName = (flupldref) => {
    const upload = uploads.find((u) => u.flupldref === flupldref);
    return upload ? upload.fluplddesc || upload.flupldref : flupldref;
  };

  const handleFailedCountClick = (run) => {
    if (run.rwsfld > 0) {
      setSelectedRun(run);
      setShowErrorDialog(true);
      setErrorRows([]);
      setErrorFilterCode("");
      // Fetch errors for this run
      fetchErrorRows(run.flupldref, run.runid, "");
    }
  };

  const fetchErrorRows = async (flupldref, runid, errorCode) => {
    if (!flupldref || !runid) {
      setErrorRows([]);
      return;
    }

    setLoadingErrors(true);
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams();
      params.append("runid", runid.toString());
      if (errorCode) {
        params.append("error_code", errorCode);
      }

      const response = await axios.get(
        `${API_BASE_URL}/file-upload/errors/${encodeURIComponent(flupldref)}?${params.toString()}`,
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.data?.success && Array.isArray(response.data.data)) {
        setErrorRows(response.data.data);
      } else {
        setErrorRows([]);
      }
    } catch (error) {
      console.error("Error fetching file upload errors:", error);
      showNotification("Failed to fetch error rows", "error");
      setErrorRows([]);
    } finally {
      setLoadingErrors(false);
    }
  };

  const formatDateTime = (dt) => {
    if (!dt) return "-";
    try {
      const d = new Date(dt);
      return d.toLocaleString();
    } catch {
      return dt;
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return "-";
    try {
      const start = new Date(startTime);
      const end = new Date(endTime);
      const diffMs = end - start;
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHour = Math.floor(diffMin / 60);
      
      if (diffHour > 0) {
        return `${diffHour}h ${diffMin % 60}m ${diffSec % 60}s`;
      } else if (diffMin > 0) {
        return `${diffMin}m ${diffSec % 60}s`;
      } else {
        return `${diffSec}s`;
      }
    } catch {
      return "-";
    }
  };

  useEffect(() => {
    fetchUploads();
    fetchConnections();
    // Check for pre-filter from URL params
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const flupldrefParam = urlParams.get("flupldref");
      if (flupldrefParam) {
        setSelectedFlupldref(flupldrefParam);
        setShowFilters(true);
      }
    }
  }, []);

  useEffect(() => {
    fetchRuns();
  }, [selectedFlupldref, status, targetConnectionId, loadMode, fileType, fileName, startDate, limit]);

  // Get unique file types from uploads
  const fileTypes = [...new Set(uploads.map((u) => u.fltyp).filter(Boolean))].sort();

  // Sorting functions
  const handleSort = (property) => {
    const isAsc = orderBy === property && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(property);
  };

  const getSortedRuns = () => {
    if (!orderBy) return runs;
    
    return [...runs].sort((a, b) => {
      let aVal = a[orderBy];
      let bVal = b[orderBy];
      
      // Handle null/undefined values
      if (aVal == null) aVal = "";
      if (bVal == null) bVal = "";
      
      // Handle dates
      if (orderBy === "strttm" || orderBy === "ndtm") {
        aVal = aVal ? new Date(aVal).getTime() : 0;
        bVal = bVal ? new Date(bVal).getTime() : 0;
      }
      
      // Handle numbers
      if (orderBy === "runid" || orderBy === "rwsprcssd" || orderBy === "rwsstccssfl" || orderBy === "rwsfld") {
        aVal = Number(aVal) || 0;
        bVal = Number(bVal) || 0;
      }
      
      // Handle strings (case-insensitive)
      if (typeof aVal === "string") {
        aVal = aVal.toLowerCase();
      }
      if (typeof bVal === "string") {
        bVal = bVal.toLowerCase();
      }
      
      if (aVal < bVal) {
        return order === "asc" ? -1 : 1;
      }
      if (aVal > bVal) {
        return order === "asc" ? 1 : -1;
      }
      return 0;
    });
  };

  const SortableTableCell = ({ children, property, ...props }) => {
    const isActive = orderBy === property;
    return (
      <TableCell
        {...props}
        sx={{
          cursor: "pointer",
          userSelect: "none",
          "&:hover": { backgroundColor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.04)" },
        }}
        onClick={() => handleSort(property)}
      >
        <Stack direction="row" alignItems="center" spacing={0.5}>
          <span>{children}</span>
          {isActive ? (
            order === "asc" ? (
              <span style={{ fontSize: "0.875rem" }}>▲</span>
            ) : (
              <span style={{ fontSize: "0.875rem" }}>▼</span>
            )
          ) : (
            <span style={{ fontSize: "0.875rem", color: "rgba(0,0,0,0.3)" }}>⇅</span>
          )}
        </Stack>
      </TableCell>
    );
  };

  const renderStatusIcon = (statusValue) => {
    const value = (statusValue || "").toUpperCase();
    let icon = <HelpOutline fontSize="small" />;
    let color = "default";
    let title = value || "UNKNOWN";

    if (value === "SUCCESS") {
      icon = <CheckCircleOutline fontSize="small" />;
      color = "success";
      title = "Success";
    } else if (value === "FAILED") {
      icon = <ErrorOutline fontSize="small" />;
      color = "error";
      title = "Failed";
    } else if (value === "PARTIAL") {
      icon = <ChangeCircle fontSize="small" />;
      color = "warning";
      title = "Partial";
    }

    return (
      <TableCell align="center">
        <Tooltip title={title}>
          <Box display="flex" justifyContent="center">
            {React.cloneElement(icon, { color })}
          </Box>
        </Tooltip>
      </TableCell>
    );
  };

  const renderLoadModeIcon = (modeValue) => {
    const value = (modeValue || "INSERT").toUpperCase();
    let icon = <HelpOutline fontSize="small" />;
    let title = value;

    if (value === "INSERT") {
      icon = <AddCircleOutline fontSize="small" />;
      title = "Insert";
    } else if (value === "TRUNCATE_LOAD") {
      icon = <DeleteSweep fontSize="small" />;
      title = "Truncate & Load";
    } else if (value === "UPSERT") {
      icon = <SyncAlt fontSize="small" />;
      title = "Upsert";
    }

    return (
      <TableCell align="center">
        <Tooltip title={title}>
          <Box display="flex" justifyContent="center">
            {icon}
          </Box>
        </Tooltip>
      </TableCell>
    );
  };

  return (
    <Box sx={{ p: 2.5 }}>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          File Upload History
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <Button
            variant={showFilters ? "contained" : "outlined"}
            startIcon={<FilterList />}
            onClick={() => setShowFilters(!showFilters)}
            color={hasActiveFilters() ? "primary" : "inherit"}
          >
            Filters {hasActiveFilters() && `(${[selectedFlupldref, status, targetConnectionId, loadMode, fileType, fileName, startDate].filter(Boolean).length})`}
          </Button>
          <TextField
            size="small"
            type="number"
            label="Limit"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 10)}
            sx={{ width: 100 }}
            inputProps={{ min: 1, max: 500 }}
          />
          <Button variant="outlined" startIcon={<Refresh />} onClick={fetchRuns}>
            Refresh
          </Button>
        </Stack>
      </Stack>

      {/* Filters Section */}
      <Collapse in={showFilters}>
        <Paper
          elevation={darkMode ? 0 : 1}
          sx={{
            p: 2,
            mb: 2,
            borderRadius: 2,
            border: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)",
          }}
        >
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="subtitle1" fontWeight={600}>
              Filter Options
            </Typography>
            {hasActiveFilters() && (
              <Button size="small" startIcon={<Clear />} onClick={clearFilters}>
                Clear All
              </Button>
            )}
          </Stack>
          <Grid container spacing={2}>
            {/* 1. File Reference */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="File Reference"
                value={selectedFlupldref}
                onChange={(e) => setSelectedFlupldref(e.target.value)}
                placeholder="Partial match on reference..."
              />
            </Grid>
            {/* 2. Status */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select value={status} onChange={(e) => setStatus(e.target.value)} label="Status">
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="SUCCESS">Success</MenuItem>
                  <MenuItem value="FAILED">Failed</MenuItem>
                  <MenuItem value="PARTIAL">Partial</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {/* 3. Target Database Connection */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Target DB Connection</InputLabel>
                <Select value={targetConnectionId} onChange={(e) => setTargetConnectionId(e.target.value)} label="Target DB Connection">
                  <MenuItem value="">All</MenuItem>
                  {connections.map((conn) => (
                    <MenuItem key={conn.conid} value={conn.conid}>
                      {conn.connm} {conn.dbhost ? `(${conn.dbhost})` : ""}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {/* 4. Load Mode */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Load Mode</InputLabel>
                <Select value={loadMode} onChange={(e) => setLoadMode(e.target.value)} label="Load Mode">
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="INSERT">Insert</MenuItem>
                  <MenuItem value="TRUNCATE_LOAD">Truncate & Load</MenuItem>
                  <MenuItem value="UPSERT">Upsert</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {/* 5. File Type */}
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>File Type</InputLabel>
                <Select value={fileType} onChange={(e) => setFileType(e.target.value)} label="File Type">
                  <MenuItem value="">All</MenuItem>
                  {fileTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {/* 6. File Name */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="File Name"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="Partial match..."
              />
            </Grid>
            {/* 7. Start Date */}
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                type="date"
                label="Start Date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </Paper>
      </Collapse>

      <Paper
        elevation={darkMode ? 0 : 1}
        sx={{
          p: 2,
          borderRadius: 2,
          border: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)",
        }}
      >
        {loading ? (
          <Box py={4} display="flex" justifyContent="center">
            <CircularProgress />
          </Box>
        ) : runs.length === 0 ? (
          <Box py={4} textAlign="center">
            <Typography variant="body2" color="text.secondary">
              No file upload runs found for the selected criteria.
            </Typography>
          </Box>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <SortableTableCell property="runid">#</SortableTableCell>
                <SortableTableCell property="flupldref">Reference</SortableTableCell>
                <SortableTableCell property="flnm">File Name</SortableTableCell>
                <SortableTableCell property="fltyp">File Type</SortableTableCell>
                <SortableTableCell property="stts">Status</SortableTableCell>
                <SortableTableCell property="ldmde">Load Mode</SortableTableCell>
                <SortableTableCell property="rwsprcssd">Processed</SortableTableCell>
                <SortableTableCell property="rwsstccssfl">Successful</SortableTableCell>
                <SortableTableCell property="rwsfld">Failed</SortableTableCell>
                <SortableTableCell property="strttm">Start Time</SortableTableCell>
                <TableCell align="center">Duration</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {getSortedRuns().map((run) => (
                <TableRow key={run.runid}>
                  <TableCell align="right">{run.runid}</TableCell>
                  <TableCell>
                    <Tooltip title={getUploadName(run.flupldref)}>
                      <Typography
                        variant="body2"
                        sx={{ maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis" }}
                      >
                        {run.flupldref}
                      </Typography>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    {run.flnm ? (
                      <Tooltip title={run.flnm}>
                        <Typography variant="body2" sx={{ maxWidth: 150, overflow: "hidden", textOverflow: "ellipsis" }}>
                          {run.flnm}
                        </Typography>
                      </Tooltip>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell align="center">
                    {run.fltyp ? (
                      <Chip size="small" label={run.fltyp} variant="outlined" />
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  {renderStatusIcon(run.stts)}
                  {renderLoadModeIcon(run.ldmde)}
                  <TableCell align="right">{run.rwsprcssd ?? "-"}</TableCell>
                  <TableCell align="right">
                    <Chip
                      size="small"
                      color="success"
                      variant="outlined"
                      label={run.rwsstccssfl ?? 0}
                    />
                  </TableCell>
                  <TableCell align="right">
                    {run.rwsfld > 0 ? (
                      <Tooltip title="Click to view error details">
                        <Chip
                          size="small"
                          color="error"
                          variant="outlined"
                          label={run.rwsfld}
                          onClick={() => handleFailedCountClick(run)}
                          sx={{
                            cursor: "pointer",
                            "&:hover": {
                              backgroundColor: "error.main",
                              color: "error.contrastText",
                            },
                          }}
                        />
                      </Tooltip>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell>{formatDateTime(run.strttm)}</TableCell>
                  <TableCell align="center">{formatDuration(run.strttm, run.ndtm)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>

      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        onClose={closeNotification}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert onClose={closeNotification} severity={notification.severity} sx={{ width: "100%" }}>
          {notification.message}
        </Alert>
      </Snackbar>

      {/* Error Details Dialog */}
      <Dialog
        open={showErrorDialog}
        onClose={() => {
          setShowErrorDialog(false);
          setSelectedRun(null);
          setErrorRows([]);
        }}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Error Rows: {selectedRun?.flupldref} (Run #{selectedRun?.runid})
        </DialogTitle>
        <DialogContent>
          {!selectedRun ? (
            <DialogContentText>No run selected.</DialogContentText>
          ) : (
            <Box sx={{ py: 1 }}>
              <Box
                sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 2,
                  mb: 2,
                  alignItems: "center",
                }}
              >
                <TextField
                  size="small"
                  label="Error Code"
                  value={errorFilterCode}
                  onChange={(e) => setErrorFilterCode(e.target.value)}
                  onBlur={() => {
                    if (selectedRun) {
                      fetchErrorRows(selectedRun.flupldref, selectedRun.runid, errorFilterCode);
                    }
                  }}
                />

                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    if (selectedRun) {
                      fetchErrorRows(selectedRun.flupldref, selectedRun.runid, errorFilterCode);
                    }
                  }}
                  disabled={loadingErrors}
                >
                  Refresh Errors
                </Button>
              </Box>

              {loadingErrors ? (
                <Box sx={{ py: 2 }}>
                  <LinearProgress />
                </Box>
              ) : errorRows.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No error rows found for this run.
                </Typography>
              ) : (
                <TableContainer
                  component={Paper}
                  sx={{
                    maxHeight: 400,
                    mt: 1,
                  }}
                >
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Row #</TableCell>
                        <TableCell>Error Code</TableCell>
                        <TableCell>Error Message</TableCell>
                        <TableCell>Row Data (JSON)</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {errorRows.map((row) => (
                        <TableRow key={row.errid}>
                          <TableCell>{(row.rwndx ?? 0) + 1}</TableCell>
                          <TableCell>
                            {row.rrcd ? (
                              <Chip
                                label={row.rrcd}
                                size="small"
                                color="error"
                                variant="outlined"
                              />
                            ) : (
                              "-"
                            )}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={row.rrmssg}>
                              <Typography
                                variant="body2"
                                sx={{
                                  maxWidth: 320,
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {row.rrmssg}
                              </Typography>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Box
                              sx={{
                                maxWidth: 360,
                                maxHeight: 80,
                                overflow: "auto",
                                fontFamily: "monospace",
                                fontSize: "0.75rem",
                                backgroundColor: darkMode
                                  ? alpha(muiTheme.palette.background.paper, 0.6)
                                  : alpha(muiTheme.palette.grey[200], 0.6),
                                p: 0.5,
                                borderRadius: 1,
                              }}
                            >
                              {row.rwdtjsn
                                ? typeof row.rwdtjsn === "string"
                                  ? row.rwdtjsn
                                  : JSON.stringify(row.rwdtjsn, null, 2)
                                : "-"}
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setShowErrorDialog(false);
              setSelectedRun(null);
              setErrorRows([]);
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileUploadHistoryPage;

