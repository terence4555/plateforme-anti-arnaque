import { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import './Chatbot.css';

const INITIAL_MESSAGES = [
  {
    role: 'bot',
    text: "Bonjour ! 👋 Je suis l'assistant Anti-Arnaque. Posez-moi vos questions sur le signalement d'arnaque, la création de compte, les preuves, etc.",
  },
];

const SUGGESTIONS = [
  'Comment signaler une arnaque ?',
  'Comment créer un compte ?',
  'Comment ajouter des preuves ?',
  'Vérifier un vendeur',
];

function Chatbot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;

    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setInput('');
    setLoading(true);

    try {
      const { data } = await api.post('/chat/', { message: msg });
      setMessages(prev => [...prev, { role: 'bot', text: data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: "Désolé, une erreur est survenue. Réessayez plus tard." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="chatbot">
      {open && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <div className="chatbot-header-left">
              <span className="chatbot-header-icon">🛡️</span>
              <span>Assistant Anti-Arnaque</span>
            </div>
            <button className="chatbot-close" onClick={() => setOpen(false)}>×</button>
          </div>

          <div className="chatbot-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg chat-${m.role}`}>
                {m.role === 'bot' && <span className="chat-avatar">🤖</span>}
                <div className="chat-bubble">{m.text}</div>
              </div>
            ))}
            {loading && (
              <div className="chat-msg chat-bot">
                <span className="chat-avatar">🤖</span>
                <div className="chat-bubble typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length <= 1 && (
            <div className="chatbot-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="suggestion-chip" onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          )}

          <div className="chatbot-input">
            <input
              type="text"
              placeholder="Posez votre question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button className="chatbot-send" onClick={() => send()} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </div>
      )}

      <button className="chatbot-toggle" onClick={() => setOpen(!open)}>
        {open ? '✕' : '💬'}
      </button>
    </div>
  );
}

export default Chatbot;
