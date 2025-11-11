'use client'

import React from 'react'
import {
  TextField,
  Checkbox,
  Tooltip,
  IconButton,
  TableCell,
  TableRow,
  Select,
  MenuItem,
  FormControl,
  Autocomplete,
} from '@mui/material'
import {
  HelpOutline as HelpOutlineIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Edit as EditIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material'

const ReferenceRow = ({
  row,
  index,
  darkMode,
  selectedRowIndex,
  isModified,
  pkSeqError,
  dataTypeOptions,
  scdTypeOptions,
  tableType,
  errorMessage,
  handleRowClick,
  handleRowChange,
  handleNumberChange,
  handleOpenSqlEditor,
  handleValidateRow,
  handleRowMenuOpen,
}) => {
  return (
    <TableRow
      key={index}
      onClick={() => handleRowClick(index)}
      className={`
            transition-colors duration-150 cursor-pointer
            ${
              isModified
                ? darkMode
                  ? 'bg-green-900/20 hover:bg-green-900/30'
                  : 'bg-green-50 hover:bg-green-100/70'
                : darkMode
                ? `hover:bg-gray-700/50 ${
                    selectedRowIndex === index ? 'bg-gray-700/70' : ''
                  }`
                : `hover:bg-blue-50/30 ${
                    selectedRowIndex === index ? 'bg-blue-50/50' : ''
                  }`
            }
          `}
      sx={{
        height: { xs: '26px', md: '26px' },
        '&:hover': {
          '& .MuiTableCell-root': {
            borderColor: darkMode
              ? 'rgba(96, 165, 250, 0.3)'
              : 'rgba(59, 130, 246, 0.3)',
          },
        },
        '&.Mui-selected, &.Mui-selected:hover': {
          '& .MuiTableCell-root': {
            borderColor: darkMode
              ? 'rgba(96, 165, 250, 0.5)'
              : 'rgba(59, 130, 246, 0.5)',
          },
        },
      }}
    >
      <TableCell className="py-0 px-0" sx={{ padding: '0px 2px' }}>
        <Checkbox
          checked={!!row.primaryKey}
          onChange={(e) =>
            handleRowChange(index, 'primaryKey', e.target.checked)
          }
          className={`${darkMode ? 'text-blue-400' : 'text-blue-500'}`}
          size="small"
          sx={{ padding: '2px', height: '26px' }}
        />
      </TableCell>
      <TableCell className="py-0 px-0" sx={{ padding: '0px 2px' }}>
        <TextField
          value={row.pkSeq || ''}
          onChange={(e) => handleNumberChange(e, index, 'pkSeq')}
          disabled={!row.primaryKey}
          size="small"
          fullWidth
          variant="outlined"
          error={!!pkSeqError}
          helperText={pkSeqError}
          inputProps={{
            min: 0,
            max: 999,
            step: 1,
            className: 'px-2 py-0 text-center',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${
            darkMode ? 'bg-gray-800/50' : 'bg-white'
          } rounded-none ${!row.primaryKey ? 'opacity-50' : ''}`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: pkSeqError
                  ? darkMode
                    ? 'rgba(239,68,68,0.7)'
                    : 'rgba(239,68,68,0.7)'
                  : 'transparent',
              },
              '&:hover fieldset': {
                borderColor: pkSeqError
                  ? darkMode
                    ? 'rgba(239,68,68,0.9)'
                    : 'rgba(239,68,68,0.9)'
                  : darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: pkSeqError
                  ? darkMode
                    ? 'rgba(239,68,68,1)'
                    : 'rgba(239,68,68,1)'
                  : '#3b82f6',
              },
              '&.Mui-disabled': {
                backgroundColor: darkMode
                  ? 'rgba(31, 41, 55, 0.5)'
                  : 'rgba(229, 231, 235, 0.5)',
                '& fieldset': {
                  borderColor: 'transparent',
                },
                '& input': {
                  color: darkMode
                    ? 'rgba(255,255,255,0.5)'
                    : 'rgba(0,0,0,0.5)',
                },
              },
            },
            '& .MuiFormHelperText-root': {
              color: darkMode
                ? 'rgba(239,68,68,0.9)'
                : 'rgba(239,68,68,0.9)',
              position: 'absolute',
              bottom: '-20px',
              margin: 0,
              fontSize: '0.625rem',
            },
          }}
        />
      </TableCell>

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <TextField
          value={row.fieldName || ''}
          disabled={!!row.mapdtlid}
          onChange={(e) => {
            const value = e.target.value.toUpperCase().slice(0, 30)
            handleRowChange(index, 'fieldName', value)
          }}
          size="small"
          fullWidth
          variant="outlined"
          inputProps={{
            maxLength: 30,
            className: 'px-2 py-0',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${
            darkMode
              ? 'bg-gray-800/50'
              : row.mapdtlid
              ? 'bg-gray-100'
              : 'bg-white'
          } rounded-none`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: 'transparent',
              },
              '&:hover fieldset': {
                borderColor: darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: '#3b82f6',
              },
              '&.Mui-disabled': {
                backgroundColor: darkMode
                  ? 'rgba(31, 41, 55, 0.5)'
                  : 'rgba(229, 231, 235, 0.5)',
                '& fieldset': {
                  borderColor: 'transparent',
                },
                '& input': {
                  color: darkMode
                    ? 'rgba(255,255,255,0.5)'
                    : 'rgba(0,0,0,0.5)',
                },
              },
            },
          }}
        />
      </TableCell>

      <TableCell
        className="py-0 px-0"
        sx={{ padding: '0px 4px', width: '100px' }}
      >
        <Autocomplete
          value={
            dataTypeOptions.find((option) => option.PRCD === row.dataType) ||
            null
          }
          disabled={!!row.mapdtlid}
          onChange={(event, newValue) => {
            handleRowChange(index, 'dataType', newValue ? newValue.PRCD : '')
          }}
          options={dataTypeOptions}
          getOptionLabel={(option) => option.PRCD}
          renderInput={(params) => (
            <TextField
              {...params}
              size="small"
              fullWidth
              variant="outlined"
              className={`${
                darkMode
                  ? 'bg-gray-800/50'
                  : row.mapdtlid
                  ? 'bg-gray-100'
                  : 'bg-white'
              } rounded-none`}
              sx={{
                '& .MuiOutlinedInput-root': {
                  height: '26px',
                  borderRadius: '0',
                  '& fieldset': {
                    borderColor: 'transparent',
                  },
                  '&:hover fieldset': {
                    borderColor: darkMode
                      ? 'rgba(96, 165, 250, 0.5)'
                      : 'rgba(59, 130, 246, 0.5)',
                  },
                  '&.Mui-focused fieldset': {
                    borderWidth: '1px !important',
                    borderColor: '#3b82f6',
                  },
                  '&.Mui-disabled': {
                    backgroundColor: darkMode
                      ? 'rgba(31, 41, 55, 0.5)'
                      : 'rgba(229, 231, 235, 0.5)',
                    '& fieldset': {
                      borderColor: 'transparent',
                    },
                    '& input': {
                      color: darkMode
                        ? 'rgba(255,255,255,0.5)'
                        : 'rgba(0,0,0,0.5)',
                    },
                  },
                },
                '& .MuiAutocomplete-inputRoot': {
                  paddingTop: '0 !important',
                  paddingBottom: '0 !important',
                },
                '& .MuiInputBase-input': {
                  padding: '2px 4px !important',
                  fontSize: '0.8rem',
                  height: '26px !important',
                  boxSizing: 'border-box',
                },
              }}
            />
          )}
          renderOption={(props, option) => (
            <li {...props}>
              <Tooltip title={option.PRDESC} placement="right" arrow>
                <span>{option.PRCD}</span>
              </Tooltip>
            </li>
          )}
          isOptionEqualToValue={(option, value) => option.PRCD === value.PRCD}
          className={darkMode ? 'text-gray-200' : ''}
          disableClearable
        />
      </TableCell>

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <TextField
          value={row.fieldDesc || ''}
          onChange={(e) => {
            const value = e.target.value.slice(0, 100)
            handleRowChange(index, 'fieldDesc', value)
          }}
          size="small"
          fullWidth
          variant="outlined"
          inputProps={{
            maxLength: 100,
            className: 'px-2 py-0',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${darkMode ? 'bg-gray-800/50' : 'bg-white'} rounded-none`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: 'transparent',
              },
              '&:hover fieldset': {
                borderColor: darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: '#3b82f6',
              },
            },
          }}
        />
      </TableCell>

      {tableType === 'DIM' && (
        <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
          <FormControl
            fullWidth
            size="small"
            variant="outlined"
            className={`${
              darkMode ? 'bg-gray-800/50' : 'bg-white'
            } rounded-none`}
          >
            <Select
              value={row.scdType || ''}
              onChange={(e) => handleRowChange(index, 'scdType', e.target.value)}
              renderValue={(value) => {
                // Find the option with matching PRCD and display its PRCD
                const option = scdTypeOptions.find((opt) => opt.PRCD === value)
                return option ? option.PRCD : value
              }}
              className={darkMode ? 'text-gray-200' : ''}
              sx={{
                height: '26px',
                borderRadius: '0',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'transparent',
                  borderRadius: '0',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: darkMode
                    ? 'rgba(96, 165, 250, 0.5)'
                    : 'rgba(59, 130, 246, 0.5)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderWidth: '1px !important',
                  borderColor: '#3b82f6',
                },
                '& .MuiSelect-select': {
                  padding: '2px 6px',
                  fontSize: '0.8rem',
                },
              }}
            >
              {scdTypeOptions.map((option) => (
                <MenuItem key={option.PRCD} value={option.PRCD}>
                  {option.PRCD}
                </MenuItem>
              ))}
              {/* Fallback option if API hasn't loaded yet */}
              {scdTypeOptions.length === 0 && (
                <>
                  <MenuItem value="1">Type 1</MenuItem>
                  <MenuItem value="2">Type 2</MenuItem>
                </>
              )}
            </Select>
          </FormControl>
        </TableCell>
      )}

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <div className="relative group">
          <TextField
            multiline
            maxRows={2}
            value={row.logic?.substring(0, 100) || ''}
            disabled
            size="small"
            fullWidth
            variant="outlined"
            placeholder="Click edit to add SQL logic"
            className={`${
              darkMode ? 'bg-gray-800/50' : 'bg-white'
            } rounded-none`}
            sx={{
              '& .MuiOutlinedInput-root': {
                fontSize: '0.75rem',
                minHeight: '20px',
                height: '26px',
                borderRadius: '0',
                '& fieldset': {
                  borderColor: 'transparent',
                  borderRadius: '0',
                },
                '&:hover fieldset': {
                  borderColor: darkMode
                    ? 'rgba(96, 165, 250, 0.5)'
                    : 'rgba(59, 130, 246, 0.5)',
                },
                '&.Mui-focused fieldset': {
                  borderWidth: '1px !important',
                  borderColor: '#3b82f6',
                },
                '&.Mui-disabled': {
                  backgroundColor: 'transparent',
                  '& fieldset': {
                    borderColor: 'transparent',
                  },
                  '& textarea': {
                    color: darkMode
                      ? 'rgba(255,255,255,0.8)'
                      : 'rgba(0,0,0,0.8)',
                  },
                },
              },
              '& .MuiInputBase-input': {
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                height: '26px',
                boxSizing: 'border-box',
                padding: '2px 4px !important',
                lineHeight: '1.2',
              },
            }}
          />
          <div className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <Tooltip title="Edit SQL Logic">
              <IconButton
                onClick={(e) => {
                  e.stopPropagation()
                  handleOpenSqlEditor(index)
                }}
                size="small"
                sx={{
                  padding: '2px',
                  backgroundColor: darkMode
                    ? 'rgba(59, 130, 246, 0.3)'
                    : 'rgba(59, 130, 246, 0.1)',
                }}
              >
                <EditIcon
                  fontSize="small"
                  className={darkMode ? 'text-blue-400' : 'text-blue-600'}
                  sx={{ fontSize: '16px' }}
                />
              </IconButton>
            </Tooltip>
          </div>
        </div>
      </TableCell>

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <TextField
          value={row.keyColumn || ''}
          onChange={(e) => {
            const value = e.target.value.slice(0, 250)
            handleRowChange(index, 'keyColumn', value)
          }}
          size="small"
          fullWidth
          variant="outlined"
          inputProps={{
            maxLength: 250,
            className: 'px-2 py-0',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${darkMode ? 'bg-gray-800/50' : 'bg-white'} rounded-none`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: 'transparent',
              },
              '&:hover fieldset': {
                borderColor: darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: '#3b82f6',
              },
            },
          }}
        />
      </TableCell>

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <TextField
          value={row.valColumn || ''}
          onChange={(e) => {
            const value = e.target.value.slice(0, 250)
            handleRowChange(index, 'valColumn', value)
          }}
          size="small"
          fullWidth
          variant="outlined"
          inputProps={{
            maxLength: 250,
            className: 'px-2 py-0',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${darkMode ? 'bg-gray-800/50' : 'bg-white'} rounded-none`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: 'transparent',
              },
              '&:hover fieldset': {
                borderColor: darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: '#3b82f6',
              },
            },
          }}
        />
      </TableCell>

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <TextField
          value={row.execSequence || ''}
          onChange={(e) => {
            // Only allow integers up to 5000
            const value = e.target.value
            if (
              value === '' ||
              (/^\d+$/.test(value) && parseInt(value) <= 5000)
            ) {
              handleRowChange(index, 'execSequence', value)
            }
          }}
          size="small"
          fullWidth
          variant="outlined"
          type="number"
          inputProps={{
            min: 0,
            max: 5000,
            className: 'px-2 py-0',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${darkMode ? 'bg-gray-800/50' : 'bg-white'} rounded-none`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: 'transparent',
              },
              '&:hover fieldset': {
                borderColor: darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: '#3b82f6',
              },
            },
            '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button':
              {
                '-webkit-appearance': 'none',
                margin: 0,
              },
            '& input[type=number]': {
              '-moz-appearance': 'textfield',
            },
          }}
        />
      </TableCell>

      <TableCell className="py-0 px-0" sx={{ padding: '0px 4px' }}>
        <TextField
          value={row.mapCombineCode || ''}
          onChange={(e) => {
            const value = e.target.value.slice(0, 30)
            handleRowChange(index, 'mapCombineCode', value)
          }}
          size="small"
          fullWidth
          variant="outlined"
          inputProps={{
            maxLength: 30,
            className: 'px-2 py-0',
            style: { height: '26px', fontSize: '0.8rem' },
          }}
          className={`${darkMode ? 'bg-gray-800/50' : 'bg-white'} rounded-none`}
          sx={{
            '& .MuiOutlinedInput-root': {
              height: '26px',
              borderRadius: '0',
              '& fieldset': {
                borderColor: 'transparent',
              },
              '&:hover fieldset': {
                borderColor: darkMode
                  ? 'rgba(96, 165, 250, 0.5)'
                  : 'rgba(59, 130, 246, 0.5)',
              },
              '&.Mui-focused fieldset': {
                borderWidth: '1px !important',
                borderColor: '#3b82f6',
              },
            },
          }}
        />
      </TableCell>

      <TableCell
        className="py-0 px-0"
        align="center"
        sx={{ padding: '0px 2px' }}
      >
        <Tooltip
          title={
            row.LogicVerFlag === ''
              ? 'Validate this row'
              : row.LogicVerFlag === 'Y'
              ? 'Logic is valid'
              : errorMessage || 'Logic is invalid'
          }
        >
          <IconButton
            onClick={(e) => {
              e.stopPropagation() // Prevent row selection
              handleValidateRow(index)
            }}
            size="small"
            sx={{
              padding: '2px',
              color:
                row.LogicVerFlag === ''
                  ? darkMode
                    ? 'rgba(156, 163, 175, 0.9)'
                    : 'rgba(75, 85, 99, 0.9)'
                  : row.LogicVerFlag === 'Y'
                  ? darkMode
                    ? 'rgba(34, 197, 94, 0.9)'
                    : 'rgba(22, 163, 74, 0.9)'
                  : darkMode
                  ? 'rgba(239, 68, 68, 0.9)'
                  : 'rgba(220, 38, 38, 0.9)',
              '&:hover': {
                color:
                  row.LogicVerFlag === ''
                    ? darkMode
                      ? 'rgba(156, 163, 175, 1)'
                      : 'rgba(75, 85, 99, 1)'
                    : row.LogicVerFlag === 'Y'
                    ? darkMode
                      ? 'rgba(34, 197, 94, 1)'
                      : 'rgba(22, 163, 74, 1)'
                    : darkMode
                    ? 'rgba(239, 68, 68, 1)'
                    : 'rgba(220, 38, 38, 1)',
              },
            }}
          >
            {row.LogicVerFlag === '' ? (
              <HelpOutlineIcon fontSize="small" sx={{ fontSize: '16px' }} />
            ) : row.LogicVerFlag === 'Y' ? (
              <CheckCircleIcon fontSize="small" sx={{ fontSize: '16px' }} />
            ) : (
              <ErrorIcon fontSize="small" sx={{ fontSize: '16px' }} />
            )}
          </IconButton>
        </Tooltip>
      </TableCell>
      {/* Add Actions cell */}
      <TableCell
        className="py-0 px-0"
        align="center"
        sx={{ padding: '0px 2px' }}
      >
        <IconButton
          onClick={(e) => handleRowMenuOpen(e, index)}
          size="small"
          sx={{
            padding: '2px',
            color: darkMode
              ? 'rgba(156, 163, 175, 0.9)'
              : 'rgba(75, 85, 99, 0.9)',
            '&:hover': {
              color: darkMode
                ? 'rgba(156, 163, 175, 1)'
                : 'rgba(75, 85, 99, 1)',
            },
          }}
        >
          <MoreVertIcon fontSize="small" sx={{ fontSize: '16px' }} />
        </IconButton>
      </TableCell>
    </TableRow>
  )
}

// Using React.memo to prevent re-renders if props haven't changed
export default React.memo(ReferenceRow) 