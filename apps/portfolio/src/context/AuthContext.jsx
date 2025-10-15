import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Create the context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // On initial load, fetch user if token exists
  useEffect(() => {
    const tokenFromStorage = localStorage.getItem('token');
    if (tokenFromStorage) {
      // ✅ Pass the token from storage to the function
      fetchUserFromToken(tokenFromStorage); 
    }
  }, []); // ⬅️ Change dependency array to [] to run only once on mount

  const fetchUserFromToken = async (authToken) => {
  setLoading(true);
  try {
    const response = await fetch('http://127.0.0.1:8000/users/me/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`, // use the passed token
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user data. Token might be invalid.');
    }

    const userData = await response.json();
    setUser(userData);
  } catch (error) {
    console.error('Authentication failed:', error);
    logout();
  } finally {
    setLoading(false);
  }
};

  const login = async (username, password) => {
  setLoading(true);
  try {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch('http://127.0.0.1:8000/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    if (!response.ok) {
      throw new Error('Invalid username or password.');
    }

    const data = await response.json();
    const newAuthToken = data.access_token;

    // 🔒 Mask the access token in console logs for safety
    console.log(
      "🔑 Received token (masked):",
      newAuthToken.slice(0, 5) + "..." + newAuthToken.slice(-5)
    ); // 👈 print of the masked token for debugging

    localStorage.setItem('token', newAuthToken);
    setToken(newAuthToken);

    // ✅ Pass the token directly
    await fetchUserFromToken(newAuthToken);

    navigate('/dashboard');
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  } finally {
    setLoading(false);
  }
};


  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);
