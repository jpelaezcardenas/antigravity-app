import React, { useState } from 'react';
import IdeasKanban from './IdeasKanban';
import CalendarioEditorial from './CalendarioEditorial';
import BorradoresReview from './BorradoresReview';
import MetricasDashboard from './MetricasDashboard';

type OpsTab = 'ideas' | 'calendario' | 'borradores' | 'metricas';

const SocialMediaOps: React.FC = () => {
  const [activeOpsTab, setActiveOpsTab] = useState<OpsTab>('ideas');

  const tabs: { id: OpsTab; label: string; icon: string }[] = [
    { id: 'ideas', label: 'Ideas', icon: '💡' },
    { id: 'calendario', label: 'Calendario', icon: '📅' },
    { id: 'borradores', label: 'Borradores', icon: '✏️' },
    { id: 'metricas', label: 'Métricas', icon: '📊' },
  ];

  return (
    <div className="space-y-6">
      {/* Module Header */}
      <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-cyan-900/40 via-blue-900/40 to-purple-900/40 border border-cyan-500/20 p-6 backdrop-blur-xl">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-cyan-500/10 via-transparent to-transparent" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-lg shadow-lg shadow-cyan-500/20">
              🚀
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Social Media OPs Systems</h2>
              <p className="text-sm text-cyan-300/70">Motor de contenido orgánico para Facebook — Contexia</p>
            </div>
          </div>
        </div>
      </div>

      {/* Sub-Navigation */}
      <div className="flex gap-1 bg-blue-950/50 border border-blue-800/50 rounded-xl p-1.5 backdrop-blur-xl">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveOpsTab(tab.id)}
            className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-300 flex items-center justify-center gap-2 ${
              activeOpsTab === tab.id
                ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                : 'text-gray-400 hover:text-gray-300 hover:bg-blue-900/30'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeOpsTab === 'ideas' && <IdeasKanban />}
        {activeOpsTab === 'calendario' && <CalendarioEditorial />}
        {activeOpsTab === 'borradores' && <BorradoresReview />}
        {activeOpsTab === 'metricas' && <MetricasDashboard />}
      </div>
    </div>
  );
};

export default SocialMediaOps;
