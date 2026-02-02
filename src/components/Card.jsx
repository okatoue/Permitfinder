import React from 'react';

/**
 * Reusable Card component for content sections
 * Supports different variants and hover effects
 */
const Card = ({
  children,
  variant = 'default',
  hover = true,
  className = '',
  ...props
}) => {
  const baseStyles = `
    bg-bg-card border border-border-color rounded-xl
    transition-all duration-200
  `;

  const variants = {
    default: 'p-8',
    compact: 'p-6',
    large: 'p-10',
  };

  const hoverStyles = hover
    ? 'hover:-translate-y-0.5 hover:border-text-muted'
    : '';

  return (
    <div
      className={`${baseStyles} ${variants[variant] || variants.default} ${hoverStyles} ${className}`.trim()}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * PropCard variant specifically for value proposition cards
 */
export const PropCard = ({ icon, title, description, className = '' }) => {
  return (
    <Card className={className}>
      {icon && (
        <div className="text-accent mb-4 block">
          {icon}
        </div>
      )}
      {title && (
        <h3 className="text-[1.1rem] mb-3 text-text-primary font-semibold">
          {title}
        </h3>
      )}
      {description && (
        <p className="text-[0.95rem] text-text-secondary leading-relaxed">
          {description}
        </p>
      )}
    </Card>
  );
};

export default Card;
