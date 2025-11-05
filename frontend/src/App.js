import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import Sidebar from './Sidebar';
import Message from './Messages';
import './App.css';

function App() {
  const [sidebarState, setSidebarState] = useState('hidden');
  const [isExpanded, setIsExpanded] = useState(false);

  // Chat state
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isScrolledUp, setIsScrolledUp] = useState(false);
  const [openThoughts, setOpenThoughts] = useState({});
  const [isFocused, setIsFocused] = useState(false);

  // Refs
  const messagesContainerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const measureCanvasRef = useRef(null);

  const handleSidebarStateChange = (state) => setSidebarState(state);

  const handleScroll = () => {
    const c = messagesContainerRef.current;
    if (!c) return;
    const { scrollTop, clientHeight, scrollHeight } = c;
    setIsScrolledUp(scrollTop + clientHeight < scrollHeight - 20);
  };

  const scrollToBottom = (behavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    if (!isScrolledUp) scrollToBottom('smooth');
  }, [messages, isScrolledUp]);

  useEffect(() => {
    if (inputRef.current) inputRef.current.style.height = '48px';
  }, []);

  useEffect(() => {
    const ta = inputRef.current;
    if (!ta) return;
    ta.style.height = '48px';
    const newHeight = Math.min(ta.scrollHeight, 320);
    ta.style.height = `${newHeight}px`;
  }, [input]);

  const measureTextWidth = (text, element) => {
    if (!measureCanvasRef.current)
      measureCanvasRef.current = document.createElement('canvas');
    const ctx = measureCanvasRef.current.getContext('2d');
    const style = window.getComputedStyle(element);
    const font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
    ctx.font = font;
    return ctx.measureText(text).width;
  };

  const evaluateExpanded = (ta) => {
    if (!ta) return false;
    if (ta.value.includes('\n')) return true;

    const lineHeight = parseFloat(window.getComputedStyle(ta).lineHeight);
    if (ta.scrollHeight > Math.ceil(lineHeight) + 2) return true;

    const firstLine = ta.value.split('\n')[0] || '';
    const paddingRight = 72;
    const availableWidth = ta.clientWidth - paddingRight - 20;
    const firstLineWidth = measureTextWidth(firstLine, ta);
    return firstLineWidth > availableWidth;
  };

  const handleInputChange = (e) => {
    const ta = e.target;
    setInput(ta.value);

    ta.style.height = '48px';
    const newHeight = Math.min(ta.scrollHeight, 320);
    ta.style.height = `${newHeight}px`;

    setIsExpanded(evaluateExpanded(ta));
  };

  const sendMessage = async () => {
    if (input.trim() === '' || isLoading) return;
    const userMessage = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsExpanded(false);

    try {
      const payload = {
        messages: [...messages, userMessage],
        max_tokens: 8192,
        temperature: 0.7,
      };
      const response = await axios.post('http://localhost:5000/api/chat', payload);
      const assistantMessage = {
        role: 'assistant',
        content: response?.data?.message?.content ?? 'No response',
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: failed to get response.' },
      ]);
    } finally {
      setIsLoading(false);
      if (inputRef.current) inputRef.current.style.height = '48px';
    }
  };

  const stopGeneration = () => {
    setIsLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={`App sidebar-${sidebarState}`}>
      <Sidebar onStateChange={handleSidebarStateChange} />

      <div className="chat-container" onClick={() => inputRef.current?.focus()}>
        <h1 className="chat-title">Ada Chat</h1>

        <div
          className="messages-container"
          ref={messagesContainerRef}
          onScroll={handleScroll}
        >
          {messages.length === 0 ? (
            <p className="empty-state">No messages yet. Start a conversation!</p>
          ) : (
            messages.map((msg, idx) => (
              <Message
                key={idx}
                msg={msg}
                messageIndex={idx}
                openThoughts={openThoughts}
                setOpenThoughts={setOpenThoughts}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {isScrolledUp && (
          <div
            className="new-message-indicator"
            onClick={() => scrollToBottom('smooth')}
          >
            <span>⬇</span>
          </div>
        )}

        {/* Improved Input area */}
        <div className="input-bar">
          <div className={`input-pill ${isExpanded ? 'expanded' : ''} ${isFocused ? 'focused' : ''}`}>
            <textarea
              ref={inputRef}
              className="input-textarea"
              placeholder="Message Ada"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              disabled={isLoading}
              aria-label="Message input"
            />
            
            {/* Attachment button */}
            <button
              className="attach-button"
              aria-label="Attach file"
              disabled={isLoading}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
              </svg>
            </button>

            {/* Send or Stop button */}
            {isLoading ? (
              <button
                className="stop-button"
                onClick={stopGeneration}
                aria-label="Stop generation"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="6" width="12" height="12" rx="1"/>
                </svg>
              </button>
            ) : (
              <button
                className={`send-button ${input.trim() !== '' ? 'active' : ''}`}
                onClick={sendMessage}
                disabled={input.trim() === ''}
                aria-label="Send message"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;