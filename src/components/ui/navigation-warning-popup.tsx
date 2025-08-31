import React from 'react';
import Button from './button';

interface NavigationWarningPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSaveAndContinue: () => void;
  onLeaveWithoutSaving: () => void;
}

export default function NavigationWarningPopup({
  isOpen,
  onClose,
  onSaveAndContinue,
  onLeaveWithoutSaving,
}: NavigationWarningPopupProps) {
  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop with inline styles for transparency */}
      <div 
        className="fixed inset-0 z-40 backdrop-blur-sm"
        style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-xl border relative">
          {/* Close button - positioned absolutely in top right */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 hover:bg-gray-100 hover:scale-110 transition-all duration-200 rounded-full p-1 cursor-pointer"
          >
            <span className="material-symbols-outlined text-xl">
              close
            </span>
          </button>
          
          {/* Content */}
          <div className="px-6 py-6 pr-12">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Close tab?
            </h2>
            
            <p className="text-gray-600 text-sm mb-6">
              Unsaved changes may be lost. Save your query to return to reserve it.
            </p>
            
            {/* Action buttons - updated styling */}
            <div className="flex gap-2">
              <Button
                onClick={onSaveAndContinue}
                className="bg-[#2BA2D4] text-white hover:bg-[#1e8cb5] hover:scale-105 transition-all duration-200 flex-1 text-sm cursor-pointer"
              >
                <span className="material-symbols-outlined mr-1 text-sm">
                  bookmark
                </span>
                Save Query
              </Button>
              
              <Button
                onClick={onLeaveWithoutSaving}
                className="bg-white text-[#2BA2D4] border border-[#2BA2D4] hover:bg-[#2BA2D4] hover:text-white hover:scale-105 transition-all duration-200 flex-1 text-sm cursor-pointer"
              >
                Close Without Saving
              </Button>
              
              <Button
                onClick={onClose}
                className="bg-gray-200 text-gray-700 hover:bg-gray-400 hover:text-gray-800 hover:scale-105 transition-all duration-200 flex-1 text-sm cursor-pointer"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}