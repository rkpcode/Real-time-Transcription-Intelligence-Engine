'use client';

import { useEffect, useState, useRef } from 'react';

interface Transcript {
    text: string;
    is_final: boolean;
    confidence: number;
    timestamp: number;
}

interface Hint {
    text: string;
    question: string;
    timestamp: number;
}

export default function StealthPrompter() {
    const [connected, setConnected] = useState(false);
    const [transcripts, setTranscripts] = useState<Transcript[]>([]);
    const [hints, setHints] = useState<Hint[]>([]);
    const [currentHint, setCurrentHint] = useState<Hint | null>(null);
    const [interimText, setInterimText] = useState('');

    const wsRef = useRef<WebSocket | null>(null);
    const transcriptEndRef = useRef<HTMLDivElement>(null);
    const hintEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Connect to WebSocket server
        const connectWebSocket = () => {
            // Change this to your receiver server IP if on different device
            const wsUrl = 'ws://localhost:8000/ws/ui';

            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('Connected to receiver');
                setConnected(true);
            };

            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                handleMessage(message);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setConnected(false);
            };

            ws.onclose = () => {
                console.log('Disconnected from receiver');
                setConnected(false);

                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            };

            wsRef.current = ws;
        };

        connectWebSocket();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const handleMessage = (message: any) => {
        switch (message.type) {
            case 'transcript':
                const data = message.data;

                if (data.is_final) {
                    // Add to transcripts
                    setTranscripts(prev => [...prev.slice(-10), data]);
                    setInterimText('');
                } else {
                    // Update interim text
                    setInterimText(data.text);
                }
                break;

            case 'hint':
                const hint = message.data;
                setHints(prev => [...prev.slice(-5), hint]);
                setCurrentHint(hint);

                // Vibrate if supported (mobile)
                if ('vibrate' in navigator) {
                    navigator.vibrate(200);
                }
                break;

            case 'status':
                console.log('Status:', message.data);
                break;
        }
    };

    const clearAll = () => {
        setTranscripts([]);
        setHints([]);
        setCurrentHint(null);
        setInterimText('');

        // Send clear context to server
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'clear_context' }));
        }
    };

    // Auto-scroll
    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcripts, interimText]);

    useEffect(() => {
        hintEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [hints]);

    return (
        <div className="min-h-screen bg-black text-white flex flex-col">
            {/* Header */}
            <div className="bg-gray-900 border-b border-gray-800 p-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <h1 className="text-lg font-bold">Stealth Prompter</h1>
                </div>
                <button
                    onClick={clearAll}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium transition"
                >
                    Clear
                </button>
            </div>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden flex flex-col">
                {/* Current Hint - Prominent Display */}
                {currentHint && (
                    <div className="bg-gradient-to-r from-purple-900 to-blue-900 p-6 border-b border-purple-700 animate-fadeIn">
                        <div className="text-xs text-purple-300 mb-2">💡 AI HINT</div>
                        <div className="text-2xl font-bold leading-tight mb-2">
                            {currentHint.text}
                        </div>
                        <div className="text-xs text-purple-400 italic">
                            Q: {currentHint.question}
                        </div>
                    </div>
                )}

                {/* Transcript Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                    {transcripts.length === 0 && !interimText && (
                        <div className="text-center text-gray-500 mt-20">
                            <div className="text-4xl mb-4">🎙️</div>
                            <p>Waiting for audio...</p>
                            <p className="text-sm mt-2">Start your interview to see transcripts</p>
                        </div>
                    )}

                    {transcripts.map((t, idx) => (
                        <div
                            key={idx}
                            className="bg-gray-900 rounded-lg p-3 border-l-4 border-blue-500"
                        >
                            <div className="text-sm leading-relaxed">{t.text}</div>
                            <div className="text-xs text-gray-500 mt-2 flex justify-between">
                                <span>Confidence: {(t.confidence * 100).toFixed(0)}%</span>
                                <span>{new Date(t.timestamp * 1000).toLocaleTimeString()}</span>
                            </div>
                        </div>
                    ))}

                    {interimText && (
                        <div className="bg-gray-800 rounded-lg p-3 border-l-4 border-yellow-500 opacity-70">
                            <div className="text-sm leading-relaxed italic">{interimText}</div>
                            <div className="text-xs text-yellow-500 mt-2">Interim...</div>
                        </div>
                    )}

                    <div ref={transcriptEndRef} />
                </div>

                {/* Previous Hints */}
                {hints.length > 1 && (
                    <div className="bg-gray-900 border-t border-gray-800 p-4 max-h-40 overflow-y-auto">
                        <div className="text-xs text-gray-500 mb-2">Previous Hints</div>
                        <div className="space-y-2">
                            {hints.slice(0, -1).reverse().map((hint, idx) => (
                                <div key={idx} className="text-sm text-gray-400 border-l-2 border-gray-700 pl-2">
                                    {hint.text}
                                </div>
                            ))}
                        </div>
                        <div ref={hintEndRef} />
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="bg-gray-900 border-t border-gray-800 p-3 text-center">
                <div className="text-xs text-gray-500">
                    {connected ? '🟢 Live' : '🔴 Disconnected'} • Interview Sathi v2.0
                </div>
            </div>
        </div>
    );
}
