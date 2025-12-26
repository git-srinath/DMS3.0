'use client'

import React, { createContext, useContext, useState, useCallback } from 'react'

const SaveContext = createContext({
  moduleId: null,
  onSave: null,
  onBack: null,
  canSave: false,
  canBack: false,
  label: null,
  registerHandlers: () => {},
  clearHandlers: () => {},
})

export const SaveProvider = ({ children }) => {
  const [state, setState] = useState({
    moduleId: null,
    onSave: null,
    onBack: null,
    canSave: false,
    canBack: false,
    label: null,
  })

  const registerHandlers = useCallback(
    ({ moduleId, onSave, onBack, canSave = true, canBack = true, label = null }) => {
      setState({
        moduleId,
        onSave,
        onBack,
        canSave,
        canBack,
        label,
      })
    },
    []
  )

  const clearHandlers = useCallback((moduleId) => {
    setState((prev) => {
      if (prev.moduleId !== moduleId) return prev
      return {
        moduleId: null,
        onSave: null,
        onBack: null,
        canSave: false,
        canBack: false,
        label: null,
      }
    })
  }, [])

  return (
    <SaveContext.Provider value={{ ...state, registerHandlers, clearHandlers }}>
      {children}
    </SaveContext.Provider>
  )
}

export const useSaveContext = () => useContext(SaveContext)


