import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';

/**
 * Layout component that wraps all pages
 * Provides consistent header, theme management, and background
 */
const Layout = () => {
  // Initialize theme from localStorage or default to dark
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme === 'dark';
    }
    // Default to dark theme (matching the mockup design)
    return true;
  });

  // Update document theme attribute and localStorage
  useEffect(() => {
    const theme = isDarkMode ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [isDarkMode]);

  const handleThemeToggle = () => {
    setIsDarkMode((prev) => !prev);
  };

  return (
    <div className="min-h-screen">
      {/* Background Mesh */}
      <div className="bg-mesh" />

      {/* Header */}
      <Header isDarkMode={isDarkMode} onThemeToggle={handleThemeToggle} />

      {/* Main Content */}
      <main className="container">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
