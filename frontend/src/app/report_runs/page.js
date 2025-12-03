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
} from "@mui/material";
import { History, Refresh } from "@mui/icons-material";
import { useTheme } from "@/context/ThemeContext";

const ReportRunsPage = () => {
  const { darkMode } = useTheme();
  const apiBase = process.env.NEXT_PUBLIC_API_URL;

  const [runs, setRuns] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedReportId, setSelectedReportId] = useState("");
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState({ open: false, message: "", severity: "info" });

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${apiBase}/api/reports`);
      setReports(res.data.data || []);
    } catch (err) {
      showNotification("Failed to load reports list", "error");
    }
  };

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (selectedReportId) params.append("reportId", selectedReportId);
      const res = await axios.get(`${apiBase}/api/report-runs?${params.toString()}`);
      setRuns(res.data.data || []);
    } catch (err) {
      showNotification("Failed to load report runs", "error");
    } finally {
      setLoading(false);
    }
  };

  const showNotification = (message, severity = "info") => {
    setNotification({ open: true, message, severity });
  };

  const closeNotification = () => setNotification((prev) => ({ ...prev, open: false }));

  const getReportName = (reportId) => {
    const report = reports.find((r) => r.reportId === reportId);
    return report ? report.reportName : reportId;
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return "-";
    try {
      const date = new Date(isoString);
      return date.toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      });
    } catch {
      return isoString || "-";
    }
  };

  useEffect(() => {
    // Load reports list once on mount
    fetchReports();
  }, []);

  useEffect(() => {
    // Reload runs whenever filters change
    fetchRuns();
  }, [selectedReportId, limit]);

  return (
    <Box sx={{ p: 2.5 }}>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight={600}>
          Report Runs
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel id="report-filter-label">Report</InputLabel>
            <Select
              labelId="report-filter-label"
              label="Report"
              value={selectedReportId}
              onChange={(e) => setSelectedReportId(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {reports.map((report) => (
                <MenuItem key={report.reportId} value={report.reportId}>
                  {report.reportName}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            size="small"
            type="number"
            label="Limit"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 10)}
            sx={{ width: 100 }}
          />
          <Button variant="outlined" startIcon={<Refresh />} onClick={fetchRuns}>
            Refresh
          </Button>
        </Stack>
      </Stack>

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
              No report runs found for the selected criteria.
            </Typography>
          </Box>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Run ID</TableCell>
                <TableCell>Report</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Rows</TableCell>
                <TableCell>Start</TableCell>
                <TableCell>End</TableCell>
                <TableCell>Formats</TableCell>
                <TableCell>Message</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {runs.map((run) => (
                <TableRow key={run.runId}>
                  <TableCell>{run.runId}</TableCell>
                  <TableCell>{getReportName(run.reportId)}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      color={
                        run.status === "SUCCESS"
                          ? "success"
                          : run.status === "FAILED"
                          ? "error"
                          : run.status === "RUNNING"
                          ? "info"
                          : "default"
                      }
                      label={run.status}
                    />
                  </TableCell>
                  <TableCell>{run.rowCount ?? "-"}</TableCell>
                  <TableCell>{formatDateTime(run.startAt)}</TableCell>
                  <TableCell>{formatDateTime(run.endAt)}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap">
                      {(run.outputFormats || []).map((format) => (
                        <Chip key={format} size="small" label={format} variant="outlined" />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    {run.message ? (
                      <Tooltip title={run.message}>
                        <span>{run.message.slice(0, 24)}...</span>
                      </Tooltip>
                    ) : (
                      "-"
                    )}
                  </TableCell>
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
    </Box>
  );
};

export default ReportRunsPage;

