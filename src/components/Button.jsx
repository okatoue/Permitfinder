import React from 'react';
import { Link } from 'react-router-dom';

/**
 * Reusable Button component with multiple variants
 * Supports both button and link rendering
 */
const Button = ({
  children,
  variant = 'primary',
  href,
  to,
  onClick,
  className = '',
  type = 'button',
  disabled = false,
  ...props
}) => {
  const baseStyles = `
    inline-block px-8 py-4 rounded-md font-semibold text-base
    cursor-pointer transition-all duration-200 ease-in-out
    disabled:opacity-50 disabled:cursor-not-allowed
  `;

  const variants = {
    primary: `
      bg-accent text-accent-text
      shadow-[0_0_15px_rgba(46,234,122,0.2)]
      border border-transparent
      hover:bg-accent-hover hover:shadow-[0_0_25px_rgba(46,234,122,0.4)]
      hover:-translate-y-0.5
    `,
    secondary: `
      bg-transparent border border-border-color
      text-text-primary
      hover:border-text-secondary hover:bg-[rgba(232,238,248,0.05)]
    `,
    link: `
      bg-transparent border-none p-0
      text-text-secondary text-[0.9rem]
      hover:text-text-primary
    `,
  };

  const combinedClassName = `${baseStyles} ${variants[variant] || variants.primary} ${className}`.trim();

  // Render as React Router Link for internal navigation
  if (to) {
    return (
      <Link to={to} className={combinedClassName} {...props}>
        {children}
      </Link>
    );
  }

  // Render as anchor for external links
  if (href) {
    return (
      <a href={href} className={combinedClassName} {...props}>
        {children}
      </a>
    );
  }

  // Render as button
  return (
    <button
      type={type}
      onClick={onClick}
      className={combinedClassName}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
