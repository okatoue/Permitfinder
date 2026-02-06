import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Button from './Button';
import Icon from './Icon';

/**
 * Header component with navigation, theme toggle, and mobile menu
 * Based on test.html navigation design
 */
const Header = ({ isDarkMode, onThemeToggle }) => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { label: 'How It Works', path: '/how-it-works' },
    { label: 'Pricing', path: '/pricing' },
    { label: 'Permits', path: '/permits' },
    { label: 'Contact', path: '/contact' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 bg-[var(--nav-bg)] backdrop-blur-xl border-b border-border-color">
      <div className="container flex justify-between items-center py-[3vh] md:py-[2vh]">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <span className="font-extrabold text-xl md:text-2xl lg:text-3xl tracking-tight text-text-primary">
            Scope Signals
          </span>
          <span className="w-2 h-2 md:w-2.5 md:h-2.5 bg-accent rounded-full shadow-[0_0_8px_var(--accent)]" />
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-8 lg:gap-12">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`text-base lg:text-lg font-medium transition-colors duration-200
                ${isActive(item.path)
                  ? 'text-text-primary'
                  : 'text-text-secondary hover:text-text-primary'
                }`}
            >
              {item.label}
            </Link>
          ))}
        </div>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-4 lg:gap-6">
          {/* Theme Toggle */}
          <button
            onClick={onThemeToggle}
            className="p-2 text-text-secondary hover:text-text-primary transition-colors duration-200"
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            <Icon name={isDarkMode ? 'sun' : 'moon'} size={24} />
          </button>

          <Button variant="link" href="#" className="mr-2 text-base lg:text-lg">
            Log In
          </Button>
          <Button variant="primary" to="/pricing">
            Check Availability
          </Button>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex md:hidden items-center gap-4">
          <button
            onClick={onThemeToggle}
            className="p-2 text-text-secondary hover:text-text-primary transition-colors duration-200"
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            <Icon name={isDarkMode ? 'sun' : 'moon'} size={22} />
          </button>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-text-primary"
            aria-label="Toggle menu"
          >
            <Icon name={isMobileMenuOpen ? 'close' : 'menu'} size={24} />
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-border-color bg-bg-card">
          <div className="container py-4 flex flex-col gap-4">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`py-2 text-[0.95rem] font-medium
                  ${isActive(item.path)
                    ? 'text-text-primary'
                    : 'text-text-secondary'
                  }`}
              >
                {item.label}
              </Link>
            ))}
            <hr className="border-border-color" />
            <Button variant="link" href="#" className="py-2">
              Log In
            </Button>
            <Button variant="primary" to="/pricing" onClick={() => setIsMobileMenuOpen(false)}>
              Check Availability
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Header;
