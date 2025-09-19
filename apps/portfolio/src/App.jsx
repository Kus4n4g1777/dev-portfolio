import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import HomePage from './pages/HomePage';
import BlogPage from './pages/BlogPage';
import TestsPage from './pages/TestsPage';
import ProjectsPage from './pages/ProjectsPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';


function Layout() {
  const { user } = useAuth();

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header visible solo si hay user */}
      {user && <Header />}

      <main className="flex-grow">
        <Routes>
          {/* Público */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protegido */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/blog" element={<BlogPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/tests" element={<TestsPage />} />
          </Route>
        </Routes>
      </main>

      {/* Footer visible solo si hay user */}
      {user && <Footer />}
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Layout />
      </AuthProvider>
    </Router>
  );
}
