// frontend/src/components/ui/Input.jsx

import { forwardRef } from 'react';

export const Input = forwardRef(({
  label,
  error,
  icon,
  className = '',
  ...props
}, ref) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          {label}
        </label>
      )}
      
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            {icon}
          </div>
        )}
        
        <input
          ref={ref}
          className={`
            w-full bg-gray-100 dark:bg-gray-800
            text-gray-900 dark:text-white
            rounded-xl px-4 py-3
            ${icon ? 'pl-10' : ''}
            border-2 border-transparent
            focus:border-primary-500 focus:bg-white dark:focus:bg-gray-900
            outline-none transition-all duration-200
            placeholder:text-gray-400
            ${error ? 'border-red-500' : ''}
            ${className}
          `}
          {...props}
        />
      </div>
      
      {error && (
        <p className="mt-1.5 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';