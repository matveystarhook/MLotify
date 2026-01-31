// frontend/src/components/ui/Card.jsx

import { motion } from 'framer-motion';

export function Card({
  children,
  className = '',
  onClick,
  hoverable = false,
  ...props
}) {
  const Component = onClick ? motion.button : motion.div;
  
  return (
    <Component
      whileTap={onClick ? { scale: 0.98 } : undefined}
      className={`
        bg-white dark:bg-gray-800
        rounded-2xl p-4
        shadow-card
        ${hoverable ? 'hover:shadow-soft transition-shadow' : ''}
        ${onClick ? 'cursor-pointer w-full text-left' : ''}
        ${className}
      `}
      onClick={onClick}
      {...props}
    >
      {children}
    </Component>
  );
}