"use client";
import React, { useState, useEffect } from "react";
import {
  Box, Container, Typography, Grid, Card, CardContent, Button, TextField, Dialog, DialogTitle, DialogContent, DialogActions, Snackbar, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, IconButton, Tooltip, CircularProgress, MenuItem, Select, FormControl, InputLabel
} from "@mui/material";
import { Add, Edit, Delete, Refresh } from "@mui/icons-material";

const apiUrl = process.env.NEXT_PUBLIC_API_URL + "/api/dbconnections";

const initialForm = {
  connm: "",
  dbtyp: "",
  constr: "",
  dbhost: "",
  dbport: "",
  dbsrvnm: "",
  usrnm: "",
  schnm: "",
  passwd: "",
  dbdescr: "",
  sslfg: "N",
};

const SUPPORTED_DB_TYPES = [
  { value: "ORACLE", label: "Oracle" },
  { value: "POSTGRESQL", label: "PostgreSQL" },
  { value: "MSSQL", label: "Microsoft SQL Server (MSSQL)" },
  { value: "SQL_SERVER", label: "SQL Server" },
  { value: "MYSQL", label: "MySQL" },
  { value: "SYBASE", label: "Sybase" },
  { value: "REDSHIFT", label: "Amazon Redshift" },
  { value: "HIVE", label: "Apache Hive" },
  { value: "SNOWFLAKE", label: "Snowflake" },
  { value: "DB2", label: "IBM DB2" },
];

