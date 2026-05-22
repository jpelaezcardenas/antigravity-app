import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import ImageManager from './ImageManager';
import BusinessDNA from './BusinessDNA';
import CampaignSuggestions from './CampaignSuggestions';
import PostEditor from './PostEditor';
import ContentLibrary from './ContentLibrary';
import PostCalendar from './PostCalendar';
import CampaignWizard from './CampaignWizard';
import InstagramCalendarWorkflow from './workflows/InstagramCalendarWorkflow';
import ProductLaunchWorkflow from './workflows/ProductLaunchWorkflow';
import StorytellingSeriesWorkflow from './workflows/StorytellingSeriesWorkflow';
import LocalCampaignWorkflow from './workflows/LocalCampaignWorkflow';
import RetargetingWorkflow from './workflows/RetargetingWorkflow';
import SocialMediaOps from './ops/SocialMediaOps';

type TabType = 'dashboard' | 'campaigns' | 'contenido' | 'calendario' | 'editor' | 'config' | 'social-ops';
type WorkflowType = 'instagram' | 'product-launch' | 'storytelling' | 'local' | 'retargeting';

interface CampaignState {
  id: string;
  nombre: string;
}

const SocialOpsView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [activeWorkflow, setActiveWorkflow] = useState<WorkflowType>('instagram');
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignState>({
    id: 'camp-001',
    nombre: 'Campaña Principal',
  });
  const [selectedImage, setSelectedImage] = useState<any>(null);
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  useEffect(() => {
    if (activeTab === 'dashboard' && !metrics) {
      setLoadingMetrics(true);
      api.getSocialDashboardMetrics()
        .then(data => setMetrics(data))
        .catch(err => console.error("Error fetching metrics", err))
        .finally(() => setLoadingMetrics(false));
    }
  }, [activeTab, metrics]);

  return (
    <div className="flex-1 flex flex-col w-full h-full text-white pt-2">
      {/* Navigation Tabs */}
      <nav className="border-b border-white/5 mb-6 sticky top-0 z-40 bg-navy-dark/95 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-2 overflow-x-auto hide-scrollbar">
            {[
              { id: 'dashboard', label: '📊 Dashboard' },
              { id: 'campaigns', label: '🎯 Campaña' },
              { id: 'contenido', label: '📸 Contenido' },
              { id: 'calendario', label: '📅 Calendario' },
              { id: 'editor', label: '✍️ Editor' },
              { id: 'social-ops', label: '🚀 Operaciones' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`px-4 py-3 text-sm font-rajdhani font-bold uppercase tracking-widest transition-all border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-ctx-teal text-ctx-teal'
                    : 'border-transparent text-gray-400 hover:text-white hover:border-white/20'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content Area */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* DASHBOARD TAB */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Presupuesto Total</p>
                <p className="text-2xl font-bold text-ctx-teal">
                  {loadingMetrics ? '...' : `$${metrics?.presupuesto_total?.toLocaleString() || '0'}`}
                </p>
              </div>
              <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Gastado</p>
                <p className="text-2xl font-bold text-yellow-400">
                  {loadingMetrics ? '...' : `$${metrics?.presupuesto_usado?.toLocaleString() || '0'}`}
                </p>
              </div>
              <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Posts Publicados</p>
                <p className="text-2xl font-bold text-green-400">
                  {loadingMetrics ? '...' : metrics?.posts_publicados || '0'}
                </p>
              </div>
              <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Engagement Promedio</p>
                <p className="text-2xl font-bold text-purple-400">
                  {loadingMetrics ? '...' : `${metrics?.engagement_promedio || '0'}%`}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* CAMPAIGNS TAB */}
        {activeTab === 'campaigns' && (
          <div className="space-y-6">
            {!isCreatingCampaign ? (
              <>
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-ctx-teal">🎯 Gestión de Campañas</h2>
                  <button
                    onClick={() => setIsCreatingCampaign(true)}
                    className="px-6 py-2 bg-ctx-teal hover:bg-ctx-teal/80 text-white font-semibold rounded-lg transition"
                  >
                    ✨ Nueva Campaña
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Business DNA */}
                  <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-ctx-teal mb-4">🧬 Business DNA</h2>
                    <BusinessDNA campaignId={selectedCampaign.id} />
                  </div>

                  {/* Campaign Suggestions */}
                  <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-ctx-teal mb-4">💡 Sugerencias</h2>
                    <CampaignSuggestions
                      campaignId={selectedCampaign.id}
                      onSelectSuggestion={(sug) => {
                        setActiveTab('editor');
                        // Would pass suggestion data to editor
                      }}
                    />
                  </div>
                </div>
              </>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setIsCreatingCampaign(false)}
                    className="text-ctx-teal hover:text-cyan-300 font-semibold"
                  >
                    ← Volver
                  </button>
                  <h2 className="text-xl font-semibold text-ctx-teal">Crear Nueva Campaña</h2>
                </div>
                <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-8">
                  <CampaignWizard />
                </div>
              </div>
            )}
          </div>
        )}

        {/* CONTENIDO TAB */}
        {activeTab === 'contenido' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-ctx-teal">📸 Biblioteca de Contenido</h2>

            <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-ctx-teal mb-4">📤 Image Manager</h3>
              <ImageManager onSelectImage={setSelectedImage} />
            </div>

            {selectedImage && (
              <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-ctx-teal mb-4">✅ Imagen Seleccionada</h3>
                <div className="flex gap-4">
                  <img
                    src={selectedImage.image_url}
                    alt={selectedImage.titulo}
                    className="w-32 h-32 object-cover rounded"
                  />
                  <div>
                    <p className="font-semibold">{selectedImage.titulo}</p>
                    <p className="text-sm text-gray-400">Categoría: {selectedImage.categoria}</p>
                    <p className="text-sm text-gray-400">Usado: {selectedImage.usos_totales} veces</p>
                    <button
                      onClick={() => setActiveTab('editor')}
                      className="mt-3 px-4 py-2 bg-ctx-teal hover:bg-ctx-teal/80 text-white text-sm rounded"
                    >
                      Usar en Post
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-ctx-teal mb-4">📚 Content Library</h3>
              <ContentLibrary />
            </div>
          </div>
        )}

        {/* CALENDARIO TAB */}
        {activeTab === 'calendario' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-ctx-teal mb-4">📅 Workflows & Calendario</h2>

            {/* Workflow Type Selector */}
            <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex gap-2 overflow-x-auto pb-2">
                {[
                  { id: 'instagram', label: '📅 Instagram Calendar', icon: '📅' },
                  { id: 'product-launch', label: '🚀 Product Launch', icon: '🚀' },
                  { id: 'storytelling', label: '📖 Storytelling Series', icon: '📖' },
                  { id: 'local', label: '📍 Local Campaign', icon: '📍' },
                  { id: 'retargeting', label: '🎯 Retargeting', icon: '🎯' },
                ].map((workflow) => (
                  <button
                    key={workflow.id}
                    onClick={() => setActiveWorkflow(workflow.id as WorkflowType)}
                    className={`px-4 py-2 text-sm font-medium rounded transition whitespace-nowrap ${
                      activeWorkflow === workflow.id
                        ? 'bg-ctx-teal text-white'
                        : 'bg-blue-900 text-gray-300 hover:bg-blue-800'
                    }`}
                  >
                    {workflow.icon} {workflow.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Workflow Content */}
            <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
              {activeWorkflow === 'instagram' && (
                <InstagramCalendarWorkflow
                  campaignId={selectedCampaign.id}
                  campaignObjective="Generar leads para declaración 2026"
                  businessDna={{
                    visual_identity: {
                      color_primary: '#2D5A7B',
                      color_secondary: '#E8A87C'
                    }
                  }}
                />
              )}
              {activeWorkflow === 'product-launch' && (
                <ProductLaunchWorkflow
                  campaignId={selectedCampaign.id}
                  productName="Auditoría Sombra"
                  productDescription="Auditoría fiscal integral con IA"
                  businessDna={{}}
                />
              )}
              {activeWorkflow === 'storytelling' && (
                <StorytellingSeriesWorkflow
                  campaignId={selectedCampaign.id}
                  storyTheme="Contador que transformó su negocio"
                  targetSegment="Contadores"
                />
              )}
              {activeWorkflow === 'local' && (
                <LocalCampaignWorkflow
                  targetCities={['Bogotá', 'Medellín']}
                  partners={['Cámara de Comercio', 'Asociación de Contadores']}
                />
              )}
              {activeWorkflow === 'retargeting' && (
                <RetargetingWorkflow productName="Auditoría Sombra" />
              )}
            </div>

            {/* Classic Calendar View */}
            <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-ctx-teal mb-4">📊 Vista Clásica</h3>
              <PostCalendar campaignId={selectedCampaign.id} />
            </div>
          </div>
        )}

        {/* EDITOR TAB */}
        {activeTab === 'editor' && (
          <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-ctx-teal mb-4">✍️ Editor de Posts</h2>
            <PostEditor
              campaignId={selectedCampaign.id}
              selectedImage={selectedImage}
            />
          </div>
        )}

        {/* CONFIG TAB */}
        {activeTab === 'config' && (
          <div className="glass-card bg-white/5 border border-white/10 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-ctx-teal mb-4">⚙️ Configuración</h2>
            <div className="space-y-4">
              <div className="p-4 bg-blue-900 rounded border border-white/10">
                <p className="text-sm">🔌 Integraciones</p>
                <button className="mt-2 px-4 py-2 bg-ctx-teal hover:bg-ctx-teal/80 text-white text-sm rounded">
                  Conectar Meta (Facebook/Instagram)
                </button>
              </div>
              <div className="p-4 bg-blue-900 rounded border border-white/10">
                <p className="text-sm">🔑 API Keys</p>
                <p className="text-xs text-gray-400 mt-2">Estado: Connected ✅</p>
              </div>
            </div>
          </div>
        )}

        {/* SOCIAL MEDIA OPS TAB */}
        {activeTab === 'social-ops' && (
          <SocialMediaOps />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 glass-card bg-white/5/30 backdrop-blur mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-400">
          <p>Contexia Social Content Ops • FASE 1A Complete ✅</p>
        </div>
      </footer>
    </div>
  );
};

export default SocialOpsView;
