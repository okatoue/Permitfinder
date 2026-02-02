import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Footer component - reusable site footer
 * Matches the HomePage footer design
 */
const Footer = () => {
  return (
    <footer className="border-t border-border-color py-10 flex flex-col md:flex-row justify-between items-center gap-4 text-text-muted text-[0.9rem]">
      <div>© 2026 Scope Signals. Built for Seattle.</div>
      <div className="flex gap-5">
        <Link to="#" className="hover:text-text-primary transition-colors">
          Privacy Policy
        </Link>
        <Link to="#" className="hover:text-text-primary transition-colors">
          Terms of Service
        </Link>
      </div>
    </footer>
  );
};

export default Footer;
