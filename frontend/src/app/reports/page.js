"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Button,
  Chip,
  Divider,
  Stack,
  IconButton,
  Tooltip,
  Table,
  TableContainer,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  CircularProgress,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Checkbox,
  ListItemText,
  Collapse,
} from "@mui/material";
import {
  Add,
  Save,
  PlayArrow,
  Refresh,
  AutoAwesome,
  Visibility,
  Stop as StopIcon,
  ArrowBack,
  Warning as WarningIcon,
  DeleteOutline,
  History,
  Schedule,
} from "@mui/icons-material";
import { useTheme } from "@/context/ThemeContext";

const OUTPUT_FORMATS = ["CSV", "TXT", "JSON", "XML", "EXCEL", "PDF", "PARQUET"];
const createEmptyPreviewState = () => ({
  loading: false,
  columns: [],
  rows: [],
  finalSql: "",
  rowCount: 0,
});

const createRow = (overrides = {}) => ({
  tempId: `row-${Math.random().toString(36).slice(2, 9)}`,
  fieldId: overrides.fieldId || null,
  fieldName: overrides.fieldName || "",
  fieldDescription: overrides.fieldDescription || "",
  sourceColumn: overrides.sourceColumn || "",
  formulaText: overrides.formulaText || "",
  isGroupBy: overrides.isGroupBy || false,
  orderBySeq: overrides.orderBySeq ?? "",
  orderByDir: overrides.orderByDir || "ASC",
});

const defaultFormState = {
  reportName: "",
  description: "",
  sqlMode: "MANAGE",
  sqlSourceId: "",
  adhocSql: "",
  dbConnectionId: "",
  defaultOutputFormat: "CSV",
  supportedFormats: ["CSV"],
  previewRowLimit: 100,
  isActive: true,
};

