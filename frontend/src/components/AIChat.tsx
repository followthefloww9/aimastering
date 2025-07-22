import React, { useState, useRef, useEffect } from 'react';
import { useAudioStore } from '../stores/audioStore';
import { chatAPI } from '../services/api';
import { MessageCircle, Send, Bot, User, Lightbulb } from 'lucide-react';
import toast from 'react-hot-toast';

const AIChat: React.FC = () => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { 
    currentTrack, 
    chatMessages, 
    addChatMessage, 
    masteringSettings,
    updateMasteringSettings 
  } = useAudioStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!message.trim() || !currentTrack || !currentTrack.is_analyzed || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user' as const,
      content: message,
      timestamp: new Date()
    };

    addChatMessage(userMessage);
    setMessage('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(
        currentTrack.id,
        message,
        masteringSettings,
        true
      );

      // Apply adjustments if provided
      if (response.adjustments) {
        updateMasteringSettings(response.adjustments);
      }

      const aiMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai' as const,
        content: response.response,
        timestamp: new Date(),
        adjustments: response.adjustments,
        suggestions: response.suggestions
      };

      addChatMessage(aiMessage);

      if (response.task_id) {
        toast.success('AI is applying changes...');
      }

    } catch (error: any) {
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai' as const,
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      addChatMessage(errorMessage);
      toast.error('Failed to process message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickCommands = [
    'Add more bass',
    'Make it brighter',
    'More vintage sound',
    'Increase punch',
    'Wider stereo image',
    'Reduce harshness'
  ];

  const handleQuickCommand = (command: string) => {
    setMessage(command);
  };

  if (!currentTrack) {
    return (
      <div className="glass rounded-xl p-6">
        <div className="text-center text-gray-400">
          <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Upload a track to start chatting with AI</p>
        </div>
      </div>
    );
  }

  if (!currentTrack.is_analyzed) {
    return (
      <div className="glass rounded-xl p-6">
        <div className="text-center text-gray-400">
          <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>AI chat will be available after track analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-6 flex flex-col">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-4">
        <Bot className="w-6 h-6 text-accent-400" />
        <h2 className="text-xl font-semibold text-white">AI Mastering Assistant</h2>
      </div>

      {/* Messages */}
      <div className="space-y-4 mb-4 max-h-[400px] overflow-y-auto">
        {chatMessages.length === 0 && (
          <div className="text-center text-gray-400 py-6">
            <Lightbulb className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p className="text-lg">Ask me to adjust your mastering!</p>
          </div>
        )}

        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.type === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-700 text-white'
              }`}
            >
              <div className="flex items-start space-x-2">
                {msg.type === 'ai' && <Bot className="w-4 h-4 mt-1 text-accent-400" />}
                {msg.type === 'user' && <User className="w-4 h-4 mt-1" />}
                <div className="flex-1">
                  <p className="text-sm">{msg.content}</p>
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-600">
                      <p className="text-xs text-gray-300 mb-1">Suggestions:</p>
                      {msg.suggestions.map((suggestion, index) => (
                        <p key={index} className="text-xs text-gray-300">• {suggestion}</p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-white px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-accent-400" />
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Commands */}
      {chatMessages.length === 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-400 mb-2">Quick commands:</p>
          <div className="flex flex-wrap gap-2">
            {quickCommands.map((command) => (
              <button
                key={command}
                onClick={() => handleQuickCommand(command)}
                className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded-full transition-colors"
              >
                {command}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex space-x-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me to adjust your mastering..."
          className="flex-1 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          rows={2}
          disabled={isLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={!message.trim() || isLoading}
          className={`px-4 py-2 rounded-lg transition-colors ${
            message.trim() && !isLoading
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-gray-700 text-gray-400 cursor-not-allowed'
          }`}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      {/* Tips */}
      <div className="mt-3 text-xs text-gray-500">
        <p>💡 <strong>How AI Chat Works:</strong> AI automatically updates mastering controls based on your requests</p>
      </div>
    </div>
  );
};

export default AIChat;
