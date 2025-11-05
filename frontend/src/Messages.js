import React, {useState} from 'react';
import ReactMarkdown from 'react-markdown';

function Message({ msg, messageIndex, openThoughts, setOpenThoughts }) {
  const isUser = msg.role === 'user';

  //Check for thinking section
  let parts = [];
  if (!isUser) {
    const regex = /<think>([\s\S]*?)<\/think>/g;
    let lastIndex = 0;
    let match;
    while((match = regex.exec(msg.content)) !== null) {
        if (match.index > lastIndex) {
            parts.push({ type: 'text', content: msg.content.slice(lastIndex, match.index) });
        }
        parts.push({ type: 'think', content: match[1], id: `${messageIndex}-${lastIndex}` });
        lastIndex = regex.lastIndex;
    }
    if (lastIndex < msg.content.length) {
        parts.push({ type: 'text', content: msg.content.slice(lastIndex) });
    }
  }else{
    parts.push({ type: 'text', content:msg.content });
  }

  return (
    <div className={`message-row ${isUser ? 'from-user' : 'from-assistant'}`}>
      {/* For assistant: avatar first, for user: avatar after bubble */}
      <div className="avatar">{isUser ? '👲🏼' : '🤖'}
      </div>
      <div className={`bubble ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
        <div className="meta">
          <span className="speaker">{isUser ? 'You' : 'Assistant'}</span>
        </div>
        <div className="content">
            {parts.map((part, index) => {
                if (part.type === 'text') 
                    return <ReactMarkdown key={index}>{part.content}</ReactMarkdown>;
                if (part.type === 'think')
                    return <ThinkBubble
                            key={index}
                            content={part.content}
                            id={part.id}
                            openThoughts={openThoughts}
                            setOpenThoughts={setOpenThoughts}
                            />;
            })}
        </div>
      </div>
    </div>
  );

  function ThinkBubble({ content, id, openThoughts, setOpenThoughts }) {
    const isOpen = openThoughts[id] || false;

    const toggleOpen = () => {
      setOpenThoughts(prev => ({...prev, [id]: !isOpen }));
    }

  return (
    <div style={{ width: 'fit-content', minWidth: '120px', marginTop: '6px' }}>
      <div className={`bubble-think ${isOpen ? 'open' : ''}`} onClick={toggleOpen}>
        <span>{isOpen ? 'Hide Thoughts' : 'Show Thoughts'}</span>
        <span className="chevron">▶</span>
      </div>
      {isOpen && (
        <div className="think-content" style={{ marginTop: '6px' }}>
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
  }
}

export default Message;
