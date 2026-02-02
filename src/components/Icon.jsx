import React from 'react';

/**
 * Reusable Icon component with common SVG icons
 * Uses currentColor for theme-aware coloring
 */
const icons = {
  lock: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
    />
  ),
  lightning: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M13 10V3L4 14h7v7l9-11h-7z"
    />
  ),
  download: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
    />
  ),
  check: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M5 13l4 4L19 7"
    />
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="5" />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
      />
    </>
  ),
  moon: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
    />
  ),
  menu: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M4 6h16M4 12h16M4 18h16"
    />
  ),
  close: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M6 18L18 6M6 6l12 12"
    />
  ),
  arrowRight: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M14 5l7 7m0 0l-7 7m7-7H3"
    />
  ),
  chevronDown: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M19 9l-7 7-7-7"
    />
  ),
};

const Icon = ({
  name,
  size = 24,
  strokeWidth = 2,
  className = '',
  ...props
}) => {
  const iconPath = icons[name];

  if (!iconPath) {
    console.warn(`Icon "${name}" not found`);
    return null;
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      className={className}
      {...props}
    >
      {iconPath}
    </svg>
  );
};

export default Icon;
