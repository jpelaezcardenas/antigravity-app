import React, { useState } from 'react';
import { useCampaignCreator } from '../store/campaignCreator';
import type { TaxDNA } from '../store/campaignCreator';

export const CampaignCreatorStep2: React.FC = () => {
  const { campaignObjective, setCampaignObjective, taxDna } = useCampaignCreator();
  const [expandedSection, setExpandedSection] = useState<string | null>('visual');

  const dna = taxDna as TaxDNA | null;

  const Section: React.FC<{ title: string; id: string; children: React.ReactNode }> = ({
    title,
    id,
    children,
  }) => (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpandedSection(expandedSection === id ? null : id)}
        className="w-full px-6 py-4 bg-gray-50 hover:bg-gray-100 flex items-center justify-between font-semibold text-gray-900"
      >
        <span>{title}</span>
        <span className={`transform transition-transform ${expandedSection === id ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      {expandedSection === id && <div className="p-6 bg-white space-y-4">{children}</div>}
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Brand Identity Review</h2>
        <p className="text-gray-600">
          Review extracted brand identity and define your campaign objective
        </p>
      </div>

      {/* Tax DNA Display */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-900">Extracted Tax DNA</h3>

        {/* Visual Identity */}
        <Section title="Visual Identity" id="visual">
          {dna?.visual_identity ? (
            <div className="space-y-3">
              {dna.visual_identity.primary_color && (
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded border border-gray-200"
                    style={{ backgroundColor: dna.visual_identity.primary_color }}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-700">Primary Color</p>
                    <p className="text-xs text-muted">{dna.visual_identity.primary_color}</p>
                  </div>
                </div>
              )}
              {dna.visual_identity.secondary_color && (
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded border border-gray-200"
                    style={{ backgroundColor: dna.visual_identity.secondary_color }}
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-700">Secondary Color</p>
                    <p className="text-xs text-muted">{dna.visual_identity.secondary_color}</p>
                  </div>
                </div>
              )}
              {dna.visual_identity.fonts && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Fonts</p>
                  <div className="flex flex-wrap gap-2">
                    {dna.visual_identity.fonts.map((font) => (
                      <span
                        key={font}
                        className="px-3 py-1 bg-gray-100 text-gray-800 text-xs rounded-full"
                      >
                        {font}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {dna.visual_identity.imagery_style && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Imagery Style</p>
                  <p className="text-sm text-gray-600">{dna.visual_identity.imagery_style}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted">No visual identity data extracted</p>
          )}
        </Section>

        {/* Verbal Identity */}
        <Section title="Verbal Identity" id="verbal">
          {dna?.verbal_identity ? (
            <div className="space-y-3">
              {dna.verbal_identity.tone && (
                <div>
                  <p className="text-sm font-medium text-gray-700">Tone</p>
                  <p className="text-sm text-gray-600">{dna.verbal_identity.tone}</p>
                </div>
              )}
              {dna.verbal_identity.key_phrases && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Key Phrases</p>
                  <div className="flex flex-wrap gap-2">
                    {dna.verbal_identity.key_phrases.map((phrase) => (
                      <span
                        key={phrase}
                        className="px-3 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                      >
                        {phrase}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {dna.verbal_identity.value_propositions && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Value Propositions</p>
                  <ul className="space-y-1">
                    {dna.verbal_identity.value_propositions.map((prop) => (
                      <li key={prop} className="text-sm text-gray-600">
                        • {prop}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <p className="text-muted">No verbal identity data extracted</p>
          )}
        </Section>

        {/* Services */}
        {dna?.servicios && dna.servicios.length > 0 && (
          <Section title="Services" id="services">
            <div className="space-y-3">
              {dna.servicios.map((service, idx) => (
                <div key={idx} className="p-3 bg-gray-50 rounded">
                  <p className="font-medium text-gray-900">{service.name}</p>
                  {service.description && <p className="text-sm text-gray-600">{service.description}</p>}
                  {service.price_model && (
                    <p className="text-xs text-muted mt-1">Pricing: {service.price_model}</p>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Compliance Rules */}
        {dna?.compliance_rules && (
          <Section title="Compliance Rules" id="compliance">
            {dna.compliance_rules.dian_alignment && (
              <div>
                <p className="text-sm font-medium text-gray-700">DIAN Alignment</p>
                <p className="text-sm text-gray-600">{dna.compliance_rules.dian_alignment}</p>
              </div>
            )}
            {dna.compliance_rules.forbidden_claims && (
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Forbidden Claims to Avoid</p>
                <div className="text-xs text-red-700 bg-red-50 p-3 rounded">
                  <p>This compliance framework will prevent publishing claims like:</p>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>Guaranteed results or savings</li>
                    <li>Tax avoidance statements</li>
                    <li>Fixed pricing without conditions</li>
                  </ul>
                </div>
              </div>
            )}
          </Section>
        )}
      </div>

      {/* Campaign Objective Input */}
      <div className="space-y-2">
        <label htmlFor="objective" className="block text-sm font-medium text-gray-700">
          Campaign Objective <span className="text-red-500">*</span>
        </label>
        <textarea
          id="objective"
          placeholder="E.g., Generate qualified leads for tax audit services, increase brand awareness, drive product trial..."
          value={campaignObjective}
          onChange={(e) => setCampaignObjective(e.target.value)}
          rows={4}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-muted">
          {campaignObjective.length} characters • Be specific about what success looks like
        </p>
      </div>

      {!campaignObjective && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            ⚠️ <strong>Next button disabled:</strong> Please enter a campaign objective to continue
          </p>
        </div>
      )}
    </div>
  );
};

export default CampaignCreatorStep2;
