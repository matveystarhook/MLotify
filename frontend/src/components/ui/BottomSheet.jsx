// frontend/src/components/ui/BottomSheet.jsx

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect } from 'react';

export function BottomSheet({
  isOpen,
  onClose,
  title,
  children,
  showHandle = true,
}) {
  // Блокируем скролл body
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onClose}
          />
          
          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50
                       bg-white dark:bg-gray-900
                       rounded-t-3xl
                       max-h-[90vh] overflow-hidden
                       flex flex-col"
          >
            {/* Handle */}
            {showHandle && (
              <div className="flex justify-center pt-3 pb-2">
                <div className="w-10 h-1 bg-gray-300 dark:bg-gray-700 rounded-full" />
              </div>
            )}
            
            {/* Header */}
            {title && (
              <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
                <h2 className="text-lg font-semibold text-center">{title}</h2>
              </div>
            )}
            
            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 safe-bottom">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}