import React, { useState, useEffect, useRef } from 'react';

const Solve = ({ navigate, accessToken, initialQuery, userEmail, onClearQuery, user }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isThinking, setIsThinking] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const chatContainerRef = useRef(null);
    const sessionInitialized = useRef(false);
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';


    const formatMessage = (content) => {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
            .replace(/\n/g, '<br>') // Line breaks
            .replace(/• /g, '• ') // Bullet points
            .replace(/\d+\. /g, (match) => `<br>${match}`) // Numbered lists
            .replace(/<br><br>/g, '<br>'); // Remove double breaks
    };

    // Auto-scroll to bottom of chat
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages, isThinking]);

    // Initialize session when component loads
    useEffect(() => {
        if (!sessionInitialized.current && userEmail) {
            initializeSession();
            sessionInitialized.current = true;
        }
    }, [userEmail]);

    const initializeSession = async () => {
        try {
            // Create new session
            const sessionRes = await fetch(`${API_URL}/create_session`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_email: userEmail })
            });
            const sessionData = await sessionRes.json();

            if (sessionData.session_id) {
                setSessionId(sessionData.session_id);

                // Send introduction message after session is created
                const userName = user?.name || user?.given_name || userEmail.split('@')[0];
                const introMessage = `Hi, I'm ${userName} and my email is ${userEmail}. I'm using SmartSolve dashboard to manage my tasks, calendar events, and get AI assistance. Please remember my details for our conversation.`;

                // Wait a bit to ensure session is set
                setTimeout(() => {
                    sendMessageToAgent(introMessage, sessionData.session_id, true);
                }, 100);
            }
        } catch (error) {
            console.error('Session initialization error:', error);
        }
    };

    const sendMessageToAgent = async (message, currentSessionId = null, isIntro = false) => {
        const useSessionId = currentSessionId || sessionId;
        setIsThinking(true);
        try {
            const res = await fetch(`${API_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    user_email: userEmail,
                    session_id: useSessionId,
                    history: messages.map(m => ({ role: m.role, content: m.content }))
                })
            });
            const data = await res.json();

            if (data.content) {
                const aiResponse = {
                    id: Date.now() + 1,
                    role: 'assistant',
                    name: 'SmartSolve',
                    content: data.content,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                };

                if (isIntro) {
                    // For intro, only add AI response
                    setMessages([aiResponse]);
                } else {
                    // For regular messages, add user message first, then AI response
                    const userMessage = {
                        id: Date.now(),
                        role: 'user',
                        content: message,
                        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    };
                    setMessages(prev => [...prev, userMessage, aiResponse]);
                }
            } else {
                throw new Error(data.error || "Failed to get AI response");
            }
        } catch (error) {
            console.error("Chat Error:", error);
            const errorMsg = {
                id: Date.now() + 2,
                role: 'assistant',
                name: 'SmartSolve',
                content: "I'm having trouble connecting right now. Please check your backend or ADK agent.",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                isError: true
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsThinking(false);
        }
    };

    // Handle initial query from dashboard
    useEffect(() => {
        if (initialQuery && sessionId) {
            sendMessageToAgent(initialQuery, sessionId, false); // Show user message
            onClearQuery();
        }
    }, [initialQuery, sessionId]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        const userText = input;
        setInput('');
        sendMessageToAgent(userText);
    };

    const handleNewSession = () => {
        setMessages([]);
        setSessionId(null);
        sessionInitialized.current = false;
        initializeSession();
    };

    return (
        <div className="flex flex-col h-full bg-background-light dark:bg-background-dark text-slate-900 dark:text-white overflow-hidden font-display">
            {/* Top App Bar */}
            <header className="shrink-0 flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800/50 z-20">
                <button
                    onClick={() => navigate('dashboard')}
                    className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors text-slate-600 dark:text-slate-300"
                >
                    <span className="material-symbols-outlined">arrow_back_ios_new</span>
                </button>
                <div className="flex flex-col items-center">
                    <h1 className="text-base font-bold leading-tight">Research Agent</h1>
                    <div className="flex items-center gap-1.5">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Online</span>
                    </div>
                </div>
                <button
                    onClick={handleNewSession}
                    className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors text-slate-600 dark:text-slate-300"
                    title="New Session"
                >
                    <span className="material-symbols-outlined">add</span>
                </button>
            </header>

            {/* Chat Stream */}
            <main
                ref={chatContainerRef}
                className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth no-scrollbar"
            >
                {/* Timestamp */}
                <div className="flex justify-center my-4">
                    <span className="text-xs font-medium text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800/50 px-3 py-1 rounded-full">Today</span>
                </div>

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} w-full items-end gap-3`}>
                        {msg.role === 'assistant' && (
                            <div className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
                                <span className="material-symbols-outlined text-white text-[18px]">smart_toy</span>
                            </div>
                        )}
                        <div className={`flex flex-col gap-1 ${msg.role === 'user' ? 'items-end max-w-[85%]' : 'max-w-[90%]'}`}>
                            {msg.role === 'assistant' && (
                                <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">{msg.name}</span>
                            )}
                            <div className={`p-3.5 rounded-2xl shadow-sm ${msg.role === 'user'
                                ? 'bg-primary text-white rounded-tr-none'
                                : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-100 dark:border-slate-800/50 rounded-tl-none'
                                }`}>
                                <p className="text-[15px] leading-relaxed" dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}></p>
                                {msg.chart && (
                                    <div className="mt-3 bg-slate-50 dark:bg-[#151b21] rounded-xl p-3 border border-slate-200 dark:border-slate-700/50">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="material-symbols-outlined text-primary text-sm">trending_up</span>
                                            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Market Growth</span>
                                        </div>
                                        <div className="flex items-baseline gap-2">
                                            <h3 className="text-2xl font-bold text-slate-800 dark:text-white">12.5%</h3>
                                            <span className="text-sm text-green-500 font-medium">+2.1% YoY</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <span className="text-[10px] text-slate-400 dark:text-slate-600 mt-1">{msg.time}</span>
                        </div>
                    </div>
                ))}

                {isThinking && (
                    <div className="flex items-start gap-3 max-w-[90%]">
                        <div className="shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
                            <span className="material-symbols-outlined text-white text-[18px]">smart_toy</span>
                        </div>
                        <div className="flex flex-col gap-1">
                            <div className="bg-white dark:bg-slate-800 px-4 py-3 rounded-2xl rounded-tl-none shadow-sm border border-slate-100 dark:border-slate-800/50 flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce"></span>
                                <span className="w-1.5 h-1.5 rounded-full bg-primary/70 animate-bounce [animation-delay:0.2s]"></span>
                                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:0.4s]"></span>
                            </div>
                        </div>
                    </div>
                )}
                <div className="h-24"></div>
            </main>

            {/* Bottom Actions Area */}
            <div className="shrink-0 z-20 w-full bg-background-light dark:bg-background-dark/95 backdrop-blur-md border-t border-slate-200 dark:border-slate-800/50 pb-safe">
                {/* Composer Input */}
                <div className="px-4 pb-4 pt-1">
                    <form onSubmit={handleSendMessage} className="flex items-end gap-2 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-2 shadow-sm transition-all">
                        <button type="button" className="flex items-center justify-center w-10 h-10 rounded-xl text-slate-400 hover:text-primary transition-colors">
                            <span className="material-symbols-outlined text-[24px]">add_circle</span>
                        </button>
                        <div className="flex-1 min-w-0 py-2.5">
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                className="w-full bg-transparent border-none p-0 text-base text-slate-800 dark:text-white placeholder:text-slate-400 focus:ring-0 outline-none"
                                placeholder="Ask SmartSolve..."
                                type="text"
                            />
                        </div>
                        <div className="flex items-center gap-1">
                            <button type="submit" className="flex items-center justify-center w-10 h-10 rounded-xl bg-primary hover:bg-blue-600 text-white shadow-md transition-all transform active:scale-95">
                                <span className="material-symbols-outlined text-[20px]">arrow_upward</span>
                            </button>
                        </div>
                    </form>
                    <div className="flex justify-center mt-2">
                        <p className="text-[10px] text-slate-400 dark:text-slate-600">SmartSolve can make mistakes. Verify important info.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Solve;