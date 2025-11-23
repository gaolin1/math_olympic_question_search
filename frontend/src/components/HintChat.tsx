import { useState, useRef, useEffect } from 'react';
import { getHint } from '../api';
import type { ChatMessage } from '../types';
import { LatexRenderer } from './LatexRenderer';

interface HintChatProps {
  problemId: string;
}

export function HintChat({ problemId }: HintChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Add user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    try {
      const response = await getHint(problemId, messages, userMessage);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.response },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="hint-chat">
      <h4>Ask for a Hint</h4>
      <div className="chat-messages">
        {messages.length === 0 && (
          <p style={{ color: '#9ca3af', fontStyle: 'italic' }}>
            Ask questions to get hints without revealing the answer...
          </p>
        )}
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.role}`}>
            <LatexRenderer latex={msg.content} />
          </div>
        ))}
        {isLoading && (
          <div className="chat-message assistant">
            <span style={{ color: '#9ca3af' }}>Thinking...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} className="chat-input-container">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="How do I start solving this?"
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
