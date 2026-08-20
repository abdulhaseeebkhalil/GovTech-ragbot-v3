import { motion } from "framer-motion";
import { Bot, User, Zap, FileText, BarChart3 } from "lucide-react";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "./button";
import { ChatMessage } from "../../lib/openai";
import Citations from './citations';

interface ChatMessageProps {
  message: ChatMessage;
  index: number;
  onActionResponse: (action: string, originalMessage: string) => void;
}

export const ChatMessageComponent: React.FC<ChatMessageProps> = ({ 
  message, 
  index, 
  onActionResponse 
}) => {
  const isUser = message.role === 'user';
  
  const handleActionClick = (action: string) => {
    onActionResponse(action, message.content);
  };

  // Clean up markdown content to ensure proper heading rendering
  const cleanMarkdownContent = (content: string): string => {
    return content
      // Fix malformed headings like "# ##" or "# Executive Summary" -> "## Executive Summary"
      .replace(/^#\s+(#{1,5})\s*(.+)$/gm, '$1 $2')
      // Fix standalone "#" followed by text -> "# text"
      .replace(/^#\s+([^#].*)$/gm, '# $1')
      // Fix headers that have extra spaces or formatting issues
      .replace(/^(#{1,6})\s{2,}(.+)$/gm, '$1 $2')
      // Ensure headers have proper spacing before them (but not at start)
      .replace(/([^\n])(\n)(#{1,6}\s)/g, '$1\n\n$3')
      // Clean up multiple consecutive newlines
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ 
        delay: index * 0.08, 
        duration: 0.4,
        ease: [0.4, 0.0, 0.2, 1]
      }}
      className={`flex gap-4 mb-8 ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      {!isUser && (
        <motion.div 
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: index * 0.08 + 0.1, duration: 0.3 }}
          className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm"
        >
          <Bot className="w-4.5 h-4.5 text-white" />
        </motion.div>
      )}
      
      <div className={`max-w-[85%] relative ${
        isUser 
          ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white ml-16 shadow-lg shadow-blue-500/25' 
          : 'bg-white/90 backdrop-blur-xl text-gray-900 mr-16 shadow-lg shadow-black/5 border border-white/20'
      } rounded-3xl px-7 py-6`}
      style={{
        backdropFilter: !isUser ? 'blur(20px) saturate(180%)' : undefined,
        WebkitBackdropFilter: !isUser ? 'blur(20px) saturate(180%)' : undefined
      }}>
        <div className="text-[15px] leading-relaxed prose prose-sm max-w-none" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-6 text-current tracking-tight">{children}</h1>,
              h2: ({ children }) => <h2 className="text-xl font-bold mb-3 mt-5 text-current tracking-tight">{children}</h2>,
              h3: ({ children }) => <h3 className="text-lg font-semibold mb-3 mt-4 text-current tracking-tight">{children}</h3>,
              h4: ({ children }) => <h4 className="text-base font-semibold mb-2 mt-3 text-current tracking-tight">{children}</h4>,
              h5: ({ children }) => <h5 className="text-sm font-semibold mb-2 mt-3 text-current tracking-tight">{children}</h5>,
              h6: ({ children }) => <h6 className="text-xs font-semibold mb-2 mt-3 text-current tracking-tight">{children}</h6>,
              p: ({ children }) => <p className="mb-4 last:mb-0 leading-relaxed text-current">{children}</p>,
              strong: ({ children }) => <strong className="font-semibold text-current">{children}</strong>,
              em: ({ children }) => <em className="italic text-current">{children}</em>,
              u: ({ children }) => <u className="underline text-current">{children}</u>,
              table: ({ children }) => (
                <div className="overflow-x-auto my-4">
                  <table className="w-full min-w-full border-collapse border border-gray-200/60 table-auto rounded-xl overflow-hidden">
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead className="bg-gray-50/80">{children}</thead>
              ),
              tbody: ({ children }) => <tbody>{children}</tbody>,
              tr: ({ children }) => (
                <tr className="border-b border-gray-100/60 hover:bg-gray-50/30 transition-colors">{children}</tr>
              ),
              th: ({ children }) => (
                <th className="border-r border-gray-200/60 px-4 py-3 text-left font-semibold text-current whitespace-nowrap text-sm">
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td className="border-r border-gray-200/60 px-4 py-3 break-words text-current">{children}</td>
              ),
              ul: ({ children }) => <ul className="list-disc list-inside mb-4 space-y-1.5 text-current">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mb-4 space-y-1.5 text-current">{children}</ol>,
              li: ({ children }) => <li className="mb-1.5 leading-relaxed text-current">{children}</li>,
              code: ({ children }) => (
                <code className={`px-2 py-1 rounded-md text-xs font-mono ${
                  isUser ? 'bg-white/20 text-white' : 'bg-gray-100/80 text-gray-800'
                }`}>
                  {children}
                </code>
              ),
              pre: ({ children }) => (
                <pre className={`p-4 rounded-2xl overflow-x-auto text-xs font-mono mb-4 leading-relaxed ${
                  isUser ? 'bg-white/15 text-white' : 'bg-gray-50/80 text-gray-800'
                }`}>
                  {children}
                </pre>
              ),
            }}
          >
            {cleanMarkdownContent(message.content)}
          </ReactMarkdown>
        </div>
        
        {!isUser && message.sources && (
          <Citations sources={message.sources} />
        )}
        
        {!isUser && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 + 0.3, duration: 0.3 }}
            className="mt-6 pt-5 border-t border-gray-100/60"
          >
            <div className="text-xs text-gray-600 mb-3 font-medium tracking-wide">Quick Actions</div>
            <div className="flex flex-wrap gap-2.5">
              <Button
                onClick={() => handleActionClick('feasibility')}
                variant="outline"
                size="sm"
                className="text-xs h-9 px-4 bg-white/80 backdrop-blur-sm border-blue-200/60 text-blue-700 hover:bg-blue-50/80 hover:border-blue-300/60 transition-all duration-200 ease-out rounded-full font-medium shadow-sm hover:shadow-md hover:scale-105"
              >
                <Zap className="w-3.5 h-3.5 mr-1.5" />
                Feasibility
              </Button>
              <Button
                onClick={() => handleActionClick('case_study')}
                variant="outline"
                size="sm"
                className="text-xs h-9 px-4 bg-white/80 backdrop-blur-sm border-purple-200/60 text-purple-700 hover:bg-purple-50/80 hover:border-purple-300/60 transition-all duration-200 ease-out rounded-full font-medium shadow-sm hover:shadow-md hover:scale-105"
              >
                <BarChart3 className="w-3.5 h-3.5 mr-1.5" />
                Case Study
              </Button>
              <Button
                onClick={() => handleActionClick('executive_report')}
                variant="outline"
                size="sm"
                className="text-xs h-9 px-4 bg-white/80 backdrop-blur-sm border-green-200/60 text-green-700 hover:bg-green-50/80 hover:border-green-300/60 transition-all duration-200 ease-out rounded-full font-medium shadow-sm hover:shadow-md hover:scale-105"
              >
                <FileText className="w-3.5 h-3.5 mr-1.5" />
                Executive Report
              </Button>
            </div>
          </motion.div>
        )}
      </div>
      
      {isUser && (
        <motion.div 
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: index * 0.08 + 0.1, duration: 0.3 }}
          className="w-9 h-9 rounded-full bg-gradient-to-br from-gray-500 to-gray-600 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm"
        >
          <User className="w-4.5 h-4.5 text-white" />
        </motion.div>
      )}
    </motion.div>
  );
};