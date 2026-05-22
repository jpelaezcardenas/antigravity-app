import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';

interface PostCalendarProps {
  campaignId: string;
}

const PostCalendar: React.FC<PostCalendarProps> = ({ campaignId }) => {
  const [currentDate] = useState(new Date());
  const [scheduledPosts, setScheduledPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchCalendar = async () => {
      setLoading(true);
      try {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        const data = await api.getSocialCalendar(year, month);
        setScheduledPosts(data.posts || []);
      } catch (error) {
        console.error("Error fetching calendar", error);
      } finally {
        setLoading(false);
      }
    };
    fetchCalendar();
  }, [currentDate]);

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const daysInMonth = getDaysInMonth(currentDate);
  const firstDay = getFirstDayOfMonth(currentDate);
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const emptyDays = Array.from({ length: firstDay }, (_, i) => i);

  const monthName = currentDate.toLocaleString('es-ES', { month: 'long', year: 'numeric' });

  // Extract scheduled days from API data
  const scheduledDaysList = scheduledPosts.map(sp => parseInt(sp.fecha.split('-')[2], 10));

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-cyan-400 mb-4 capitalize">{monthName}</h3>
      </div>

      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <div className="grid grid-cols-7 gap-2">
          {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map((day) => (
            <div key={day} className="text-center text-sm font-semibold text-cyan-400 py-2">
              {day}
            </div>
          ))}

          {emptyDays.map((_, i) => (
            <div key={`empty-${i}`} className="aspect-square"></div>
          ))}

          {days.map((day) => (
            <div
              key={day}
              className={`aspect-square flex items-center justify-center rounded text-sm font-medium transition ${
                scheduledDaysList.includes(day)
                  ? 'bg-cyan-600 text-white'
                  : 'bg-blue-900 text-gray-300 hover:bg-blue-800'
              }`}
            >
              {day}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-blue-950 border border-blue-800 rounded-lg p-6">
        <h4 className="text-cyan-400 font-semibold mb-3">📅 Posts Programados {loading && '...'}</h4>
        <div className="space-y-2 text-sm">
          {scheduledPosts.length === 0 && !loading && (
            <p className="text-gray-400">No hay posts programados este mes.</p>
          )}
          {scheduledPosts.map(group => (
            group.posts.map((post: any) => (
              <div key={post.id} className="flex justify-between items-center p-2 bg-blue-900 rounded">
                <span>{group.fecha} - {post.plataforma}</span>
                <span className="text-cyan-400">{post.titulo}</span>
              </div>
            ))
          ))}
        </div>
      </div>

      <button className="w-full px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-semibold rounded-lg transition">
        ➕ Programar Nuevo Post
      </button>
    </div>
  );
};

export default PostCalendar;
