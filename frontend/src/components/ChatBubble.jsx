import React from 'react'
import { Bot, User } from 'lucide-react'

/**
 * ChatBubble — reusable chat message component.
 * Props:
 *   message  : string  — message text (supports \n line breaks)
 *   isBot    : boolean — true = left-aligned bot bubble, false = right-aligned user bubble
 *   timestamp: string  — optional time label
 */
export default function ChatBubble({ message, isBot, timestamp, imageUrl }) {
  // Convert **bold** markdown to <strong> and \n to <br>
  const formatText = (text) => {
    if (!text) return ''
    return text
      .split('\n')
      .map((line, i) => {
        const parts = line.split(/(\*\*[^*]+\*\*)/)
        return (
          <span key={i}>
            {parts.map((part, j) =>
              part.startsWith('**') && part.endsWith('**') ? (
                <strong key={j}>{part.slice(2, -2)}</strong>
              ) : (
                part
              )
            )}
            {i < text.split('\n').length - 1 && <br />}
          </span>
        )
      })
  }

  if (isBot) {
    return (
      <div className="flex items-start gap-2 max-w-[85%]">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-secondary flex items-center justify-center mt-1">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div>
          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">
              {formatText(message)}
            </p>
          </div>
          {timestamp && (
            <p className="text-xs text-gray-400 mt-1 ml-1">{timestamp}</p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2 max-w-[85%] ml-auto flex-row-reverse">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center mt-1">
        <User className="w-4 h-4 text-gray-600" />
      </div>
      <div>
        <div className="bg-brand-primary rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
          {imageUrl && (
            <img
              src={imageUrl}
              alt="Uploaded scam screenshot"
              className="w-full max-w-xs max-h-48 object-cover rounded-xl mb-2 border border-blue-300"
            />
          )}
          <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">
            {message}
          </p>
        </div>
        {timestamp && (
          <p className="text-xs text-gray-400 mt-1 mr-1 text-right">{timestamp}</p>
        )}
      </div>
    </div>
  )
}
