"use client";

import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Stack,
  Step,
  StepLabel,
  Stepper,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { Add, ArrowBack, DeleteOutline, Edit, PlayArrow, Refresh, Save, Visibility } from "@mui/icons-material";
import { useTheme } from "@/context/ThemeContext";
import { Bar, Line, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const defaultForm = {
  dashboardName: "",
  description: "",
  isActive: true,
};

const createWidgetDraft = () => ({
  widgetName: "",
  widgetType: "TABLE",
  sourceMode: "SQL",
  dbConnectionId: "",
  adhocSql: "",
  layoutSlot: "TOP_LEFT",
  isActive: true,
});

const widgetLayoutOptions = [
  { value: "TOP_LEFT", label: "Top Left" },
  { value: "TOP_RIGHT", label: "Top Right" },
  { value: "MIDDLE_LEFT", label: "Middle Left" },
  { value: "MIDDLE_RIGHT", label: "Middle Right" },
  { value: "BOTTOM_LEFT", label: "Bottom Left" },
  { value: "BOTTOM_RIGHT", label: "Bottom Right" },
  { value: "BOTTOM_FULL", label: "Bottom Full Width" },
];

const layoutOrderMap = {
  TOP_LEFT: 1,
  TOP_RIGHT: 2,
  MIDDLE_LEFT: 3,
  MIDDLE_RIGHT: 4,
  BOTTOM_LEFT: 5,
  BOTTOM_RIGHT: 6,
  BOTTOM_FULL: 7,
};

const defaultLayoutSequence = [
  "TOP_LEFT",
  "TOP_RIGHT",
  "MIDDLE_LEFT",
  "MIDDLE_RIGHT",
  "BOTTOM_LEFT",
  "BOTTOM_RIGHT",
  "BOTTOM_FULL",
];

const slotToLayoutJson = (slot, index) => {
  const slotMap = {
    TOP_LEFT: { x: 0, y: 0, w: 6, h: 4 },
    TOP_RIGHT: { x: 6, y: 0, w: 6, h: 4 },
    MIDDLE_LEFT: { x: 0, y: 4, w: 6, h: 4 },
    MIDDLE_RIGHT: { x: 6, y: 4, w: 6, h: 4 },
    BOTTOM_LEFT: { x: 0, y: 8, w: 6, h: 4 },
    BOTTOM_RIGHT: { x: 6, y: 8, w: 6, h: 4 },
    BOTTOM_FULL: { x: 0, y: 12, w: 12, h: 4 },
  };
  const fallback = { x: 0, y: index * 2, w: 12, h: 6 };
  const chosen = slotMap[slot] || fallback;
  return JSON.stringify({ slot: slot || "AUTO", ...chosen });
};

const parseLayoutSlot = (layoutJson) => {
  if (!layoutJson) return "TOP_LEFT";
  try {
    const parsed = typeof layoutJson === "string" ? JSON.parse(layoutJson) : layoutJson;
    if (parsed?.slot && layoutOrderMap[parsed.slot]) {
      return parsed.slot;
    }
  } catch (_error) {
  }
  return "TOP_LEFT";
};

const DashboardCreatorPage = () => {
  const { darkMode } = useTheme();
  const apiBase = process.env.NEXT_PUBLIC_API_URL;
  const wizardSteps = [
    "Dashboard Details",
    "Data Source & SQL",
    "Preview & Chart",
    "Widget Assembly",
    "Save & Export",
  ];

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dashboards, setDashboards] = useState([]);
  const [selectedDashboardId, setSelectedDashboardId] = useState(null);
  const [form, setForm] = useState(defaultForm);
  const [isEditMode, setIsEditMode] = useState(false);

  const [sqlSources, setSqlSources] = useState([]);
  const [dbConnections, setDbConnections] = useState([]);
  const [widgets, setWidgets] = useState([]);
  const [widgetDraft, setWidgetDraft] = useState(createWidgetDraft());
  const [editingWidgetIndex, setEditingWidgetIndex] = useState(null);
  const [rowLimit, setRowLimit] = useState(100);
  const [sqlDescribe, setSqlDescribe] = useState([]);
  const [preview, setPreview] = useState({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
  const [previewLoading, setPreviewLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [chartXAxis, setChartXAxis] = useState("");
  const [chartYAxis, setChartYAxis] = useState("");
  const [exportHistory, setExportHistory] = useState([]);
  const [loadingExportHistory, setLoadingExportHistory] = useState(false);

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [notification, setNotification] = useState({ open: false, message: "", severity: "info" });
  const [activeStep, setActiveStep] = useState(0);
  const [isWizardMode, setIsWizardMode] = useState(true);
  const [wizardDialogOpen, setWizardDialogOpen] = useState(false);
  const [viewMode, setViewMode] = useState("creator");
  const [dashboardOutput, setDashboardOutput] = useState([]);
  const [loadingDashboardOutput, setLoadingDashboardOutput] = useState(false);
  const [draggingWidgetIndex, setDraggingWidgetIndex] = useState(null);
  const [showCreatorScreen, setShowCreatorScreen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const showNotification = (message, severity = "info") => {
    setNotification({ open: true, message, severity });
  };

  const closeNotification = () => {
    setNotification((prev) => ({ ...prev, open: false }));
  };

  const fetchDashboards = async () => {
    const response = await axios.get(`${apiBase}/api/dashboards`);
    setDashboards(response.data?.data || []);
  };

  const fetchSqlSources = async () => {
    const response = await axios.get(`${apiBase}/api/dashboards/sql-sources`);
    setSqlSources(response.data?.data || []);
  };

  const fetchConnections = async () => {
    const response = await axios.get(`${apiBase}/api/dbconnections`);
    setDbConnections(response.data?.data || []);
  };

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchDashboards(), fetchSqlSources(), fetchConnections()]);
      showNotification("Dashboard Creator workspace loaded", "success");
    } catch (error) {
      showNotification("Failed to load Dashboard Creator workspace", "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchExportHistory = async (dashboardId = null) => {
    setLoadingExportHistory(true);
    try {
      const endpoint = dashboardId
        ? `${apiBase}/api/dashboards/${dashboardId}/export-history?limit=50`
        : `${apiBase}/api/dashboards/export-history?limit=50`;
      const response = await axios.get(endpoint);
      setExportHistory(response.data?.data || []);
    } catch (error) {
      showNotification("Failed to load export history", "error");
    } finally {
      setLoadingExportHistory(false);
    }
  };

  const loadDashboardOutput = async (widgetsPayload) => {
    const widgetsToLoad = widgetsPayload || [];
    if (!widgetsToLoad.length) {
      setDashboardOutput([]);
      return;
    }

    setLoadingDashboardOutput(true);
    try {
      const responses = await Promise.all(
        widgetsToLoad.map(async (widget, index) => {
          if (!widget?.adhocSql?.trim()) {
            return {
              index,
              widget,
              data: { columns: [], rows: [], rowCount: 0, sourceDbType: null },
              error: "No SQL configured",
            };
          }

          try {
            const response = await axios.post(`${apiBase}/api/dashboards/preview-widget`, {
              sqlText: widget.adhocSql,
              dbConnectionId: widget.dbConnectionId ? Number(widget.dbConnectionId) : null,
              rowLimit: Number(rowLimit) || 100,
            });
            return {
              index,
              widget,
              data: response.data?.data || { columns: [], rows: [], rowCount: 0, sourceDbType: null },
              error: null,
            };
          } catch (error) {
            return {
              index,
              widget,
              data: { columns: [], rows: [], rowCount: 0, sourceDbType: null },
              error: error.response?.data?.message || "Failed to load widget output",
            };
          }
        })
      );

      setDashboardOutput(responses);
    } finally {
      setLoadingDashboardOutput(false);
    }
  };

  const resetBuilder = () => {
    setSelectedDashboardId(null);
    setIsEditMode(false);
    setForm(defaultForm);
    setWidgets([]);
    setWidgetDraft(createWidgetDraft());
    setEditingWidgetIndex(null);
    setSqlDescribe([]);
    setPreview({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
    setActiveStep(0);
    setIsWizardMode(true);
    setWizardDialogOpen(false);
    setViewMode("creator");
    setDashboardOutput([]);
    setShowCreatorScreen(false);
    setViewDialogOpen(false);
    setDeleteTarget(null);
  };

  useEffect(() => {
    fetchInitialData();
    fetchExportHistory();
  }, []);

  const selectedDashboard = useMemo(
    () => dashboards.find((item) => item.dashboardId === selectedDashboardId) || null,
    [dashboards, selectedDashboardId]
  );

  const handleSelectDashboard = async (dashboardId) => {
    if (!dashboardId) {
      resetBuilder();
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`${apiBase}/api/dashboards/${dashboardId}`);
      const data = response.data?.data;
      setSelectedDashboardId(data.dashboardId);
      setIsEditMode(true);
      setForm({
        dashboardName: data.dashboardName || "",
        description: data.description || "",
        isActive: data.isActive ?? true,
      });

      const loadedWidgets = (data.widgets || []).map((widget) => ({
        widgetName: widget.widgetName || "",
        widgetType: widget.widgetType || "TABLE",
        sourceMode: widget.sourceMode || "SQL",
        dbConnectionId: widget.dbConnectionId ? String(widget.dbConnectionId) : "",
        adhocSql: widget.adhocSql || "",
        layoutSlot: parseLayoutSlot(widget.layoutJson),
        isActive: widget.isActive ?? true,
      }));

      setWidgets(loadedWidgets);
      setWidgetDraft(createWidgetDraft());
      setEditingWidgetIndex(null);

      setSqlDescribe([]);
      setPreview({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
      setViewMode("viewer");
      await fetchExportHistory(data.dashboardId);
      await loadDashboardOutput(loadedWidgets);
    } catch (error) {
      showNotification("Failed to load dashboard details", "error");
    } finally {
      setLoading(false);
    }
  };

  const buildPayload = () => {
    const payload = {
      dashboardName: form.dashboardName?.trim(),
      description: form.description,
      isActive: Boolean(form.isActive),
      widgets: widgets
        .filter((widget) => widget.adhocSql?.trim())
        .map((widget, index) => ({
          widgetName: widget.widgetName?.trim() || `Widget ${index + 1}`,
          widgetType: widget.widgetType || "TABLE",
          sourceMode: widget.sourceMode || "SQL",
          adhocSql: widget.adhocSql,
          dbConnectionId: widget.dbConnectionId ? Number(widget.dbConnectionId) : null,
          configJson: JSON.stringify({
            chartType: widget.widgetType || "TABLE",
            generatedBy: "dashboard_creator_v1",
          }),
          layoutJson: slotToLayoutJson(widget.layoutSlot || "TOP_LEFT", index),
          isActive: widget.isActive ?? true,
        })),
    };

    return payload;
  };

  const handleClearWidgetDraft = () => {
    setWidgetDraft(createWidgetDraft());
    setEditingWidgetIndex(null);
    setSqlDescribe([]);
    setPreview({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
    setChartXAxis("");
    setChartYAxis("");
  };

  const handleStartAddWidget = () => {
    setWidgetDraft(createWidgetDraft());
    setEditingWidgetIndex(null);
    setSqlDescribe([]);
    setPreview({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
    setChartXAxis("");
    setChartYAxis("");
  };

  const handleSaveWidget = () => {
    if (!widgetDraft.widgetName?.trim()) {
      showNotification("Widget name is required", "warning");
      return;
    }
    if (!widgetDraft.adhocSql?.trim()) {
      showNotification("Widget SQL is required", "warning");
      return;
    }

    const normalizedWidget = {
      ...widgetDraft,
      widgetName: widgetDraft.widgetName.trim(),
      widgetType: widgetDraft.widgetType || "TABLE",
      sourceMode: "SQL",
      adhocSql: widgetDraft.adhocSql,
      dbConnectionId: widgetDraft.dbConnectionId || "",
      layoutSlot: widgetDraft.layoutSlot || "TOP_LEFT",
      isActive: widgetDraft.isActive ?? true,
    };

    setWidgets((prev) => {
      const next = [...prev];
      if (editingWidgetIndex !== null && editingWidgetIndex >= 0 && editingWidgetIndex < next.length) {
        next[editingWidgetIndex] = normalizedWidget;
      } else {
        next.push(normalizedWidget);
      }
      return next;
    });

    showNotification(editingWidgetIndex !== null ? "Widget updated in draft" : "Widget added to draft", "success");
    setEditingWidgetIndex(null);
    setWidgetDraft(createWidgetDraft());
  };

  const handleEditWidget = (index) => {
    const selected = widgets[index];
    if (!selected) return;
    setEditingWidgetIndex(index);
    setWidgetDraft({ ...selected });
    setSqlDescribe([]);
    setPreview({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
    setChartXAxis("");
    setChartYAxis("");
  };

  const handleWidgetDragStart = (index) => {
    setDraggingWidgetIndex(index);
  };

  const handleWidgetDragEnd = () => {
    setDraggingWidgetIndex(null);
  };

  const handleWidgetDropToSlot = (slot) => {
    if (draggingWidgetIndex === null || draggingWidgetIndex < 0) {
      return;
    }

    setWidgets((prev) => {
      const next = [...prev];
      if (!next[draggingWidgetIndex]) {
        return prev;
      }
      next[draggingWidgetIndex] = {
        ...next[draggingWidgetIndex],
        layoutSlot: slot,
      };
      return next;
    });

    if (editingWidgetIndex === draggingWidgetIndex) {
      setWidgetDraft((prev) => ({ ...prev, layoutSlot: slot }));
    }

    showNotification(`Widget moved to ${slot.replace("_", " ")}`, "success");
    setDraggingWidgetIndex(null);
  };

  const handleResetLayout = () => {
    if (!widgets.length) {
      showNotification("No widgets available to reset layout", "info");
      return;
    }

    setWidgets((prev) =>
      prev.map((widget, index) => ({
        ...widget,
        layoutSlot: defaultLayoutSequence[index % defaultLayoutSequence.length],
      }))
    );

    if (editingWidgetIndex !== null && widgets[editingWidgetIndex]) {
      const newSlot = defaultLayoutSequence[editingWidgetIndex % defaultLayoutSequence.length];
      setWidgetDraft((prev) => ({ ...prev, layoutSlot: newSlot }));
    }

    showNotification("Layout reset to default positions", "success");
  };

  const renderLayoutBoard = () => (
    <Box sx={{ mt: 1.5 }}>
      <Typography variant="subtitle2" fontWeight={600} mb={1}>Drag & Drop Layout</Typography>
      <Typography variant="caption" color="text.secondary" display="block" mb={1.25}>
        Drag a widget row (or chip) and drop it into the target position.
      </Typography>
      <Grid container spacing={1.25}>
        {widgetLayoutOptions.map((slotOption) => {
          const slotWidgets = widgets
            .map((widget, index) => ({ ...widget, _index: index }))
            .filter((widget) => (widget.layoutSlot || "TOP_LEFT") === slotOption.value);

          const isDropTargetActive = draggingWidgetIndex !== null;
          return (
            <Grid item xs={12} md={slotOption.value === "BOTTOM_FULL" ? 12 : 6} key={`layout-slot-${slotOption.value}`}>
              <Paper
                variant="outlined"
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  handleWidgetDropToSlot(slotOption.value);
                }}
                sx={{
                  p: 1.25,
                  minHeight: 86,
                  borderStyle: "dashed",
                  borderColor: isDropTargetActive ? "primary.main" : "divider",
                  backgroundColor: isDropTargetActive ? "action.hover" : "transparent",
                }}
              >
                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={0.75}>
                  <Typography variant="caption" fontWeight={700}>{slotOption.label}</Typography>
                  <Chip size="small" label={`${slotWidgets.length} widget${slotWidgets.length === 1 ? "" : "s"}`} />
                </Stack>

                {slotWidgets.length === 0 ? (
                  <Typography variant="caption" color="text.secondary">Drop widget here</Typography>
                ) : (
                  <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
                    {slotWidgets.map((slotWidget) => (
                      <Chip
                        key={`slot-widget-${slotWidget._index}`}
                        label={slotWidget.widgetName || `Widget ${slotWidget._index + 1}`}
                        draggable
                        onDragStart={() => handleWidgetDragStart(slotWidget._index)}
                        onDragEnd={handleWidgetDragEnd}
                        onClick={() => handleEditWidget(slotWidget._index)}
                        sx={{ cursor: "grab" }}
                      />
                    ))}
                  </Stack>
                )}
              </Paper>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );

  const getNumericColumns = (columns, rows) => {
    if (!columns?.length || !rows?.length) return [];
    return columns.filter((column) => {
      for (const row of rows) {
        const value = row?.[column];
        if (value === null || value === undefined || value === "") continue;
        const parsed = Number(value);
        return Number.isFinite(parsed);
      }
      return false;
    });
  };

  const buildChartDataset = () => {
    const rows = preview?.rows || [];
    const columns = preview?.columns || [];
    if (!rows.length || !columns.length) return null;

    const xColumn = chartXAxis || columns[0];
    const numericColumns = getNumericColumns(columns, rows);
    const yColumn = chartYAxis || numericColumns[0] || columns[1] || columns[0];
    if (!xColumn || !yColumn) return null;

    const labels = rows.slice(0, 30).map((row) => String(row?.[xColumn] ?? ""));
    const values = rows.slice(0, 30).map((row) => {
      const parsed = Number(row?.[yColumn]);
      return Number.isFinite(parsed) ? parsed : 0;
    });

    const palette = [
      "rgba(59, 130, 246, 0.75)",
      "rgba(16, 185, 129, 0.75)",
      "rgba(245, 158, 11, 0.75)",
      "rgba(239, 68, 68, 0.75)",
      "rgba(139, 92, 246, 0.75)",
      "rgba(20, 184, 166, 0.75)",
    ];

    return {
      labels,
      datasets: [
        {
          label: `${yColumn} by ${xColumn}`,
          data: values,
          backgroundColor:
            widgetDraft.widgetType === "PIE"
              ? labels.map((_, index) => palette[index % palette.length])
              : "rgba(59, 130, 246, 0.75)",
          borderColor: "rgba(59, 130, 246, 1)",
          borderWidth: 1,
          fill: widgetDraft.widgetType === "AREA",
          tension: 0.25,
        },
      ],
      xColumn,
      yColumn,
    };
  };

  const buildChartDatasetFromData = ({ rows, columns, widgetType, xAxis = "", yAxis = "" }) => {
    const safeRows = rows || [];
    const safeColumns = columns || [];
    if (!safeRows.length || !safeColumns.length) return null;

    const xColumn = xAxis || safeColumns[0];
    const numericColumns = getNumericColumns(safeColumns, safeRows);
    const yColumn = yAxis || numericColumns[0] || safeColumns[1] || safeColumns[0];
    if (!xColumn || !yColumn) return null;

    const labels = safeRows.slice(0, 30).map((row) => String(row?.[xColumn] ?? ""));
    const values = safeRows.slice(0, 30).map((row) => {
      const parsed = Number(row?.[yColumn]);
      return Number.isFinite(parsed) ? parsed : 0;
    });

    const palette = [
      "rgba(59, 130, 246, 0.75)",
      "rgba(16, 185, 129, 0.75)",
      "rgba(245, 158, 11, 0.75)",
      "rgba(239, 68, 68, 0.75)",
      "rgba(139, 92, 246, 0.75)",
      "rgba(20, 184, 166, 0.75)",
    ];

    return {
      labels,
      datasets: [
        {
          label: `${yColumn} by ${xColumn}`,
          data: values,
          backgroundColor:
            widgetType === "PIE" ? labels.map((_, index) => palette[index % palette.length]) : "rgba(59, 130, 246, 0.75)",
          borderColor: "rgba(59, 130, 246, 1)",
          borderWidth: 1,
          fill: widgetType === "AREA",
          tension: 0.25,
        },
      ],
      xColumn,
      yColumn,
    };
  };

  const handleRemoveWidget = (index) => {
    setWidgets((prev) => prev.filter((_, itemIndex) => itemIndex !== index));
    if (editingWidgetIndex === index) {
      setWidgetDraft(createWidgetDraft());
      setEditingWidgetIndex(null);
    }
    showNotification("Widget removed from draft", "info");
  };

  const handleSave = async () => {
    if (!form.dashboardName?.trim()) {
      showNotification("Dashboard name is required", "warning");
      return;
    }

    if (widgets.length === 0) {
      showNotification("Add at least one widget before saving", "warning");
      return;
    }

    setSaving(true);
    try {
      const payload = buildPayload();
      let savedDashboardId = selectedDashboardId;
      if (isEditMode && selectedDashboardId) {
        await axios.put(`${apiBase}/api/dashboards/${selectedDashboardId}`, payload);
        showNotification("Dashboard updated", "success");
      } else {
        const response = await axios.post(`${apiBase}/api/dashboards`, payload);
        savedDashboardId = response.data?.data?.dashboardId || null;
        setSelectedDashboardId(savedDashboardId);
        setIsEditMode(true);
        setViewMode("viewer");
        showNotification("Dashboard created", "success");
      }

      await fetchDashboards();
      await fetchExportHistory(savedDashboardId || null);
      await loadDashboardOutput(widgets);
      return savedDashboardId;
    } catch (error) {
      showNotification(error.response?.data?.message || "Failed to save dashboard", "error");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const validateStep = (stepIndex) => {
    if (stepIndex === 0) {
      if (!form.dashboardName?.trim()) {
        showNotification("Step 1: Enter Dashboard Name", "warning");
        return false;
      }
      return true;
    }

    if (stepIndex === 1) {
      if (!widgetDraft.widgetName?.trim()) {
        showNotification("Step 2: Enter Widget Name", "warning");
        return false;
      }
      if (!widgetDraft.adhocSql?.trim()) {
        showNotification("Step 2: Enter SQL query", "warning");
        return false;
      }
      return true;
    }

    if (stepIndex === 2) {
      if (!preview?.rows?.length) {
        showNotification("Step 3: Click Preview to generate chart/data", "warning");
        return false;
      }
      return true;
    }

    if (stepIndex === 3) {
      if (!widgets.length) {
        showNotification("Step 4: Add at least one widget to draft", "warning");
        return false;
      }
      return true;
    }

    return true;
  };

  const handleWizardNext = () => {
    if (!isWizardMode) {
      return;
    }
    if (!validateStep(activeStep)) {
      return;
    }
    setActiveStep((prev) => Math.min(prev + 1, wizardSteps.length - 1));
  };

  const handleWizardBack = () => {
    if (!isWizardMode) {
      return;
    }
    setActiveStep((prev) => Math.max(prev - 1, 0));
  };

  const handleModeChange = (mode) => {
    if (mode === "wizard") {
      setIsWizardMode(true);
      setActiveStep(0);
      setWizardDialogOpen(true);
      showNotification("Wizard mode enabled", "info");
      return;
    }

    setIsWizardMode(false);
    setWizardDialogOpen(false);
    setActiveStep(wizardSteps.length - 1);
    showNotification("Advanced mode enabled", "info");
  };

  const handleWizardFinish = async () => {
    const savedDashboardId = await handleSave();
    if (!savedDashboardId) {
      return;
    }
    await handleSelectDashboard(savedDashboardId);
    setWizardDialogOpen(false);
    setIsWizardMode(false);
    setViewMode("viewer");
    showNotification("Wizard completed. Dashboard is now shown on main page.", "success");
  };

  const handleRefreshSelectedDashboard = async () => {
    if (!selectedDashboardId) {
      showNotification("Select a dashboard to refresh", "info");
      return;
    }
    await handleSelectDashboard(selectedDashboardId);
  };

  const handleAddNewDashboard = () => {
    setSelectedDashboardId(null);
    setIsEditMode(false);
    setForm(defaultForm);
    setWidgets([]);
    setWidgetDraft(createWidgetDraft());
    setEditingWidgetIndex(null);
    setSqlDescribe([]);
    setPreview({ columns: [], rows: [], rowCount: 0, sourceDbType: null });
    setViewMode("creator");
    setShowCreatorScreen(true);
    setIsWizardMode(false);
    setWizardDialogOpen(false);
  };

  const handleEditDashboard = async (dashboardId) => {
    await handleSelectDashboard(dashboardId);
    setViewMode("creator");
    setShowCreatorScreen(true);
    setIsWizardMode(false);
    setWizardDialogOpen(false);
  };

  const handleViewDashboard = async (dashboardId) => {
    await handleSelectDashboard(dashboardId);
    setViewDialogOpen(true);
  };

  const handleOpenDeleteDashboard = (dashboard) => {
    setDeleteTarget(dashboard || null);
    setSelectedDashboardId(dashboard?.dashboardId || selectedDashboardId);
    setDeleteDialogOpen(true);
  };

  const handleBackToDashboardList = async () => {
    setShowCreatorScreen(false);
    setViewMode("creator");
    await fetchDashboards();
  };

  const wizardHelpText = useMemo(() => {
    switch (activeStep) {
      case 0:
        return "Step 1: Enter dashboard name, owner, and description.";
      case 1:
        return "Step 2: Configure data source and SQL for a widget.";
      case 2:
        return "Step 3: Use Preview and validate chart/table output.";
      case 3:
        return "Step 4: Add/update widget in draft and verify widget list.";
      case 4:
        return "Step 5: Save dashboard and export to PDF/PPT.";
      default:
        return "Follow steps to create dashboard.";
    }
  }, [activeStep]);

  const handleExport = async (format) => {
    if (!selectedDashboardId) {
      showNotification("Select or save a dashboard before export", "warning");
      return;
    }

    setExporting(true);
    try {
      const response = await axios.post(
        `${apiBase}/api/dashboards/${selectedDashboardId}/export`,
        {
          format,
          rowLimit: Number(rowLimit) || 500,
        },
        {
          responseType: "blob",
        }
      );

      const extension = format === "PPT" ? "pptx" : "pdf";
      const defaultName = `${(form.dashboardName || "dashboard").replace(/[^a-zA-Z0-9-_]/g, "_")}.${extension}`;

      const contentDisposition = response.headers["content-disposition"] || "";
      const match = contentDisposition.match(/filename=\"?([^\";]+)\"?/i);
      const fileName = match?.[1] || defaultName;

      const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.setAttribute("download", fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(blobUrl);

      showNotification(`${format} export downloaded`, "success");
      await fetchExportHistory(selectedDashboardId);
    } catch (error) {
      showNotification(error.response?.data?.message || `Failed to export ${format}`, "error");
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    const targetDashboardId = deleteTarget?.dashboardId || selectedDashboardId;
    if (!targetDashboardId) return;

    try {
      await axios.delete(`${apiBase}/api/dashboards/${targetDashboardId}`);
      showNotification("Dashboard deleted", "success");
      setDeleteDialogOpen(false);
      setDeleteTarget(null);
      resetBuilder();
      await fetchDashboards();
      await fetchExportHistory();
    } catch (error) {
      showNotification("Failed to delete dashboard", "error");
    }
  };

  const handleDescribeSql = async () => {
    if (!widgetDraft.adhocSql?.trim()) {
      showNotification("Enter SQL text to describe columns", "warning");
      return;
    }

    try {
      const response = await axios.post(`${apiBase}/api/dashboards/describe-sql`, {
        sqlText: widgetDraft.adhocSql,
        dbConnectionId: widgetDraft.dbConnectionId ? Number(widgetDraft.dbConnectionId) : null,
      });
      setSqlDescribe(response.data?.data?.columns || []);
      showNotification("SQL columns described successfully", "success");
    } catch (error) {
      showNotification(error.response?.data?.message || "Failed to describe SQL", "error");
    }
  };

  const handlePreviewSql = async () => {
    if (!widgetDraft.adhocSql?.trim()) {
      showNotification("Enter SQL text to preview", "warning");
      return;
    }

    setPreviewLoading(true);
    try {
      const response = await axios.post(`${apiBase}/api/dashboards/preview-widget`, {
        sqlText: widgetDraft.adhocSql,
        dbConnectionId: widgetDraft.dbConnectionId ? Number(widgetDraft.dbConnectionId) : null,
        rowLimit: Number(rowLimit) || 100,
      });
      const previewData = response.data?.data || { columns: [], rows: [], rowCount: 0, sourceDbType: null };
      setPreview(previewData);

      const previewColumns = previewData?.columns || [];
      const previewRows = previewData?.rows || [];
      const numericColumns = getNumericColumns(previewColumns, previewRows);
      setChartXAxis(previewColumns[0] || "");
      setChartYAxis(numericColumns[0] || previewColumns[1] || previewColumns[0] || "");

      showNotification("Widget preview loaded", "success");
    } catch (error) {
      showNotification(error.response?.data?.message || "Failed to preview SQL", "error");
    } finally {
      setPreviewLoading(false);
    }
  };

  const panelBorder = darkMode ? "1px solid rgba(255,255,255,0.16)" : "1px solid rgba(0,0,0,0.05)";

  const renderDashboardViewerContent = () => {
    if (loadingDashboardOutput) {
      return <Box py={4} display="flex" justifyContent="center"><CircularProgress size={24} /></Box>;
    }

    if (dashboardOutput.length === 0) {
      return <Typography variant="body2" color="text.secondary">No widget output available.</Typography>;
    }

    return (
      <Grid container spacing={1.5}>
        {dashboardOutput
          .slice()
          .sort((a, b) => {
            const aSlot = a.widget?.layoutSlot || "TOP_LEFT";
            const bSlot = b.widget?.layoutSlot || "TOP_LEFT";
            return (layoutOrderMap[aSlot] || 999) - (layoutOrderMap[bSlot] || 999);
          })
          .map((widgetItem) => {
            const slot = widgetItem.widget?.layoutSlot || "TOP_LEFT";
            const isFull = slot === "BOTTOM_FULL";
            return (
              <Grid item xs={12} md={isFull ? 12 : 6} key={`viewer-widget-grid-${widgetItem.index}`}>
                <Paper variant="outlined" sx={{ p: 1.5, height: "100%" }}>
                  <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" mb={1}>
                    <Typography variant="subtitle2" fontWeight={600} color="text.primary">
                      {widgetItem.widget?.widgetName || `Widget ${widgetItem.index + 1}`}
                    </Typography>
                    <Stack direction="row" spacing={0.5}>
                      <Chip size="small" label={`Rows: ${widgetItem.data?.rowCount || 0}`} />
                    </Stack>
                  </Stack>

                  {widgetItem.error ? (
                    <Alert severity="warning">{widgetItem.error}</Alert>
                  ) : widgetItem.data?.rows?.length ? (
                    (() => {
                      const widgetType = (widgetItem.widget?.widgetType || "TABLE").toUpperCase();
                      if (widgetType === "TABLE") {
                        const totalRows = widgetItem.data?.rowCount || (widgetItem.data?.rows || []).length || 0;
                        const shownRows = (widgetItem.data?.rows || []).length;
                        return (
                          <Box>
                            <Typography variant="caption" color="text.secondary" display="block" mb={0.75}>
                              Rows shown: {shownRows.toLocaleString()} / {totalRows.toLocaleString()}
                            </Typography>
                            <Box sx={{ maxHeight: 380, overflow: "auto", border: "1px solid", borderColor: "divider", borderRadius: 1 }}>
                              <Table size="small" stickyHeader>
                                <TableHead>
                                  <TableRow>
                                    {(widgetItem.data.columns || []).map((column) => (
                                      <TableCell key={`viewer-col-${widgetItem.index}-${column}`}>{column}</TableCell>
                                    ))}
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {(widgetItem.data.rows || []).map((row, rowIndex) => (
                                    <TableRow key={`viewer-row-${widgetItem.index}-${rowIndex}`}>
                                      {(widgetItem.data.columns || []).map((column) => (
                                        <TableCell key={`viewer-cell-${widgetItem.index}-${rowIndex}-${column}`}>
                                          {String(row[column] ?? "")}
                                        </TableCell>
                                      ))}
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </Box>
                          </Box>
                        );
                      }

                      const chartModel = buildChartDatasetFromData({
                        rows: widgetItem.data.rows || [],
                        columns: widgetItem.data.columns || [],
                        widgetType,
                      });

                      if (!chartModel) {
                        return <Typography variant="body2" color="text.secondary">No chart data available.</Typography>;
                      }

                      const chartOptions = {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: true, position: "top" },
                        },
                      };

                      if (widgetType === "BAR") {
                        return <Box sx={{ height: 260 }}><Bar data={chartModel} options={chartOptions} /></Box>;
                      }
                      if (widgetType === "LINE" || widgetType === "AREA") {
                        return <Box sx={{ height: 260 }}><Line data={chartModel} options={chartOptions} /></Box>;
                      }
                      if (widgetType === "PIE") {
                        return <Box sx={{ height: 280 }}><Pie data={chartModel} options={chartOptions} /></Box>;
                      }
                      if (widgetType === "KPI") {
                        const values = chartModel.datasets?.[0]?.data || [];
                        const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                        return (
                          <Paper variant="outlined" sx={{ p: 2 }}>
                            <Typography variant="caption" color="text.secondary">KPI ({chartModel.yColumn})</Typography>
                            <Typography variant="h4" fontWeight={700}>{Number(total).toLocaleString()}</Typography>
                          </Paper>
                        );
                      }

                      return <Typography variant="body2" color="text.secondary">Unsupported widget type.</Typography>;
                    })()
                  ) : (
                    <Typography variant="body2" color="text.secondary">No data returned for this widget.</Typography>
                  )}
                </Paper>
              </Grid>
            );
          })}
      </Grid>
    );
  };

  if (!showCreatorScreen) {
    return (
      <Box sx={{ p: 2.5 }}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1.5} mb={2}>
          <Typography variant="h6" fontWeight={600} color="text.primary">Dashboards</Typography>
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" color="primary" startIcon={<Refresh />} onClick={fetchInitialData}>Refresh</Button>
            <Button variant="contained" color="primary" startIcon={<Add />} onClick={handleAddNewDashboard}>Add New Dashboard</Button>
          </Stack>
        </Stack>

        <Paper elevation={darkMode ? 0 : 1} sx={{ p: 2, borderRadius: 2, border: panelBorder }}>
          {loading ? (
            <Box py={4} display="flex" justifyContent="center"><CircularProgress size={24} /></Box>
          ) : dashboards.length === 0 ? (
            <Typography variant="body2" color="text.secondary">No dashboards available.</Typography>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Dashboard Name</TableCell>
                  <TableCell>Created Date</TableCell>
                  <TableCell>Widgets</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dashboards.map((dashboard) => (
                  <TableRow key={`list-dashboard-${dashboard.dashboardId}`} hover>
                    <TableCell>{dashboard.dashboardName}</TableCell>
                    <TableCell>{dashboard.createdAt ? new Date(dashboard.createdAt).toLocaleString() : "-"}</TableCell>
                    <TableCell>{dashboard.widgetCount || 0}</TableCell>
                    <TableCell>
                      <Chip size="small" label={dashboard.isActive ? "Active" : "Inactive"} color={dashboard.isActive ? "success" : "default"} />
                    </TableCell>
                    <TableCell align="right">
                      <Stack direction="row" spacing={1} justifyContent="flex-end">
                        <Button size="small" variant="outlined" color="info" startIcon={<Visibility />} onClick={() => handleViewDashboard(dashboard.dashboardId)}>View</Button>
                        <Button size="small" variant="outlined" color="primary" startIcon={<Edit />} onClick={() => handleEditDashboard(dashboard.dashboardId)}>Edit</Button>
                        <Button size="small" variant="outlined" color="error" startIcon={<DeleteOutline />} onClick={() => handleOpenDeleteDashboard(dashboard)}>Delete</Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Paper>

        <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} fullWidth maxWidth="xl">
          <DialogTitle>
            <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1}>
              <Typography variant="h6">View Dashboard: {form.dashboardName || (selectedDashboardId ? `#${selectedDashboardId}` : "-")}</Typography>
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" color="primary" size="small" onClick={handleRefreshSelectedDashboard} disabled={!selectedDashboardId || loadingDashboardOutput}>
                  {loadingDashboardOutput ? "Refreshing..." : "Refresh Dashboard"}
                </Button>
                <Button variant="outlined" size="small" onClick={() => handleExport("PDF")} disabled={exporting || !selectedDashboardId}>
                  {exporting ? "Exporting..." : "Export PDF"}
                </Button>
                <Button variant="outlined" size="small" onClick={() => handleExport("PPT")} disabled={exporting || !selectedDashboardId}>
                  {exporting ? "Exporting..." : "Export PPT"}
                </Button>
              </Stack>
            </Stack>
          </DialogTitle>
          <DialogContent dividers>{renderDashboardViewerContent()}</DialogContent>
          <DialogActions>
            <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>

        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Delete Dashboard</DialogTitle>
          <DialogContent>
            <Typography variant="body2">
              {deleteTarget
                ? `Delete dashboard "${deleteTarget.dashboardName}"? This action is permanent and cannot be retrieved.`
                : "Delete selected dashboard? This action is permanent and cannot be retrieved."}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button color="error" variant="contained" onClick={handleDelete}>Delete</Button>
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
    <Box sx={{ p: 2.5 }}>
      <Paper
        elevation={darkMode ? 0 : 1}
        sx={{
          p: 1.5,
          mb: 2,
          borderRadius: 2,
          border: panelBorder,
        }}
      >
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }} spacing={1}>
          <Typography variant="subtitle2" fontWeight={600} color="text.primary">Creation Mode</Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant={isWizardMode ? "contained" : "outlined"}
              onClick={() => handleModeChange("wizard")}
            >
              Start Wizard
            </Button>
            <Button
              variant={!isWizardMode ? "contained" : "outlined"}
              onClick={() => handleModeChange("advanced")}
            >
              Advanced Mode
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1.5} mb={2}>
        <Typography variant="h6" fontWeight={600} color="text.primary">Dashboards</Typography>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" startIcon={<ArrowBack />} onClick={handleBackToDashboardList}>Back to Dashboards</Button>
          <Button
            variant={viewMode === "viewer" ? "contained" : "outlined"}
            onClick={() => setViewMode("viewer")}
            disabled={!selectedDashboardId}
          >
            View Dashboard
          </Button>
          <Button
            variant={viewMode === "creator" ? "contained" : "outlined"}
            onClick={() => setViewMode("creator")}
          >
            Creator
          </Button>
          <Button variant="outlined" startIcon={<Refresh />} onClick={fetchInitialData}>Refresh</Button>
          <Button variant="outlined" onClick={handleRefreshSelectedDashboard} disabled={!selectedDashboardId}>Refresh Dashboard</Button>
          <Button variant="outlined" startIcon={<Add />} onClick={resetBuilder}>New Dashboard</Button>
          <Button variant="contained" startIcon={<Save />} onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </Stack>
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Paper
            elevation={darkMode ? 0 : 1}
            sx={{
              p: 2,
              borderRadius: 2,
              border: panelBorder,
            }}
          >
            {viewMode === "viewer" && selectedDashboardId ? (
              <>
                <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" mb={1.5}>
                  <Typography variant="subtitle1" fontWeight={600} color="text.primary">
                    Dashboard Output: {form.dashboardName || `#${selectedDashboardId}`}
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => loadDashboardOutput(widgets)}
                    disabled={loadingDashboardOutput}
                  >
                    {loadingDashboardOutput ? "Loading Output..." : "Refresh Output"}
                  </Button>
                </Stack>

                {loadingDashboardOutput ? (
                  <Box py={4} display="flex" justifyContent="center"><CircularProgress size={24} /></Box>
                ) : dashboardOutput.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No widget output available.</Typography>
                ) : (
                  <Grid container spacing={1.5}>
                    {dashboardOutput
                      .slice()
                      .sort((a, b) => {
                        const aSlot = a.widget?.layoutSlot || "TOP_LEFT";
                        const bSlot = b.widget?.layoutSlot || "TOP_LEFT";
                        return (layoutOrderMap[aSlot] || 999) - (layoutOrderMap[bSlot] || 999);
                      })
                      .map((widgetItem) => {
                        const slot = widgetItem.widget?.layoutSlot || "TOP_LEFT";
                        const isFull = slot === "BOTTOM_FULL";
                        return (
                      <Grid item xs={12} md={isFull ? 12 : 6} key={`viewer-widget-grid-${widgetItem.index}`}>
                      <Paper key={`viewer-widget-${widgetItem.index}`} variant="outlined" sx={{ p: 1.5, height: "100%" }}>
                        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" mb={1}>
                          <Typography variant="subtitle2" fontWeight={600} color="text.primary">
                            {widgetItem.widget?.widgetName || `Widget ${widgetItem.index + 1}`}
                          </Typography>
                          <Stack direction="row" spacing={0.5}>
                            <Chip size="small" label={`Rows: ${widgetItem.data?.rowCount || 0}`} />
                          </Stack>
                        </Stack>

                        {widgetItem.error ? (
                          <Alert severity="warning">{widgetItem.error}</Alert>
                        ) : widgetItem.data?.rows?.length ? (
                          (() => {
                            const widgetType = (widgetItem.widget?.widgetType || "TABLE").toUpperCase();
                            if (widgetType === "TABLE") {
                              const totalRows = widgetItem.data?.rowCount || (widgetItem.data?.rows || []).length || 0;
                              const shownRows = (widgetItem.data?.rows || []).length;
                              return (
                                <Box>
                                  <Typography variant="caption" color="text.secondary" display="block" mb={0.75}>
                                    Rows shown: {shownRows.toLocaleString()} / {totalRows.toLocaleString()}
                                  </Typography>
                                  <Box sx={{ maxHeight: 380, overflow: "auto", border: "1px solid", borderColor: "divider", borderRadius: 1 }}>
                                    <Table size="small" stickyHeader>
                                      <TableHead>
                                        <TableRow>
                                          {(widgetItem.data.columns || []).map((column) => (
                                            <TableCell key={`viewer-col-${widgetItem.index}-${column}`}>{column}</TableCell>
                                          ))}
                                        </TableRow>
                                      </TableHead>
                                      <TableBody>
                                        {(widgetItem.data.rows || []).map((row, rowIndex) => (
                                          <TableRow key={`viewer-row-${widgetItem.index}-${rowIndex}`}>
                                            {(widgetItem.data.columns || []).map((column) => (
                                              <TableCell key={`viewer-cell-${widgetItem.index}-${rowIndex}-${column}`}>
                                                {String(row[column] ?? "")}
                                              </TableCell>
                                            ))}
                                          </TableRow>
                                        ))}
                                      </TableBody>
                                    </Table>
                                  </Box>
                                </Box>
                              );
                            }

                            const chartModel = buildChartDatasetFromData({
                              rows: widgetItem.data.rows || [],
                              columns: widgetItem.data.columns || [],
                              widgetType,
                            });

                            if (!chartModel) {
                              return <Typography variant="body2" color="text.secondary">No chart data available.</Typography>;
                            }

                            const chartOptions = {
                              responsive: true,
                              maintainAspectRatio: false,
                              plugins: {
                                legend: { display: true, position: "top" },
                              },
                            };

                            if (widgetType === "BAR") {
                              return <Box sx={{ height: 260 }}><Bar data={chartModel} options={chartOptions} /></Box>;
                            }
                            if (widgetType === "LINE" || widgetType === "AREA") {
                              return <Box sx={{ height: 260 }}><Line data={chartModel} options={chartOptions} /></Box>;
                            }
                            if (widgetType === "PIE") {
                              return <Box sx={{ height: 280 }}><Pie data={chartModel} options={chartOptions} /></Box>;
                            }
                            if (widgetType === "KPI") {
                              const values = chartModel.datasets?.[0]?.data || [];
                              const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                              return (
                                <Paper variant="outlined" sx={{ p: 2 }}>
                                  <Typography variant="caption" color="text.secondary">KPI ({chartModel.yColumn})</Typography>
                                  <Typography variant="h4" fontWeight={700}>{Number(total).toLocaleString()}</Typography>
                                </Paper>
                              );
                            }

                            return <Typography variant="body2" color="text.secondary">Unsupported widget type.</Typography>;
                          })()
                        ) : (
                          <Typography variant="body2" color="text.secondary">No data returned for this widget.</Typography>
                        )}
                      </Paper>
                      </Grid>
                      );
                    })}
                  </Grid>
                )}
              </>
            ) : (
              <>
            <Typography variant="subtitle1" fontWeight={600} mb={1.5}>
              {isEditMode ? `Edit Dashboard #${selectedDashboardId}` : "Create Dashboard"}
            </Typography>

            <Grid container spacing={1.5}>
              <Grid item xs={12} md={9}>
                <TextField
                  fullWidth
                  size="small"
                  label="Dashboard Name"
                  value={form.dashboardName}
                  onChange={(e) => setForm((prev) => ({ ...prev, dashboardName: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={form.isActive}
                      onChange={(e) => setForm((prev) => ({ ...prev, isActive: e.target.checked }))}
                    />
                  }
                  label="Active"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  minRows={2}
                  size="small"
                  label="Description"
                  value={form.description}
                  onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                />
              </Grid>

              {(!isWizardMode || activeStep >= 1) && (
              <>
              <Grid item xs={12}>
                <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }}>
                  <Typography variant="subtitle2" fontWeight={600}>Widget Builder</Typography>
                  <Stack direction="row" spacing={1} mt={{ xs: 1, md: 0 }}>
                    {editingWidgetIndex !== null && (
                      <Button variant="outlined" onClick={handleStartAddWidget}>Add New Widget</Button>
                    )}
                    <Button variant="outlined" onClick={handleResetLayout} disabled={!widgets.length}>Reset Layout</Button>
                    <Button variant="outlined" onClick={handleClearWidgetDraft}>Clear</Button>
                    <Button variant="contained" startIcon={editingWidgetIndex !== null ? <Edit /> : <Add />} onClick={handleSaveWidget}>
                      {editingWidgetIndex !== null ? "Update Widget" : "Add Widget"}
                    </Button>
                  </Stack>
                </Stack>
              </Grid>

              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Widget Name"
                  value={widgetDraft.widgetName}
                  onChange={(e) => setWidgetDraft((prev) => ({ ...prev, widgetName: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel id="widget-type-label">Widget Type</InputLabel>
                  <Select
                    labelId="widget-type-label"
                    label="Widget Type"
                    value={widgetDraft.widgetType}
                    onChange={(e) => setWidgetDraft((prev) => ({ ...prev, widgetType: e.target.value }))}
                  >
                    <MenuItem value="TABLE">TABLE</MenuItem>
                    <MenuItem value="BAR">BAR</MenuItem>
                    <MenuItem value="LINE">LINE</MenuItem>
                    <MenuItem value="PIE">PIE</MenuItem>
                    <MenuItem value="KPI">KPI</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Row Limit"
                  type="number"
                  value={rowLimit}
                  onChange={(e) => setRowLimit(Number(e.target.value) || 100)}
                />
              </Grid>

              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel id="widget-layout-slot-label">Widget Position</InputLabel>
                  <Select
                    labelId="widget-layout-slot-label"
                    label="Widget Position"
                    value={widgetDraft.layoutSlot || "TOP_LEFT"}
                    onChange={(e) => setWidgetDraft((prev) => ({ ...prev, layoutSlot: e.target.value }))}
                  >
                    {widgetLayoutOptions.map((option) => (
                      <MenuItem key={`layout-option-${option.value}`} value={option.value}>{option.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth size="small">
                  <InputLabel id="db-connection-id-label">DB Connection (optional)</InputLabel>
                  <Select
                    labelId="db-connection-id-label"
                    label="DB Connection (optional)"
                    value={widgetDraft.dbConnectionId}
                    onChange={(e) => setWidgetDraft((prev) => ({ ...prev, dbConnectionId: e.target.value }))}
                  >
                    <MenuItem value="">Metadata DB</MenuItem>
                    {dbConnections.map((conn) => (
                      <MenuItem key={conn.conid} value={String(conn.conid)}>
                        {conn.connm}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <Stack direction="row" spacing={1} height="100%" alignItems="center" justifyContent="flex-end">
                  <Button variant="outlined" onClick={handleDescribeSql}>Describe SQL</Button>
                  <Button variant="outlined" startIcon={<PlayArrow />} onClick={handlePreviewSql} disabled={previewLoading}>
                    {previewLoading ? "Previewing..." : "Preview"}
                  </Button>
                </Stack>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  minRows={6}
                  size="small"
                  label="Adhoc SQL"
                  value={widgetDraft.adhocSql}
                  onChange={(e) => setWidgetDraft((prev) => ({ ...prev, adhocSql: e.target.value }))}
                  placeholder="SELECT * FROM your_table"
                />
              </Grid>
              </>
              )}

              {(!isWizardMode || activeStep >= 3) && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" fontWeight={600} mb={1}>Widgets In Draft</Typography>
                {widgets.length === 0 ? (
                  <Typography variant="body2" color="text.secondary">No widgets added yet.</Typography>
                ) : (
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Position</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {widgets.map((widget, index) => (
                        <TableRow
                          key={`${widget.widgetName}-${index}`}
                          selected={editingWidgetIndex === index}
                          draggable
                          onDragStart={() => handleWidgetDragStart(index)}
                          onDragEnd={handleWidgetDragEnd}
                          sx={{ cursor: "grab" }}
                        >
                          <TableCell>{widget.widgetName}</TableCell>
                          <TableCell>{widget.widgetType}</TableCell>
                          <TableCell>{widget.layoutSlot || "TOP_LEFT"}</TableCell>
                          <TableCell align="right">
                            <Stack direction="row" spacing={1} justifyContent="flex-end">
                              <Button size="small" startIcon={<Edit />} onClick={() => handleEditWidget(index)}>Edit</Button>
                              <Button size="small" color="error" startIcon={<DeleteOutline />} onClick={() => handleRemoveWidget(index)}>Remove</Button>
                            </Stack>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}

                {widgets.length > 0 && renderLayoutBoard()}
              </Grid>
              )}
            </Grid>
              </>
            )}
          </Paper>
        </Grid>
      </Grid>

      {viewMode === "creator" && (!isWizardMode || activeStep >= 2) && (
      <Grid container spacing={2} mt={0.5}>
        <Grid item xs={12} md={6}>
          <Paper
            elevation={darkMode ? 0 : 1}
            sx={{
              p: 2,
              borderRadius: 2,
              border: panelBorder,
            }}
          >
            <Typography variant="subtitle2" fontWeight={600} mb={1}>Column Discovery</Typography>
            {sqlDescribe.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No SQL description loaded.</Typography>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Column</TableCell>
                    <TableCell>Data Type</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sqlDescribe.map((column) => (
                    <TableRow key={column.name}>
                      <TableCell>{column.name}</TableCell>
                      <TableCell>{column.dataType || "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper
            elevation={darkMode ? 0 : 1}
            sx={{
              p: 2,
              borderRadius: 2,
              border: panelBorder,
            }}
          >
            <Typography variant="subtitle2" fontWeight={600} mb={1}>Widget Preview</Typography>
            <Stack direction="row" spacing={1} mb={1}>
              <Chip size="small" label={`Rows: ${preview.rowCount || 0}`} />
              <Chip size="small" label={`DB: ${preview.sourceDbType || "-"}`} />
            </Stack>

            {preview.rows?.length && widgetDraft.widgetType !== "TABLE" && (
              <Grid container spacing={1} mb={1.5}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel id="chart-x-axis-label">X Axis</InputLabel>
                    <Select
                      labelId="chart-x-axis-label"
                      label="X Axis"
                      value={chartXAxis}
                      onChange={(e) => setChartXAxis(e.target.value)}
                    >
                      {(preview.columns || []).map((column) => (
                        <MenuItem key={`x-${column}`} value={column}>{column}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel id="chart-y-axis-label">Y Axis</InputLabel>
                    <Select
                      labelId="chart-y-axis-label"
                      label="Y Axis"
                      value={chartYAxis}
                      onChange={(e) => setChartYAxis(e.target.value)}
                    >
                      {getNumericColumns(preview.columns || [], preview.rows || []).map((column) => (
                        <MenuItem key={`y-${column}`} value={column}>{column}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            )}

            {preview.rows?.length && widgetDraft.widgetType !== "TABLE" && (() => {
              const chartModel = buildChartDataset();
              if (!chartModel) {
                return <Typography variant="body2" color="text.secondary">Unable to build chart from current preview data.</Typography>;
              }

              const chartOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, position: "top" },
                },
              };

              if (widgetDraft.widgetType === "BAR") {
                return <Box sx={{ height: 300, mb: 1.5 }}><Bar data={chartModel} options={chartOptions} /></Box>;
              }
              if (widgetDraft.widgetType === "LINE" || widgetDraft.widgetType === "AREA") {
                return <Box sx={{ height: 300, mb: 1.5 }}><Line data={chartModel} options={chartOptions} /></Box>;
              }
              if (widgetDraft.widgetType === "PIE") {
                return <Box sx={{ height: 320, mb: 1.5 }}><Pie data={chartModel} options={chartOptions} /></Box>;
              }
              if (widgetDraft.widgetType === "KPI") {
                const values = chartModel.datasets?.[0]?.data || [];
                const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                return (
                  <Paper variant="outlined" sx={{ p: 2, mb: 1.5 }}>
                    <Typography variant="caption" color="text.secondary">KPI ({chartModel.yColumn})</Typography>
                    <Typography variant="h4" fontWeight={700}>{Number(total).toLocaleString()}</Typography>
                  </Paper>
                );
              }

              return null;
            })()}

            {preview.rows?.length ? (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {(preview.columns || []).map((column) => (
                      <TableCell key={column}>{column}</TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preview.rows.slice(0, 10).map((row, index) => (
                    <TableRow key={index}>
                      {(preview.columns || []).map((column) => (
                        <TableCell key={`${index}-${column}`}>{String(row[column] ?? "")}</TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Typography variant="body2" color="text.secondary">No preview rows loaded.</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
      )}

      {viewMode === "creator" && (!isWizardMode || activeStep >= 4) && (
      <Grid container spacing={2} mt={0.5}>
        <Grid item xs={12}>
          <Paper
            elevation={darkMode ? 0 : 1}
            sx={{
              p: 2,
              borderRadius: 2,
              border: panelBorder,
            }}
          >
            <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" mb={1}>
              <Typography variant="subtitle2" fontWeight={600}>Export History</Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => fetchExportHistory(selectedDashboardId)}
                disabled={loadingExportHistory}
              >
                Refresh History
              </Button>
            </Stack>

            {loadingExportHistory ? (
              <Box py={3} display="flex" justifyContent="center"><CircularProgress size={22} /></Box>
            ) : exportHistory.length === 0 ? (
              <Typography variant="body2" color="text.secondary">No export operations found.</Typography>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Time</TableCell>
                    <TableCell>Dashboard</TableCell>
                    <TableCell>Format</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>User</TableCell>
                    <TableCell>File</TableCell>
                    <TableCell>Size</TableCell>
                    <TableCell>Message</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {exportHistory.map((entry) => (
                    <TableRow key={entry.exportId || `${entry.dashboardId}-${entry.exportedAt}`}>
                      <TableCell>{entry.exportedAt ? new Date(entry.exportedAt).toLocaleString() : "-"}</TableCell>
                      <TableCell>{entry.dashboardName || entry.dashboardId || "-"}</TableCell>
                      <TableCell>{entry.exportFormat || "-"}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={entry.status || "-"}
                          color={entry.status === "SUCCESS" ? "success" : entry.status === "FAILED" ? "error" : "default"}
                        />
                      </TableCell>
                      <TableCell>{entry.exportedBy || "-"}</TableCell>
                      <TableCell>{entry.fileName || "-"}</TableCell>
                      <TableCell>{entry.fileSizeBytes ?? "-"}</TableCell>
                      <TableCell>{entry.message || "-"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Paper>
        </Grid>
      </Grid>
      )}

      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Dashboard</DialogTitle>
        <DialogContent>
          <Typography variant="body2">
            {deleteTarget
              ? `Delete dashboard "${deleteTarget.dashboardName}"? This action is permanent and cannot be retrieved.`
              : selectedDashboard
              ? `Delete dashboard "${selectedDashboard.dashboardName}"? This action is permanent and cannot be retrieved.`
              : "Delete selected dashboard? This action is permanent and cannot be retrieved."}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={handleDelete}>Delete</Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={wizardDialogOpen}
        onClose={() => setWizardDialogOpen(false)}
        fullWidth
        maxWidth="lg"
      >
        <DialogTitle>Dashboard Creator</DialogTitle>
        <DialogContent dividers>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 2 }}>
            {wizardSteps.map((label) => (
              <Step key={`wizard-modal-${label}`}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          <Typography variant="body2" color="text.secondary" mb={2}>{wizardHelpText}</Typography>

          {activeStep === 0 && (
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={9}>
                <TextField
                  fullWidth
                  size="small"
                  label="Dashboard Name"
                  value={form.dashboardName}
                  onChange={(e) => setForm((prev) => ({ ...prev, dashboardName: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControlLabel
                  control={<Switch checked={form.isActive} onChange={(e) => setForm((prev) => ({ ...prev, isActive: e.target.checked }))} />}
                  label="Active"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  minRows={2}
                  size="small"
                  label="Description"
                  value={form.description}
                  onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                />
              </Grid>
            </Grid>
          )}

          {activeStep === 1 && (
            <Grid container spacing={1.5}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Widget Name"
                  value={widgetDraft.widgetName}
                  onChange={(e) => setWidgetDraft((prev) => ({ ...prev, widgetName: e.target.value }))}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel id="wizard-widget-type-label">Widget Type</InputLabel>
                  <Select
                    labelId="wizard-widget-type-label"
                    label="Widget Type"
                    value={widgetDraft.widgetType}
                    onChange={(e) => setWidgetDraft((prev) => ({ ...prev, widgetType: e.target.value }))}
                  >
                    <MenuItem value="TABLE">TABLE</MenuItem>
                    <MenuItem value="BAR">BAR</MenuItem>
                    <MenuItem value="LINE">LINE</MenuItem>
                    <MenuItem value="PIE">PIE</MenuItem>
                    <MenuItem value="KPI">KPI</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel id="wizard-widget-layout-slot-label">Widget Position</InputLabel>
                  <Select
                    labelId="wizard-widget-layout-slot-label"
                    label="Widget Position"
                    value={widgetDraft.layoutSlot || "TOP_LEFT"}
                    onChange={(e) => setWidgetDraft((prev) => ({ ...prev, layoutSlot: e.target.value }))}
                  >
                    {widgetLayoutOptions.map((option) => (
                      <MenuItem key={`wizard-layout-option-${option.value}`} value={option.value}>{option.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel id="wizard-db-connection-id-label">DB Connection</InputLabel>
                  <Select
                    labelId="wizard-db-connection-id-label"
                    label="DB Connection"
                    value={widgetDraft.dbConnectionId}
                    onChange={(e) => setWidgetDraft((prev) => ({ ...prev, dbConnectionId: e.target.value }))}
                  >
                    <MenuItem value="">Metadata DB</MenuItem>
                    {dbConnections.map((conn) => (
                      <MenuItem key={`wizard-conn-${conn.conid}`} value={String(conn.conid)}>
                        {conn.connm}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  minRows={6}
                  size="small"
                  label="Adhoc SQL"
                  value={widgetDraft.adhocSql}
                  onChange={(e) => setWidgetDraft((prev) => ({ ...prev, adhocSql: e.target.value }))}
                  placeholder="SELECT * FROM your_table"
                />
              </Grid>
              <Grid item xs={12}>
                <Stack direction="row" spacing={1} justifyContent="flex-end">
                  <Button variant="outlined" onClick={handleDescribeSql}>Describe SQL</Button>
                  <Button variant="outlined" startIcon={<PlayArrow />} onClick={handlePreviewSql} disabled={previewLoading}>
                    {previewLoading ? "Previewing..." : "Preview"}
                  </Button>
                </Stack>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="subtitle2" fontWeight={600} mb={1}>Describe SQL Output</Typography>
                  {sqlDescribe.length ? (
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Column</TableCell>
                          <TableCell>Type</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sqlDescribe.map((column) => (
                          <TableRow key={`wizard-describe-${column.name}`}>
                            <TableCell>{column.name}</TableCell>
                            <TableCell>{column.dataType || "-"}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <Typography variant="body2" color="text.secondary">Click Describe SQL to see columns.</Typography>
                  )}
                </Paper>
              </Grid>

              <Grid item xs={12} md={6}>
                <Paper variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="subtitle2" fontWeight={600} mb={1}>Preview Output</Typography>
                  <Stack direction="row" spacing={1} mb={1}>
                    <Chip size="small" label={`Rows: ${preview.rowCount || 0}`} />
                    <Chip size="small" label={`DB: ${preview.sourceDbType || "-"}`} />
                  </Stack>

                  {preview.rows?.length && widgetDraft.widgetType !== "TABLE" && (() => {
                    const chartModel = buildChartDataset();
                    if (!chartModel) {
                      return <Typography variant="body2" color="text.secondary">Unable to build chart from current preview data.</Typography>;
                    }

                    const chartOptions = {
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: true, position: "top" },
                      },
                    };

                    if (widgetDraft.widgetType === "BAR") {
                      return <Box sx={{ height: 220, mb: 1 }}><Bar data={chartModel} options={chartOptions} /></Box>;
                    }
                    if (widgetDraft.widgetType === "LINE" || widgetDraft.widgetType === "AREA") {
                      return <Box sx={{ height: 220, mb: 1 }}><Line data={chartModel} options={chartOptions} /></Box>;
                    }
                    if (widgetDraft.widgetType === "PIE") {
                      return <Box sx={{ height: 240, mb: 1 }}><Pie data={chartModel} options={chartOptions} /></Box>;
                    }
                    if (widgetDraft.widgetType === "KPI") {
                      const values = chartModel.datasets?.[0]?.data || [];
                      const total = values.reduce((sum, value) => sum + Number(value || 0), 0);
                      return (
                        <Paper variant="outlined" sx={{ p: 1.5, mb: 1 }}>
                          <Typography variant="caption" color="text.secondary">KPI ({chartModel.yColumn})</Typography>
                          <Typography variant="h5" fontWeight={700}>{Number(total).toLocaleString()}</Typography>
                        </Paper>
                      );
                    }

                    return null;
                  })()}

                  {preview.rows?.length ? (
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {(preview.columns || []).map((column) => (
                            <TableCell key={`wizard-preview-quick-col-${column}`}>{column}</TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(preview.rows || []).slice(0, 5).map((row, rowIndex) => (
                          <TableRow key={`wizard-preview-quick-row-${rowIndex}`}>
                            {(preview.columns || []).map((column) => (
                              <TableCell key={`wizard-preview-quick-cell-${rowIndex}-${column}`}>{String(row[column] ?? "")}</TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  ) : (
                    <Typography variant="body2" color="text.secondary">Click Preview to see query output and chart.</Typography>
                  )}
                </Paper>
              </Grid>
            </Grid>
          )}

          {activeStep === 2 && (
            <Box>
              <Stack direction="row" spacing={1} mb={1}>
                <Chip size="small" label={`Rows: ${preview.rowCount || 0}`} />
                <Chip size="small" label={`DB: ${preview.sourceDbType || "-"}`} />
              </Stack>
              {preview.rows?.length ? (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      {(preview.columns || []).map((column) => (
                        <TableCell key={`wizard-preview-col-${column}`}>{column}</TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(preview.rows || []).slice(0, 8).map((row, index) => (
                      <TableRow key={`wizard-preview-row-${index}`}>
                        {(preview.columns || []).map((column) => (
                          <TableCell key={`wizard-preview-cell-${index}-${column}`}>{String(row[column] ?? "")}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <Typography variant="body2" color="text.secondary">No preview rows loaded yet.</Typography>
              )}
            </Box>
          )}

          {activeStep === 3 && (
            <Box>
              <Stack direction="row" spacing={1} justifyContent="space-between" mb={1}>
                <Typography variant="subtitle2" fontWeight={600}>Widget Draft</Typography>
                <Stack direction="row" spacing={1}>
                  {editingWidgetIndex !== null && (
                    <Button variant="outlined" onClick={handleStartAddWidget}>Add New Widget</Button>
                  )}
                  <Button variant="outlined" onClick={handleResetLayout} disabled={!widgets.length}>Reset Layout</Button>
                  <Button variant="contained" startIcon={editingWidgetIndex !== null ? <Edit /> : <Add />} onClick={handleSaveWidget}>
                    {editingWidgetIndex !== null ? "Update Widget" : "Add Widget"}
                  </Button>
                </Stack>
              </Stack>
              {widgets.length === 0 ? (
                <Typography variant="body2" color="text.secondary">No widgets in draft.</Typography>
              ) : (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {widgets.map((widget, index) => (
                      <TableRow
                        key={`wizard-widget-${index}`}
                        draggable
                        onDragStart={() => handleWidgetDragStart(index)}
                        onDragEnd={handleWidgetDragEnd}
                        sx={{ cursor: "grab" }}
                      >
                        <TableCell>{widget.widgetName}</TableCell>
                        <TableCell>{widget.widgetType}</TableCell>
                        <TableCell align="right">
                          <Stack direction="row" spacing={1} justifyContent="flex-end">
                            <Button size="small" onClick={() => handleEditWidget(index)}>Edit</Button>
                            <Button size="small" color="error" onClick={() => handleRemoveWidget(index)}>Remove</Button>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}

              {widgets.length > 0 && renderLayoutBoard()}
            </Box>
          )}

          {activeStep === 4 && (
            <Stack spacing={1.5}>
              <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
                <Button variant="contained" startIcon={<Save />} onClick={handleSave} disabled={saving}>
                  {saving ? "Saving..." : "Save Dashboard"}
                </Button>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Current dashboard: {selectedDashboardId ? `${form.dashboardName || "Dashboard"} (#${selectedDashboardId})` : "Not saved yet"}
              </Typography>
            </Stack>
          )}

          <Paper variant="outlined" sx={{ p: 1.5, mt: 2 }}>
            <Typography variant="subtitle2" fontWeight={600} mb={0.5}>Step Result</Typography>
            {activeStep === 0 && (
              <Typography variant="body2" color="text.secondary">
                Name: {form.dashboardName || "-"} | Active: {form.isActive ? "Yes" : "No"}
              </Typography>
            )}
            {activeStep === 1 && (
              <Typography variant="body2" color="text.secondary">
                Widget: {widgetDraft.widgetName || "-"} | Position: {widgetDraft.layoutSlot || "TOP_LEFT"} | SQL Length: {(widgetDraft.adhocSql || "").length} | Connection: {widgetDraft.dbConnectionId || "Metadata DB"}
              </Typography>
            )}
            {activeStep === 2 && (
              <Typography variant="body2" color="text.secondary">
                Preview rows: {preview.rowCount || 0} | Columns: {(preview.columns || []).join(", ") || "-"}
              </Typography>
            )}
            {activeStep === 3 && (
              <Typography variant="body2" color="text.secondary">
                Draft widgets: {widgets.length}
              </Typography>
            )}
            {activeStep === 4 && (
              <Typography variant="body2" color="text.secondary">
                Export history entries: {exportHistory.length}
              </Typography>
            )}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setWizardDialogOpen(false)}>Close</Button>
          <Button variant="outlined" onClick={handleWizardBack} disabled={activeStep === 0}>Back</Button>
          {activeStep < wizardSteps.length - 1 ? (
            <Button variant="contained" onClick={handleWizardNext}>Next</Button>
          ) : (
            <Button variant="contained" onClick={handleWizardFinish}>Finish</Button>
          )}
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
};

export default DashboardCreatorPage;
