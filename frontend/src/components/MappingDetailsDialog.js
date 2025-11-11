import { useTheme, useMediaQuery } from '@mui/material';

export default function MappingDetailsDialog({ 
  open, 
  onClose, 
  selectedJob, 
  mappingData, 
  mappingLoading 
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center overflow-y-auto p-4">
      <div className="bg-white rounded-xl w-full max-w-[95vw] mx-auto my-4 shadow-2xl border border-gray-100">
        {/* Dialog Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div className="flex items-center space-x-3">
            <h2 className="text-white text-xl font-semibold">Mapping Details</h2>
            {selectedJob?.MAPREF && (
              <span className="bg-white/20 text-white px-3 py-1 rounded-full text-sm font-medium backdrop-blur-sm">
                {selectedJob.MAPREF}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            aria-label="Close dialog"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Dialog Content */}
        <div className="p-6 max-h-[calc(100vh-12rem)] overflow-y-auto">
          {mappingLoading ? (
            <div className="flex justify-center items-center h-40">
              <div className="animate-spin rounded-full h-12 w-12 border-t-3 border-b-3 border-blue-500"></div>
            </div>
          ) : mappingData ? (
            <div className="space-y-6">
              {/* Mapping Reference Card */}
              <div className="bg-gray-50 rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200 bg-white">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center">
                    <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Mapping Reference Information
                  </h3>
                </div>
                <div className="p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {Object.entries(mappingData.mapping_reference).map(([key, value]) => (
                    <div key={key} className="bg-white p-3 rounded-lg border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                      <span className="text-xs text-gray-500 block capitalize">
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="text-sm font-medium text-gray-800">
                        {value?.toString() || '—'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Mapping Details Table */}
              <div className="rounded-xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="px-6 py-3 bg-white border-b border-gray-200 flex justify-between items-center">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center">
                    <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 7v10c0 2 1 3 3 3h10c2 0 3-1 3-3V7c0-2-1-3-3-3H7c-2 0-3 1-3 3z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-8" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17v-8" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 9h6" />
                    </svg>
                    Mapping Details
                  </h3>
                  <span className="text-xs bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-medium">
                    {mappingData.mapping_details.length} entries
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target Column</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key Column</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value Column</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Is Key</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Key Sequence</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SCD Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Logic Verify</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Map Combine Code</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Execution Sequence</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mapping Logic</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {mappingData.mapping_details.map((detail, index) => (
                        <tr key={detail.MAPDTLID} className={`hover:bg-blue-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                          <td className="px-4 py-3 text-sm">{detail.MAPDTLID}</td>
                          <td className="px-4 py-3 text-sm font-medium text-blue-700">{detail.TRGCLNM}</td>
                          <td className="px-4 py-3 text-sm">{detail.TRGCLDESC}</td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 font-medium">
                              {detail.TRGCLDTYP}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">{detail.KEYCLNM}</td>
                          <td className="px-4 py-3 text-sm">{detail.VALCLNM}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded-full font-medium ${detail.TRGPKFLG === 'Y' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                              {detail.TRGPKFLG === 'Y' ? 'Yes' : 'No'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">{detail.TRGPKSEQ || '—'}</td>
                          <td className="px-4 py-3 text-sm">{detail.SCDTYP || '—'}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs rounded-full font-medium ${detail.LGVRFYFLG === 'Y' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'}`}>
                              {detail.LGVRFYFLG === 'Y' ? 'Yes' : 'No'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">{detail.MAPCMBCD || '—'}</td>
                          <td className="px-4 py-3 text-sm">{detail.EXCSEQ}</td>
                          <td className="px-4 py-3 text-sm">
                            <div className="max-w-xs truncate group relative cursor-pointer" title={detail.MAPLOGIC}>
                              {detail.MAPLOGIC}
                              {detail.MAPLOGIC && detail.MAPLOGIC.length > 20 && (
                                <div className="absolute hidden group-hover:block z-10 bottom-full left-0 bg-gray-800 text-white p-2 rounded text-xs max-w-md">
                                  {detail.MAPLOGIC}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-40 bg-gray-50 rounded-lg">
              <svg className="w-12 h-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-500 text-sm font-medium">No mapping data available.</p>
              <p className="text-gray-400 text-xs mt-1">Please select a valid mapping reference.</p>
            </div>
          )}
        </div>

        {/* Dialog Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-xl flex justify-end">
          <button
            onClick={onClose}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm hover:shadow-md flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}