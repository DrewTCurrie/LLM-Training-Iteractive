// Sidebar.js
import React, { useState, useEffect, useRef } from 'react';
import './App.css'; // keeping single CSS file for simplicity

function Sidebar({ onStateChange }) {
  const [isPinned, setIsPinned] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const wrapperRef = useRef(null);

  // Inform parent App about current sidebar state
  useEffect(() => {
    if (isPinned) onStateChange?.('pinned');
    else if (isVisible) onStateChange?.('visible');
    else onStateChange?.('hidden');
  }, [isPinned, isVisible, onStateChange]);

  // Toggle cycle when clicking hamburger:
  // hidden -> visible -> pinned -> hidden
  const handleHamburgerClick = () => {
    if (!isVisible && !isPinned) {
      setIsVisible(true);
      return;
    }
    if (isVisible && !isPinned) {
      setIsPinned(true);
      setIsVisible(true);
      return;
    }
    // pinned -> hide
    setIsPinned(false);
    setIsVisible(false);
  };

  // Hover behavior: show when hovering wrapper (hamburger or sidebar),
  // but don't hide while pinned.
  const handleMouseEnter = () => {
    if (!isPinned) setIsVisible(true);
  };
  const handleMouseLeave = () => {
    if (!isPinned) setIsVisible(false);
  };

  return (
    <div
      ref={wrapperRef}
      className="sidebar-root"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* top bar area: title + fixed hamburger */}
      <header className="top-bar">
        <div className="title">
          <span className="app-name">Ada Chat</span>
          <button
            className="hamburger"
            onClick={handleHamburgerClick}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Sidebar panel (hidden by default) */}
      <aside
        className={`sidebar ${isVisible || isPinned ? 'visible' : ''} ${
          isPinned ? 'pinned' : ''
        }`}
        aria-hidden={!(isVisible || isPinned)}
      >
        <div className="sidebar-inner">
          <div className="sidebar-header">
            <div className="sidebar-logo">Message Ada</div>
          </div>
          <button className="new-conversation-btn">New Conversation</button>

          <div className="conversations-list">
            <div className="conversation-item">
              <span className="conversation-title">Example Chat</span>
              <button className="delete-btn" aria-label="Delete">🗑️</button>
            </div>

            <div className="conversation-item">
              <span className="conversation-title">Project Notes</span>
              <button className="delete-btn" aria-label="Delete">🗑️</button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default Sidebar;
