import React, { useState, useEffect } from 'react';
import '../../styles/workflows.css';

interface LaunchPost {
  titulo: string;
  contenido: string;
  fase: 'teaser' | 'reveal' | 'convert';
  canal: string;
  emoji: string;
  cta: string;
  hashtags: string[];
}

interface Timeline {
  fecha: string;
  canal: string;
  post: LaunchPost;
}

interface Phase {
  name: string;
  color: string;
  description: string;
}

const ProductLaunchWorkflow: React.FC<{
  campaignId?: string;
  productName?: string;
  productDescription?: string;
  businessDna?: any;
}> = ({ campaignId = 'demo-launch', productName = 'Auditoría Sombra', productDescription = 'Auditoría fiscal completa' }) => {
  const [campaign, setCampaign] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedPost, setSelectedPost] = useState<LaunchPost | null>(null);
  const [weeks, setWeeks] = useState(4);

  const PHASE_COLORS: Record<string, string> = {
    teaser: '#FF6B6B',
    reveal: '#4ECDC4',
    convert: '#FFE66D'
  };

  const PHASE_INFO: Record<string, Phase> = {
    teaser: {
      name: '🤫 Teaser (Semana 1)',
      color: '#FF6B6B',
      description: 'Build mystery & anticipation'
    },
    reveal: {
      name: '🚀 Reveal (Semana 2)',
      color: '#4ECDC4',
      description: 'Full launch & details'
    },
    convert: {
      name: '💰 Convert (Semanas 3-4)',
      color: '#FFE66D',
      description: 'Urgency & social proof'
    }
  };

  useEffect(() => {
    generateCampaign();
  }, []);

  const generateCampaign = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/social-content-ops/workflows/product-launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: campaignId,
          product_name: productName,
          product_description: productDescription,
          weeks: 4
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCampaign(data);
      } else {
        setCampaign(generateMockCampaign());
      }
    } catch (error) {
      console.error('Error generating campaign:', error);
      setCampaign(generateMockCampaign());
    } finally {
      setLoading(false);
    }
  };

  const generateMockCampaign = () => ({
    product_name: productName,
    total_posts: 18,
    timeline: {
      teaser: [
        {
          fecha: '2026-05-26',
          canal: 'instagram',
          post: {
            titulo: '🤫 Algo viene...',
            contenido: `Estamos preparando algo especial. ¿Adivinan qué es? 👀`,
            fase: 'teaser',
            canal: 'instagram',
            emoji: '🤫',
            cta: 'Síguenos para enterarte primero',
            hashtags: ['#proximamente', '#novedad']
          }
        },
        {
          fecha: '2026-05-27',
          canal: 'tiktok',
          post: {
            titulo: '⏰ Cuenta regresiva',
            contenido: `En 7 días te mostramos cómo revolucionamos la auditoría fiscal.`,
            fase: 'teaser',
            canal: 'tiktok',
            emoji: '⏰',
            cta: 'Guarda este video',
            hashtags: ['#lanzamiento']
          }
        }
      ],
      reveal: [
        {
          fecha: '2026-06-02',
          canal: 'instagram',
          post: {
            titulo: `🚀 Presentamos: ${productName}`,
            contenido: `${productDescription}. Diseñado para revolucionar tu práctica.`,
            fase: 'reveal',
            canal: 'instagram',
            emoji: '🚀',
            cta: 'Link en bio',
            hashtags: ['#lanzamiento', '#novedades']
          }
        }
      ],
      convert: [
        {
          fecha: '2026-06-09',
          canal: 'instagram',
          post: {
            titulo: '⏱️ 30% OFF termina en 3 días',
            contenido: 'Si quieres ahorrar, es ahora o nunca.',
            fase: 'convert',
            canal: 'instagram',
            emoji: '⏱️',
            cta: 'No te arrepientas',
            hashtags: ['#oferta']
          }
        }
      ]
    },
    channels_used: {
      instagram: 9,
      tiktok: 2,
      email: 4,
      whatsapp: 2,
      linkedin: 1
    },
    metrics: {
      expected_reach: 5000,
      expected_engagement: 300,
      expected_conversions: 15,
      conversion_rate: '0.3-0.5%'
    }
  });

  if (!campaign) {
    return <div className="workflow-container">Cargando campaña...</div>;
  }

  const teaserPosts = campaign.timeline?.teaser || [];
  const revealPosts = campaign.timeline?.reveal || [];
  const convertPosts = campaign.timeline?.convert || [];
  const allPosts = [...teaserPosts, ...revealPosts, ...convertPosts];

  return (
    <div className="workflow-container">
      <div className="workflow-header">
        <h2>🚀 Product Launch: {campaign.product_name}</h2>
        <p className="subtitle">3-Fase: Teaser → Reveal → Convert (28 días)</p>
        <button onClick={generateCampaign} disabled={loading} className="btn-primary">
          {loading ? 'Generando...' : 'Generar nueva campaña'}
        </button>
      </div>

      <div className="phases-grid">
        {Object.entries(PHASE_INFO).map(([phaseKey, phase]) => (
          <div key={phaseKey} className="phase-card" style={{ borderLeftColor: PHASE_COLORS[phaseKey] }}>
            <h3>{phase.name}</h3>
            <p className="phase-description">{phase.description}</p>
            <div className="phase-posts-count">
              {phaseKey === 'teaser' && `${teaserPosts.length} posts`}
              {phaseKey === 'reveal' && `${revealPosts.length} posts`}
              {phaseKey === 'convert' && `${convertPosts.length} posts`}
            </div>
          </div>
        ))}
      </div>

      <div className="timeline-container">
        <h3>📅 Timeline de Publicación</h3>
        <div className="posts-grid">
          {allPosts.map((item: any, idx: number) => (
            <div
              key={idx}
              className="post-card"
              style={{ borderTopColor: PHASE_COLORS[item.post.fase] }}
              onClick={() => setSelectedPost(item.post)}
            >
              <div className="post-header">
                <span className="post-emoji">{item.post.emoji}</span>
                <span className="post-fase">{item.post.fase}</span>
              </div>
              <h4>{item.post.titulo}</h4>
              <p className="post-preview">{item.post.contenido.substring(0, 60)}...</p>
              <div className="post-meta">
                <span className="canal-badge">{item.post.canal}</span>
                <span className="fecha">{item.fecha}</span>
              </div>
            </div>
          ))}
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
              <div className="post-meta-detail">
                <span className="badge fase">{selectedPost.fase}</span>
                <span className="badge canal">{selectedPost.canal}</span>
              </div>
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

export default ProductLaunchWorkflow;
