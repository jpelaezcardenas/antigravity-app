import React from 'react';

interface PostEditorProps {
  campaignId: string;
  selectedImage?: any;
}

const PostEditor: React.FC<PostEditorProps> = ({ campaignId, selectedImage }) => {
  const [content, setContent] = React.useState('');
  const [platform, setPlatform] = React.useState('instagram');

  return (
    <div className="space-y-6">
      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-cyan-400 mb-4">📝 Contenido del Post</h3>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Escribe tu contenido aquí..."
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

      <button className="w-full px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-semibold rounded-lg transition">
        ✨ Publicar Post
      </button>
    </div>
  );
};

export default PostEditor;
