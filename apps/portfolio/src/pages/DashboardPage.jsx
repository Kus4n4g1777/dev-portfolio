import React from 'react';
import { useAuth } from '../context/AuthContext';

const DashboardPage = () => {
  const { user, logout } = useAuth();

  if (!user) {
    return (
      <div className="text-center p-8">
        <h1 className="text-xl font-semibold">Loading user data...</h1>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-xl bg-white rounded-xl shadow-lg p-8 text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">Welcome, {user.username}!</h1>
        <p className="text-gray-600 mb-8">This is your protected dashboard. You can add charts, data, and other private content here.</p>
        <button
          onClick={logout}
          className="py-2 px-6 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition duration-150 ease-in-out"
        >
          Log Out
        </button>
      </div>
    </div>
  );
};

export default DashboardPage;
