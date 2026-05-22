import React, { useState } from 'react';
import { api } from '../../services/api';

interface PostEditorProps {
  campaignId: string;
  selectedImage?: any;
}

const PostEditor: React.FC<PostEditorProps> = ({ campaignId, selectedImage }) => {
  const [content, setContent] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [topic, setTopic] = useState('');
  const [generating, setGenerating] = useState(false);

  const handleGenerateContent = async () => {
    if (!topic) return;
    setGenerating(true);
    try {
      const result = await api.generateSocialContent(topic, platform);
      if (result && result.respuesta_final) {
        setContent(result.respuesta_final);
      } else if (typeof result === 'string') {
        setContent(result);
      } else {
        setContent(JSON.stringify(result, null, 2));
      }
    } catch (error) {
      console.error("Error generating content:", error);
      alert("Hubo un error al conectar con la IA. Intenta de nuevo.");
    } finally {
      setGenerating(false);
    }
  };

  const handlePublish = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await api.createSocialPost({
        campaign_id: campaignId,
        titulo: content.substring(0, 50) + '...',
        contenido: content,
        plataforma: platform,
        fecha_programada: new Date().toISOString().split('T')[0],
        hora_programada: '10:00:00'
      });
      setSaved(true);
      setContent('');
      setTopic('');
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Error creating post:", error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-cyan-400 mb-4">🤖 Asistente Creativo I.A.</h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Escribe el tema o idea principal de tu post..."
            className="flex-1 bg-blue-900 border border-blue-700 text-white rounded px-4 py-2 text-sm focus:outline-none focus:border-cyan-500"
          />
          <button
            onClick={handleGenerateContent}
            disabled={generating || !topic}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-semibold rounded-lg transition disabled:opacity-50 whitespace-nowrap"
          >
            {generating ? '✨ Generando...' : '✨ Generar Copy'}
          </button>
        </div>
      </div>

      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-cyan-400 mb-4">📝 Contenido del Post</h3>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Escribe tu contenido aquí o géneralo con IA..."
          rows={8}
          className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2 text-sm"
        />
      </div>

      {selectedImage && (
        <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-cyan-400 mb-4">🖼️ Imagen Seleccionada</h3>
          <img
            src={selectedImage.image_url}
            alt={selectedImage.titulo}
            className="w-full max-w-sm rounded"
          />
        </div>
      )}

      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-cyan-400 mb-4">📱 Plataforma</h3>
        <select
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="w-full bg-blue-900 border border-blue-700 text-white rounded px-3 py-2"
        >
          <option value="instagram">Instagram</option>
          <option value="facebook">Facebook</option>
          <option value="tiktok">TikTok</option>
        </select>
      </div>

      <button 
        onClick={handlePublish}
        disabled={saving || !content}
        className={`w-full px-4 py-3 font-semibold rounded-lg transition ${saved ? 'bg-green-600 hover:bg-green-700 text-white' : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white disabled:opacity-50'}`}
      >
        {saving ? '⏳ Guardando...' : saved ? '✅ Post Programado' : '✨ Programar Post'}
      </button>
    </div>
  );
};

export default PostEditor;
