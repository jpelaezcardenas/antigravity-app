import React, { useState, useEffect } from 'react';
import { useCampaignCreator } from '../store/campaignCreator';
import type { CampaignOption } from '../store/campaignCreator';

export const CampaignCreatorStep3: React.FC = () => {
  const {
    campaignObjective,
    taxDna,
    campaignOptions,
    setCampaignOptions,
    selectedOption,
    selectOption,
    nextStep,
  } = useCampaignCreator();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (campaignOptions.length === 0) {
      loadCampaignOptions();
    }
  }, []);

  const loadCampaignOptions = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/agents/planner/generate-options', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_objective: campaignObjective,
          tax_dna: taxDna,
          budget: 5000,
          timeline_weeks: 4,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setCampaignOptions(data.campaign_options || []);

      // Auto-select recommended option if available
      const recommended = data.campaign_options?.find((opt: CampaignOption) => opt.recommended);
      if (recommended) {
        selectOption(recommended);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate campaign options');
    } finally {
      setLoading(false);
    }
  };

  const OptionCard: React.FC<{ option: CampaignOption; isSelected: boolean; onSelect: () => void }> = ({
    option,
    isSelected,
    onSelect,
  }) => (
    <button
      onClick={onSelect}
      className={`w-full p-6 rounded-lg border-2 transition-all text-left ${
        isSelected
          ? 'border-blue-600 bg-blue-50 shadow-lg'
          : 'border-gray-200 bg-white hover:border-blue-400 hover:shadow-md'
      }`}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">{option.name}</h3>
            <p className="text-sm text-gray-600">{option.type}</p>
          </div>
          {option.recommended && (
            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full whitespace-nowrap ml-2">
              ⭐ Recommended
            </span>
          )}
        </div>

        {/* Description */}
        {option.description && <p className="text-sm text-gray-700">{option.description}</p>}

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4 py-4 border-t border-b border-gray-200">
          {option.total_posts && (
            <div>
              <p className="text-xs text-muted">Total Posts</p>
              <p className="text-lg font-semibold text-gray-900">{option.total_posts}</p>
            </div>
          )}
          {option.duration_weeks && (
            <div>
              <p className="text-xs text-muted">Duration</p>
              <p className="text-lg font-semibold text-gray-900">{option.duration_weeks}w</p>
            </div>
          )}
          {option.expected_roi && (
            <div>
              <p className="text-xs text-muted">Expected ROI</p>
              <p className="text-lg font-semibold text-green-600">{option.expected_roi.toFixed(1)}x</p>
            </div>
          )}
        </div>

        {/* Channels */}
        {option.channels && (
          <div>
            <p className="text-xs font-medium text-gray-700 mb-2">Channels</p>
            <div className="flex flex-wrap gap-2">
              {option.channels.map((channel) => (
                <span
                  key={channel}
                  className="px-3 py-1 bg-gray-100 text-gray-800 text-xs rounded-full"
                >
                  {channel}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Selection Indicator */}
        {isSelected && (
          <div className="flex items-center justify-center gap-2 pt-2 text-blue-600 font-semibold">
            ✓ Selected
          </div>
        )}
      </div>
    </button>
  );

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Campaign Selection</h2>
        <p className="text-gray-600">
          Choose the campaign type that best matches your objective
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Generating campaign options...</p>
          </div>
        </div>
      ) : error ? (
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
          <button
            onClick={loadCampaignOptions}
            className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold"
          >
            Retry
          </button>
        </div>
      ) : campaignOptions.length === 0 ? (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
          <p className="text-gray-600">No campaign options available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {campaignOptions.map((option, idx) => (
            <OptionCard
              key={idx}
              option={option}
              isSelected={selectedOption?.name === option.name}
              onSelect={() => selectOption(option)}
            />
          ))}
        </div>
      )}

      {!selectedOption && campaignOptions.length > 0 && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ <strong>Next button disabled:</strong> Please select a campaign option to continue
          </p>
        </div>
      )}

      {selectedOption && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">
            ✓ <strong>Selected:</strong> {selectedOption.name}
            {selectedOption.expected_roi && ` • Expected ROI: ${selectedOption.expected_roi.toFixed(1)}x`}
          </p>
        </div>
      )}
    </div>
  );
};

export default CampaignCreatorStep3;
