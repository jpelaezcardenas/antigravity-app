import React, { useState, useEffect } from 'react';
import '../../../styles/workflows.css';

interface StoryPost {
  titulo: string;
  contenido: string;
  fase: string;
  canal: string;
  emoji: string;
  cta: string;
  hashtags: string[];
}

interface Timeline {
  fecha: string;
  dia_semana: string;
  canal: string;
  post: StoryPost;
}

const StorytellingSeriesWorkflow: React.FC<{
  campaignId?: string;
  storyTheme?: string;
  targetSegment?: string;
}> = ({ campaignId = 'demo-story', storyTheme = 'PyME struggling with tax compliance', targetSegment = 'Empresarios' }) => {
  const [campaign, setCampaign] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPost, setSelectedPost] = useState<StoryPost | null>(null);

  const PHASE_COLORS: Record<string, string> = {
    setup: '#FF6B6B',
    complication: '#FFA500',
    conflict: '#FF4444',
    turning_point: '#FFD700',
    resolution: '#4ECDC4',
    cta: '#2ECC71'
  };

  const PHASE_NAMES: Record<string, string> = {
    setup: '📖 Setup',
    complication: '😰 Complication',
    conflict: '⚠️ Conflict',
    turning_point: '✨ Turning Point',
    resolution: '✅ Resolution',
    cta: '🎯 CTA'
  };

  useEffect(() => {
    generateSeries();
  }, []);

  const generateSeries = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/social-content-ops/workflows/storytelling-series', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          story_theme: storyTheme,
          target_segment: targetSegment,
          protagonist_profile: {
            name: 'Our Hero',
            pain_point: 'Riesgos fiscales',
            solution: 'Auditoría integral',
            desired_outcome: 'Tranquilidad fiscal'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCampaign(data);
      } else {
        setCampaign(generateMockSeries());
      }
    } catch (error) {
      console.error('Error generating series:', error);
      setCampaign(generateMockSeries());
    } finally {
      setLoading(false);
    }
  };

  const generateMockSeries = () => ({
    story_theme: storyTheme,
    target_segment: targetSegment,
    total_posts: 6,
    timeline: [
      {
        fecha: '2026-05-26',
        dia_semana: 'Monday',
        canal: 'instagram',
        post: {
          titulo: '📖 La historia comienza',
          contenido: 'Introducimos a nuestro protagonista y su problema...',
          fase: 'setup',
          canal: 'instagram',
          emoji: '📖',
          cta: 'Continúa leyendo',
          hashtags: ['#historia']
        }
      },
      {
        fecha: '2026-05-29',
        dia_semana: 'Thursday',
        canal: 'instagram',
        post: {
          titulo: '😰 El problema se agrava',
          contenido: 'La tensión aumenta cuando las cosas se complican...',
          fase: 'complication',
          canal: 'instagram',
          emoji: '😰',
          cta: '¿Qué pasó después?',
          hashtags: ['#tension']
        }
      },
      {
        fecha: '2026-06-01',
        dia_semana: 'Sunday',
        canal: 'tiktok',
        post: {
          titulo: '⚠️ El momento crítico',
          contenido: 'Crisis máxima. Todo parece perdido.',
          fase: 'conflict',
          canal: 'tiktok',
          emoji: '⚠️',
          cta: 'El cambio llegó cuando...',
          hashtags: ['#crisismoment']
        }
      },
      {
        fecha: '2026-06-04',
        dia_semana: 'Wednesday',
        canal: 'instagram',
        post: {
          titulo: '✨ El giro inesperado',
          contenido: 'Un cambio transformador llega en el momento exacto.',
          fase: 'turning_point',
          canal: 'instagram',
          emoji: '✨',
          cta: 'La transformación fue inmediata',
          hashtags: ['#cambio']
        }
      },
      {
        fecha: '2026-06-07',
        dia_semana: 'Saturday',
        canal: 'linkedin',
        post: {
          titulo: '✅ 90 días después',
          contenido: 'Los resultados hablan por sí solos. Éxito total.',
          fase: 'resolution',
          canal: 'linkedin',
          emoji: '✅',
          cta: 'Tu historia puede ser similar',
          hashtags: ['#exito']
        }
      },
      {
        fecha: '2026-06-10',
        dia_semana: 'Tuesday',
        canal: 'whatsapp',
        post: {
          titulo: '🎯 ¿Tu historia es similar?',
          contenido: 'Si enfrentas los mismos desafíos, tenemos la solución.',
          fase: 'cta',
          canal: 'whatsapp',
          emoji: '🎯',
          cta: 'Agenda una consulta gratuita',
          hashtags: ['#solucion']
        }
      }
    ],
    channels_used: {
      instagram: 3,
      linkedin: 1,
      tiktok: 1,
      whatsapp: 1
    },
    arc_summary: {
      hero: 'Contador/Empresario',
      conflict: 'Riesgos fiscales desconocidos',
      resolution: 'Auditoría integral que transforma el negocio'
    },
    metrics: {
      expected_reach: 8000,
      expected_engagement: 500,
      expected_conversions: 20,
      conversion_rate: '0.25%'
    }
  });

  if (!campaign) {
    return <div className="workflow-container">Cargando serie...</div>;
  }

  const timeline = campaign.timeline || [];

  return (
    <div className="workflow-container">
      <div className="workflow-header">
        <h2>📖 Storytelling Series</h2>
        <p className="subtitle">{campaign.story_theme} (6 posts, 15 días)</p>
        <button onClick={generateSeries} disabled={loading} className="btn-primary">
          {loading ? 'Generando...' : 'Generar nueva serie'}
        </button>
      </div>

      <div className="story-arc-container">
        <h3>📈 Narrative Arc</h3>
        <div className="arc-visual">
          {Object.entries(PHASE_NAMES).map(([phase, label], idx) => (
            <div key={phase} className="arc-stage">
              <div
                className="arc-dot"
                style={{ backgroundColor: PHASE_COLORS[phase] }}
              />
              <span className="arc-label">{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="timeline-container">
        <h3>📅 Story Timeline</h3>
        <div className="story-timeline">
          {timeline.map((item: Timeline, idx: number) => (
            <div key={idx} className="story-post-item">
              <div className="timeline-marker" style={{ backgroundColor: PHASE_COLORS[item.post.fase] }} />
              <div className="story-post-content" onClick={() => setSelectedPost(item.post)}>
                <div className="post-header">
                  <span className="post-numero">Post {idx + 1}</span>
                  <span className="post-fecha">{item.fecha}</span>
                </div>
                <h4>{item.post.titulo}</h4>
                <p className="post-preview">{item.post.contenido.substring(0, 80)}...</p>
                <div className="post-footer">
                  <span className="canal-badge">{item.canal}</span>
                  <span className="phase-badge" style={{ backgroundColor: PHASE_COLORS[item.post.fase] }}>
                    {PHASE_NAMES[item.post.fase]}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="story-summary">
        <h3>🎬 Arc Summary</h3>
        <div className="summary-cards">
          <div className="summary-card">
            <strong>Hero:</strong>
            <p>{campaign.arc_summary.hero}</p>
          </div>
          <div className="summary-card">
            <strong>Conflict:</strong>
            <p>{campaign.arc_summary.conflict}</p>
          </div>
          <div className="summary-card">
            <strong>Resolution:</strong>
            <p>{campaign.arc_summary.resolution}</p>
          </div>
        </div>
      </div>

      <div className="metrics-section">
        <h3>📊 Métricas Esperadas</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_reach.toLocaleString()}</div>
            <div className="metric-label">Reach esperado</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_engagement}</div>
            <div className="metric-label">Engagement estimado</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_conversions}</div>
            <div className="metric-label">Conversiones esperadas</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.conversion_rate}</div>
            <div className="metric-label">Conversion rate</div>
          </div>
        </div>
      </div>

      {selectedPost && (
        <div className="modal-overlay" onClick={() => setSelectedPost(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedPost(null)}>✕</button>
            <div className="post-detail">
              <h2>{selectedPost.emoji} {selectedPost.titulo}</h2>
              <p className="post-content">{selectedPost.contenido}</p>
              <div className="post-cta">
                <strong>CTA:</strong> {selectedPost.cta}
              </div>
              {selectedPost.hashtags.length > 0 && (
                <div className="hashtags">
                  {selectedPost.hashtags.map((tag: string, i: number) => (
                    <span key={i} className="hashtag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StorytellingSeriesWorkflow;
