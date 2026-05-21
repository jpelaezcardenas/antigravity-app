import React, { useState, useEffect } from 'react';
import '../../styles/workflows.css';

interface CityPost {
  fecha: string;
  canal: string;
  ciudad: string;
  post: any;
}

interface CityData {
  ciudad: string;
  total_posts: number;
  timeline: CityPost[];
  canales: Record<string, number>;
  eventos: string[];
  partners: string[];
}

const LocalCampaignWorkflow: React.FC<{
  targetCities?: string[];
  partners?: string[];
}> = ({
  targetCities = ['Bogotá', 'Medellín'],
  partners = ['Cámara de Comercio', 'Asociación de Contadores']
}) => {
  const [campaign, setCampaign] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedCity, setSelectedCity] = useState(targetCities[0]);
  const [selectedPost, setSelectedPost] = useState<any>(null);

  const CITY_COLORS: Record<string, string> = {
    'Bogotá': '#FF6B6B',
    'Medellín': '#4ECDC4',
    'Cali': '#FFD700',
    'Barranquilla': '#95E1D3',
    'Bucaramanga': '#FF8C94'
  };

  const PHASE_COLORS: Record<string, string> = {
    awareness: '#FF6B6B',
    engagement: '#4ECDC4',
    conversion: '#2ECC71'
  };

  useEffect(() => {
    generateCampaign();
  }, []);

  const generateCampaign = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/social-content-ops/workflows/local-campaign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: 'local-campaign-demo',
          target_cities: targetCities,
          partner_networks: partners
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
    target_cities: targetCities,
    total_posts: 21,
    campaigns_per_city: {
      'Bogotá': {
        ciudad: 'Bogotá',
        total_posts: 7,
        timeline: [
          {
            fecha: '2026-05-26',
            canal: 'instagram',
            ciudad: 'Bogotá',
            post: {
              titulo: '📍 Llegamos a Bogotá',
              contenido: 'Después del éxito en otras ciudades, hoy nos complace estar en Bogotá.',
              fase: 'awareness',
              canal: 'instagram',
              emoji: '📍',
              cta: 'Entérate cómo',
              hashtags: ['#bogotá', '#fiscal']
            }
          }
        ],
        canales: { instagram: 3, whatsapp: 2, linkedin: 1, facebook: 1 },
        eventos: ['Webinar Riesgos Fiscales 2026 - Bogotá', 'Workshop Contadores Bogotá'],
        partners: partners
      },
      'Medellín': {
        ciudad: 'Medellín',
        total_posts: 7,
        timeline: [
          {
            fecha: '2026-05-26',
            canal: 'instagram',
            ciudad: 'Medellín',
            post: {
              titulo: '📍 Llegamos a Medellín',
              contenido: 'Estamos listos para transformar la auditoría fiscal en Medellín.',
              fase: 'awareness',
              canal: 'instagram',
              emoji: '📍',
              cta: 'Entérate cómo',
              hashtags: ['#medellín', '#fiscal']
            }
          }
        ],
        canales: { instagram: 3, whatsapp: 2, linkedin: 1, facebook: 1 },
        eventos: ['Webinar Riesgos Fiscales 2026 - Medellín'],
        partners: partners
      }
    },
    metrics: {
      expected_local_reach: 15000,
      expected_engagement: 1200,
      expected_event_attendees: 200,
      expected_partnership_generated_leads: 50
    }
  });

  if (!campaign) {
    return <div className="workflow-container">Cargando campaña local...</div>;
  }

  const currentCity = selectedCity;
  const cityData = campaign.campaigns_per_city?.[currentCity];
  const cityPosts = cityData?.timeline || [];

  return (
    <div className="workflow-container">
      <div className="workflow-header">
        <h2>📍 Local Campaign</h2>
        <p className="subtitle">Geo-targeted: Events + Partnerships</p>
        <button onClick={generateCampaign} disabled={loading} className="btn-primary">
          {loading ? 'Generando...' : 'Generar nueva campaña'}
        </button>
      </div>

      <div className="cities-selector">
        <h3>🏙️ Ciudades</h3>
        <div className="city-buttons">
          {targetCities.map((city) => (
            <button
              key={city}
              className={`city-btn ${selectedCity === city ? 'active' : ''}`}
              style={{
                backgroundColor: selectedCity === city ? CITY_COLORS[city] : 'transparent',
                borderColor: CITY_COLORS[city]
              }}
              onClick={() => setSelectedCity(city)}
            >
              {city}
            </button>
          ))}
        </div>
      </div>

      {cityData && (
        <>
          <div className="city-info">
            <h3>📊 {currentCity}</h3>
            <div className="city-stats">
              <div className="stat-card">
                <strong>{cityData.total_posts}</strong>
                <span>Posts</span>
              </div>
              <div className="stat-card">
                <strong>{Object.values(cityData.canales).reduce((a: number, b: number) => a + b, 0)}</strong>
                <span>Total actividades</span>
              </div>
              <div className="stat-card">
                <strong>{cityData.eventos.length}</strong>
                <span>Eventos</span>
              </div>
              <div className="stat-card">
                <strong>{cityData.partners.length}</strong>
                <span>Alianzas</span>
              </div>
            </div>
          </div>

          <div className="city-events">
            <h3>📅 Eventos en {currentCity}</h3>
            <div className="events-list">
              {cityData.eventos.map((evento: string, idx: number) => (
                <div key={idx} className="event-item">
                  <span className="event-icon">📅</span>
                  <span className="event-name">{evento}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="timeline-container">
            <h3>📝 Posts en {currentCity}</h3>
            <div className="local-posts-grid">
              {cityPosts.map((item: CityPost, idx: number) => (
                <div
                  key={idx}
                  className="post-card"
                  style={{ borderTopColor: PHASE_COLORS[item.post.fase] }}
                  onClick={() => setSelectedPost(item.post)}
                >
                  <div className="post-header">
                    <span className="post-emoji">{item.post.emoji}</span>
                    <span className="post-fecha">{item.fecha}</span>
                  </div>
                  <h4>{item.post.titulo}</h4>
                  <p className="post-preview">{item.post.contenido.substring(0, 60)}...</p>
                  <div className="post-meta">
                    <span className="canal-badge">{item.canal}</span>
                    <span className="fase-badge">{item.post.fase}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <div className="metrics-section">
        <h3>📊 Métricas Generales</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_local_reach.toLocaleString()}</div>
            <div className="metric-label">Reach local esperado</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_engagement}</div>
            <div className="metric-label">Engagement estimado</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_event_attendees}</div>
            <div className="metric-label">Asistentes a eventos</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_partnership_generated_leads}</div>
            <div className="metric-label">Leads por alianzas</div>
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
                {selectedPost.evento && <span className="badge evento">{selectedPost.evento}</span>}
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

export default LocalCampaignWorkflow;
