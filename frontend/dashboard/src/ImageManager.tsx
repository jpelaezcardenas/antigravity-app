import React, { useState, useEffect } from 'react';

interface Image {
  id: string;
  titulo: string;
  image_url?: string;
  file_path?: string;
  categoria: string;
  color_palette: string[];
  generated_by: string;
  usos_totales: number;
}

interface ImageManagerProps {
  onSelectImage?: (image: Image) => void;
}

const ImageManager: React.FC<ImageManagerProps> = ({ onSelectImage }) => {
  const [images, setImages] = useState<Image[]>([]);
  const [filteredImages, setFilteredImages] = useState<Image[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [categoria, setCategoria] = useState<string>('');
  const [plataforma, setPlataforma] = useState<string>('');
  const [generatedBy, setGeneratedBy] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const API_BASE = 'http://localhost:8080/api/v1/social-content-ops/content';

  // Fetch images
  useEffect(() => {
    fetchImages();
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = images;

    if (categoria) {
      filtered = filtered.filter((img) => img.categoria === categoria);
    }
    if (generatedBy) {
      filtered = filtered.filter((img) => img.generated_by === generatedBy);
    }

    setFilteredImages(filtered);
  }, [images, categoria, generatedBy]);

  const fetchImages = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/images`);

      if (!response.ok) throw new Error('Failed to fetch images');

      const data = await response.json();
      setImages(data || []);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error al cargar imágenes';
      setError(message);
      // Fallback mock data
      setImages([
        {
          id: '1',
          titulo: 'Finanzas - Gráfico 1',
          image_url: 'https://via.placeholder.com/400x300?text=Finance+1',
          categoria: 'finanzas',
          color_palette: ['#1e40af', '#0ea5e9'],
          generated_by: 'canva',
          usos_totales: 5,
        },
        {
          id: '2',
          titulo: 'Marketing - Banner',
          image_url: 'https://via.placeholder.com/400x300?text=Marketing',
          categoria: 'marketing',
          color_palette: ['#16a34a', '#22c55e'],
          generated_by: 'photoshoot',
          usos_totales: 3,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('categoria', categoria || 'general');

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/images/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      await fetchImages();
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload error';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddFromURL = async () => {
    const url = prompt('Ingresa la URL de la imagen:');
    if (!url) return;

    const titulo = prompt('Título de la imagen:') || 'Sin título';

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/images/from-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_url: url,
          titulo,
          categoria: categoria || 'general',
        }),
      });

      if (!response.ok) throw new Error('Failed to add image');

      await fetchImages();
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!confirm('¿Eliminar esta imagen?')) return;

    try {
      const response = await fetch(`${API_BASE}/images/${imageId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Delete failed');

      setImages(images.filter((img) => img.id !== imageId));
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Delete error';
      setError(message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-red-500/10 border border-red-500 text-red-500 p-3 rounded text-sm">
          ⚠️ {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3 flex-wrap">
        <label className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded cursor-pointer transition">
          📤 Subir Imagen
          <input type="file" accept="image/*" onChange={handleFileUpload} hidden />
        </label>
        <button
          onClick={handleAddFromURL}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition"
        >
          🔗 Desde URL
        </button>
        <button
          onClick={() => window.open('https://www.canva.com', '_blank')}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded transition"
        >
          ✨ Photoshoot (Canva)
        </button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div>
          <label className="text-sm text-gray-400">Categoría</label>
          <select
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            className="w-full bg-blue-950 border border-blue-800 text-white rounded px-3 py-2 text-sm"
          >
            <option value="">Todas</option>
            <option value="finanzas">Finanzas</option>
            <option value="marketing">Marketing</option>
            <option value="comportamiento">Comportamiento</option>
            <option value="general">General</option>
          </select>
        </div>

        <div>
          <label className="text-sm text-gray-400">Generado por</label>
          <select
            value={generatedBy}
            onChange={(e) => setGeneratedBy(e.target.value)}
            className="w-full bg-blue-950 border border-blue-800 text-white rounded px-3 py-2 text-sm"
          >
            <option value="">Todos</option>
            <option value="manual">Manual</option>
            <option value="canva">Canva AI</option>
            <option value="photoshoot">Photoshoot</option>
            <option value="upload">Upload</option>
          </select>
        </div>
      </div>

      {/* Image Grid */}
      {loading ? (
        <div className="text-center py-8 text-gray-400">Cargando imágenes...</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {filteredImages.map((image) => (
            <div
              key={image.id}
              className="relative group bg-blue-950 rounded overflow-hidden cursor-pointer hover:ring-2 hover:ring-cyan-400 transition"
              onClick={() => onSelectImage?.(image)}
            >
              {/* Image */}
              <img
                src={image.image_url || 'https://via.placeholder.com/200x200?text=No+Image'}
                alt={image.titulo}
                className="w-full aspect-square object-cover group-hover:opacity-75 transition"
              />

              {/* Overlay */}
              <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition flex flex-col justify-between p-2">
                <div>
                  <p className="text-xs text-white font-semibold truncate">{image.titulo}</p>
                  <p className="text-xs text-gray-300">{image.categoria}</p>
                </div>

                {/* Quick Actions */}
                <div className="flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectImage?.(image);
                    }}
                    className="flex-1 bg-cyan-600 hover:bg-cyan-700 text-white text-xs py-1 rounded"
                  >
                    Usar
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteImage(image.id);
                    }}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white text-xs py-1 rounded"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Usage Count */}
              <div className="absolute top-1 right-1 bg-blue-600 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">
                {image.usos_totales}
              </div>
            </div>
          ))}
        </div>
      )}

      {filteredImages.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-400">
          <p>No hay imágenes que coincidan con los filtros</p>
          <p className="text-xs mt-2">Crea, sube o importa imágenes para comenzar</p>
        </div>
      )}
    </div>
  );
};

export default ImageManager;
