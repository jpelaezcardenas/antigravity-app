import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Send } from 'lucide-react';
import { MOCK_CHAT_INITIAL, TATY_RESPONSES, TATY_SUGGESTIONS, type ChatMessage } from '../../data/mockData';

// WhatsApp SVG icon inline
const WhatsAppIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

const getResponse = (msg: string): string => {
  const lower = msg.toLowerCase();
  if (lower.includes('impuesto') || lower.includes('apartar')) return TATY_RESPONSES['impuestos'];
  if (lower.includes('renta') || lower.includes('declarar')) return TATY_RESPONSES['renta'];
  if (lower.includes('deducci') || lower.includes('deducir')) return TATY_RESPONSES['deducciones'];
  if (lower.includes('iva') || lower.includes('bimestral')) return TATY_RESPONSES['iva'];
  return TATY_RESPONSES['default'];
};

export const TatyView = () => {
  const [messages, setMessages] = useState<ChatMessage[]>(MOCK_CHAT_INITIAL);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, typing]);

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    const userMsg: ChatMessage = { id: `msg_${Date.now()}`, role: 'user', content: text.trim(), timestamp: new Date().toISOString() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setTyping(true);

    setTimeout(() => {
      const resp: ChatMessage = { id: `msg_${Date.now() + 1}`, role: 'taty', content: getResponse(text), timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, resp]);
      setTyping(false);
    }, 1200 + Math.random() * 800);
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-200px)]">
      {/* Header - WhatsApp style */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-b-none p-4 flex items-center gap-4 border-b-0">
        <div className="relative">
          <div className="w-12 h-12 rounded-full bg-[#25D366] flex items-center justify-center">
            <WhatsAppIcon className="w-7 h-7 text-white" />
          </div>
          <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-navy-dark" />
        </div>
        <div>
          <h3 className="text-white font-bold text-lg">Taty 💚</h3>
          <p className="text-green-400 text-xs font-rajdhani uppercase tracking-widest">Tu amiga contadora • En línea</p>
        </div>
      </motion.div>

      {/* Chat Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto bg-navy-dark/50 backdrop-blur-sm border-x border-white/10 p-4 space-y-3 custom-scrollbar"
        style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.02\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")' }}>
        <AnimatePresence>
          {messages.map(msg => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 10, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#005C4B] text-white rounded-br-sm'
                  : 'bg-white/10 text-gray-200 rounded-bl-sm border border-white/5'
              }`}>
                {msg.role === 'taty' && <p className="text-[#25D366] font-bold text-xs mb-1">Taty 💚</p>}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className={`text-[10px] mt-1 text-right ${msg.role === 'user' ? 'text-white/40' : 'text-gray-500'}`}>
                  {new Date(msg.timestamp).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {typing && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
            <div className="bg-white/10 rounded-2xl rounded-bl-sm px-4 py-3 border border-white/5">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Suggestions */}
      <div className="border-x border-white/10 bg-navy-dark/30 px-4 py-2 flex gap-2 overflow-x-auto">
        {TATY_SUGGESTIONS.map((s, i) => (
          <button key={i} onClick={() => sendMessage(s)}
            className="flex-shrink-0 px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-xs text-gray-300 hover:bg-ctx-teal/10 hover:border-ctx-teal/20 hover:text-ctx-teal transition-all">
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="glass-card rounded-t-none p-4 border-t-0 flex items-center gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage(input)}
          placeholder="Escríbele a Taty..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-sm text-white focus:outline-none focus:border-[#25D366]/50 transition-colors"
        />
        <button onClick={() => sendMessage(input)} disabled={!input.trim()}
          className="p-3 bg-[#25D366] rounded-xl hover:bg-[#20BA5C] transition-colors disabled:opacity-30">
          <Send className="w-5 h-5 text-white" />
        </button>
      </div>
    </div>
  );
};
