import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Create the context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // On initial load, try to fetch the user if a token exists
  useEffect(() => {
    if (token) {
      fetchUserFromToken();
    }
  }, [token]);

  // Function to fetch user data from the protected endpoint
  const fetchUserFromToken = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/users/me/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user data. Token might be invalid.');
      }

      const userData = await response.json();
      setUser(userData);
    } catch (error) {
      console.error('Authentication failed:', error);
      // Clear token if it's invalid
      logout();
    } finally {
      setLoading(false);
    }
  };

  // Function to handle login
  const login = async (username, password) => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('http://127.0.0.1:8000/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        throw new Error('Invalid username or password.');
      }

      const data = await response.json();
      const newAuthToken = data.access_token;

      // Store the token and update state
      localStorage.setItem('token', newAuthToken);
      setToken(newAuthToken);

      // Fetch user data after successful login
      await fetchUserFromToken();
      navigate('/dashboard'); // Navigate to the dashboard after login
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Function to handle logout
  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    navigate('/'); // Redirect to home page or login
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook to use the context
export const useAuth = () => useContext(AuthContext);
