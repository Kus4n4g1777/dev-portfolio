import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Header.css';

const Header = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-gray-800 p-4 text-white">
      <ul className="flex justify-center space-x-6">
        <li>
          <Link to="/" className="nav-link">Home</Link>
        </li>
        <li>
          <Link to="/blog" className="nav-link">Blog</Link>
        </li>
        <li>
          <Link to="/projects" className="nav-link">Projects</Link>
        </li>
        {user ? (
          <>
            <li>
              <Link to="/dashboard" className="nav-link">Dashboard</Link>
            </li>
            <li>
              <button onClick={logout} className="nav-link">Logout</button>
            </li>
          </>
        ) : (
          <li>
            <Link to="/login" className="nav-link">Login</Link>
          </li>
        )}
      </ul>
    </nav>
  );
};

export default Header;
