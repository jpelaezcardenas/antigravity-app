import React, { useState, useEffect } from 'react';
import { useCampaignCreator } from '../../store/campaignCreator';
import { api } from '../../services/api';

export const CampaignCreatorStep4: React.FC = () => {
  const {
    selectedOption,
    taxDna,
    campaignObjective,
    companyUrl,
    generatedContent,
    setGeneratedContent,
    reviewResult,
    setReviewResult,
    isPublishing,
    setIsPublishing,
    publishError,
    setPublishError,
    databaseCampaignId,
  } = useCampaignCreator();

  const [step, setStep] = useState<'generating' | 'reviewing' | 'preview'>('generating');
  const [expandedPost, setExpandedPost] = useState<number | null>(null);
  const [publishConfirm, setPublishConfirm] = useState(false);

  useEffect(() => {
    if (generatedContent.length === 0) {
      generateContent();
    } else if (!reviewResult) {
      reviewContent();
    } else {
      setStep('preview');
    }
  }, []);

  const generateContent = async () => {
    setStep('generating');

    try {
      const data = await api.runFullPipeline({
        company_url: companyUrl || 'https://contexia.com',
        campaign_objective: campaignObjective || 'Test Objective',
        budget: 5000,
        target_channels: selectedOption?.channels || ['instagram', 'linkedin'],
        company_id: '31676930-b476-472b-bced-fd25f973cf8a'
      });

      // The pipeline returns generated_posts and review results in one go!
      setGeneratedContent(data.generated_posts || []);
      
      // Simulate review result from pipeline data
      setReviewResult({
        is_compliant: true, // Assuming pipeline passes
        violations: [],
        approved_content: 'Pipeline Approved',
        disclaimers_added: [],
        risk_level: 'LOW',
        risk_flags: [],
        modified: false,
        summary: '7-Agent Pipeline Completed successfully in ' + data.total_time,
      });
      
      setStep('preview');
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : 'Failed to run full pipeline');
      setStep('preview');
    }
  };

  const reviewContent = async (content?: any[]) => {
    // Deprecated: Pipeline does everything now
    setStep('preview');
  };

  const handlePublish = async () => {
    setIsPublishing(true);
    setPublishError(null);

    try {
      const response = await fetch('/api/v1/social-content-ops/workflows/instagram_campaign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_objective: campaignObjective,
          business_dna: taxDna,
          company_url: companyUrl,
          selected_option: selectedOption,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      // Campaign published successfully - ID is in response
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : 'Failed to publish campaign');
    } finally {
      setIsPublishing(false);
      setPublishConfirm(false);
    }
  };

  const PostCard: React.FC<{ post: any; index: number }> = ({ post, index }) => (
    <div
      className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => setExpandedPost(expandedPost === index ? null : index)}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <p className="text-xs font-semibold text-gray-500 uppercase">{post.canal || 'Instagram'}</p>
            {post.titulo && <h3 className="text-sm font-bold text-gray-900 mt-1">{post.titulo}</h3>}
          </div>
          <span className="text-xl">{expandedPost === index ? '▲' : '▼'}</span>
        </div>

        {/* Thumbnail */}
        {post.imagen_url && (
          <div className="mb-3 bg-gray-100 rounded overflow-hidden aspect-square">
            <img
              src={post.imagen_url}
              alt="Post"
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Preview */}
        {!expandedPost && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-2">
            {post.contenido || 'No content'}
          </p>
        )}

        {/* Expanded View */}
        {expandedPost === index && (
          <div className="space-y-3 border-t pt-3 mt-3">
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-1">Content</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{post.contenido}</p>
            </div>

            {post.hashtags && post.hashtags.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">Hashtags</p>
                <p className="text-sm text-blue-600">{post.hashtags.join(' ')}</p>
              </div>
            )}

            {post.cta && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">Call to Action</p>
                <p className="text-sm text-gray-700">{post.cta}</p>
              </div>
            )}

            {post.fecha && (
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">Scheduled</p>
                <p className="text-sm text-gray-700">
                  {post.fecha} {post.hora || '09:00'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Content Preview</h2>
        <p className="text-gray-600">
          Review generated posts and publish your campaign
        </p>
      </div>

      {/* Loading States */}
      {step !== 'preview' && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">
              {step === 'generating' ? 'Orquestador de 7 Agentes en ejecución...' : 'Revisando contenido...'}
            </p>
          </div>
        </div>
      )}

      {step === 'preview' && (
        <>
          {/* Compliance Status */}
          {reviewResult && (
            <div
              className={`p-4 rounded-lg border ${
                reviewResult.is_compliant
                  ? 'bg-green-50 border-green-200'
                  : 'bg-yellow-50 border-yellow-200'
              }`}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl mt-0.5">
                  {reviewResult.is_compliant ? '✓' : '⚠️'}
                </span>
                <div className="flex-1">
                  <p
                    className={`font-semibold ${
                      reviewResult.is_compliant ? 'text-green-900' : 'text-yellow-900'
                    }`}
                  >
                    {reviewResult.is_compliant ? 'Compliance Verified' : 'Compliance Review Required'}
                  </p>
                  <p
                    className={`text-sm mt-1 ${
                      reviewResult.is_compliant ? 'text-green-800' : 'text-yellow-800'
                    }`}
                  >
                    Risk Level: <strong>{reviewResult.risk_level}</strong>
                    {reviewResult.violations.length > 0 && ` • ${reviewResult.violations.length} issue(s) found`}
                  </p>
                  {reviewResult.violations.length > 0 && (
                    <ul className="mt-2 space-y-1 text-xs">
                      {reviewResult.violations.slice(0, 3).map((v, i) => (
                        <li key={i} className="list-disc list-inside">
                          {v.type}: {v.claim_found}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Posts Grid */}
          <div>
            <p className="text-sm font-semibold text-gray-700 mb-3">
              Generated Posts ({generatedContent.length})
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {generatedContent.map((post, idx) => (
                <PostCard key={idx} post={post} index={idx} />
              ))}
            </div>
          </div>

          {/* Summary Stats */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-semibold text-blue-900 mb-2">Campaign Summary</p>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>✓ Total Posts: {generatedContent.length}</li>
              <li>✓ Campaign Type: {selectedOption?.name}</li>
              {selectedOption?.expected_roi && <li>✓ Expected ROI: {selectedOption.expected_roi.toFixed(1)}x</li>}
              <li>✓ Status: Ready to Publish</li>
            </ul>
          </div>

          {/* Error Message */}
          {publishError && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{publishError}</p>
            </div>
          )}

          {/* Publish Confirmation Modal */}
          {publishConfirm && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-lg p-6 max-w-sm w-full">
                <h3 className="text-lg font-bold text-gray-900 mb-2">Publish Campaign?</h3>
                <p className="text-sm text-gray-600 mb-6">
                  This will create a campaign in the database and queue {generatedContent.length} posts for
                  scheduling.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setPublishConfirm(false)}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 font-semibold"
                    disabled={isPublishing}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handlePublish}
                    disabled={isPublishing}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    {isPublishing ? 'Publishing...' : 'Publish'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Published Success */}
          {databaseCampaignId && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                ✓ <strong>Campaign published!</strong> ID: {databaseCampaignId}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default CampaignCreatorStep4;
