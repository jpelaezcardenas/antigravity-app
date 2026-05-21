import React, { useState } from 'react';
import ImageManager from './ImageManager';
import BusinessDNA from './BusinessDNA';
import CampaignSuggestions from './CampaignSuggestions';
import PostEditor from './PostEditor';
import ContentLibrary from './ContentLibrary';
import PostCalendar from './PostCalendar';
import CampaignWizard from './components/CampaignWizard';
import InstagramCalendarWorkflow from './components/workflows/InstagramCalendarWorkflow';
import ProductLaunchWorkflow from './components/workflows/ProductLaunchWorkflow';
import StorytellingSeriesWorkflow from './components/workflows/StorytellingSeriesWorkflow';
import LocalCampaignWorkflow from './components/workflows/LocalCampaignWorkflow';
import RetargetingWorkflow from './components/workflows/RetargetingWorkflow';
import SocialMediaOps from './components/ops/SocialMediaOps';

type TabType = 'dashboard' | 'campaigns' | 'contenido' | 'calendario' | 'editor' | 'config' | 'social-ops';
type WorkflowType = 'instagram' | 'product-launch' | 'storytelling' | 'local' | 'retargeting';

interface CampaignState {
  id: string;
  nombre: string;
}

const BunkerApp: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [activeWorkflow, setActiveWorkflow] = useState<WorkflowType>('instagram');
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignState>({
    id: 'camp-001',
    nombre: 'Campaña Principal',
  });
  const [selectedImage, setSelectedImage] = useState<any>(null);
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-950 via-blue-900 to-black text-white">
      {/* Header */}
      <header className="border-b border-blue-800 bg-blue-950/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-cyan-400">🎯 Social Content Ops</h1>
              <p className="text-sm text-gray-400">Gestiona tu estrategia de contenido en redes sociales</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-semibold">{selectedCampaign.nombre}</p>
              <select
                value={selectedCampaign.id}
                onChange={(e) =>
                  setSelectedCampaign({ ...selectedCampaign, id: e.target.value })
                }
                className="mt-1 bg-blue-900 border border-blue-700 text-white rounded px-3 py-1 text-sm"
              >
                <option value="camp-001">Campaña Principal</option>
                <option value="camp-002">Lanzamiento Producto</option>
                <option value="camp-003">Local Campaign</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="border-b border-blue-800 bg-blue-950/30 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1 overflow-x-auto">
            {[
              { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
              { id: 'campaigns', label: '🎯 Campaña', icon: '🎯' },
              { id: 'contenido', label: '📸 Contenido', icon: '📸' },
              { id: 'calendario', label: '📅 Calendario', icon: '📅' },
              { id: 'editor', label: '✍️ Editor', icon: '✍️' },
              { id: 'social-ops', label: '🚀 Social Media OPs', icon: '🚀' },
              { id: 'config', label: '⚙️ Config', icon: '⚙️' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`px-4 py-3 text-sm font-medium transition border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-cyan-400 text-cyan-400 bg-blue-800/30'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
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
              <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Presupuesto Total</p>
                <p className="text-2xl font-bold text-cyan-400">$10,000</p>
              </div>
              <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Gastado</p>
                <p className="text-2xl font-bold text-yellow-400">$8,500</p>
              </div>
              <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Posts Publicados</p>
                <p className="text-2xl font-bold text-green-400">26</p>
              </div>
              <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                <p className="text-gray-400 text-sm">Engagement Promedio</p>
                <p className="text-2xl font-bold text-purple-400">8.4%</p>
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
                  <h2 className="text-xl font-semibold text-cyan-400">🎯 Gestión de Campañas</h2>
                  <button
                    onClick={() => setIsCreatingCampaign(true)}
                    className="px-6 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg transition"
                  >
                    ✨ Nueva Campaña
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Business DNA */}
                  <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-cyan-400 mb-4">🧬 Business DNA</h2>
                    <BusinessDNA campaignId={selectedCampaign.id} />
                  </div>

                  {/* Campaign Suggestions */}
                  <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-cyan-400 mb-4">💡 Sugerencias</h2>
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
                    className="text-cyan-400 hover:text-cyan-300 font-semibold"
                  >
                    ← Volver
                  </button>
                  <h2 className="text-xl font-semibold text-cyan-400">Crear Nueva Campaña</h2>
                </div>
                <div className="bg-blue-950 border border-blue-800 rounded-lg p-8">
                  <CampaignWizard />
                </div>
              </div>
            )}
          </div>
        )}

        {/* CONTENIDO TAB */}
        {activeTab === 'contenido' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-cyan-400">📸 Biblioteca de Contenido</h2>

            <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-cyan-400 mb-4">📤 Image Manager</h3>
              <ImageManager onSelectImage={setSelectedImage} />
            </div>

            {selectedImage && (
              <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-cyan-400 mb-4">✅ Imagen Seleccionada</h3>
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
                      className="mt-3 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded"
                    >
                      Usar en Post
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-cyan-400 mb-4">📚 Content Library</h3>
              <ContentLibrary />
            </div>
          </div>
        )}

        {/* CALENDARIO TAB */}
        {activeTab === 'calendario' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">📅 Workflows & Calendario</h2>

            {/* Workflow Type Selector */}
            <div className="bg-blue-950 border border-blue-800 rounded-lg p-4">
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
                        ? 'bg-cyan-600 text-white'
                        : 'bg-blue-900 text-gray-300 hover:bg-blue-800'
                    }`}
                  >
                    {workflow.icon} {workflow.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Workflow Content */}
            <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
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
            <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-cyan-400 mb-4">📊 Vista Clásica</h3>
              <PostCalendar campaignId={selectedCampaign.id} />
            </div>
          </div>
        )}

        {/* EDITOR TAB */}
        {activeTab === 'editor' && (
          <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">✍️ Editor de Posts</h2>
            <PostEditor
              campaignId={selectedCampaign.id}
              selectedImage={selectedImage}
            />
          </div>
        )}

        {/* CONFIG TAB */}
        {activeTab === 'config' && (
          <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-cyan-400 mb-4">⚙️ Configuración</h2>
            <div className="space-y-4">
              <div className="p-4 bg-blue-900 rounded border border-blue-800">
                <p className="text-sm">🔌 Integraciones</p>
                <button className="mt-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded">
                  Conectar Meta (Facebook/Instagram)
                </button>
              </div>
              <div className="p-4 bg-blue-900 rounded border border-blue-800">
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
      <footer className="border-t border-blue-800 bg-blue-950/30 backdrop-blur mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-400">
          <p>Contexia Social Content Ops • FASE 1A Complete ✅</p>
        </div>
      </footer>
    </div>
  );
};

export default BunkerApp;
