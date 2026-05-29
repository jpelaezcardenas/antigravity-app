import React, { useState, useEffect } from 'react';

interface BusinessDNA {
  campaign_id: string;
  audience_profile: {
    edad?: string;
    ingresos?: string;
    profesion?: string;
    ubicacion?: string;
    pain_points?: string[];
  };
  tone_guidelines: {
    formalidad?: string;
    jerga?: string;
    emojis?: boolean;
    length?: string;
  };
  objectives: string[];
  key_differentiators: string[];
}

interface BusinessDNAProps {
  campaignId: string;
  onSave?: (dna: BusinessDNA) => void;
}

const BusinessDNA: React.FC<BusinessDNAProps> = ({ campaignId, onSave }) => {
  const [dna, setDNA] = useState<BusinessDNA>({
    campaign_id: campaignId,
    audience_profile: {},
    tone_guidelines: {},
    objectives: [],
    key_differentiators: [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const API_BASE = 'http://localhost:8080/api/v1/social-content-ops/content';

  // Load existing DNA
  useEffect(() => {
    fetchDNA();
  }, [campaignId]);

  const fetchDNA = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}/business-dna`);

      if (!response.ok) throw new Error('Failed to fetch DNA');

      const data = await response.json();
      if (data.campaign_id) {
        setDNA(data);
      }
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar DNA';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}/business-dna`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dna),
      });

      if (!response.ok) throw new Error('Failed to save DNA');

      const saved = await response.json();
      setDNA(saved);
      setSuccess(true);
      onSave?.(saved);

      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al guardar';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const updateAudienceProfile = (key: string, value: string | string[]) => {
    setDNA((prev) => ({
      ...prev,
      audience_profile: {
        ...prev.audience_profile,
        [key]: value,
      },
    }));
  };

  const updateToneGuidelines = (key: string, value: string | boolean) => {
    setDNA((prev) => ({
      ...prev,
      tone_guidelines: {
        ...prev.tone_guidelines,
        [key]: value,
      },
    }));
  };

  const addObjective = (objective: string) => {
    if (objective && !dna.objectives.includes(objective)) {
      setDNA((prev) => ({
        ...prev,
        objectives: [...prev.objectives, objective],
      }));
    }
  };

  const removeObjective = (objective: string) => {
    setDNA((prev) => ({
      ...prev,
      objectives: prev.objectives.filter((obj) => obj !== objective),
    }));
  };

  const addDifferentiator = (diff: string) => {
    if (diff && !dna.key_differentiators.includes(diff)) {
      setDNA((prev) => ({
        ...prev,
        key_differentiators: [...prev.key_differentiators, diff],
      }));
    }
  };

  const removeDifferentiator = (diff: string) => {
    setDNA((prev) => ({
      ...prev,
      key_differentiators: prev.key_differentiators.filter((d) => d !== diff),
    }));
  };

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="bg-red-500/10 border border-red-500 text-red-500 p-3 rounded text-sm">
          ⚠️ {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/10 border border-green-500 text-green-500 p-3 rounded text-sm">
          ✅ Business DNA guardado correctamente
        </div>
      )}

      {/* Section 1: Audience Profile */}
      <div className="bg-blue-950 rounded-lg p-6 border border-blue-800">
        <h3 className="text-lg font-semibold text-primary mb-4">👥 Perfil de Audiencia</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-muted mb-2">Edad Target</label>
            <input
              type="text"
              value={dna.audience_profile.edad || ''}
              onChange={(e) => updateAudienceProfile('edad', e.target.value)}
              placeholder="ej: 25-45 años"
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Nivel de Ingresos</label>
            <select
              value={dna.audience_profile.ingresos || ''}
              onChange={(e) => updateAudienceProfile('ingresos', e.target.value)}
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            >
              <option value="">Seleccionar</option>
              <option value="bootstrap">Bootstrap / Iniciando</option>
              <option value="mid">Medio (1-100K USD/año)</option>
              <option value="high">Alto (100K-1M USD/año)</option>
              <option value="enterprise">Enterprise (1M+ USD/año)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Profesión/Tipo de Negocio</label>
            <input
              type="text"
              value={dna.audience_profile.profesion || ''}
              onChange={(e) => updateAudienceProfile('profesion', e.target.value)}
              placeholder="ej: PyMEs, Freelancers, Dropshippers, Content Creators"
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Ubicación</label>
            <input
              type="text"
              value={dna.audience_profile.ubicacion || ''}
              onChange={(e) => updateAudienceProfile('ubicacion', e.target.value)}
              placeholder="ej: Colombia, LATAM, Global"
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Pain Points (Problemas)</label>
            <textarea
              value={(dna.audience_profile.pain_points || []).join(', ')}
              onChange={(e) => updateAudienceProfile('pain_points', e.target.value.split(',').map((p) => p.trim()))}
              placeholder="ej: Reportes tarde, Complejidad fiscal, Falta de claridad"
              rows={3}
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
      </div>

      {/* Section 2: Tone Guidelines */}
      <div className="bg-blue-950 rounded-lg p-6 border border-blue-800">
        <h3 className="text-lg font-semibold text-primary mb-4">🎨 Tono de Marca</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-muted mb-2">Formalidad</label>
            <select
              value={dna.tone_guidelines.formalidad || ''}
              onChange={(e) => updateToneGuidelines('formalidad', e.target.value)}
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            >
              <option value="">Seleccionar</option>
              <option value="formal">Formal (corporativo)</option>
              <option value="semiformal">Semi-formal (profesional amigable)</option>
              <option value="casual">Casual (cercano, accesible)</option>
              <option value="playful">Desenfadado (divertido, trendy)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Jerga/Lenguaje</label>
            <select
              value={dna.tone_guidelines.jerga || ''}
              onChange={(e) => updateToneGuidelines('jerga', e.target.value)}
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            >
              <option value="">Seleccionar</option>
              <option value="tecnico">Técnico (especializado)</option>
              <option value="accesible">Accesible (fácil de entender)</option>
              <option value="educativo">Educativo (explicativo)</option>
            </select>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={dna.tone_guidelines.emojis === true}
              onChange={(e) => updateToneGuidelines('emojis', e.target.checked)}
              id="emojis"
              className="w-4 h-4"
            />
            <label htmlFor="emojis" className="text-sm text-muted">
              ✨ Usar emojis frecuentemente
            </label>
          </div>

          <div>
            <label className="block text-sm text-muted mb-2">Longitud de Posts</label>
            <select
              value={dna.tone_guidelines.length || ''}
              onChange={(e) => updateToneGuidelines('length', e.target.value)}
              className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            >
              <option value="">Seleccionar</option>
              <option value="corto">Corto (50-100 caracteres)</option>
              <option value="medio">Medio (100-250 caracteres)</option>
              <option value="largo">Largo (250+ caracteres)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Section 3: Objectives */}
      <div className="bg-blue-950 rounded-lg p-6 border border-blue-800">
        <h3 className="text-lg font-semibold text-primary mb-4">🎯 Objetivos de Campaña</h3>

        <div className="space-y-3">
          <div className="flex gap-2">
            <select
              id="objective-select"
              className="flex-1 bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
            >
              <option value="">Seleccionar objetivo</option>
              <option value="awareness">Awareness (Dar a conocer)</option>
              <option value="engagement">Engagement (Interacción)</option>
              <option value="conversion">Conversion (Ventas)</option>
              <option value="retention">Retention (Retención)</option>
              <option value="advocacy">Advocacy (Defensores de marca)</option>
            </select>
            <button
              onClick={() => {
                const select = document.getElementById('objective-select') as HTMLSelectElement;
                addObjective(select.value);
                select.value = '';
              }}
              className="px-3 py-2 bg-primary-dim hover:bg-primary-dim text-white rounded text-sm"
            >
              ➕
            </button>
          </div>

          <div className="flex flex-wrap gap-2">
            {dna.objectives.map((obj) => (
              <span key={obj} className="bg-primary-dim text-white px-3 py-1 rounded text-sm flex items-center gap-2">
                {obj}
                <button onClick={() => removeObjective(obj)} className="text-primary hover:text-white">
                  ✕
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Section 4: Key Differentiators */}
      <div className="bg-blue-950 rounded-lg p-6 border border-blue-800">
        <h3 className="text-lg font-semibold text-primary mb-4">✨ Diferenciales Clave</h3>

        <div className="space-y-3">
          <input
            type="text"
            id="diff-input"
            placeholder="ej: Tiempo real, Automatización, Precisión"
            className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
          />
          <button
            onClick={() => {
              const input = document.getElementById('diff-input') as HTMLInputElement;
              addDifferentiator(input.value);
              input.value = '';
            }}
            className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm"
          >
            ➕ Agregar Diferencial
          </button>

          <div className="space-y-2">
            {dna.key_differentiators.map((diff) => (
              <div key={diff} className="flex justify-between items-center bg-blue-900 p-2 rounded">
                <span className="text-sm text-muted">{diff}</span>
                <button
                  onClick={() => removeDifferentiator(diff)}
                  className="text-red-500 hover:text-red-400 text-sm"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={loading}
        className="w-full px-4 py-3 bg-gradient-to-r from-primary to-blue-600 hover:from-primary-dim hover:to-blue-700 text-white font-semibold rounded-lg transition disabled:opacity-50"
      >
        {loading ? '💾 Guardando...' : '💾 Guardar Business DNA'}
      </button>
    </div>
  );
};

export default BusinessDNA;
