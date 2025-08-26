import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = () => (
  <nav className="bg-gray-800 p-4">
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
    </ul>
  </nav>
);

export default Header;
