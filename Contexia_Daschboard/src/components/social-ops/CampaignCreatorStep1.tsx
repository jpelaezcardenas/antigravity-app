import React, { useState } from 'react';
import { useCampaignCreator } from '../../store/campaignCreator';

export const CampaignCreatorStep1: React.FC = () => {
  const {
    companyUrl,
    setCompanyUrl,
    isLoadingTaxDna,
    setIsLoadingTaxDna,
    setTaxDna,
    nextStep,
  } = useCampaignCreator();

  const [inputValue, setInputValue] = useState(companyUrl);
  const [error, setError] = useState<string | null>(null);

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url.startsWith('http') ? url : `https://${url}`);
      return true;
    } catch {
      return false;
    }
  };

  const handleAnalyze = async () => {
    setError(null);

    if (!inputValue.trim()) {
      setError('Please enter a company URL');
      return;
    }

    if (!validateUrl(inputValue)) {
      setError('Please enter a valid URL (e.g., https://company.com)');
      return;
    }

    setCompanyUrl(inputValue);
    setIsLoadingTaxDna(true);

    try {
      const urlToAnalyze = inputValue.startsWith('http') ? inputValue : `https://${inputValue}`;
      const response = await fetch('/api/v1/agents/onboarding/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_url: urlToAnalyze }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setTaxDna(data.tax_dna);
      nextStep();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze company. Please try again.');
    } finally {
      setIsLoadingTaxDna(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAnalyze();
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Company Analysis</h2>
        <p className="text-gray-600">
          Enter your company website URL to extract brand identity and compliance rules
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="companyUrl" className="block text-sm font-medium text-gray-700">
          Company Website URL
        </label>
        <input
          id="companyUrl"
          type="url"
          placeholder="https://example.com or example.com"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoadingTaxDna}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <button
        onClick={handleAnalyze}
        disabled={isLoadingTaxDna}
        className={`w-full px-6 py-3 rounded-lg font-semibold ${
          isLoadingTaxDna
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {isLoadingTaxDna ? (
          <div className="flex items-center justify-center gap-2">
            <div className="w-4 h-4 border-2 border-gray-400 border-t-white rounded-full animate-spin" />
            Extracting Tax DNA...
          </div>
        ) : (
          'Analyze'
        )}
      </button>

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          💡 <strong>Tip:</strong> We'll extract your brand colors, fonts, tone, services, and compliance rules
          from your website to create on-brand campaigns.
        </p>
      </div>
    </div>
  );
};

export default CampaignCreatorStep1;
