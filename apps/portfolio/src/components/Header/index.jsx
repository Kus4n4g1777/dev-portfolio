import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Header.css';

const Header = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-gray-800 w-full">
      <ul className="nav-link flex justify-center space-x-6 py-4">
        <li>
          <Link to="/"  className ="nav-item">Home</Link>
        </li>
        <li>
          <Link to="/blog" className ="nav-item">Blog</Link>
        </li>
        <li>
          <Link to="/projects" className ="nav-item">Projects</Link>
        </li>
        <li>
          <Link to="/tests" className ="nav-item">Tests</Link>
        </li>
        {user ? (
          <>
            <li>
              <Link to="/dashboard" className ="nav-item">Dashboard</Link>
            </li>
            <li>
              <Link to="#" onClick={logout} className="nav-item">
                Logout
              </Link>
            </li>
          </>
        ) : (
          <li>
            <Link to="/login" className ="nav-item">Login</Link>
          </li>
        )}
      </ul>
    </nav>
  );
};

export default Header;
