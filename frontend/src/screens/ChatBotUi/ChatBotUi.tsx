import { AnimatePresence, motion } from "framer-motion";
import { Send, MessageSquare, Plus, Menu, Trash2, Edit3, Check, X, ChevronLeft, FileText, Users, Globe, HelpCircle, BarChart3, FileBarChart, ClipboardList, MessageCircle, Home, Eye, Search, Scale, FileCheck, Download } from "lucide-react";
import React, { useState, useRef, useEffect } from "react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { EGovBotLogo } from "../../components/ui/logo";
import { ChatMessageComponent } from "../../components/ui/chat-message";
import { TypingIndicator } from "../../components/ui/typing-indicator";
import { SiriAnimation } from "../../components/ui/siri-animation";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../../components/ui/dialog";
import { ChatMessage, generateResponse, generateActionResponse } from "../../lib/openai";
import jsPDF from 'jspdf';
import JSZip from 'jszip';

interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
}

export const ChatBotUi = (): JSX.Element => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [webSearchEnabled, setWebSearchEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Legal Analysis Mode States
  const [mode, setMode] = useState<'chat' | 'legal'>('chat');
  const [narrative, setNarrative] = useState("");
  const [petition, setPetition] = useState("");
  const [legalResults, setLegalResults] = useState<any>(null);
  const [activeResultTab, setActiveResultTab] = useState<'summary' | 'entities' | 'issues' | 'laws' | 'commentary' | 'documents' | 'judgment'>('summary');

  const suggestions = [
    "How can I apply for a CNIC?",
    "What are the Digital Pakistan initiatives?",
    "How do I access government services online?",
    "Tell me about e-governance services"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Document generation and download functions
  const generateDocument = (docType: string) => {
    console.log(`Generating ${docType} document...`);
    // This would typically call a backend API to generate the document
    // For now, we'll show a success message
    alert(`${docType.charAt(0).toUpperCase() + docType.slice(1)} document generated successfully!`);
  };

  const downloadDocument = (docType: string, format: 'txt' | 'pdf') => {
    if (!legalResults.results) {
      alert('No analysis results available. Please complete the legal analysis first.');
      return;
    }

    let content = '';
    let filename = '';

    switch (docType) {
      case 'plaint':
        // Try multiple sources for plaint content
        if (legalResults.results.commentary?.petition_critique) {
          content = typeof legalResults.results.commentary.petition_critique === 'string'
            ? legalResults.results.commentary.petition_critique
            : legalResults.results.commentary.petition_critique?.text || 
              legalResults.results.commentary.petition_critique?.description ||
              'Petition critique content not available';
        } else if (legalResults.results.processed_data?.narrative) {
          // Fallback to narrative data
          const narrative = legalResults.results.processed_data.narrative;
          content = `NARRATIVE ANALYSIS:\n\n${narrative.claims?.map((claim: any, idx: number) => 
            `${idx + 1}. ${typeof claim === 'string' ? claim : claim.text || claim.description || JSON.stringify(claim)}`
          ).join('\n') || 'No claims found'}\n\nENTITIES IDENTIFIED:\n${Object.entries(narrative.entities || {}).map(([type, entities]: [string, any]) => 
            `${type}: ${entities.map((e: any) => e.text).join(', ')}`
          ).join('\n')}`;
        } else {
          content = 'Plaint/Petition document content not available. Please ensure legal analysis is complete.';
        }
        filename = `plaint_${new Date().toISOString().split('T')[0]}`;
        break;
        
      case 'statement':
        // Try multiple sources for statement content
        if (legalResults.results.commentary?.counter_arguments) {
          content = typeof legalResults.results.commentary.counter_arguments === 'string'
            ? legalResults.results.commentary.counter_arguments
            : legalResults.results.commentary.counter_arguments?.text ||
              legalResults.results.commentary.counter_arguments?.description ||
              'Counter arguments content not available';
        } else if (legalResults.results.processed_data?.petition) {
          // Fallback to petition data
          const petition = legalResults.results.processed_data.petition;
          content = `PETITION ANALYSIS:\n\n${petition.claims?.map((claim: any, idx: number) => 
            `${idx + 1}. ${typeof claim === 'string' ? claim : claim.text || claim.description || JSON.stringify(claim)}`
          ).join('\n') || 'No claims found'}\n\nENTITIES IDENTIFIED:\n${Object.entries(petition.entities || {}).map(([type, entities]: [string, any]) => 
            `${type}: ${entities.map((e: any) => e.text).join(', ')}`
          ).join('\n')}`;
        } else {
          content = 'Written statement content not available. Please ensure legal analysis is complete.';
        }
        filename = `written_statement_${new Date().toISOString().split('T')[0]}`;
        break;
        
      case 'appeal':
        // Appeal content (this was working)
        if (legalResults.results.commentary?.legal_conclusion) {
          content = typeof legalResults.results.commentary.legal_conclusion === 'string'
            ? legalResults.results.commentary.legal_conclusion
            : legalResults.results.commentary.legal_conclusion?.text ||
              legalResults.results.commentary.legal_conclusion?.judgment ||
              legalResults.results.commentary.legal_conclusion?.description ||
              'Legal conclusion content not available';
        } else {
          content = 'Appeal document content not available. Please ensure legal analysis is complete.';
        }
        filename = `appeal_${new Date().toISOString().split('T')[0]}`;
        break;
        
      default:
        alert('Invalid document type');
        return;
    }

    // Ensure we have content before proceeding
    if (!content || content.trim() === '') {
      alert(`No content available for ${docType} document. Please ensure the legal analysis is complete and contains relevant data.`);
      return;
    }

    if (format === 'txt') {
      // Add document header
      const documentHeader = `
LEGAL DOCUMENT - ${docType.toUpperCase()}
Generated on: ${new Date().toLocaleDateString()}
Based on Legal Analysis Results

========================================

`;

      const fullContent = documentHeader + content;

      // Download as TXT file
      const blob = new Blob([fullContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else if (format === 'pdf') {
      // Generate proper PDF using jsPDF
      const doc = new jsPDF();
      
      // Set font
      doc.setFont('helvetica');
      
      // Add header
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text(`LEGAL DOCUMENT - ${docType.toUpperCase()}`, 20, 30);
      
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, 40);
      doc.text('Based on Legal Analysis Results', 20, 45);
      
      // Add line separator
      doc.line(20, 50, 190, 50);
      
      // Add content
      doc.setFontSize(12);
      doc.setFont('helvetica', 'normal');
      
      // Split content into lines and add to PDF
      const lines = doc.splitTextToSize(content, 170);
      let yPosition = 60;
      
      for (let i = 0; i < lines.length; i++) {
        if (yPosition > 280) {
          doc.addPage();
          yPosition = 20;
        }
        doc.text(lines[i], 20, yPosition);
        yPosition += 6;
      }
      
      // Add footer
      const pageCount = doc.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.text(`Page ${i} of ${pageCount}`, 20, 290);
        doc.text('Generated by GovTech Legal Analysis System', 120, 290);
      }
      
      // Save the PDF
      doc.save(`${filename}.pdf`);
    }
  };

  // Download all documents functionality
  const downloadAllDocuments = async (format: 'txt' | 'pdf', asZip: boolean = false) => {
    if (!legalResults.results) {
      alert('No analysis results available. Please complete the legal analysis first.');
      return;
    }

    const documents = ['plaint', 'statement', 'appeal'];
    const zip = new JSZip();
    const dateStr = new Date().toISOString().split('T')[0];

    // Generate content for all documents
    const documentContents = documents.map(docType => {
      let content = '';
      let filename = '';

      switch (docType) {
        case 'plaint':
          if (legalResults.results.commentary?.petition_critique) {
            content = typeof legalResults.results.commentary.petition_critique === 'string'
              ? legalResults.results.commentary.petition_critique
              : legalResults.results.commentary.petition_critique?.text || 
                legalResults.results.commentary.petition_critique?.description ||
                'Petition critique content not available';
          } else if (legalResults.results.processed_data?.narrative) {
            const narrative = legalResults.results.processed_data.narrative;
            content = `NARRATIVE ANALYSIS:\n\n${narrative.claims?.map((claim: any, idx: number) => 
              `${idx + 1}. ${typeof claim === 'string' ? claim : claim.text || claim.description || JSON.stringify(claim)}`
            ).join('\n') || 'No claims found'}\n\nENTITIES IDENTIFIED:\n${Object.entries(narrative.entities || {}).map(([type, entities]: [string, any]) => 
              `${type}: ${entities.map((e: any) => e.text).join(', ')}`
            ).join('\n')}`;
          } else {
            content = 'Plaint/Petition document content not available.';
          }
          filename = `plaint_${dateStr}`;
          break;
          
        case 'statement':
          if (legalResults.results.commentary?.counter_arguments) {
            content = typeof legalResults.results.commentary.counter_arguments === 'string'
              ? legalResults.results.commentary.counter_arguments
              : legalResults.results.commentary.counter_arguments?.text ||
                legalResults.results.commentary.counter_arguments?.description ||
                'Counter arguments content not available';
          } else if (legalResults.results.processed_data?.petition) {
            const petition = legalResults.results.processed_data.petition;
            content = `PETITION ANALYSIS:\n\n${petition.claims?.map((claim: any, idx: number) => 
              `${idx + 1}. ${typeof claim === 'string' ? claim : claim.text || claim.description || JSON.stringify(claim)}`
            ).join('\n') || 'No claims found'}\n\nENTITIES IDENTIFIED:\n${Object.entries(petition.entities || {}).map(([type, entities]: [string, any]) => 
              `${type}: ${entities.map((e: any) => e.text).join(', ')}`
            ).join('\n')}`;
          } else {
            content = 'Written statement content not available.';
          }
          filename = `written_statement_${dateStr}`;
          break;
          
        case 'appeal':
          if (legalResults.results.commentary?.legal_conclusion) {
            content = typeof legalResults.results.commentary.legal_conclusion === 'string'
              ? legalResults.results.commentary.legal_conclusion
              : legalResults.results.commentary.legal_conclusion?.text ||
                legalResults.results.commentary.legal_conclusion?.judgment ||
                legalResults.results.commentary.legal_conclusion?.description ||
                'Legal conclusion content not available';
          } else {
            content = 'Appeal document content not available.';
          }
          filename = `appeal_${dateStr}`;
          break;
      }

      return { docType, content, filename };
    });

    if (asZip) {
      // Create zip file with all documents
      for (const { docType, content, filename } of documentContents) {
        if (content && content.trim() !== '') {
          const documentHeader = `
LEGAL DOCUMENT - ${docType.toUpperCase()}
Generated on: ${new Date().toLocaleDateString()}
Based on Legal Analysis Results

========================================

`;

          const fullContent = documentHeader + content;

          if (format === 'txt') {
            zip.file(`${filename}.txt`, fullContent);
          } else if (format === 'pdf') {
            // Generate PDF and add to zip
            const doc = new jsPDF();
            doc.setFont('helvetica');
            
            doc.setFontSize(16);
            doc.setFont('helvetica', 'bold');
            doc.text(`LEGAL DOCUMENT - ${docType.toUpperCase()}`, 20, 30);
            
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, 40);
            doc.text('Based on Legal Analysis Results', 20, 45);
            
            doc.line(20, 50, 190, 50);
            
            doc.setFontSize(12);
            doc.setFont('helvetica', 'normal');
            
            const lines = doc.splitTextToSize(content, 170);
            let yPosition = 60;
            
            for (let i = 0; i < lines.length; i++) {
              if (yPosition > 280) {
                doc.addPage();
                yPosition = 20;
              }
              doc.text(lines[i], 20, yPosition);
              yPosition += 6;
            }
            
            const pageCount = doc.getNumberOfPages();
            for (let i = 1; i <= pageCount; i++) {
              doc.setPage(i);
              doc.setFontSize(8);
              doc.text(`Page ${i} of ${pageCount}`, 20, 290);
              doc.text('Generated by GovTech Legal Analysis System', 120, 290);
            }
            
            const pdfBlob = doc.output('blob');
            zip.file(`${filename}.pdf`, pdfBlob);
          }
        }
      }

      // Generate and download zip file
      const zipBlob = await zip.generateAsync({ type: 'blob' });
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `legal_documents_${dateStr}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      alert(`All ${format.toUpperCase()} documents downloaded as ZIP file!`);
    } else {
      // Download all documents separately
      for (const { docType, content, filename } of documentContents) {
        if (content && content.trim() !== '') {
          const documentHeader = `
LEGAL DOCUMENT - ${docType.toUpperCase()}
Generated on: ${new Date().toLocaleDateString()}
Based on Legal Analysis Results

========================================

`;

          const fullContent = documentHeader + content;

          if (format === 'txt') {
            const blob = new Blob([fullContent], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          } else if (format === 'pdf') {
            const doc = new jsPDF();
            doc.setFont('helvetica');
            
            doc.setFontSize(16);
            doc.setFont('helvetica', 'bold');
            doc.text(`LEGAL DOCUMENT - ${docType.toUpperCase()}`, 20, 30);
            
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, 40);
            doc.text('Based on Legal Analysis Results', 20, 45);
            
            doc.line(20, 50, 190, 50);
            
            doc.setFontSize(12);
            doc.setFont('helvetica', 'normal');
            
            const lines = doc.splitTextToSize(content, 170);
            let yPosition = 60;
            
            for (let i = 0; i < lines.length; i++) {
              if (yPosition > 280) {
                doc.addPage();
                yPosition = 20;
              }
              doc.text(lines[i], 20, yPosition);
              yPosition += 6;
            }
            
            const pageCount = doc.getNumberOfPages();
            for (let i = 1; i <= pageCount; i++) {
              doc.setPage(i);
              doc.setFontSize(8);
              doc.text(`Page ${i} of ${pageCount}`, 20, 290);
              doc.text('Generated by GovTech Legal Analysis System', 120, 290);
            }
            
            doc.save(`${filename}.pdf`);
          }
        }
      }
      
      alert(`All ${format.toUpperCase()} documents downloaded separately!`);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat sessions from localStorage on component mount
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      const sessions = JSON.parse(savedSessions).map((session: any) => ({
        ...session,
        createdAt: new Date(session.createdAt),
        messages: session.messages.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }));
      setChatSessions(sessions);
    }
  }, []);

  // Save chat sessions to localStorage whenever they change
  useEffect(() => {
    if (chatSessions.length > 0) {
      localStorage.setItem('chatSessions', JSON.stringify(chatSessions));
    }
  }, [chatSessions]);

  // Update current session messages when messages change
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      setChatSessions(prev => prev.map(session => 
        session.id === currentSessionId 
          ? { ...session, messages: [...messages] }
          : session
      ));
    }
  }, [messages, currentSessionId]);

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    // Create new session if none exists
    if (!currentSessionId) {
      const newSessionId = Date.now().toString();
      const newSession: ChatSession = {
        id: newSessionId,
        title: text.slice(0, 30) + (text.length > 30 ? '...' : ''),
        messages: [],
        createdAt: new Date()
      };
      setChatSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSessionId);
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await generateResponse(text, messages, webSearchEnabled);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize for the technical difficulty. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionResponse = async (action: string, originalMessage: string) => {
    setIsLoading(true);
    
    // Check if the conversation context is too simple for detailed analysis
    const isSimpleChat = () => {
      // If there are no messages yet, it's definitely too simple
      if (messages.length === 0) {
        return true;
      }
      
      // Only check USER messages, not assistant responses
      const userMessages = messages.filter(msg => msg.role === 'user');
      const recentUserMessages = userMessages.slice(-3); // Check last 3 user messages
      const userMessageTexts = recentUserMessages.map(msg => msg.content.toLowerCase());
      
      // Check for simple greetings or casual conversation
      const simplePatterns = [
        /^(hi|hello|hey|good morning|good afternoon|good evening)\b/,
        /^(how are you|what's up|what are you|who are you)\b/,
        /^(thanks|thank you|ok|okay|yes|no)\b/,
        /^.{1,20}$/ // Very short messages
      ];
      
      const hasSimpleContent = userMessageTexts.some(msg => 
        simplePatterns.some(pattern => pattern.test(msg.trim()))
      );
      
      // Check if there's insufficient government/policy related content in USER messages
      const governmentKeywords = [
        'government', 'policy', 'service', 'department', 'ministry', 'public',
        'citizen', 'administration', 'regulation', 'law', 'budget', 'project',
        'initiative', 'reform', 'development', 'infrastructure', 'governance',
        // Disaster management and flood-related terms
        'flood', 'disaster', 'emergency', 'monsoon', 'pdma', 'contingency',
        'preparedness', 'response', 'management', 'kp', 'khyber pakhtunkhwa',
        'chief secretary', 'deputy commissioner', 'district', 'provincial',
        'planning', 'coordination', 'safety', 'vulnerability', 'assessment',
        'mitigation', 'relief', 'rehabilitation', 'damage', 'report', 'advisory'
      ];
      
      const hasGovernmentContent = userMessageTexts.some(msg =>
        governmentKeywords.some(keyword => msg.includes(keyword))
      );
      
      // Check if user is asking for detailed analysis in their messages
      const userConversationText = userMessageTexts.join(' ');
      const isDetailedRequest = userConversationText.includes('detail') || 
                               userConversationText.includes('complete') ||
                               userConversationText.includes('comprehensive') ||
                               userConversationText.includes('analysis') ||
                               userConversationText.includes('insight') ||
                               userConversationText.includes('report');
      
      // Return true (simple chat) if:
      // 1. Has simple content (like greetings) AND
      // 2. No government-related content in user messages AND
      // 3. No detailed analysis request from user
      return hasSimpleContent && !hasGovernmentContent && !isDetailedRequest;
    };
    
    try {
      if (isSimpleChat()) {
        // Provide a helpful message when there's not enough data for analysis
        const insufficientDataMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `I don't have enough specific government or policy-related information in our conversation to provide a meaningful ${action.replace('_', ' ')} analysis. Please share more details about a specific government service, policy, or initiative you'd like me to analyze, and I'll be happy to help with a detailed ${action.replace('_', ' ')}.`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, insufficientDataMessage]);
      } else {
        const response = await generateActionResponse(
          action as 'feasibility' | 'case_study' | 'executive_report',
          originalMessage,
          messages.map(m => m.content).join('\n') // Use full conversation context
        );
        
        const assistantMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error generating action response:', error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'I apologize for the technical difficulty with the specialized analysis. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
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

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteSession = () => {
    if (sessionToDelete) {
      setChatSessions(prev => prev.filter(session => session.id !== sessionToDelete));
      if (currentSessionId === sessionToDelete) {
        setMessages([]);
        setCurrentSessionId(null);
      }
      setDeleteDialogOpen(false);
      setSessionToDelete(null);
    }
  };

  const handleStartEdit = (sessionId: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(sessionId);
    setEditingTitle(currentTitle);
  };

  const handleSaveEdit = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editingTitle.trim()) {
      setChatSessions(prev => prev.map(session => 
        session.id === sessionId 
          ? { ...session, title: editingTitle.trim() }
          : session
      ));
    }
    setEditingSessionId(null);
    setEditingTitle("");
  };

  const handleReturnHome = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
    setEditingTitle("");
  };

  const handleLegalAnalysis = async () => {
    if (!narrative.trim() || !petition.trim()) {
      alert("Please fill in both narrative and petition fields");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/legal/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ narrative, petition })
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setLegalResults(data);
      setActiveResultTab('summary');
    } catch (error) {
      console.error('Legal analysis error:', error);
      alert('Failed to perform legal analysis. Please ensure the backend is connected.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <AnimatePresence>
        {isSidebarVisible && (
          <motion.div 
             initial={{ x: -288, opacity: 0 }}
             animate={{ x: 0, opacity: 1 }}
             exit={{ x: -288, opacity: 0 }}
             transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="w-72 bg-gradient-to-b from-gray-100 to-gray-50 backdrop-blur-xl border-r-2 border-gray-300 text-gray-800 flex flex-col shadow-2xl"
          >
        {/* Header */}
        <div className="p-6 border-b border-gray-100/80">
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.3 }}
            className="flex items-center justify-between mb-6"
          >
            <div className="flex items-center gap-3">
              <EGovBotLogo />
            </div>
            <button
              onClick={() => setIsSidebarVisible(false)}
              className="p-2 hover:bg-gray-100/80 rounded-lg transition-colors duration-200"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600" />
            </button>
          </motion.div>
          <motion.div
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <Button
              onClick={() => {
                setMessages([]);
                setCurrentSessionId(null);
              }}
              className="w-full bg-white/80 hover:bg-white hover:shadow-md text-gray-700 border border-gray-200/60 hover:border-gray-300/60 rounded-xl flex items-center gap-3 py-3 px-4 font-medium transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98]"
            >
              <Plus className="w-4.5 h-4.5" />
              New Chat
            </Button>
          </motion.div>
        </div>
        
        {/* Chat History */}
        <div className="flex-1 p-6 overflow-y-auto" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
          <style>{`
            .sidebar-scroll::-webkit-scrollbar {
              display: none;
            }
          `}</style>
          <div className="text-xs text-gray-500 mb-4 font-medium tracking-wide uppercase">Recent Chats</div>
          <div className="space-y-2">
            {chatSessions.map((session, index) => (
              <motion.div 
                key={session.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 + 0.3, duration: 0.3 }}
                onClick={() => {
                  if (editingSessionId !== session.id) {
                    setCurrentSessionId(session.id);
                    setMessages(session.messages);
                  }
                }}
                className={`group rounded-xl p-4 cursor-pointer transition-all duration-200 ease-out hover:scale-[1.02] active:scale-[0.98] ${
                  currentSessionId === session.id 
                    ? 'bg-blue-50/80 border border-blue-200/60 shadow-sm' 
                    : 'bg-white/60 hover:bg-white/80 hover:shadow-sm border border-transparent hover:border-gray-200/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    currentSessionId === session.id 
                      ? 'bg-blue-100/80 text-blue-600' 
                      : 'bg-gray-100/80 text-gray-600'
                  }`}>
                    <MessageSquare className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    {editingSessionId === session.id ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              handleSaveEdit(session.id, e as any);
                            } else if (e.key === 'Escape') {
                              handleCancelEdit(e as any);
                            }
                          }}
                          className="flex-1 text-sm font-medium bg-white/80 border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-300"
                          autoFocus
                        />
                        <button
                          onClick={(e) => handleSaveEdit(session.id, e)}
                          className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
                        >
                          <Check className="w-3 h-3" />
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="p-1 text-red-600 hover:bg-red-50 rounded transition-colors"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <>
                        <span className="text-sm font-medium truncate block text-gray-800">
                          {session.title}
                        </span>
                        <span className="text-xs text-gray-500 font-normal">
                          {session.createdAt.toLocaleDateString()}
                        </span>
                      </>
                    )}
                  </div>
                  {editingSessionId !== session.id && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <button
                        onClick={(e) => handleStartEdit(session.id, session.title, e)}
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all duration-200"
                        title="Edit name"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => handleDeleteSession(session.id, e)}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200"
                        title="Delete chat"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
          {chatSessions.length === 0 && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-sm text-gray-400 text-center py-8 font-medium"
            >
              No recent chats
            </motion.div>
          )}
        </div>
        
        {/* Footer */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.3 }}
          className="p-6 border-t border-gray-100/80 bg-white/40 backdrop-blur-sm"
        >
          <div className="text-xs text-gray-500 font-medium leading-relaxed">
            Government of KPK<br />
            <span className="text-gray-400">Performance Management & Reforms Unit</span>
          </div>
        </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative">
        {/* Sidebar Toggle Button */}
        <AnimatePresence>
          {!isSidebarVisible && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              onClick={() => setIsSidebarVisible(true)}
              className="absolute top-4 left-4 z-30 p-3 bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200/60 hover:bg-white hover:shadow-xl transition-all duration-200 hover:scale-105"
            >
              <Menu className="w-5 h-5 text-gray-700" />
            </motion.button>
          )}
        </AnimatePresence>
        {/* Logo Watermark */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
          <img 
            src="/ChatGPT Image Sep 1, 2025, 03_05_41 PM.png" 
            alt="Logo Watermark" 
            className="w-[500px] h-[500px] opacity-25 object-contain"
          />
        </div>
        
        {messages.length === 0 ? (
          /* Welcome Screen */
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="flex-1 overflow-y-auto bg-gradient-to-br from-emerald-50/30 to-white relative z-10"
          >
            <div className="max-w-4xl mx-auto p-8 relative">
              {/* Siri Animation - Center */}
               <motion.div 
                 initial={{ scale: 0.8, opacity: 0 }}
                 animate={{ scale: 1, opacity: 1 }}
                 transition={{ delay: 0.2, duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
                 className="flex flex-col items-center mb-12"
               >
                 <div className="relative">
                   <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-xl transform scale-110"></div>
                   <div className="relative">
                     <SiriAnimation width={120} height={120} />
                   </div>
                 </div>
                 <motion.div 
                   initial={{ opacity: 0, y: 15 }}
                   animate={{ opacity: 1, y: 0 }}
                   transition={{ delay: 0.5, duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
                   className="mt-6 text-center"
                 >
                   <div className="text-2xl font-bold text-green-700 mb-4">
                     GovTech
                   </div>
                   <div className="text-xl text-gray-700 font-semibold leading-relaxed">
                     Government of KPK<br />
                     <span className="text-lg text-gray-600 font-medium">Performance Management & Reforms Unit</span>
                   </div>
                 </motion.div>
               </motion.div>

              {/* Mode Toggle Buttons */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.35, duration: 0.5 }}
                className="flex gap-4 justify-center mb-12"
              >
                <Button
                  onClick={() => {
                    setMode('chat');
                    setLegalResults(null);
                  }}
                  className={`px-8 py-4 rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-2 ${
                    mode === 'chat'
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                      : 'bg-white/90 text-gray-700 border-2 border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <MessageCircle className="w-5 h-5" />
                  General Chat
                </Button>
                <Button
                  onClick={() => {
                    setMode('legal');
                    setMessages([]);
                    setCurrentSessionId(null);
                  }}
                  className={`px-8 py-4 rounded-2xl font-semibold shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-2 ${
                    mode === 'legal'
                      ? 'bg-gradient-to-r from-purple-500 to-violet-600 text-white'
                      : 'bg-white/90 text-gray-700 border-2 border-gray-200 hover:border-purple-300'
                  }`}
                >
                  <Scale className="w-5 h-5" />
                  Legal Analysis
                </Button>
              </motion.div>

              {/* Modern Compact Action Cards - Horizontal Layout - Only in Chat Mode */}
              {mode === 'chat' && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
                  className="mb-8"
                >
                  <div className="flex flex-wrap gap-4 justify-center">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.4, duration: 0.4 }}
                    className="group relative bg-white/90 backdrop-blur-sm p-4 rounded-xl border border-gray-200/60 shadow-lg w-48 h-32"
                  >
                    <div className="flex flex-col h-full">
                      <div className="flex items-center justify-between mb-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                          <BarChart3 className="w-4 h-4 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-gray-900 mb-1">Feasibility Simulation</h3>
                        <p className="text-xs text-gray-600 leading-tight">Simulate Before You Decide </p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5, duration: 0.4 }}
                    className="group relative bg-white/90 backdrop-blur-sm p-4 rounded-xl border border-gray-200/60 shadow-lg w-48 h-32"
                  >
                    <div className="flex flex-col h-full">
                      <div className="flex items-center justify-between mb-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-sm">
                          <FileBarChart className="w-4 h-4 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-gray-900 mb-1">Comparative Analysis</h3>
                        <p className="text-xs text-gray-600 leading-tight">Compare Strategies, Outcomes & Lessons</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6, duration: 0.4 }}
                    className="group relative bg-white/90 backdrop-blur-sm p-4 rounded-xl border border-gray-200/60 shadow-lg w-48 h-32"
                  >
                    <div className="flex flex-col h-full">
                      <div className="flex items-center justify-between mb-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-violet-600 rounded-lg flex items-center justify-center shadow-sm">
                          <ClipboardList className="w-4 h-4 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-gray-900 mb-1">Executive Summary</h3>
                        <p className="text-xs text-gray-600 leading-tight">Your Report, Simplified for Decision-Making</p>
                      </div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.7, duration: 0.4 }}
                    className="group relative bg-white/90 backdrop-blur-sm p-4 rounded-xl border border-gray-200/60 shadow-lg w-48 h-32"
                  >
                    <div className="flex flex-col h-full">
                      <div className="flex items-center justify-between mb-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg flex items-center justify-center shadow-sm">
                          <Eye className="w-4 h-4 text-white" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-gray-900 mb-1">Future Mirror</h3>
                        <p className="text-xs text-gray-600 leading-tight">See How Today's Decisions May Shape Tomorrow</p>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </motion.div>
              )}

              {/* Legal Analysis Mode - Input Textareas */}
              {mode === 'legal' && !legalResults && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.5 }}
                  className="space-y-6"
                >
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Narrative Input */}
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <h3 className="text-lg font-semibold text-gray-900">Your Narrative</h3>
                      </div>
                      <textarea
                        value={narrative}
                        onChange={(e) => setNarrative(e.target.value)}
                        className="w-full h-72 p-6 rounded-2xl border-2 border-gray-200 focus:border-blue-400 focus:ring-4 focus:ring-blue-100 bg-white/90 backdrop-blur-sm shadow-lg transition-all duration-200 resize-none text-gray-800 placeholder-gray-400"
                        placeholder="Enter your narrative here..."
                      />
                    </div>

                    {/* Petition Input */}
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <FileCheck className="w-5 h-5 text-purple-600" />
                        <h3 className="text-lg font-semibold text-gray-900">Opponent's Petition</h3>
                      </div>
                      <textarea
                        value={petition}
                        onChange={(e) => setPetition(e.target.value)}
                        className="w-full h-72 p-6 rounded-2xl border-2 border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-100 bg-white/90 backdrop-blur-sm shadow-lg transition-all duration-200 resize-none text-gray-800 placeholder-gray-400"
                        placeholder="Enter opponent's petition here..."
                      />
                    </div>
                  </div>

                  {/* Analyze Button */}
                  <div className="flex justify-center mt-8">
                    <Button
                      onClick={handleLegalAnalysis}
                      disabled={isLoading || !narrative.trim() || !petition.trim()}
                      className="bg-gradient-to-r from-purple-500 to-violet-600 hover:from-purple-600 hover:to-violet-700 text-white px-8 py-4 rounded-2xl font-semibold shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3"
                    >
                      {isLoading ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <Scale className="w-5 h-5" />
                          Run Multi-Agent Analysis
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Loading Animation */}
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex flex-col items-center mt-8"
                    >
                      <SiriAnimation width={100} height={100} />
                      <p className="mt-4 text-gray-600 font-medium">Analyzing your legal documents...</p>
                    </motion.div>
                  )}
                </motion.div>
              )}

              {/* Legal Analysis Results */}
              {mode === 'legal' && legalResults && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-6"
                >
                  {/* Back Button */}
                  <div className="flex justify-between items-center">
                    <Button
                      onClick={() => setLegalResults(null)}
                      className="bg-blue-50 hover:bg-blue-100 text-blue-700 px-6 py-3 rounded-xl border border-blue-200 hover:border-blue-300 transition-all duration-200 hover:scale-105 active:scale-95 shadow-sm hover:shadow-md"
                    >
                      New Analysis
                    </Button>
                  </div>

                  {/* Results Tabs */}
                  <div className="flex gap-2 overflow-x-auto pb-2">
                    {[
                      { id: 'summary', label: 'Executive Summary', icon: ClipboardList },
                      { id: 'entities', label: 'Entities & Claims', icon: Users },
                      { id: 'issues', label: 'Legal Issues', icon: BarChart3 },
                      { id: 'laws', label: 'Relevant Laws', icon: FileText },
                      { id: 'commentary', label: 'Commentary', icon: MessageSquare },
                      { id: 'documents', label: 'Documents', icon: FileText },
                      { id: 'judgment', label: 'Judgment', icon: Scale }
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveResultTab(tab.id as any)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl font-medium whitespace-nowrap transition-all duration-200 ${
                          activeResultTab === tab.id
                            ? 'bg-gradient-to-r from-purple-500 to-violet-600 text-white shadow-lg'
                            : 'bg-white/90 text-gray-700 border border-gray-200 hover:border-purple-300 hover:shadow-md'
                        }`}
                      >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Results Content */}
                  <div className="bg-white/90 backdrop-blur-sm rounded-xl border border-gray-200 shadow-lg p-6">
                    {/* Executive Summary */}
                    {activeResultTab === 'summary' && legalResults.results && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">Executive Summary</h3>

                        {/* Status */}
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <span className="font-semibold text-green-900">Status: {legalResults.status}</span>
                          </div>
                        </div>

                        {/* Key Metrics */}
                        {legalResults.results.case_analysis && (
                          <div className="grid grid-cols-3 gap-4">
                            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                              <div className="text-2xl font-bold text-blue-900">
                                {legalResults.results.case_analysis.legal_issues?.length || 0}
                              </div>
                              <div className="text-sm text-blue-700">Legal Issues Found</div>
                            </div>
                            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                              <div className="text-2xl font-bold text-green-900">
                                {legalResults.results.case_analysis.strengths?.length || 0}
                              </div>
                              <div className="text-sm text-green-700">Strengths</div>
                            </div>
                            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                              <div className="text-2xl font-bold text-red-900">
                                {legalResults.results.case_analysis.weaknesses?.length || 0}
                              </div>
                              <div className="text-sm text-red-700">Weaknesses</div>
                            </div>
                          </div>
                        )}

                        {/* Key Findings */}
                        {legalResults.results.case_analysis?.summary && (
                          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <h4 className="font-semibold text-gray-900 mb-2">Case Summary</h4>
                            <p className="text-gray-700 whitespace-pre-wrap">{legalResults.results.case_analysis.summary}</p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Entities & Claims */}
                    {activeResultTab === 'entities' && legalResults.results?.processed_data && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">Entities & Claims</h3>

                        {/* Narrative Entities */}
                        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                          <h4 className="font-semibold text-blue-900 mb-3">Narrative Entities</h4>
                          <div className="space-y-2">
                            {legalResults.results.processed_data.narrative?.entities ? (
                              Object.entries(legalResults.results.processed_data.narrative.entities).map(([entityType, entities]: [string, any]) => (
                                entities.length > 0 && (
                                  <div key={entityType} className="mb-3">
                                    <h5 className="text-sm font-medium text-blue-800 mb-2">{entityType}</h5>
                                    <div className="flex flex-wrap gap-2">
                                      {entities.map((entity: any, idx: number) => (
                                        <div key={idx} className="bg-white rounded px-3 py-2 text-sm border border-blue-200">
                                          <span className="font-medium text-blue-900">{entity.text}</span>
                                          <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{entityType}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )
                              ))
                            ) : (
                              <div className="text-sm text-gray-500 italic">No entities extracted from narrative</div>
                            )}
                          </div>
                        </div>

                        {/* Petition Entities */}
                        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                          <h4 className="font-semibold text-purple-900 mb-3">Petition Entities</h4>
                          <div className="space-y-2">
                            {legalResults.results.processed_data.petition?.entities ? (
                              Object.entries(legalResults.results.processed_data.petition.entities).map(([entityType, entities]: [string, any]) => (
                                entities.length > 0 && (
                                  <div key={entityType} className="mb-3">
                                    <h5 className="text-sm font-medium text-purple-800 mb-2">{entityType}</h5>
                                    <div className="flex flex-wrap gap-2">
                                      {entities.map((entity: any, idx: number) => (
                                        <div key={idx} className="bg-white rounded px-3 py-2 text-sm border border-purple-200">
                                          <span className="font-medium text-purple-900">{entity.text}</span>
                                          <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">{entityType}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )
                              ))
                            ) : (
                              <div className="text-sm text-gray-500 italic">No entities extracted from petition</div>
                            )}
                          </div>
                        </div>

                        {/* Claims Comparison */}
                        <div className="grid md:grid-cols-2 gap-4">
                          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <h4 className="font-semibold text-gray-900 mb-2">Narrative Claims ({legalResults.results.processed_data.narrative?.claims?.length || 0})</h4>
                            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                              {legalResults.results.processed_data.narrative?.claims?.map((claim: any, idx: number) => (
                                <li key={idx}>
                                  {typeof claim === 'string' ? claim : claim.text || claim.description || JSON.stringify(claim)}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <h4 className="font-semibold text-gray-900 mb-2">Petition Claims ({legalResults.results.processed_data.petition?.claims?.length || 0})</h4>
                            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                              {legalResults.results.processed_data.petition?.claims?.map((claim: any, idx: number) => (
                                <li key={idx}>
                                  {typeof claim === 'string' ? claim : claim.text || claim.description || JSON.stringify(claim)}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* Inconsistencies */}
                        {legalResults.results.processed_data?.inconsistencies && legalResults.results.processed_data.inconsistencies.length > 0 && (
                          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                            <h4 className="font-semibold text-red-900 mb-3">⚠️ Identified Inconsistencies</h4>
                            <div className="space-y-2">
                              {legalResults.results.processed_data.inconsistencies.map((inc: any, idx: number) => (
                                <div key={idx} className="bg-white rounded px-3 py-2 text-sm border border-red-200">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`text-xs px-2 py-1 rounded ${
                                      inc.severity === 'high' ? 'bg-red-100 text-red-700' :
                                      inc.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                      'bg-gray-100 text-gray-700'
                                    }`}>
                                      {inc.severity || 'low'}
                                    </span>
                                    <span className="font-medium text-red-900">{inc.type || 'Inconsistency'}</span>
                                  </div>
                                  <p className="text-gray-700">{inc.description}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Legal Issues */}
                    {activeResultTab === 'issues' && legalResults.results?.case_analysis && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">Legal Issues Analysis</h3>

                        {/* Legal Issues List */}
                        <div className="space-y-3">
                          {legalResults.results.case_analysis.legal_issues?.map((issue: any, idx: number) => (
                            <div key={idx} className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                              <div className="flex items-start gap-3">
                                <div className="w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold flex-shrink-0">
                                  {idx + 1}
                                </div>
                                <div className="flex-1">
                                  <h4 className="font-semibold text-orange-900 mb-1">{issue.issue || issue.title || issue.description}</h4>
                                  {issue.category && (
                                    <span className="inline-block text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded mb-2">
                                      {issue.category}
                                    </span>
                                  )}
                                  {issue.details && <p className="text-sm text-gray-700 mt-2">{issue.details}</p>}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Strengths & Weaknesses */}
                        <div className="grid md:grid-cols-2 gap-4 mt-6">
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <h4 className="font-semibold text-green-900 mb-3">Strengths</h4>
                            <ul className="space-y-2">
                              {legalResults.results.case_analysis.strengths?.map((strength: any, idx: number) => (
                                <li key={idx} className="text-sm text-gray-700">
                                  <span className="text-green-600 mr-2">✓</span>
                                  {typeof strength === 'string' ? strength : strength.description || strength.point}
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                            <h4 className="font-semibold text-red-900 mb-3">Weaknesses</h4>
                            <ul className="space-y-2">
                              {legalResults.results.case_analysis.weaknesses?.map((weakness: any, idx: number) => (
                                <li key={idx} className="text-sm text-gray-700">
                                  <span className="text-red-600 mr-2">⚠</span>
                                  {typeof weakness === 'string' ? weakness : weakness.description || weakness.point}
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Relevant Laws */}
                    {activeResultTab === 'laws' && legalResults.results?.law_retrieval && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">Relevant Legal Provisions</h3>

                        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200 mb-4">
                          <div className="text-lg font-bold text-blue-900">
                            {legalResults.results.law_retrieval.all_relevant_sections?.length || 0} Sections Retrieved
                          </div>
                        </div>

                        {/* Law Sections */}
                        <div className="space-y-3">
                          {legalResults.results.law_retrieval.all_relevant_sections?.map((section: any, idx: number) => (
                            <div key={idx} className="bg-white rounded-lg p-4 border-l-4 border-blue-500 shadow-sm">
                              <div className="flex items-start justify-between mb-2">
                                <h4 className="font-semibold text-gray-900">{section.title || `Section ${idx + 1}`}</h4>
                                {section.score && (
                                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                    Relevance: {(section.score * 100).toFixed(0)}%
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-700 whitespace-pre-wrap">{section.text || section.content}</p>
                              {section.metadata && (
                                <div className="mt-2 text-xs text-gray-500">
                                  {section.metadata.section && `Section: ${section.metadata.section}`}
                                  {section.metadata.chapter && ` | Chapter: ${section.metadata.chapter}`}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Legal Commentary */}
                    {activeResultTab === 'commentary' && legalResults.results?.commentary && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">Legal Commentary</h3>

                        {/* Petition Critique */}
                        {legalResults.results.commentary.petition_critique && (
                          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                            <h4 className="font-semibold text-purple-900 mb-3">Petition Critique</h4>
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">
                              {typeof legalResults.results.commentary.petition_critique === 'string'
                                ? legalResults.results.commentary.petition_critique
                                : legalResults.results.commentary.petition_critique?.text || 
                                  legalResults.results.commentary.petition_critique?.description ||
                                  'No critique available'}
                            </div>
                          </div>
                        )}

                        {/* Counter Arguments */}
                        {legalResults.results.commentary.counter_arguments && (
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <h4 className="font-semibold text-green-900 mb-3">Counter Arguments</h4>
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">
                              {typeof legalResults.results.commentary.counter_arguments === 'string'
                                ? legalResults.results.commentary.counter_arguments
                                : legalResults.results.commentary.counter_arguments?.text ||
                                  legalResults.results.commentary.counter_arguments?.description ||
                                  'No counter arguments available'}
                            </div>
                          </div>
                        )}

                        {/* Strategic Recommendations */}
                        {legalResults.results.commentary.recommendations && (
                          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <h4 className="font-semibold text-blue-900 mb-3">Strategic Recommendations</h4>
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">
                              {typeof legalResults.results.commentary.recommendations === 'string'
                                ? legalResults.results.commentary.recommendations
                                : legalResults.results.commentary.recommendations?.strategic_recommendations ||
                                  legalResults.results.commentary.recommendations?.text ||
                                  legalResults.results.commentary.recommendations?.description ||
                                  'No recommendations available'}
                            </div>
                          </div>
                        )}

                        {/* Procedural Guidance */}
                        {legalResults.results.commentary.procedural_guidance && (
                          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                            <h4 className="font-semibold text-yellow-900 mb-3">Procedural Guidance</h4>
                            <div className="text-sm text-gray-700">
                              {legalResults.results.commentary.procedural_guidance.steps ? (
                                <ol className="list-decimal list-inside space-y-2">
                                  {legalResults.results.commentary.procedural_guidance.steps.map((step: any, idx: number) => (
                                    <li key={idx} className="mb-2">
                                      <span className="font-medium">{step.action || step.step || step}</span>
                                      {step.statutory_basis && (
                                        <div className="text-xs text-gray-500 mt-1">
                                          Statutory Basis: {step.statutory_basis}
                                        </div>
                                      )}
                                    </li>
                                  ))}
                                </ol>
                              ) : (
                                <div className="whitespace-pre-wrap">
                                  {typeof legalResults.results.commentary.procedural_guidance === 'string'
                                    ? legalResults.results.commentary.procedural_guidance
                                    : legalResults.results.commentary.procedural_guidance?.text ||
                                      legalResults.results.commentary.procedural_guidance?.description ||
                                      'No procedural guidance available'}
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Legal Conclusion/Judgment */}
                        {legalResults.results.commentary.legal_conclusion && (
                          <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                            <h4 className="font-semibold text-indigo-900 mb-3">⚖️ Legal Conclusion</h4>
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">
                              {typeof legalResults.results.commentary.legal_conclusion === 'string'
                                ? legalResults.results.commentary.legal_conclusion
                                : legalResults.results.commentary.legal_conclusion?.text ||
                                  legalResults.results.commentary.legal_conclusion?.judgment ||
                                  legalResults.results.commentary.legal_conclusion?.description ||
                                  'No legal conclusion available'}
                            </div>
                            {legalResults.results.commentary.legal_conclusion?.law_sections_used && (
                              <div className="mt-3 pt-3 border-t border-indigo-200">
                                <h5 className="text-xs font-medium text-indigo-800 mb-2">Referenced Legal Provisions:</h5>
                                <ul className="text-xs text-gray-600 space-y-1">
                                  {legalResults.results.commentary.legal_conclusion.law_sections_used.map((section: string, idx: number) => (
                                    <li key={idx}>• {section}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Documents */}
                    {activeResultTab === 'documents' && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">📋 Generated Documents</h3>
                        
                        {/* Document Generation Status */}
                        {legalResults.results && (
                          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <div className="flex items-center gap-2 mb-2">
                              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                              <span className="font-semibold text-green-900">Analysis Complete - Documents Ready for Generation</span>
                            </div>
                            <p className="text-sm text-green-700">
                              Based on your narrative and petition analysis, you can now generate formal legal documents.
                            </p>
                          </div>
                        )}

                        {/* Generated Documents Display */}
                        {legalResults.results && (
                          <div className="space-y-4">
                            {/* Plaint/Petition */}
                            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                              <div className="flex items-center justify-between mb-3">
                                <div>
                                  <h4 className="font-semibold text-gray-900">📄 Plaint/Petition</h4>
                                  <p className="text-sm text-gray-600">Formal legal complaint document</p>
                                </div>
                                <div className="flex gap-2">
                                  <button 
                                    onClick={() => generateDocument('plaint')}
                                    className="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600 transition-colors"
                                  >
                                    Generate
                                  </button>
                                </div>
                              </div>
                              <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 min-h-[100px]">
                                {legalResults.results.commentary?.petition_critique ? (
                                  <div className="whitespace-pre-wrap">
                                    {typeof legalResults.results.commentary.petition_critique === 'string'
                                      ? legalResults.results.commentary.petition_critique
                                      : legalResults.results.commentary.petition_critique?.text || 
                                        legalResults.results.commentary.petition_critique?.description ||
                                        'Generating petition critique...'}
                                  </div>
                                ) : (
                                  <div className="text-gray-500 italic">Click Generate to create your plaint/petition document</div>
                                )}
                              </div>
                              <div className="flex gap-2 mt-3">
                                <button 
                                  onClick={() => downloadDocument('plaint', 'txt')}
                                  className="bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600 transition-colors"
                                >
                                  📥 Download TXT
                                </button>
                                <button 
                                  onClick={() => downloadDocument('plaint', 'pdf')}
                                  className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600 transition-colors"
                                >
                                  📄 Download PDF
                                </button>
                              </div>
                            </div>

                            {/* Written Statement */}
                            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                              <div className="flex items-center justify-between mb-3">
                                <div>
                                  <h4 className="font-semibold text-gray-900">📝 Written Statement</h4>
                                  <p className="text-sm text-gray-600">Defense response document</p>
                                </div>
                                <div className="flex gap-2">
                                  <button 
                                    onClick={() => generateDocument('statement')}
                                    className="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600 transition-colors"
                                  >
                                    Generate
                                  </button>
                                </div>
                              </div>
                              <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 min-h-[100px]">
                                {legalResults.results.commentary?.counter_arguments ? (
                                  <div className="whitespace-pre-wrap">
                                    {typeof legalResults.results.commentary.counter_arguments === 'string'
                                      ? legalResults.results.commentary.counter_arguments
                                      : legalResults.results.commentary.counter_arguments?.text ||
                                        legalResults.results.commentary.counter_arguments?.description ||
                                        'Generating counter arguments...'}
                                  </div>
                                ) : (
                                  <div className="text-gray-500 italic">Click Generate to create your written statement</div>
                                )}
                              </div>
                              <div className="flex gap-2 mt-3">
                                <button 
                                  onClick={() => downloadDocument('statement', 'txt')}
                                  className="bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600 transition-colors"
                                >
                                  📥 Download TXT
                                </button>
                                <button 
                                  onClick={() => downloadDocument('statement', 'pdf')}
                                  className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600 transition-colors"
                                >
                                  📄 Download PDF
                                </button>
                              </div>
                            </div>

                            {/* Appeal */}
                            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
                              <div className="flex items-center justify-between mb-3">
                                <div>
                                  <h4 className="font-semibold text-gray-900">⚖️ Appeal</h4>
                                  <p className="text-sm text-gray-600">Appeal against court decision</p>
                                </div>
                                <div className="flex gap-2">
                                  <button 
                                    onClick={() => generateDocument('appeal')}
                                    className="bg-blue-500 text-white px-4 py-2 rounded text-sm hover:bg-blue-600 transition-colors"
                                  >
                                    Generate
                                  </button>
                                </div>
                              </div>
                              <div className="bg-gray-50 rounded p-3 text-sm text-gray-700 min-h-[100px]">
                                {legalResults.results.commentary?.legal_conclusion ? (
                                  <div className="whitespace-pre-wrap">
                                    {typeof legalResults.results.commentary.legal_conclusion === 'string'
                                      ? legalResults.results.commentary.legal_conclusion
                                      : legalResults.results.commentary.legal_conclusion?.text ||
                                        legalResults.results.commentary.legal_conclusion?.judgment ||
                                        legalResults.results.commentary.legal_conclusion?.description ||
                                        'Generating legal conclusion...'}
                                  </div>
                                ) : (
                                  <div className="text-gray-500 italic">Click Generate to create your appeal document</div>
                                )}
                              </div>
                              <div className="flex gap-2 mt-3">
                                <button 
                                  onClick={() => downloadDocument('appeal', 'txt')}
                                  className="bg-green-500 text-white px-3 py-1 rounded text-xs hover:bg-green-600 transition-colors"
                                >
                                  📥 Download TXT
                                </button>
                                <button 
                                  onClick={() => downloadDocument('appeal', 'pdf')}
                                  className="bg-red-500 text-white px-3 py-1 rounded text-xs hover:bg-red-600 transition-colors"
                                >
                                  📄 Download PDF
                                </button>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Document Generation Options */}
                        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                          <h4 className="font-semibold text-yellow-900 mb-3">📄 Document Generation Options</h4>
                          <div className="space-y-3">
                            <label className="flex items-center gap-2">
                              <input type="checkbox" className="rounded" defaultChecked />
                              <span className="text-sm text-gray-700">Enhanced formatting with sophisticated legal language</span>
                            </label>
                            <label className="flex items-center gap-2">
                              <input type="checkbox" className="rounded" defaultChecked />
                              <span className="text-sm text-gray-700">Generate PDF versions for download</span>
                            </label>
                            <label className="flex items-center gap-2">
                              <input type="checkbox" className="rounded" defaultChecked />
                              <span className="text-sm text-gray-700">Include statutory citations and references</span>
                            </label>
                          </div>
                        </div>

                        {/* Download All Options */}
                        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
                          <h4 className="font-semibold text-purple-900 mb-3 flex items-center gap-2">
                            <Download className="w-5 h-5" />
                            Download All Documents
                          </h4>
                          <p className="text-sm text-purple-700 mb-4">
                            Download all three legal documents at once in your preferred format
                          </p>
                          <div className="grid md:grid-cols-2 gap-3">
                            {/* Download All as Separate Files */}
                            <div className="space-y-2">
                              <h5 className="font-medium text-purple-800 text-sm">Download Separately</h5>
                              <div className="flex gap-2">
                                <button 
                                  onClick={() => downloadAllDocuments('txt', false)}
                                  className="flex-1 bg-green-500 text-white px-3 py-2 rounded text-sm hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <Download className="w-4 h-4" />
                                  All TXT Files
                                </button>
                                <button 
                                  onClick={() => downloadAllDocuments('pdf', false)}
                                  className="flex-1 bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <Download className="w-4 h-4" />
                                  All PDF Files
                                </button>
                              </div>
                            </div>
                            
                            {/* Download All as ZIP */}
                            <div className="space-y-2">
                              <h5 className="font-medium text-purple-800 text-sm">Download as ZIP</h5>
                              <div className="flex gap-2">
                                <button 
                                  onClick={() => downloadAllDocuments('txt', true)}
                                  className="flex-1 bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <Download className="w-4 h-4" />
                                  TXT ZIP
                                </button>
                                <button 
                                  onClick={() => downloadAllDocuments('pdf', true)}
                                  className="flex-1 bg-indigo-500 text-white px-3 py-2 rounded text-sm hover:bg-indigo-600 transition-colors flex items-center justify-center gap-2"
                                >
                                  <Download className="w-4 h-4" />
                                  PDF ZIP
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Document Generation Info */}
                        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                          <h4 className="font-semibold text-gray-900 mb-3">ℹ️ Document Generation Info</h4>
                          <div className="text-sm text-gray-700 space-y-2">
                            <p>• Documents are generated based on your narrative and petition analysis</p>
                            <p>• All documents follow Pakistani legal formatting standards</p>
                            <p>• Generated documents can be downloaded in TXT or PDF format</p>
                            <p>• Documents include proper legal citations and statutory references</p>
                            <p>• PDF generation uses professional legal document formatting</p>
                            <p>• ZIP downloads include all three documents in a single archive</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Judgment */}
                    {activeResultTab === 'judgment' && (
                      <div className="space-y-4">
                        <h3 className="text-xl font-bold text-gray-900 mb-4">⚖️ Legal Judgment</h3>
                        
                        {legalResults.results?.commentary?.legal_conclusion ? (
                          <div className="space-y-4">
                            {/* Judgment Header */}
                            <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                              <div className="flex items-center gap-2 mb-2">
                                <Scale className="w-5 h-5 text-indigo-600" />
                                <h4 className="font-semibold text-indigo-900">Comprehensive Legal Judgment</h4>
                              </div>
                              <div className="text-sm text-gray-600">
                                Generated: {legalResults.results.commentary.legal_conclusion.generated_at || 'N/A'} | 
                                Issues Addressed: {legalResults.results.commentary.legal_conclusion.issues_addressed || 0} | 
                                Statutory Provisions: {legalResults.results.commentary.legal_conclusion.law_sections_used?.length || 0}
                              </div>
                            </div>

                            {/* Judgment Text */}
                            <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
                              <div className="prose prose-sm max-w-none">
                                <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                                  {typeof legalResults.results.commentary.legal_conclusion === 'string'
                                    ? legalResults.results.commentary.legal_conclusion
                                    : legalResults.results.commentary.legal_conclusion?.text ||
                                      legalResults.results.commentary.legal_conclusion?.judgment ||
                                      legalResults.results.commentary.legal_conclusion?.description ||
                                      'No judgment text available'}
                                </div>
                              </div>
                            </div>

                            {/* Statutory Provisions */}
                            {legalResults.results.commentary.legal_conclusion?.law_sections_used && (
                              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                                <h4 className="font-semibold text-green-900 mb-3">📚 Statutory Provisions Referenced</h4>
                                <div className="space-y-2">
                                  {legalResults.results.commentary.legal_conclusion.law_sections_used.map((citation: string, idx: number) => (
                                    <div key={idx} className="bg-white rounded px-3 py-2 text-sm border border-green-200">
                                      <span className="font-medium text-green-900">{idx + 1}.</span>
                                      <span className="ml-2 text-gray-700">{citation}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Decision Summary */}
                            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                              <h4 className="font-semibold text-purple-900 mb-3">📊 Decision Summary</h4>
                              <div className="grid md:grid-cols-2 gap-4">
                                <div className="bg-white rounded p-3 border border-purple-200">
                                  <h5 className="font-medium text-purple-900 mb-1">Primary Decision</h5>
                                  <p className="text-sm text-gray-700">
                                    {legalResults.results.commentary.legal_conclusion?.decision || 'Decision pending analysis'}
                                  </p>
                                </div>
                                <div className="bg-white rounded p-3 border border-purple-200">
                                  <h5 className="font-medium text-purple-900 mb-1">Confidence Level</h5>
                                  <p className="text-sm text-gray-700">
                                    {legalResults.results.commentary.legal_conclusion?.confidence || 'High'}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 text-center">
                            <Scale className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                            <h4 className="font-semibold text-gray-900 mb-2">No Judgment Available</h4>
                            <p className="text-sm text-gray-600 mb-4">
                              Complete the legal analysis to generate a comprehensive judgment based on your case details.
                            </p>
                            <button 
                              onClick={() => setActiveResultTab('summary')}
                              className="bg-purple-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-600 transition-colors"
                            >
                              View Analysis Results
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

            </div>
          </motion.div>
        ) : (
          /* Chat Messages */
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="flex-1 overflow-y-auto bg-gradient-to-b from-gray-50/30 to-white/50 relative z-10"
            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
          >
            <style>{`
              .chat-scroll::-webkit-scrollbar {
                display: none;
              }
            `}</style>
            {/* Home Button */}
            <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-xl border-b border-gray-100/60 p-4">
              <div className="max-w-3xl mx-auto flex justify-between items-center">
                <motion.button
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  onClick={handleReturnHome}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-xl border border-blue-200/60 hover:border-blue-300/60 transition-all duration-200 hover:scale-105 active:scale-95 shadow-sm hover:shadow-md"
                >
                  <Home className="w-4 h-4" />
                  <span className="font-medium text-sm">Return to Home</span>
                </motion.button>
                <div className="text-sm text-gray-500 font-medium">
                  {currentSessionId && chatSessions.find(s => s.id === currentSessionId)?.title}
                </div>
              </div>
            </div>
            <div className="max-w-3xl mx-auto p-6">
              {messages.map((message, index) => (
                <ChatMessageComponent 
                  key={message.id} 
                  message={message} 
                  index={index} 
                  onActionResponse={handleActionResponse}
                />
              ))}
              <AnimatePresence>
                {isLoading && <TypingIndicator />}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          </motion.div>
        )}

        {/* Input Area - Only show in chat mode */}
        {mode === 'chat' && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="border-t border-gray-100/60 bg-white/80 backdrop-blur-xl p-6"
          >
            <div className="max-w-3xl mx-auto">
              {/* Web Search Toggle */}
              <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setWebSearchEnabled(!webSearchEnabled)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition-all duration-200 ${
                    webSearchEnabled 
                      ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 text-green-700 shadow-sm' 
                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Search className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    {webSearchEnabled ? 'Web Search: ON' : 'Web Search: OFF'}
                  </span>
                </motion.button>
                {webSearchEnabled && (
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-xs text-green-600 font-medium"
                  >
                    Searching web + local knowledge
                  </motion.div>
                )}
              </div>
            </div>
            
            <div className="flex gap-4 items-end">
              <div className="flex-1 relative">
                <motion.div
                  whileFocus={{ scale: 1.01 }}
                  className="relative"
                >
                  <Input
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="w-full p-5 pr-14 border border-gray-200/60 rounded-2xl focus:border-blue-300/60 focus:ring-2 focus:ring-blue-100/60 resize-none bg-white/90 backdrop-blur-sm shadow-sm hover:shadow-md transition-all duration-200 ease-out text-gray-800 placeholder-gray-400 font-medium"
                    placeholder={webSearchEnabled ? "Ask me anything - I'll search the web and local knowledge..." : "Ask me anything about government services..."}
                    disabled={isLoading}
                  />
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Button 
                      onClick={() => handleSendMessage()}
                      disabled={!inputValue.trim() || isLoading}
                      className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white p-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 ease-out disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
                    >
                      <Send className="w-4.5 h-4.5" />
                    </Button>
                  </div>
                </motion.div>
              </div>
            </div>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-xs text-gray-400 mt-4 text-center font-medium"
            > 
              GovTech can make mistakes. Consider checking important information.
            </motion.div>
          </div>
        </motion.div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Chat</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{chatSessions.find(s => s.id === sessionToDelete)?.title || 'this chat'}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDeleteSession}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};