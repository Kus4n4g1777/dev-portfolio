import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import HomePage from './pages/HomePage';
import BlogPage from './pages/BlogPage';
import ProjectsPage from './pages/ProjectsPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app-container">
          <Header />
          <main className="container mx-auto p-4 flex-grow">
            <Routes>
              {/* This is the only public route */}
              <Route path="/login" element={<LoginPage />} />

              {/* All other routes are now protected */}
              <Route
                path="*"
                element={
                  <ProtectedRoute>
                    <Routes>
                      <Route path="/" element={<HomePage />} />
                      <Route path="/blog" element={<BlogPage />} />
                      <Route path="/projects" element={<ProjectsPage />} />
                      <Route path="/dashboard" element={<DashboardPage />} />
                    </Routes>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
