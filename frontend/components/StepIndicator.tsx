import React from 'react';
import { FiCheck } from 'react-icons/fi';

type StepIndicatorProps = {
  currentStep: number;
  totalSteps: number;
  stepTitles?: string[];
};

export default function StepIndicator({
  currentStep,
  totalSteps,
  stepTitles = [],
}: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center mb-8 overflow-x-auto">
      <div className="flex items-center space-x-2 sm:space-x-4">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
          <div key={step} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all
                  ${
                    currentStep === step
                      ? 'bg-primary-600 text-white ring-4 ring-primary-100'
                      : currentStep > step
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 text-gray-600'
                  }
                `}
              >
                {currentStep > step ? (
                  <FiCheck className="w-5 h-5" />
                ) : (
                  <span>{step}</span>
                )}
              </div>
              {stepTitles[step - 1] && (
                <span
                  className={`
                    text-xs mt-2 text-center max-w-[80px] sm:max-w-none
                    ${currentStep === step ? 'text-primary-600 font-medium' : 'text-gray-500'}
                  `}
                >
                  {stepTitles[step - 1]}
                </span>
              )}
            </div>
            {step < totalSteps && (
              <div
                className={`
                  w-8 sm:w-12 h-0.5 mx-1 sm:mx-2 transition-all
                  ${currentStep > step ? 'bg-green-500' : 'bg-gray-200'}
                `}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
