import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { token, loading } = useAuth();

  // If loading, show a loading message
  if (loading) {
    return <div className="text-center mt-20">Loading...</div>;
  }

  // If there's no token, redirect to the home page (which will show the login)
  if (!token) {
    return <Navigate to="/" replace />;
  }

  // Otherwise, render the child components (the protected page)
  return children;
};

export default ProtectedRoute;
