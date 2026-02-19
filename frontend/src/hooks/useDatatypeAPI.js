/**
 * Custom hook for Datatype API operations
 * Handles all API calls to the parameter mapping endpoints
 * Phase 2B: Datatypes Management
 */

import { useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const useDatatypeAPI = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Get current user ID from headers (placeholder)
  const getCurrentUserId = useCallback(() => {
    // This would come from your auth context
    return localStorage.getItem('userId') || 'system'
  }, [])

  /**
   * Get all supported databases
   */
  const getSupportedDatabases = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(`${API_BASE_URL}/mapping/supported_databases`, {
        headers: {
          'X-User': getCurrentUserId(),
        },
      })
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [getCurrentUserId])

  /**
   * Get datatypes for a specific database
   */
  const getDatatypesForDatabase = useCallback(async (dbtype) => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.get(
        `${API_BASE_URL}/mapping/datatypes_for_database?dbtype=${dbtype}`,
        {
          headers: {
            'X-User': getCurrentUserId(),
          },
        }
      )
      return response.data
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [getCurrentUserId])

  /**
   * Get datatype suggestions for a target database
   */
  const getDatatypeSuggestions = useCallback(
    async (targetDbtype, basedOnUsage = true) => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.post(
          `${API_BASE_URL}/mapping/datatype_suggestions?target_dbtype=${targetDbtype}&based_on_usage=${basedOnUsage}`,
          {},
          {
            headers: {
              'X-User': getCurrentUserId(),
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Get impact analysis for changing a datatype
   */
  const getImpactAnalysis = useCallback(
    async (prcd, newValue, dbtype) => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.get(
          `${API_BASE_URL}/mapping/datatype_impact_analysis?prcd=${prcd}&new_prval=${newValue}&dbtype=${dbtype}`,
          {
            headers: {
              'X-User': getCurrentUserId(),
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Get datatype usage statistics
   */
  const getDatatypeUsageStats = useCallback(
    async (dbtype = null) => {
      try {
        setLoading(true)
        setError(null)
        const url = dbtype
          ? `${API_BASE_URL}/mapping/datatype_usage_stats?dbtype=${dbtype}`
          : `${API_BASE_URL}/mapping/datatype_usage_stats`
        const response = await axios.get(url, {
          headers: {
            'X-User': getCurrentUserId(),
          },
        })
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Update a datatype
   */
  const updateDatatype = useCallback(
    async (prcd, dbtype, newValue, reason = '') => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.put(
          `${API_BASE_URL}/mapping/datatype_update`,
          {
            PRCD: prcd,
            DBTYP: dbtype,
            NEW_PRVAL: newValue,
            REASON: reason || undefined,
          },
          {
            headers: {
              'X-User': getCurrentUserId(),
              'Content-Type': 'application/json',
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Add a datatype
   */
  const addDatatype = useCallback(
    async (prcd, dbtype, value, description = '', reason = '') => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.post(
          `${API_BASE_URL}/mapping/datatype_add`,
          {
            PRCD: prcd,
            DBTYP: dbtype,
            PRVAL: value,
            PRDESC: description || undefined,
            REASON: reason || undefined,
          },
          {
            headers: {
              'X-User': getCurrentUserId(),
              'Content-Type': 'application/json',
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Remove a datatype
   */
  const removeDatatype = useCallback(
    async (prcd, dbtype) => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.delete(
          `${API_BASE_URL}/mapping/datatype_remove?prcd=${prcd}&dbtyp=${dbtype}`,
          {
            headers: {
              'X-User': getCurrentUserId(),
            },
          }
        )
        return response.data
      } catch (err) {
        // Handle 403 Forbidden errors (GENERIC records protected)
        if (err.response?.status === 403) {
          const detail = err.response?.data?.detail
          const errorData = typeof detail === 'string' ? JSON.parse(detail) : detail
          return errorData
        }
        
        // Handle 409 Conflict errors (validation failures)
        if (err.response?.status === 409) {
          const detail = err.response?.data?.detail
          const errorData = typeof detail === 'string' ? JSON.parse(detail) : detail
          return errorData
        }
        
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Validate all mappings for a database
   */
  const validateAllMappings = useCallback(
    async (dbtype) => {
      try {
        setLoading(true)
        setError(null)
        console.log(`[Validation] Validating mappings for: ${dbtype}`)
        
        const response = await axios.post(
          `${API_BASE_URL}/mapping/validate_all_mappings?dbtype=${dbtype}`,
          {},
          {
            headers: {
              'X-User': getCurrentUserId(),
            },
          }
        )
        console.log(`[Validation] Response:`, response.data)
        return response.data
      } catch (err) {
        console.error(`[Validation] Error:`, {
          status: err.response?.status,
          statusText: err.response?.statusText,
          detail: err.response?.data?.detail,
          database: dbtype,
        })
        
        let errorMsg = err.response?.data?.detail || err.message
        
        // Provide more helpful error messages for common issues
        if (err.response?.status === 404) {
          errorMsg = `Validation endpoint not found for database "${dbtype}". This database may not have validation configured yet. Please ensure:\n1. Database is properly registered\n2. Datatypes exist for this database\n3. Backend validation endpoint is available`
        } else if (err.response?.status === 400) {
          errorMsg = `Invalid request for database "${dbtype}": ${errorMsg}`
        }
        
        setError(errorMsg)
        const error = new Error(errorMsg)
        error.originalError = err
        throw error
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Add a new supported database
   */
  const addSupportedDatabase = useCallback(
    async (dbtype, dbdesc) => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.post(
          `${API_BASE_URL}/mapping/supported_database_add`,
          {
            DBTYP: dbtype,
            DBDESC: dbdesc,
          },
          {
            headers: {
              'X-User': getCurrentUserId(),
              'Content-Type': 'application/json',
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        const error = new Error(errorMsg)
        error.originalError = err
        throw error
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Clone datatypes from generic to new database
   */
  const cloneDatatypes = useCallback(
    async (targetDbtype) => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.post(
          `${API_BASE_URL}/mapping/clone_datatypes_from_generic`,
          {
            TARGET_DBTYPE: targetDbtype,
          },
          {
            headers: {
              'X-User': getCurrentUserId(),
              'Content-Type': 'application/json',
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        const error = new Error(errorMsg)
        error.originalError = err
        throw error
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  /**
   * Verify datatype compatibility
   */
  const verifyDatatypeCompatibility = useCallback(
    async (prcd, newValue, dbtype) => {
      try {
        setLoading(true)
        setError(null)
        const response = await axios.post(
          `${API_BASE_URL}/mapping/validate_datatype_compatibility`,
          {
            PRCD: prcd,
            PRVAL: newValue,
            DBTYPE: dbtype,
          },
          {
            headers: {
              'X-User': getCurrentUserId(),
              'Content-Type': 'application/json',
            },
          }
        )
        return response.data
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message
        setError(errorMsg)
        throw err
      } finally {
        setLoading(false)
      }
    },
    [getCurrentUserId]
  )

  return {
    loading,
    error,
    setError,
    getSupportedDatabases,
    getDatatypesForDatabase,
    getDatatypeSuggestions,
    getImpactAnalysis,
    getDatatypeUsageStats,
    updateDatatype,
    addDatatype,
    removeDatatype,
    validateAllMappings,
    addSupportedDatabase,
    cloneDatatypes,
    verifyDatatypeCompatibility,
  }
}
