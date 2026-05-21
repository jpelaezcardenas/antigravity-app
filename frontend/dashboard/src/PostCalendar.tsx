import React, { useState } from 'react';

interface PostCalendarProps {
  campaignId: string;
}

const PostCalendar: React.FC<PostCalendarProps> = ({ campaignId }) => {
  const [currentDate] = useState(new Date());

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

  const mockScheduledDays = [5, 12, 19, 26];

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
                mockScheduledDays.includes(day)
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
        <h4 className="text-cyan-400 font-semibold mb-3">📅 Posts Programados</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center p-2 bg-blue-900 rounded">
            <span>Mayo 5 - Instagram</span>
            <span className="text-cyan-400">Aversión a Pérdidas</span>
          </div>
          <div className="flex justify-between items-center p-2 bg-blue-900 rounded">
            <span>Mayo 12 - Facebook</span>
            <span className="text-cyan-400">Dropshipper Case Study</span>
          </div>
          <div className="flex justify-between items-center p-2 bg-blue-900 rounded">
            <span>Mayo 19 - TikTok</span>
            <span className="text-cyan-400">Efecto Dotación</span>
          </div>
          <div className="flex justify-between items-center p-2 bg-blue-900 rounded">
            <span>Mayo 26 - Instagram</span>
            <span className="text-cyan-400">Claridad Predictiva</span>
          </div>
        </div>
      </div>

      <button className="w-full px-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white font-semibold rounded-lg transition">
        ➕ Programar Nuevo Post
      </button>
    </div>
  );
};

export default PostCalendar;
