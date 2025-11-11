'use client';

const InactivityLogoutModal = ({ setShowInactivityModal, logout }) => {

  const handleLogout = () => {
    if (logout) {
      logout();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm z-50 flex justify-center items-center transition-opacity duration-300 ease-in-out">
      <div className="bg-white p-8 rounded-lg shadow-xl text-center transform transition-all duration-300 ease-in-out scale-95 hover:scale-100">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">Session Expired</h2>
        <p className="mb-6 text-gray-600">You have been logged out due to inactivity.</p>
        <button
          onClick={handleLogout}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-6 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-300"
        >
          Go to Login
        </button>
      </div>
    </div>
  );
};

export default InactivityLogoutModal; 