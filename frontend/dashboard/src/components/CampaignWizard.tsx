import React from 'react';
import { useCampaignCreator } from '../store/campaignCreator';
import { CampaignCreatorStep1 } from './CampaignCreatorStep1';
import { CampaignCreatorStep2 } from './CampaignCreatorStep2';
import { CampaignCreatorStep3 } from './CampaignCreatorStep3';
import { CampaignCreatorStep4 } from './CampaignCreatorStep4';

interface StepProps {
  step: number;
  children: React.ReactNode;
}

const StepContainer: React.FC<StepProps> = ({ step, children }) => {
  const { currentStep } = useCampaignCreator();
  if (currentStep !== step) return null;
  return <div className="step-content">{children}</div>;
};

export const CampaignWizard: React.FC = () => {
  const {
    currentStep,
    nextStep,
    prevStep,
    isStepValid,
    resetWizard,
    companyUrl,
    campaignObjective,
    selectedOption,
    generatedContent,
  } = useCampaignCreator();

  const handleNext = () => {
    if (isStepValid(currentStep)) {
      nextStep();
    }
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to start over? All progress will be lost.')) {
      resetWizard();
    }
  };

  return (
    <div className="campaign-wizard bg-white rounded-lg shadow-lg p-8">
      {/* Header */}
      <div className="wizard-header mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Campaign</h1>
        <p className="text-gray-600">
          Generate AI-powered social media campaigns with Tax DNA extraction and DIAN compliance
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="progress-indicator mb-8">
        <div className="flex justify-between items-center">
          {[1, 2, 3, 4].map((step) => (
            <div key={step} className="flex items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                  currentStep >= step ? 'bg-blue-600' : 'bg-gray-300'
                }`}
              >
                {step}
              </div>
              {step < 4 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    currentStep > step ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm">
          <span className={currentStep >= 1 ? 'text-blue-600 font-semibold' : 'text-muted'}>
            Company
          </span>
          <span className={currentStep >= 2 ? 'text-blue-600 font-semibold' : 'text-muted'}>
            Objective
          </span>
          <span className={currentStep >= 3 ? 'text-blue-600 font-semibold' : 'text-muted'}>
            Campaign
          </span>
          <span className={currentStep >= 4 ? 'text-blue-600 font-semibold' : 'text-muted'}>
            Review
          </span>
        </div>
      </div>

      {/* Step Status */}
      <div className="step-status mb-6 text-center">
        <p className="text-gray-600">
          Step {currentStep} of 4
          {currentStep === 1 && ': Company Analysis'}
          {currentStep === 2 && ': Brand Review'}
          {currentStep === 3 && ': Campaign Selection'}
          {currentStep === 4 && ': Content Preview'}
        </p>
      </div>

      {/* Steps Content */}
      <StepContainer step={1}>
        <CampaignCreatorStep1 />
      </StepContainer>

      <StepContainer step={2}>
        <CampaignCreatorStep2 />
      </StepContainer>

      <StepContainer step={3}>
        <CampaignCreatorStep3 />
      </StepContainer>

      <StepContainer step={4}>
        <CampaignCreatorStep4 />
      </StepContainer>

      {/* Navigation Buttons */}
      <div className="wizard-navigation flex justify-between mt-8 pt-8 border-t">
        <button
          onClick={() => {
            if (currentStep === 1) {
              handleReset();
            } else {
              prevStep();
            }
          }}
          className={`px-6 py-2 rounded-lg font-semibold ${
            currentStep === 1
              ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              : 'bg-gray-500 text-white hover:bg-gray-600'
          }`}
        >
          {currentStep === 1 ? 'Reset' : 'Back'}
        </button>

        <div className="flex gap-4">
          <button
            onClick={handleReset}
            className="px-6 py-2 rounded-lg font-semibold bg-gray-200 text-gray-700 hover:bg-gray-300"
          >
            Cancel
          </button>

          <button
            onClick={handleNext}
            disabled={!isStepValid(currentStep)}
            className={`px-6 py-2 rounded-lg font-semibold ${
              isStepValid(currentStep)
                ? 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer'
                : 'bg-gray-300 text-muted cursor-not-allowed'
            }`}
          >
            {currentStep === 4 ? 'Publish Campaign' : 'Next'}
          </button>
        </div>
      </div>

      {/* Status Summary */}
      {currentStep > 1 && (
        <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h3 className="font-semibold text-blue-900 mb-2">Current Progress:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            {companyUrl && <li className="flex items-center">✓ Company URL: {companyUrl}</li>}
            {campaignObjective && (
              <li className="flex items-center">✓ Campaign Objective: {campaignObjective}</li>
            )}
            {selectedOption && (
              <li className="flex items-center">✓ Selected: {selectedOption.name}</li>
            )}
            {generatedContent.length > 0 && (
              <li className="flex items-center">✓ Generated {generatedContent.length} posts</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CampaignWizard;