const ReportsPage = () => {
  const { darkMode } = useTheme();
  const apiBase = process.env.NEXT_PUBLIC_API_URL;

  const [reports, setReports] = useState([]);
  const [selectedReportId, setSelectedReportId] = useState(null);
  const [form, setForm] = useState(defaultFormState);
  const [reportRows, setReportRows] = useState([createRow()]);
  const [formulas, setFormulas] = useState([]);
  const [preview, setPreview] = useState(() => createEmptyPreviewState());
  const [finalSql, setFinalSql] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: "", severity: "info" });
  const [sqlSources, setSqlSources] = useState([]);
  const [dbConnections, setDbConnections] = useState([]);
  const [executeDialog, setExecuteDialog] = useState(false);
  const [executeOptions, setExecuteOptions] = useState({
    rowLimit: 1000,
    outputFormats: ["CSV"],
  });
  const [loadingReports, setLoadingReports] = useState(false);
  const [hasActiveSchedule, setHasActiveSchedule] = useState(false);
  const [sqlPreviewText, setSqlPreviewText] = useState("");
  const [showReportForm, setShowReportForm] = useState(false);
  const [sqlLookupOpen, setSqlLookupOpen] = useState(false);
  const [sqlLookupSearch, setSqlLookupSearch] = useState("");
  const [importingColumns, setImportingColumns] = useState(false);
  const [showFinalSql, setShowFinalSql] = useState(false);
  const [groupByAlert, setGroupByAlert] = useState({ show: false, fields: [] });

  const showNotification = (message, severity = "info") => {
    setNotification({ open: true, message, severity });
  };

  const closeNotification = () => {
    setNotification((prev) => ({ ...prev, open: false }));
  };

  const fetchReports = async () => {
    const response = await axios.get(`${apiBase}/api/reports`);
    setReports(response.data.data || []);
  };

  const fetchSqlSources = async () => {
    const response = await axios.get(`${apiBase}/api/reports/sql-sources`);
    setSqlSources(response.data.data || []);
  };

  const fetchConnections = async () => {
    const response = await axios.get(`${apiBase}/api/dbconnections`);
    setDbConnections(response.data.data || []);
  };

  const fetchInitialData = async () => {
    setLoadingReports(true);
    try {
      await Promise.all([fetchReports(), fetchSqlSources(), fetchConnections()]);
      showNotification("Loaded report workspace", "success");
    } catch (err) {
      showNotification("Failed to load report workspace", "error");
    } finally {
      setLoadingReports(false);
    }
  };

  const resetForm = () => {
    setForm(defaultFormState);
    setReportRows([createRow()]);
    setPreview(createEmptyPreviewState());
    setFinalSql("");
    setSqlPreviewText("");
    setHasActiveSchedule(false);
    setSelectedReportId(null);
    setShowFinalSql(false);
    setSqlLookupSearch("");
  };

  useEffect(() => {
    // Load initial data once on mount
    fetchInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelectReport = async (reportId) => {
    if (!reportId) {
      resetForm();
      return;
    }
    setLoading(true);
    try {
      const response = await axios.get(`${apiBase}/api/reports/${reportId}`);
      const data = response.data.data;
      const matchedSource = sqlSources.find((src) => src.id === data.sqlSourceId);
      const derivedDbConnectionId = data.dbConnectionId || matchedSource?.connectionId || "";
      setSelectedReportId(data.reportId);
      setForm({
        reportName: data.reportName,
        description: data.description || "",
        sqlMode: data.sqlSourceId ? "MANAGE" : "ADHOC",
        sqlSourceId: data.sqlSourceId || "",
        adhocSql: data.adhocSql || "",
        dbConnectionId: derivedDbConnectionId,
        defaultOutputFormat: data.defaultOutputFormat || "CSV",
        supportedFormats: data.supportedFormats?.length ? data.supportedFormats : ["CSV"],
        previewRowLimit: data.previewRowLimit || 100,
        isActive: data.isActive,
      });
      setReportRows(
        (data.fields || [])
          .filter((field) => (field.panelType || "").toUpperCase() === "DETAIL")
          .map((field) =>
            createRow({
              fieldId: field.fieldId,
              fieldName: field.fieldName,
              fieldDescription: field.notes || "",
              sourceColumn: field.sourceColumn || "",
              formulaText: field.inlineFormula || "",
              isGroupBy: Boolean(field.isGroupBy),
              orderBySeq: field.orderBySeq ? String(field.orderBySeq) : "",
              orderByDir: field.orderByDir || "ASC",
            })
          )
      );
      setHasActiveSchedule(data.hasActiveSchedule);
      setFinalSql(data.finalSql || "");
      setShowFinalSql(false);
      setPreview(createEmptyPreviewState());
      if (data.sqlSourceId && matchedSource?.code) {
        await loadSqlTextFromSource(matchedSource);
      } else {
        setSqlPreviewText(data.adhocSql || "");
      }
    } catch (err) {
      showNotification("Failed to load report definition", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewReport = () => {
    resetForm();
    setShowReportForm(true);
  };

  const handleEditReport = async (reportId) => {
    await handleSelectReport(reportId);
    setShowReportForm(true);
  };

  const handleReturnToList = () => {
    resetForm();
    setShowReportForm(false);
  };

  const loadSqlTextFromSource = async (source) => {
    if (!source?.code) {
      return;
    }
    try {
      const resp = await axios.get(
        `${apiBase}/manage-sql/fetch-sql-logic?sql_code=${encodeURIComponent(source.code)}`
      );
      if (resp.data?.success) {
        const sqlText = resp.data.data?.sql_content || "";
        setSqlPreviewText(sqlText);
      }
    } catch (err) {
      showNotification("Unable to fetch SQL logic for selected source", "error");
    }
  };

  const applySqlSourceSelection = (source) => {
    setForm((prev) => ({
      ...prev,
      sqlSourceId: source?.id || "",
      dbConnectionId: source?.connectionId || prev.dbConnectionId,
      adhocSql: "",
      sqlMode: source ? "MANAGE" : prev.sqlMode,
    }));
    setShowFinalSql(false);
  };

  const handleSqlLookupSelect = async (source) => {
    if (!source) return;
    setSqlLookupOpen(false);
    setSqlLookupSearch("");
    applySqlSourceSelection(source);
    await loadSqlTextFromSource(source);
  };

  const clearSqlSourceSelection = () => {
    setForm((prev) => ({
      ...prev,
      sqlSourceId: "",
      sqlMode: "ADHOC",
      adhocSql: sqlPreviewText || prev.adhocSql || "",
    }));
    setShowFinalSql(false);
  };

  const handleSqlTextChange = (value) => {
    setSqlPreviewText(value);
    setForm((prev) => {
      const next = { ...prev, adhocSql: value };
      if (value) {
        next.sqlMode = "ADHOC";
        next.sqlSourceId = "";
      } else if (prev.sqlSourceId) {
        next.sqlMode = "MANAGE";
      }
      return next;
    });
    setShowFinalSql(false);
  };

  const handleImportColumns = async () => {
    const sqlText = (form.sqlMode === "ADHOC" ? form.adhocSql : sqlPreviewText) || "";
    if (!sqlText.trim()) {
      showNotification("Provide SQL text before importing columns", "warning");
      return;
    }
    setImportingColumns(true);
    try {
      const response = await axios.post(`${apiBase}/api/reports/describe-sql`, {
        sqlText,
        dbConnectionId: form.dbConnectionId || null,
      });
      const columns = response.data?.data?.columns || response.data?.data || [];
      if (!columns.length) {
        showNotification("No columns detected for the current SQL", "info");
        return;
      }
      setReportRows(
        columns.map((column) =>
          createRow({
            fieldName: column.name,
            sourceColumn: column.name,
          })
        )
      );
      showNotification(`Imported ${columns.length} columns from SQL`, "success");
    } catch (err) {
      const message = err.response?.data?.message || "Unable to import columns";
      showNotification(message, "error");
    } finally {
      setImportingColumns(false);
    }
  };

  const handleFormChange = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const addRow = () => {
    setReportRows((prev) => [...prev, createRow()]);
  };

  const removeRow = (tempId) => {
    setReportRows((prev) => (prev.length === 1 ? prev : prev.filter((row) => row.tempId !== tempId)));
  };

  const updateRow = (tempId, key, value) => {
    setReportRows((prev) =>
      prev.map((row) =>
        row.tempId === tempId ? { ...row, [key]: value } : row
      )
    );
    if (key === "isGroupBy" || key === "orderBySeq" || key === "orderByDir" || key === "formulaText") {
      setTimeout(checkGroupByAlert, 0);
    }
  };

  const resolveSqlSourceLabel = (source) => {
    if (!source) return "";
    return source.code || source.sql_code || source.sqlCode || `SQL-${source.id}`;
  };

  const resolveConnectionName = (connectionId) => {
    if (!connectionId) return "";
    const match = dbConnections.find((conn) => Number(conn.conid) === Number(connectionId));
    return match?.connm || `Connection ${connectionId}`;
  };

  const buildFieldsPayload = () => {
    return reportRows.map((row, index) => ({
      fieldId: row.fieldId,
      panelType: "DETAIL",
      rowOrder: index + 1,
      fieldName: row.fieldName,
      fieldAlias: row.fieldDescription || row.fieldName,
      sourceColumn: row.sourceColumn?.trim() || "",
      inlineFormula: row.formulaText?.trim() || "",
      dataType: "",
      formatMask: "",
      isVisible: true,
      notes: row.fieldDescription,
      isGroupBy: Boolean(row.isGroupBy),
      orderBySeq: row.orderBySeq ? Number(row.orderBySeq) : null,
      orderByDir: row.orderBySeq ? (row.orderByDir || "ASC") : null,
    }));
  };

  const checkGroupByAlert = () => {
    const hasGroupBy = reportRows.some((row) => row.isGroupBy);
    if (!hasGroupBy) {
      setGroupByAlert({ show: false, fields: [] });
      return;
    }
    const violations = reportRows
      .filter((row) => !row.isGroupBy)
      .filter((row) => !(row.formulaText || "").trim())
      .map((row) => row.fieldName || row.fieldDescription || "Unnamed field");
    setGroupByAlert({ show: violations.length > 0, fields: violations });
  };

  const buildPayload = () => ({
    reportName: form.reportName,
    description: form.description,
    sqlSourceId: form.sqlMode === "MANAGE" ? form.sqlSourceId : null,
    adhocSql: form.sqlMode === "ADHOC" ? form.adhocSql : null,
    dbConnectionId: form.dbConnectionId || null,
    defaultOutputFormat: form.defaultOutputFormat,
    supportedFormats: form.supportedFormats,
    previewRowLimit: form.previewRowLimit,
    isActive: form.isActive,
    fields: buildFieldsPayload(),
    formulas: formulas.map((formula) => ({
      formulaId: formula.formulaId,
      name: formula.name,
      expression: formula.expression,
      helpText: formula.helpText,
    })),
  });

  const handleSaveReport = async () => {
    checkGroupByAlert();
    const hasGroupBy = reportRows.some((row) => row.isGroupBy);
    if (hasGroupBy) {
      const unresolved = reportRows
        .filter((row) => !row.isGroupBy)
        .some((row) => !(row.formulaText || "").trim());
      if (unresolved) {
        showNotification("Resolve group-by warnings before saving", "warning");
        return;
      }
    }
    if (!form.reportName.trim()) {
      showNotification("Report name is required", "warning");
      return;
    }
    if (form.sqlMode === "MANAGE" && !form.sqlSourceId) {
      showNotification("Select a SQL source", "warning");
      return;
    }
    if (form.sqlMode === "ADHOC" && !form.adhocSql.trim()) {
      showNotification("Provide ad hoc SQL text", "warning");
      return;
    }
    setSaving(true);
    try {
      const payload = buildPayload();
      if (selectedReportId) {
        const response = await axios.put(`${apiBase}/api/reports/${selectedReportId}`, payload);
        showNotification("Report updated successfully", "success");
        setHasActiveSchedule(response.data.data?.hasActiveSchedule);
        setFinalSql(response.data.data?.finalSql || "");
      } else {
        const response = await axios.post(`${apiBase}/api/reports`, payload);
        showNotification("Report created successfully", "success");
        setSelectedReportId(response.data.data.reportId);
        setFinalSql(response.data.data?.finalSql || "");
      }
      await fetchReports();
    } catch (err) {
      const message = err.response?.data?.message || "Failed to save report";
      showNotification(message, "error");
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    if (!selectedReportId) {
      showNotification("Save the report before previewing", "info");
      return;
    }
    setPreview((prev) => ({ ...prev, loading: true }));
    try {
      const response = await axios.post(`${apiBase}/api/reports/${selectedReportId}/preview`, {
        rowLimit: form.previewRowLimit,
      });
      const data = response.data.data;
      const rowCount = data.rowCount ?? (data.rows ? data.rows.length : 0);
      const nextPreview = {
        loading: false,
        columns: data.columns || [],
        rows: data.rows || [],
        rowCount,
        finalSql: data.finalSql || "",
      };
      setPreview(nextPreview);
      if (data.finalSql) {
        setFinalSql(data.finalSql);
      }
      showNotification(`Preview loaded (${rowCount} rows)`, "success");
    } catch (err) {
      const message = err.response?.data?.message || "Failed to fetch preview";
      showNotification(message, "error");
      setPreview((prev) => ({ ...prev, loading: false }));
    }
  };

  const handleExecute = () => {
    if (!selectedReportId) {
      showNotification("Save the report before executing", "info");
      return;
    }
    setExecuteDialog(true);
  };

  const confirmExecute = async () => {
    try {
      await axios.post(`${apiBase}/api/reports/${selectedReportId}/execute`, {
        rowLimit: executeOptions.rowLimit,
        outputFormats: executeOptions.outputFormats,
      });
      showNotification("Report execution queued", "success");
      setExecuteDialog(false);
    } catch (err) {
      const message = err.response?.data?.message || "Failed to queue report execution";
      showNotification(message, "error");
    }
  };

  const [scheduleDialog, setScheduleDialog] = useState({ open: false, report: null });
  const [scheduleForm, setScheduleForm] = useState({ 
    frequency: "DAILY", 
    status: "ACTIVE",
    day: "MON",
    dayOfMonth: "01",
    hour: "09",
    minute: "00",
    outputFormat: "CSV",
    destination: "FILE",
    email: "",
    filePath: ""
  });
  const [savingSchedule, setSavingSchedule] = useState(false);
  const [stopScheduleDialog, setStopScheduleDialog] = useState({ open: false, report: null });
  const [stoppingSchedule, setStoppingSchedule] = useState(false);
  const [runDialog, setRunDialog] = useState({ open: false, report: null });
  const [runForm, setRunForm] = useState({ outputFormat: "CSV", destination: "DOWNLOAD", email: "", filePath: "" });
  const [runningReport, setRunningReport] = useState(false);

  const openScheduleDialog = (report) => {
    // Parse existing timeParam if available
    const timeParam = report.scheduleTimeParam || "";
    const parts = timeParam.split("_");
    let day = "MON", dayOfMonth = "01", hour = "09", minute = "00";
    
    for (const part of parts) {
      if (part.includes(":")) {
        const [h, m] = part.split(":");
        hour = h || "09";
        minute = m || "00";
      } else if (["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"].includes(part)) {
        day = part;
      } else if (/^\d{1,2}$/.test(part)) {
        dayOfMonth = part.padStart(2, "0");
      }
    }
    
    setScheduleForm({
      frequency: report.scheduleFrequency || "DAILY",
      status: report.scheduleStatus || "ACTIVE",
      day,
      dayOfMonth,
      hour,
      minute,
      outputFormat: report.scheduleOutputFormat || report.defaultOutputFormat || (report.supportedFormats?.[0] || "CSV"),
      destination: report.scheduleDestination || "FILE",
      email: "",
      filePath: ""
    });
    setScheduleDialog({ open: true, report });
  };

  const closeScheduleDialog = () => {
    setScheduleDialog({ open: false, report: null });
  };

  const openRunDialog = (report) => {
    setRunForm({ outputFormat: report.defaultOutputFormat || "CSV", destination: "DOWNLOAD", email: "", filePath: "" });
    setRunDialog({ open: true, report });
  };

  const closeRunDialog = () => {
    setRunDialog({ open: false, report: null });
  };

  const handleRunReport = async () => {
    const report = runDialog.report;
    if (!report) return;
    
    setRunningReport(true);
    
    // For DOWNLOAD destination, trigger file download synchronously
    if (runForm.destination === "DOWNLOAD") {
      try {
        const response = await axios.post(
          `${apiBase}/api/reports/${report.reportId}/execute`,
          { outputFormat: runForm.outputFormat },
          { responseType: "blob" }
        );
        
        // Create download link
        const contentDisposition = response.headers["content-disposition"];
        let filename = `report_${report.reportId}.${runForm.outputFormat.toLowerCase()}`;
        if (contentDisposition) {
          const match = contentDisposition.match(/filename=([^;]+)/);
          if (match) filename = match[1].replace(/"/g, "");
        }
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        
        showNotification("Report downloaded successfully", "success");
        closeRunDialog();
      } catch (err) {
        console.error("Execute report error:", err);
        // Try to parse error from blob response
        if (err.response?.data instanceof Blob) {
          const text = await err.response.data.text();
          try {
            const json = JSON.parse(text);
            showNotification(json.message || "Failed to execute report", "error");
          } catch {
            showNotification("Failed to execute report", "error");
          }
        } else {
          const message = err.response?.data?.message || "Failed to execute report";
          showNotification(message, "error");
        }
      } finally {
        setRunningReport(false);
      }
    } else {
      // For EMAIL/FILE destinations, queue for async processing
      try {
        const response = await axios.post(`${apiBase}/api/reports/${report.reportId}/execute-async`, {
          outputFormat: runForm.outputFormat,
          destination: runForm.destination,
          email: runForm.destination === "EMAIL" ? runForm.email : undefined,
          filePath: runForm.destination === "FILE" ? runForm.filePath : undefined,
        });
        
        if (response.data?.success) {
          const destMsg = runForm.destination === "EMAIL" 
            ? `Report will be sent to ${runForm.email}` 
            : `Report will be saved to ${runForm.filePath || "default output directory"}`;
          showNotification(`Report queued successfully. ${destMsg}`, "success");
          closeRunDialog();
        } else {
          showNotification(response.data?.message || "Failed to queue report", "error");
        }
      } catch (err) {
        console.error("Queue report error:", err);
        const message = err.response?.data?.message || "Failed to queue report";
        showNotification(message, "error");
      } finally {
        setRunningReport(false);
      }
    }
  };

  const buildTimeParam = () => {
    const { frequency, day, dayOfMonth, hour, minute } = scheduleForm;
    const time = `${hour}:${minute}`;
    if (frequency === "WEEKLY") {
      return `WK_${day}_${time}`;
    } else if (frequency === "MONTHLY") {
      return `MN_${dayOfMonth}_${time}`;
    } else {
      return `DL_${time}`;
    }
  };

  const handleSaveSchedule = async () => {
    const report = scheduleDialog.report;
    if (!report) return;
    setSavingSchedule(true);
    try {
      const timeParam = buildTimeParam();
      const payload = {
        frequency: scheduleForm.frequency,
        status: scheduleForm.status,
        timeParam,
        outputFormat: scheduleForm.outputFormat,
        destination: scheduleForm.destination,
        email: scheduleForm.destination === "EMAIL" ? scheduleForm.email.trim() : undefined,
        filePath: scheduleForm.destination === "FILE" ? scheduleForm.filePath.trim() : undefined,
      };
      if (report.scheduleId) {
        await axios.put(`${apiBase}/api/report-schedules/${report.scheduleId}`, payload);
      } else {
        await axios.post(`${apiBase}/api/report-schedules`, {
          reportId: report.reportId,
          ...payload,
        });
      }
      showNotification("Schedule saved successfully", "success");
      closeScheduleDialog();
      fetchReports();
    } catch (err) {
      const message = err.response?.data?.message || "Failed to save schedule";
      showNotification(message, "error");
    } finally {
      setSavingSchedule(false);
    }
  };

  const handleStopSchedule = async () => {
    const report = stopScheduleDialog.report;
    if (!report || !report.scheduleId) return;
    setStoppingSchedule(true);
    try {
      await axios.delete(`${apiBase}/api/report-schedules/${report.scheduleId}`);
      showNotification("Schedule stopped successfully", "success");
      setStopScheduleDialog({ open: false, report: null });
      fetchReports();
    } catch (err) {
      const message = err.response?.data?.message || "Failed to stop schedule";
      showNotification(message, "error");
    } finally {
      setStoppingSchedule(false);
    }
  };

  const openStopScheduleDialog = (report) => {
    if (report.scheduleId) {
      setStopScheduleDialog({ open: true, report });
    }
  };

  const closeStopScheduleDialog = () => {
    setStopScheduleDialog({ open: false, report: null });
  };

  const getScheduleLabel = (report) => {
    if (!report.scheduleFrequency) return "None";
    return report.scheduleFrequency;
  };

  const getScheduleStatusColor = (report) => {
    if (!report.scheduleFrequency) return "default";
    if (report.scheduleStatus === "PAUSED") return "warning";
    if (report.scheduleStatus === "ACTIVE") return "success";
    return "default";
  };

  const formatDateTime = (isoString) => {
    if (!isoString) return "-";
    try {
      const date = new Date(isoString);
      // Display in Indian local time (IST), standard DD/MM/YYYY, 24-hour clock
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

  if (!showReportForm) {
    return (
      <Box
        sx={{
          p: 2.5,
          borderRadius: 2,
          backgroundColor: darkMode ? "rgba(17,24,39,0.35)" : "transparent",
          color: darkMode ? "rgba(255,255,255,0.92)" : "inherit",
        }}
      >
        <Stack direction="row" justifyContent="flex-end" alignItems="center" sx={{ mb: 2 }}>
          <Button variant="contained" startIcon={<Add />} onClick={handleCreateNewReport}>
            Add Report
          </Button>
        </Stack>
        {loadingReports ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper} elevation={darkMode ? 0 : 1} sx={{ borderRadius: 2, border: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)" }}>
            <Table size="small">
              <TableHead>
                <TableRow
                  sx={{
                    backgroundColor: darkMode ? "rgba(31,41,55,0.8)" : "rgba(0,0,0,0.03)",
                  }}
                >
                  <TableCell>Name</TableCell>
                  <TableCell>Target Connection</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell>Schedule</TableCell>
                  <TableCell>Next Run</TableCell>
                  <TableCell>Last Run</TableCell>
                  <TableCell>Output Format</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.reportId} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>{report.reportName}</Typography>
                      {report.description && (
                        <Typography variant="caption" color="text.secondary">{report.description}</Typography>
                      )}
                    </TableCell>
                    <TableCell>{resolveConnectionName(report.dbConnectionId) || "Metadata"}</TableCell>
                    <TableCell align="center">
                      <Chip size="small" color={report.isActive ? "success" : "default"} label={report.isActive ? "Active" : "Inactive"} />
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={0.5} alignItems="center">
                        <Chip
                          size="small"
                          variant={report.scheduleFrequency ? "filled" : "outlined"}
                          color={report.scheduleFrequency ? getScheduleStatusColor(report) : "default"}
                          label={report.scheduleFrequency || "Not Scheduled"}
                          onClick={() => openScheduleDialog(report)}
                          sx={{ cursor: "pointer", minWidth: 100 }}
                        />
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{formatDateTime(report.scheduleNextRun)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{formatDateTime(report.scheduleLastRun)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Chip size="small" variant="outlined" label={report.defaultOutputFormat || "CSV"} />
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <Tooltip title="Edit Report">
                          <IconButton size="small" onClick={() => handleEditReport(report.reportId)}>
                            <Visibility fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Run Report">
                          <IconButton size="small" color="primary" onClick={() => openRunDialog(report)} disabled={!report.isActive}>
                            <PlayArrow fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Schedule Report">
                          <IconButton size="small" color="success" onClick={() => openScheduleDialog(report)}>
                            <Schedule fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View History">
                          <IconButton size="small" color="info" onClick={() => window.location.href = `/report_runs?reportId=${report.reportId}`}>
                            <History fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        {report.scheduleFrequency && (
                          <Tooltip title="Stop Schedule">
                            <IconButton size="small" color="error" onClick={() => openStopScheduleDialog(report)}>
                              <StopIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}

        <Dialog open={scheduleDialog.open} onClose={closeScheduleDialog} fullWidth maxWidth="sm">
  <DialogTitle>Schedule Report</DialogTitle>
  <DialogContent dividers>
    <Stack spacing={2} sx={{ mt: 1 }}>
      {/* Report name (read-only) */}
      {scheduleDialog.report && (
        <TextField
          label="Report"
          value={scheduleDialog.report.reportName}
          fullWidth
          InputProps={{ readOnly: true }}
          size="small"
        />
      )}

      {/* Schedule pattern */}
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <FormControl fullWidth size="small">
          <InputLabel>Frequency</InputLabel>
          <Select
            label="Frequency"
            value={scheduleForm.frequency}
            onChange={(e) =>
              setScheduleForm((prev) => ({ ...prev, frequency: e.target.value }))
            }
          >
            <MenuItem value="DAILY">Daily</MenuItem>
            <MenuItem value="WEEKLY">Weekly</MenuItem>
            <MenuItem value="MONTHLY">Monthly</MenuItem>
            <MenuItem value="HOURLY">Hourly</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth size="small">
          <InputLabel>Status</InputLabel>
          <Select
            label="Status"
            value={scheduleForm.status}
            onChange={(e) =>
              setScheduleForm((prev) => ({ ...prev, status: e.target.value }))
            }
          >
            <MenuItem value="ACTIVE">Active</MenuItem>
            <MenuItem value="PAUSED">Paused</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {/* Weekly / Monthly specific selectors */}
      {scheduleForm.frequency === "WEEKLY" && (
        <FormControl fullWidth size="small">
          <InputLabel>Day of Week</InputLabel>
          <Select
            label="Day of Week"
            value={scheduleForm.day}
            onChange={(e) =>
              setScheduleForm((prev) => ({ ...prev, day: e.target.value }))
            }
          >
            <MenuItem value="MON">Monday</MenuItem>
            <MenuItem value="TUE">Tuesday</MenuItem>
            <MenuItem value="WED">Wednesday</MenuItem>
            <MenuItem value="THU">Thursday</MenuItem>
            <MenuItem value="FRI">Friday</MenuItem>
            <MenuItem value="SAT">Saturday</MenuItem>
            <MenuItem value="SUN">Sunday</MenuItem>
          </Select>
        </FormControl>
      )}

      {scheduleForm.frequency === "MONTHLY" && (
        <FormControl fullWidth size="small">
          <InputLabel>Day of Month</InputLabel>
          <Select
            label="Day of Month"
            value={scheduleForm.dayOfMonth}
            onChange={(e) =>
              setScheduleForm((prev) => ({ ...prev, dayOfMonth: e.target.value }))
            }
          >
            {Array.from({ length: 31 }, (_, i) => {
              const d = String(i + 1).padStart(2, "0");
              return (
                <MenuItem key={d} value={d}>
                  {d}
                </MenuItem>
              );
            })}
          </Select>
        </FormControl>
      )}

      {/* Time (Hour / Minute) */}
      <Box>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Time (24-hour format)
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <FormControl size="small" sx={{ width: 100 }}>
            <InputLabel>Hour</InputLabel>
            <Select
              label="Hour"
              value={scheduleForm.hour}
              onChange={(e) =>
                setScheduleForm((prev) => ({ ...prev, hour: e.target.value }))
              }
            >
              {Array.from({ length: 24 }, (_, i) => (
                <MenuItem key={i} value={String(i).padStart(2, "0")}>
                  {String(i).padStart(2, "0")}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Typography variant="h6">:</Typography>
          <FormControl size="small" sx={{ width: 100 }}>
            <InputLabel>Minute</InputLabel>
            <Select
              label="Minute"
              value={scheduleForm.minute}
              onChange={(e) =>
                setScheduleForm((prev) => ({ ...prev, minute: e.target.value }))
              }
            >
              {Array.from({ length: 60 }, (_, i) => (
                <MenuItem key={i} value={String(i).padStart(2, "0")}>
                  {String(i).padStart(2, "0")}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Box>

      {/* Delivery options */}
      <Typography variant="subtitle2">Delivery Options</Typography>

      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <FormControl fullWidth size="small">
          <InputLabel>Output Format</InputLabel>
          <Select
            label="Output Format"
            value={scheduleForm.outputFormat}
            onChange={(e) =>
              setScheduleForm((prev) => ({ ...prev, outputFormat: e.target.value }))
            }
          >
            {OUTPUT_FORMATS.map((fmt) => (
              <MenuItem key={fmt} value={fmt}>
                {fmt}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl fullWidth size="small">
          <InputLabel>Destination</InputLabel>
          <Select
            label="Destination"
            value={scheduleForm.destination}
            onChange={(e) =>
              setScheduleForm((prev) => ({ ...prev, destination: e.target.value }))
            }
          >
            <MenuItem value="FILE">File</MenuItem>
            <MenuItem value="EMAIL">Email</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {scheduleForm.destination === "EMAIL" && (
        <TextField
          label="Email Recipients"
          value={scheduleForm.email}
          onChange={(e) =>
            setScheduleForm((prev) => ({ ...prev, email: e.target.value }))
          }
          helperText="Comma-separated list of email addresses"
          fullWidth
          size="small"
        />
      )}

      {scheduleForm.destination === "FILE" && (
        <TextField
          label="File Path / Directory"
          value={scheduleForm.filePath}
          onChange={(e) =>
            setScheduleForm((prev) => ({ ...prev, filePath: e.target.value }))
          }
          helperText="Full file path (e.g. D:\\Reports\\sales.csv) or directory (e.g. D:\\Reports). Leave blank to use the default report_output folder."
          fullWidth
          size="small"
        />
      )}

      {/* Read-only schedule info */}
      {scheduleDialog.report && (
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <TextField
            label="Next Run At"
            value={formatDateTime(scheduleDialog.report.scheduleNextRun)}
            InputProps={{ readOnly: true }}
            fullWidth
            size="small"
          />
          <TextField
            label="Last Run At"
            value={formatDateTime(scheduleDialog.report.scheduleLastRun)}
            InputProps={{ readOnly: true }}
            fullWidth
            size="small"
          />
        </Stack>
      )}
    </Stack>
  </DialogContent>
  <DialogActions>
    <Button onClick={closeScheduleDialog} disabled={savingSchedule || stoppingSchedule}>
      Cancel
    </Button>
    {scheduleDialog.report?.scheduleId && (
      <Button 
        onClick={() => openStopScheduleDialog(scheduleDialog.report)} 
        color="error" 
        disabled={savingSchedule || stoppingSchedule}
        startIcon={<StopIcon />}
      >
        Stop Schedule
      </Button>
    )}
    <Button onClick={handleSaveSchedule} variant="contained" disabled={savingSchedule || stoppingSchedule}>
      {savingSchedule ? "Saving..." : "Save Schedule"}
    </Button>
  </DialogActions>
</Dialog>

        <Dialog open={runDialog.open} onClose={closeRunDialog} fullWidth maxWidth="sm">
          <DialogTitle>Run Report: {runDialog.report?.reportName}</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={2} sx={{ mt: 1 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Output Format</InputLabel>
                <Select
                  label="Output Format"
                  value={runForm.outputFormat}
                  onChange={(e) => setRunForm((prev) => ({ ...prev, outputFormat: e.target.value }))}
                >
                  <MenuItem value="CSV">CSV</MenuItem>
                  <MenuItem value="EXCEL">Excel (.xlsx)</MenuItem>
                  <MenuItem value="JSON">JSON</MenuItem>
                  <MenuItem value="PDF">PDF</MenuItem>
                  <MenuItem value="XML">XML</MenuItem>
                  <MenuItem value="PARQUET">Parquet</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth size="small">
                <InputLabel>Destination</InputLabel>
                <Select
                  label="Destination"
                  value={runForm.destination}
                  onChange={(e) => setRunForm((prev) => ({ ...prev, destination: e.target.value }))}
                >
                  <MenuItem value="DOWNLOAD">Download</MenuItem>
                  <MenuItem value="EMAIL">Email</MenuItem>
                  <MenuItem value="FILE">Save to File Path</MenuItem>
                </Select>
              </FormControl>
              {runForm.destination === "EMAIL" && (
                <TextField
                  fullWidth
                  size="small"
                  label="Email Recipients"
                  placeholder="email1@example.com, email2@example.com"
                  value={runForm.email}
                  onChange={(e) => setRunForm((prev) => ({ ...prev, email: e.target.value }))}
                />
              )}
              {runForm.destination === "FILE" && (
                <TextField
                  fullWidth
                  size="small"
                  label="Output Path"
                  placeholder="C:\Reports\myreport.csv or /home/user/reports/"
                  value={runForm.filePath}
                  onChange={(e) => setRunForm((prev) => ({ ...prev, filePath: e.target.value }))}
                  helperText="Enter full file path (e.g., C:\Reports\sales.csv) or directory (e.g., C:\Reports\). Leave empty for default output directory."
                />
              )}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeRunDialog}>Cancel</Button>
            <Button variant="contained" color="primary" onClick={handleRunReport} disabled={runningReport} startIcon={<PlayArrow />}>
              {runningReport ? "Running..." : "Run Report"}
            </Button>
          </DialogActions>
        </Dialog>

        <Dialog open={stopScheduleDialog.open} onClose={closeStopScheduleDialog} fullWidth maxWidth="sm">
          <DialogTitle>Stop Schedule</DialogTitle>
          <DialogContent>
            <DialogContentText sx={{ mb: 2 }}>
              Are you sure you want to stop the schedule for report "{stopScheduleDialog.report?.reportName}"?
            </DialogContentText>
            <Typography variant="body2" color="warning.main" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon fontSize="small" />
              This report will no longer be automatically scheduled for future runs.
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeStopScheduleDialog} disabled={stoppingSchedule}>
              Cancel
            </Button>
            <Button 
              onClick={handleStopSchedule} 
              variant="contained" 
              color="error" 
              disabled={stoppingSchedule}
              startIcon={stoppingSchedule ? <CircularProgress size={16} /> : <StopIcon />}
            >
              {stoppingSchedule ? "Stopping..." : "Stop Schedule"}
            </Button>
          </DialogActions>
        </Dialog>

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
  }

  return (
    <Box
      sx={{
        px: 2.5,
        pb: 2.5,
        pt: 0,
        color: darkMode ? "rgba(255,255,255,0.92)" : "inherit",
      }}
    >
      <Box
        sx={{
          position: "sticky",
          top: 48, // Below the 48px navbar
          zIndex: 20,
          mx: -2.5,
          px: 2.5,
          py: 1,
          mb: 2,
          backgroundColor: darkMode ? "rgba(17,17,17,0.95)" : "rgba(255,255,255,0.95)",
          backdropFilter: "blur(8px)",
          borderBottom: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.08)",
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1}>
          <Tooltip title="Back to Reports">
            <IconButton size="small" onClick={handleReturnToList}>
              <ArrowBack fontSize="small" />
            </IconButton>
          </Tooltip>
          <Typography variant="subtitle1" fontWeight={600} sx={{ flexGrow: 1 }}>
            {selectedReportId ? "Edit Report" : "New Report"}
          </Typography>
          <Tooltip title={saving ? "Saving..." : "Save report"}>
            <span>
              <IconButton
                color="primary"
                size="small"
                onClick={handleSaveReport}
                disabled={saving}
              >
                <Save fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>
      </Box>
      <Stack spacing={2.5}>
        <PanelCard
          title="Report Panel"
          subtitle="Define the base configuration and metadata for your report."
          darkMode={darkMode}
        >
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Report Name"
                value={form.reportName}
                onChange={(e) => handleFormChange("reportName", e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Description"
                value={form.description}
                onChange={(e) => handleFormChange("description", e.target.value)}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel id="db-connection-select">Target Connection</InputLabel>
                <Select
                  labelId="db-connection-select"
                  label="Target Connection"
                  value={form.dbConnectionId}
                  onChange={(e) => handleFormChange("dbConnectionId", e.target.value)}
                >
                  <MenuItem value="">Metadata Connection</MenuItem>
                  {dbConnections.map((conn) => (
                    <MenuItem key={conn.conid} value={conn.conid}>
                      {conn.connm}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={form.isActive}
                    onChange={(e) => handleFormChange("isActive", e.target.checked)}
                  />
                }
                label="Active"
              />
            </Grid>
            <Grid item xs={12} md={1}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  setSqlLookupOpen(true);
                  setSqlLookupSearch("");
                }}
              >
                Lookup
              </Button>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                minRows={4}
                maxRows={4}
                InputProps={{ sx: { overflowY: "auto" } }}
                label="SQL Text"
                value={form.sqlMode === "ADHOC" ? form.adhocSql : sqlPreviewText}
                onChange={(e) => handleSqlTextChange(e.target.value)}
                placeholder="Type SQL or use the Lookup button to pull from Manage SQL"
              />
              {!!form.sqlSourceId && (
                <Stack direction="row" spacing={1} alignItems="center" mt={1}>
                  <Chip
                    label={`Using ${resolveSqlSourceLabel(sqlSources.find((src) => src.id === form.sqlSourceId)) || `SQL-${form.sqlSourceId}`}`}
                    onDelete={clearSqlSourceSelection}
                    variant="outlined"
                  />
                  {resolveConnectionName(form.dbConnectionId) && (
                    <Typography variant="caption" color="text.secondary">
                      Connection: {resolveConnectionName(form.dbConnectionId)}
                    </Typography>
                  )}
                </Stack>
              )}
            </Grid>
          </Grid>
        </PanelCard>

        <PanelCard
          title="Details Panel"
          subtitle="Map SQL columns, capture formulas, and control grouping and ordering."
          darkMode={darkMode}
          actions={
            <Button
              variant="outlined"
              size="small"
              startIcon={<AutoAwesome />}
              onClick={handleImportColumns}
              disabled={importingColumns || (!sqlPreviewText && !form.adhocSql)}
            >
              {importingColumns ? "Importing..." : "Import Columns"}
            </Button>
          }
        >
          <Stack spacing={2}>
            {groupByAlert.show && (
              <Alert severity="warning">
                Group By is selected. Ensure non-grouped fields use aggregate formulas. Review:{" "}
                {groupByAlert.fields.join(", ")}
              </Alert>
            )}
            <FieldPanel
              title="Report Field Mapping"
              actions={
                <Button size="small" startIcon={<Add />} onClick={addRow}>
                  Add Row
                </Button>
              }
              darkMode={darkMode}
            >
              <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ width: 50 }}>#</TableCell>
                    <TableCell>Report Field</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Source Column</TableCell>
                  <TableCell>Formula</TableCell>
                  <TableCell align="center">Group By</TableCell>
                  <TableCell>Order Seq</TableCell>
                  <TableCell>Order Dir</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {reportRows.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={9} align="center">
                        <Typography variant="body2" color="text.secondary">
                          No rows. Click Add Row to add fields.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                  {reportRows.map((row, index) => (
                    <TableRow key={row.tempId} hover sx={{ '& td': { py: 1 } }}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          size="small"
                          value={row.fieldName}
                          onChange={(e) => updateRow(row.tempId, "fieldName", e.target.value)}
                          placeholder="Report field"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          size="small"
                          value={row.fieldDescription}
                          onChange={(e) => updateRow(row.tempId, "fieldDescription", e.target.value)}
                          placeholder="Description"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          size="small"
                          value={row.sourceColumn}
                          onChange={(e) => updateRow(row.tempId, "sourceColumn", e.target.value)}
                          placeholder="e.g. SRC_COLUMN"
                        />
                      </TableCell>
                      <TableCell>
                        <TextField
                          fullWidth
                          size="small"
                          value={row.formulaText}
                          onChange={(e) => updateRow(row.tempId, "formulaText", e.target.value)}
                          placeholder="CASE WHEN ..."
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Checkbox
                          checked={Boolean(row.isGroupBy)}
                          onChange={(e) => updateRow(row.tempId, "isGroupBy", e.target.checked)}
                        />
                      </TableCell>
                      <TableCell sx={{ minWidth: 110 }}>
                        <TextField
                          fullWidth
                          size="small"
                          type="number"
                          value={row.orderBySeq}
                          onChange={(e) => updateRow(row.tempId, "orderBySeq", e.target.value)}
                          placeholder="1"
                          InputProps={{ inputProps: { min: 1 } }}
                        />
                      </TableCell>
                      <TableCell sx={{ minWidth: 120 }}>
                        <FormControl fullWidth size="small">
                          <Select
                            value={row.orderByDir}
                            onChange={(e) => updateRow(row.tempId, "orderByDir", e.target.value)}
                          >
                            <MenuItem value="ASC">ASC</MenuItem>
                            <MenuItem value="DESC">DESC</MenuItem>
                          </Select>
                        </FormControl>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Remove row">
                          <span>
                            <IconButton size="small" onClick={() => removeRow(row.tempId)} disabled={reportRows.length === 1}>
                              <DeleteOutline fontSize="small" />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              </TableContainer>
            </FieldPanel>
          </Stack>
        </PanelCard>

        <PanelCard
          title="Preview Panel"
          subtitle="Validate sample data."
          darkMode={darkMode}
          actions={
            <Stack direction="row" spacing={1} alignItems="center">
              <TextField
                size="small"
                type="number"
                label="Limit Rows"
                value={form.previewRowLimit}
                onChange={(e) => handleFormChange("previewRowLimit", Number(e.target.value))}
                InputProps={{ inputProps: { min: 1, max: 1000 } }}
                sx={{ width: 120 }}
              />
              {(preview.finalSql || finalSql) && (
                <Button
                  variant="text"
                  size="small"
                  onClick={() => setShowFinalSql(true)}
                >
                  View SQL
                </Button>
              )}
              <Button
                variant="outlined"
                size="small"
                startIcon={<Visibility />}
                onClick={handlePreview}
                disabled={!selectedReportId || preview.loading}
              >
                {preview.loading ? "Loading..." : "Preview"}
              </Button>
            </Stack>
          }
        >
          <Stack spacing={2}>
            {preview.loading ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress size={28} />
              </Box>
            ) : preview.rows.length ? (
              <Box sx={{ maxHeight: 320, overflow: "auto" }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ width: 50 }}>#</TableCell>
                      {preview.columns.map((col) => (
                        <TableCell key={col}>{col}</TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {preview.rows.map((row, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{idx + 1}</TableCell>
                        {preview.columns.map((col) => (
                          <TableCell key={`${idx}-${col}`}>{row[col]}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>
            ) : (
              <Box py={3} textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  Save the report and run a preview to view sample rows.
                </Typography>
              </Box>
            )}
          </Stack>
        </PanelCard>
      </Stack>

      <Dialog open={executeDialog} onClose={() => setExecuteDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>Execute Report</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2} mt={1}>
            <TextField
              type="number"
              label="Row Limit"
              value={executeOptions.rowLimit}
              onChange={(e) =>
                setExecuteOptions((prev) => ({ ...prev, rowLimit: Number(e.target.value) || 0 }))
              }
            />
            <FormControl fullWidth>
              <InputLabel id="execute-format-select">Output Formats</InputLabel>
              <Select
                labelId="execute-format-select"
                multiple
                label="Output Formats"
                value={executeOptions.outputFormats}
                onChange={(e) =>
                  setExecuteOptions((prev) => ({ ...prev, outputFormats: e.target.value }))
                }
                renderValue={(selected) => selected.join(", ")}
              >
                {OUTPUT_FORMATS.map((format) => (
                  <MenuItem key={format} value={format}>
                    <Checkbox checked={executeOptions.outputFormats.indexOf(format) > -1} />
                    <ListItemText primary={format} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialog(false)}>Cancel</Button>
          <Button variant="contained" startIcon={<PlayArrow />} onClick={confirmExecute}>
            Queue Execution
          </Button>
        </DialogActions>
      </Dialog>

      <SqlLookupDialog
        open={sqlLookupOpen}
        onClose={() => {
          setSqlLookupOpen(false);
          setSqlLookupSearch("");
        }}
        sources={sqlSources}
        search={sqlLookupSearch}
        onSearchChange={setSqlLookupSearch}
        onSelect={handleSqlLookupSelect}
        resolveConnectionName={resolveConnectionName}
        resolveSqlSourceLabel={resolveSqlSourceLabel}
      />

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

      <Dialog open={showFinalSql} onClose={() => setShowFinalSql(false)} fullWidth maxWidth="md">
        <DialogTitle>Final SQL</DialogTitle>
        <DialogContent dividers>
          <Paper
            variant="outlined"
            sx={{ p: 2, backgroundColor: darkMode ? "rgba(17,24,39,0.7)" : "#fafafa", maxHeight: 400, overflow: "auto" }}
          >
            <Typography
              component="pre"
              sx={{ m: 0, fontFamily: "monospace", fontSize: 13, whiteSpace: "pre-wrap" }}
            >
              {preview.finalSql || finalSql}
            </Typography>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFinalSql(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

const SqlLookupDialog = ({
  open,
  onClose,
  sources,
  search,
  onSearchChange,
  onSelect,
  resolveConnectionName,
  resolveSqlSourceLabel,
}) => {
  const normalizedSearch = search.trim().toLowerCase();
  const filteredSources = normalizedSearch
    ? sources.filter((source) => {
        const label = resolveSqlSourceLabel(source).toLowerCase();
        const connectionName = (resolveConnectionName(source.connectionId) || "").toLowerCase();
        return label.includes(normalizedSearch) || connectionName.includes(normalizedSearch);
      })
    : sources;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>Manage SQL Lookup</DialogTitle>
      <DialogContent dividers>
        <TextField
          fullWidth
          autoFocus
          label="Search by code or connection"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        <Stack spacing={1.5} mt={2}>
          {filteredSources.map((source) => {
            const label = resolveSqlSourceLabel(source);
            const connectionName = resolveConnectionName(source.connectionId);
            return (
              <Paper key={source.id} variant="outlined" sx={{ p: 1.5 }}>
                <Stack
                  direction={{ xs: "column", md: "row" }}
                  spacing={1}
                  alignItems={{ xs: "flex-start", md: "center" }}
                  justifyContent="space-between"
                >
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      {label || `SQL-${source.id}`}
                    </Typography>
                    {connectionName && (
                      <Typography variant="caption" color="text.secondary">
                        Connection: {connectionName}
                      </Typography>
                    )}
                  </Box>
                  <Button variant="contained" size="small" onClick={() => onSelect(source)}>
                    Use SQL
                  </Button>
                </Stack>
              </Paper>
            );
          })}
          {!filteredSources.length && (
            <Typography variant="body2" color="text.secondary">
              No SQL entries match your search.
            </Typography>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

const PanelCard = ({ title, subtitle, children, actions, darkMode }) => (
  <Paper
    elevation={darkMode ? 0 : 1}
    sx={{
      p: 2.5,
      borderRadius: 2,
      border: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)",
    }}
  >
    <Stack direction={{ xs: "column", sm: "row" }} alignItems={subtitle ? "flex-start" : "center"} justifyContent="space-between" spacing={0.8} mb={1.5}>
      <Box>
        <Typography variant="subtitle1" fontWeight={600}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
      {actions}
    </Stack>
    <Divider sx={{ mb: 1.5 }} />
    {children}
  </Paper>
);

const FieldPanel = ({ title, actions, children, darkMode }) => (
  <Paper
    variant="outlined"
    sx={{
      borderRadius: 2,
      border: darkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.08)",
      backgroundColor: darkMode ? "rgba(17,24,39,0.7)" : "#fff",
      p: 1.5,
    }}
  >
    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1.5}>
      <Typography variant="subtitle2" fontWeight={600}>
        {title}
      </Typography>
      {actions}
    </Stack>
    {children}
  </Paper>
);

export default ReportsPage;