const RegisterDBConnectionsPage = () => {
  const [connections, setConnections] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editId, setEditId] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: "", severity: "info" });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionValidated, setConnectionValidated] = useState(false);
  const [validationMessage, setValidationMessage] = useState("");

  const showSnackbar = (message, severity = "info") => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const fetchConnections = async () => {
    setLoading(true);
    try {
      const response = await fetch(apiUrl);
      const result = await response.json();
      if (result.success) {
        setConnections(result.data || []);
      } else {
        const errorMsg = result.message || "Failed to fetch connections. Please check if the database server is running.";
        showSnackbar(errorMsg, "error");
        // Set empty array on error so UI doesn't break
        setConnections([]);
      }
    } catch (error) {
      console.error("Error fetching connections:", error);
      const errorMsg = "Network error: Unable to reach the server. Please check your connection and ensure the backend is running.";
      showSnackbar(errorMsg, "error");
      setConnections([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  const handleAdd = () => {
    setForm(initialForm);
    setEditId(null);
    setConnectionValidated(false);
    setValidationMessage("");
    setDialogOpen(true);
  };

  const handleEdit = (record) => {
    setForm({ ...record, dbport: record.dbport || "" });
    setEditId(record.conid);
    setConnectionValidated(false);
    setValidationMessage("");
    setDialogOpen(true);
  };

  const handleDelete = async (conid) => {
    if (!window.confirm("This will deactivate the connection entry. Proceed?")) return;
    setDeletingId(conid);
    try {
      const response = await fetch(`${apiUrl}/${conid}`, { method: "DELETE" });
      const result = await response.json();
      if (result.success) {
        showSnackbar("Connection deactivated successfully", "success");
        fetchConnections();
      } else {
        const errorMsg = result.message || "Failed to deactivate connection. Please check database connection and try again.";
        showSnackbar(errorMsg, "error");
      }
    } catch (e) {
      console.error("Error deleting connection:", e);
      showSnackbar("Network error: Unable to reach the server. Please check your connection.", "error");
    } finally {
      setDeletingId(null);
    }
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setForm(initialForm);
    setEditId(null);
    setConnectionValidated(false);
    setValidationMessage("");
  };

  const handleValidate = async () => {
    // Validate required fields
    if (!form.connm || !form.dbtyp || !form.dbhost || !form.dbport || !form.dbsrvnm || !form.usrnm || !form.schnm || !form.passwd) {
      showSnackbar("Please fill in all required fields before testing connection", "warning");
      return;
    }

    setTestingConnection(true);
    setValidationMessage("");
    try {
      const response = await fetch(`${apiUrl}/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const result = await response.json();
      
      if (result.success) {
        setConnectionValidated(true);
        setValidationMessage(result.message || "Connection test successful!");
        showSnackbar(result.message || "Connection test successful!", "success");
      } else {
        setConnectionValidated(false);
        const errorMsg = result.message || "Connection test failed. Please check your credentials.";
        setValidationMessage(errorMsg);
        showSnackbar(errorMsg, "error");
      }
    } catch (err) {
      console.error("Error testing connection:", err);
      setConnectionValidated(false);
      const errorMsg = "Network error: Unable to test connection. Please check your connection.";
      setValidationMessage(errorMsg);
      showSnackbar(errorMsg, "error");
    } finally {
      setTestingConnection(false);
    }
  };

  const handleInputChange = (e) => {
    let { name, value } = e.target;
    if (name === "sslfg") value = value.toUpperCase().startsWith("Y") ? "Y" : "N";
    setForm((f) => ({ ...f, [name]: value }));
    // Reset validation when form fields change
    if (connectionValidated) {
      setConnectionValidated(false);
      setValidationMessage("");
    }
  };


  const handleFormSubmit = async (e) => {
    e.preventDefault();
    
    // Check if connection is validated before allowing save
    if (!connectionValidated) {
      showSnackbar("Please test the connection first to validate the credentials before saving.", "warning");
      return;
    }
    
    setSaving(true);
    try {
      const apiTarget = editId ? `${apiUrl}/${editId}` : apiUrl;
      const method = editId ? "PUT" : "POST";
      const response = await fetch(apiTarget, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const result = await response.json();
      if (result.success) {
        showSnackbar(editId ? "Connection updated successfully" : "Connection added successfully", "success");
        setConnectionValidated(false);
        setValidationMessage("");
        fetchConnections();
        handleDialogClose();
      } else {
        const errorMsg = result.message || "Operation failed. Please check database connection and try again.";
        showSnackbar(errorMsg, "error");
      }
    } catch (err) {
      console.error("Error saving connection:", err);
      showSnackbar("Network error: Unable to reach the server. Please check your connection.", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Container maxWidth="xl" sx={{ py: 2, px: 3, mb: 4 }}>
        <Grid container spacing={2} alignItems="center" sx={{ mb: 2 }}>
          <Grid item>
            <Button variant="contained" startIcon={<Add />} onClick={handleAdd}>
              Add Connection
            </Button>
          </Grid>
          <Grid item>
            <Button variant="outlined" startIcon={<Refresh />} onClick={fetchConnections} disabled={loading}>
              Refresh
            </Button>
          </Grid>
        </Grid>
        <Card sx={{ borderRadius: 2, bgcolor: "background.paper" }}>
          <CardContent>
            {loading ? (
              <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 6 }}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Host</TableCell>
                      <TableCell>Port</TableCell>
                      <TableCell>Service/DB Name</TableCell>
                      <TableCell>User</TableCell>
                      <TableCell>Schema</TableCell>
                      <TableCell>SSL</TableCell>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {connections.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={10} align="center" sx={{ py: 4 }}>
                          <Typography variant="body2" color="text.secondary">
                            {loading ? "Loading..." : "No database connections found. Click 'Add Connection' to create one."}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ) : (
                      connections.map((conn) => (
                        <TableRow key={conn.conid} hover>
                          <TableCell>{conn.connm}</TableCell>
                          <TableCell>{conn.dbtyp}</TableCell>
                          <TableCell>{conn.dbhost}</TableCell>
                          <TableCell>{conn.dbport}</TableCell>
                          <TableCell>{conn.dbsrvnm}</TableCell>
                          <TableCell>{conn.usrnm}</TableCell>
                          <TableCell>{conn.schnm}</TableCell>
                          <TableCell>{conn.sslfg === "Y" ? "Yes" : "No"}</TableCell>
                          <TableCell>{conn.dbdescr}</TableCell>
                          <TableCell align="right">
                            <Tooltip title="Edit"><span><IconButton size="small" onClick={() => handleEdit(conn)}><Edit /></IconButton></span></Tooltip>
                            <Tooltip title="Deactivate"><span><IconButton size="small" color="error" onClick={() => handleDelete(conn.conid)} disabled={deletingId === conn.conid}><Delete /></IconButton></span></Tooltip>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
        <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="sm" fullWidth>
          <DialogTitle>{editId ? "Edit" : "Add"} DB Connection</DialogTitle>
          <DialogContent dividers>
            <form id="db-conn-form" onSubmit={handleFormSubmit}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}><TextField label="Connection Name" name="connm" value={form.connm} onChange={handleInputChange} fullWidth required /></Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth required>
                    <InputLabel>Database Type</InputLabel>
                    <Select
                      label="Database Type"
                      name="dbtyp"
                      value={form.dbtyp}
                      onChange={handleInputChange}
                    >
                      {SUPPORTED_DB_TYPES.map((db) => (
                        <MenuItem key={db.value} value={db.value}>
                          {db.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Connection String (preferred)"
                    name="constr"
                    value={form.constr}
                    onChange={handleInputChange}
                    fullWidth
                    placeholder="e.g. postgres://user:pass@host:5432/dbname"
                    helperText="Provide a full DSN/connection string. Use the fields below only if a connection string is unavailable."
                  />
                </Grid>
                <Grid item xs={12} sm={6}><TextField label="Host / IP" name="dbhost" value={form.dbhost} onChange={handleInputChange} fullWidth /></Grid>
                <Grid item xs={12} sm={6}><TextField label="Port" name="dbport" value={form.dbport} type="number" onChange={handleInputChange} fullWidth /></Grid>
                <Grid item xs={12} sm={6}><TextField label="Service / Database Name" name="dbsrvnm" value={form.dbsrvnm} onChange={handleInputChange} fullWidth /></Grid>
                <Grid item xs={12} sm={6}><TextField label="Username" name="usrnm" value={form.usrnm} onChange={handleInputChange} fullWidth required /></Grid>
                <Grid item xs={12} sm={6}><TextField label="Schema" name="schnm" value={form.schnm || ""} onChange={handleInputChange} fullWidth required helperText="Mandatory for all connections; use Username value when not separately applicable." /></Grid>
                <Grid item xs={12} sm={6}><TextField label="Password" name="passwd" value={form.passwd} onChange={handleInputChange} type="password" fullWidth required /></Grid>
                <Grid item xs={12} sm={6}><TextField label="SSL (Y/N)" name="sslfg" value={form.sslfg} onChange={handleInputChange} fullWidth /></Grid>
                <Grid item xs={12}><TextField label="Description" name="dbdescr" value={form.dbdescr} onChange={handleInputChange} multiline minRows={2} fullWidth /></Grid>
              </Grid>
            </form>
          </DialogContent>
          {validationMessage && (
            <Box sx={{ px: 3, pb: 1 }}>
              <Alert 
                severity={connectionValidated ? "success" : "error"} 
                sx={{ mb: 1 }}
              >
                {validationMessage}
              </Alert>
            </Box>
          )}
          <DialogActions sx={{ px: 3, pb: 2, pt: 1 }}>
            <Button onClick={handleDialogClose}>Cancel</Button>
            <Button 
              onClick={handleValidate} 
              disabled={testingConnection || !form.connm || !form.dbtyp || !form.dbhost || !form.dbport || !form.dbsrvnm || !form.usrnm || !form.schnm || !form.passwd} 
              variant="outlined" 
              color="primary" 
              sx={{ mr: 1 }}
              startIcon={testingConnection ? <CircularProgress size={16} /> : null}
            >
              {testingConnection ? "Testing..." : "Test Connection"}
            </Button>
            <Button
              type="submit"
              form="db-conn-form"
              variant="contained"
              color="success"
              disabled={saving || !connectionValidated}
              title={!connectionValidated ? "Please test connection first" : ""}
            >
              {saving ? "Saving..." : editId ? "Update" : "Add"}
            </Button>
          </DialogActions>
        </Dialog>
        <Snackbar 
          open={snackbar.open} 
          autoHideDuration={snackbar.severity === "error" ? 6000 : 3000} 
          onClose={handleCloseSnackbar} 
          anchorOrigin={{ vertical: "top", horizontal: "center" }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Box>
  );
};

export default RegisterDBConnectionsPage;
