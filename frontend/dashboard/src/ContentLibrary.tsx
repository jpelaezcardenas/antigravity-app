import React, { useState, useEffect } from 'react';

interface ContentItem {
  id: string;
  titulo: string;
  tipo: string;
  plataforma: string;
  contenido: string;
  usos_totales: number;
}

const ContentLibrary: React.FC = () => {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    fetchContent();
  }, []);

  const fetchContent = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/social-content-ops/content-library');
      if (response.ok) {
        const data = await response.json();
        setContent(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Error loading content library:', err);
      setContent([
        {
          id: '1',
          titulo: 'Aversión a Pérdidas - Neuromarketing',
          tipo: 'post',
          plataforma: 'tiktok',
          contenido: 'Behavioral psychology content',
          usos_totales: 3
        },
        {
          id: '2',
          titulo: 'Efecto Dotación en Finanzas',
          tipo: 'template',
          plataforma: 'instagram',
          contenido: 'Financial psychology template',
          usos_totales: 5
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredContent =
    filterType === 'all'
      ? content
      : content.filter((item) => item.tipo === filterType);

  return (
    <div className="space-y-6">
      <div className="flex gap-2 border-b border-blue-800">
        <button
          onClick={() => setFilterType('all')}
          className={`px-4 py-2 text-sm transition ${
            filterType === 'all'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          📋 Todo
        </button>
        <button
          onClick={() => setFilterType('post')}
          className={`px-4 py-2 text-sm transition ${
            filterType === 'post'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          📝 Posts
        </button>
        <button
          onClick={() => setFilterType('template')}
          className={`px-4 py-2 text-sm transition ${
            filterType === 'template'
              ? 'text-cyan-400 border-b-2 border-cyan-400'
              : 'text-gray-400 hover:text-gray-300'
          }`}
        >
          🎨 Templates
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-400">Cargando contenido...</div>
      ) : filteredContent.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p>No hay contenido disponible</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredContent.map((item) => (
            <div key={item.id} className="bg-blue-950 border border-blue-800 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="text-cyan-400 font-semibold">{item.titulo}</h4>
                  <p className="text-sm text-gray-400">{item.plataforma.toUpperCase()}</p>
                </div>
                <span className="text-xs bg-cyan-600 text-white px-2 py-1 rounded">
                  {item.usos_totales} usos
                </span>
              </div>
              <p className="text-sm text-gray-300 mb-3">{item.contenido}</p>
              <button className="px-3 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm rounded transition">
                Usar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentLibrary;
