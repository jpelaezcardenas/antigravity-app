import React, { useState, useEffect } from 'react';
import '../../../styles/workflows.css';

interface RetargetingMessage {
  titulo: string;
  contenido: string;
  segmento: string;
  canal: string;
  dia: number;
  urgency_level: string;
  emoji: string;
  cta: string;
  offer?: string;
}

const RetargetingWorkflow: React.FC<{
  productName?: string;
}> = ({ productName = 'Auditoría Sombra' }) => {
  const [campaign, setCampaign] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState('website_visitor');
  const [selectedMessage, setSelectedMessage] = useState<RetargetingMessage | null>(null);

  const SEGMENTS = [
    { id: 'website_visitor', name: 'Website Visitors', icon: '👁️', color: '#FF6B6B' },
    { id: 'email_subscriber', name: 'Email Subscribers', icon: '📧', color: '#4ECDC4' },
    { id: 'social_follower', name: 'Social Followers', icon: '👥', color: '#FFD700' },
    { id: 'previous_customer', name: 'Previous Customers', icon: '💎', color: '#2ECC71' },
    { id: 'trial_user', name: 'Trial Users', icon: '⭐', color: '#9B59B6' },
    { id: 'competitive_lost', name: 'Lost to Competitor', icon: '⚔️', color: '#FF4444' }
  ];

  const URGENCY_COLORS: Record<string, string> = {
    soft: '#FFD700',
    medium: '#FFA500',
    high: '#FF6B6B'
  };

  useEffect(() => {
    generateSequence();
  }, []);

  const generateSequence = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/social-content-ops/workflows/retargeting', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_id: 'retargeting-demo',
          target_segment: selectedSegment,
          product_name: productName,
          offer_level: 'standard'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCampaign(data);
      } else {
        setCampaign(generateMockSequence());
      }
    } catch (error) {
      console.error('Error generating sequence:', error);
      setCampaign(generateMockSequence());
    } finally {
      setLoading(false);
    }
  };

  const generateMockSequence = () => ({
    segment: selectedSegment,
    segment_name: SEGMENTS.find(s => s.id === selectedSegment)?.name || 'Unknown',
    product: productName,
    total_messages: 6,
    timeline: [
      {
        fecha: '2026-05-26',
        numero_mensaje: 1,
        canal: 'email',
        mensaje: {
          titulo: '🤔 Casi te ibas sin entender',
          contenido: 'Notamos que visitaste nuestro sitio pero no terminaste el formulario.',
          segmento: selectedSegment,
          canal: 'email',
          dia: 1,
          urgency_level: 'soft',
          emoji: '🤔',
          cta: 'Entiendo, cuéntame más'
        }
      }
    ],
    metrics: {
      expected_open_rate: '35-45%',
      expected_click_rate: '8-12%',
      expected_conversion_rate: '5-8%',
      estimated_recovered_customers: '10-15% conversion'
    }
  });

  const handleSegmentChange = (segmentId: string) => {
    setSelectedSegment(segmentId);
    setSelectedMessage(null);
  };

  useEffect(() => {
    if (selectedSegment && campaign?.segment !== selectedSegment) {
      generateSequence();
    }
  }, [selectedSegment]);

  if (!campaign) {
    return <div className="workflow-container">Cargando secuencia...</div>;
  }

  const segmentInfo = SEGMENTS.find(s => s.id === selectedSegment);
  const timeline = campaign.timeline || [];

  return (
    <div className="workflow-container">
      <div className="workflow-header">
        <h2>🎯 Retargeting Workflow</h2>
        <p className="subtitle">Personalized sequences for 6 user segments</p>
        <button onClick={generateSequence} disabled={loading} className="btn-primary">
          {loading ? 'Generando...' : 'Generar nueva secuencia'}
        </button>
      </div>

      <div className="segments-selector">
        <h3>👥 User Segments</h3>
        <div className="segments-grid">
          {SEGMENTS.map((segment) => (
            <button
              key={segment.id}
              className={`segment-btn ${selectedSegment === segment.id ? 'active' : ''}`}
              style={{
                backgroundColor: selectedSegment === segment.id ? segment.color : 'transparent',
                borderColor: segment.color
              }}
              onClick={() => handleSegmentChange(segment.id)}
            >
              <span className="segment-icon">{segment.icon}</span>
              <span className="segment-name">{segment.name}</span>
            </button>
          ))}
        </div>
      </div>

      {segmentInfo && (
        <div className="segment-detail-header" style={{ borderLeftColor: segmentInfo.color }}>
          <h3>{segmentInfo.icon} {campaign.segment_name}</h3>
          <div className="segment-strategy">
            <div className="strategy-item">
              <strong>Pain Point:</strong>
              <p>{campaign.segment_strategy?.pain_point || 'Understanding the value'}</p>
            </div>
            <div className="strategy-item">
              <strong>Approach:</strong>
              <p>{campaign.segment_strategy?.approach || 'Personalized messaging'}</p>
            </div>
          </div>
        </div>
      )}

      <div className="timeline-container">
        <h3>📅 6-Message Retargeting Sequence</h3>
        <div className="retargeting-timeline">
          {timeline.map((item: any, idx: number) => (
            <div key={idx} className="retargeting-message-item">
              <div className="timeline-day">
                <span className="day-number">Day {item.numero_mensaje}</span>
                <span className="day-date">{item.fecha}</span>
              </div>
              <div
                className="message-card"
                style={{
                  borderLeftColor: URGENCY_COLORS[item.mensaje.urgency_level],
                  backgroundColor: URGENCY_COLORS[item.mensaje.urgency_level] + '15'
                }}
                onClick={() => setSelectedMessage(item.mensaje)}
              >
                <div className="message-header">
                  <span className="emoji">{item.mensaje.emoji}</span>
                  <span className="urgency-badge" style={{ backgroundColor: URGENCY_COLORS[item.mensaje.urgency_level] }}>
                    {item.mensaje.urgency_level}
                  </span>
                </div>
                <h4>{item.mensaje.titulo}</h4>
                <p className="message-preview">{item.mensaje.contenido.substring(0, 70)}...</p>
                <div className="message-footer">
                  <span className="canal-badge">{item.canal}</span>
                  {item.mensaje.offer && (
                    <span className="offer-badge">🎁 {item.mensaje.offer}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="metrics-section">
        <h3>📊 Métricas Esperadas</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_open_rate}</div>
            <div className="metric-label">Open rate</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_click_rate}</div>
            <div className="metric-label">Click rate</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.expected_conversion_rate}</div>
            <div className="metric-label">Conversion rate</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{campaign.metrics.estimated_recovered_customers}</div>
            <div className="metric-label">Recovery potential</div>
          </div>
        </div>
      </div>

      {selectedMessage && (
        <div className="modal-overlay" onClick={() => setSelectedMessage(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedMessage(null)}>✕</button>
            <div className="message-detail">
              <h2>{selectedMessage.emoji} {selectedMessage.titulo}</h2>
              <div className="message-meta">
                <span className="badge canal">{selectedMessage.canal}</span>
                <span
                  className="badge urgency"
                  style={{ backgroundColor: URGENCY_COLORS[selectedMessage.urgency_level] }}
                >
                  {selectedMessage.urgency_level}
                </span>
                {selectedMessage.offer && (
                  <span className="badge offer">🎁 {selectedMessage.offer}</span>
                )}
              </div>
              <p className="message-content">{selectedMessage.contenido}</p>
              <div className="message-cta">
                <strong>CTA:</strong> {selectedMessage.cta}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RetargetingWorkflow;
