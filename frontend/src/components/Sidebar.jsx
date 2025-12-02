import React, { useState } from 'react';
import { Settings, Lock, Eye, EyeOff } from 'lucide-react';

export function Sidebar({ token, onTokenChange }) {
    const [isOpen, setIsOpen] = useState(false);
    const [showToken, setShowToken] = useState(false);

    return (
        <>
            {/* Sidebar Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed top-6 right-6 sm:top-8 sm:right-8 z-50 p-3 glass-strong rounded-lg hover:bg-primary/10 transition-colors border border-border/50 shadow-lg"
                aria-label="Toggle sidebar"
            >
                <Settings className="w-5 h-5 text-text" />
            </button>

            {/* Sidebar Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar Panel */}
            <div
                className={`fixed top-0 right-0 h-full w-80 sm:w-96 glass-strong border-l border-border shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
                    isOpen ? 'translate-x-0' : 'translate-x-full'
                }`}
            >
                <div className="flex flex-col h-full p-6">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-text flex items-center gap-2">
                            <Lock className="w-5 h-5 text-primary" />
                            Settings
                        </h2>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="text-muted hover:text-text transition-colors"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Token Input Section */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-text mb-2">
                                GitHub Token (for Private Repos)
                            </label>
                            <div className="relative">
                                <input
                                    type={showToken ? 'text' : 'password'}
                                    value={token || ''}
                                    onChange={(e) => onTokenChange(e.target.value)}
                                    placeholder="ghp_xxxxxxxxxxxx"
                                    className="w-full px-4 py-3 bg-background/50 border border-border rounded-lg text-text placeholder-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowToken(!showToken)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-text transition-colors"
                                    aria-label={showToken ? 'Hide token' : 'Show token'}
                                >
                                    {showToken ? (
                                        <EyeOff className="w-5 h-5" />
                                    ) : (
                                        <Eye className="w-5 h-5" />
                                    )}
                                </button>
                            </div>
                            <p className="text-xs text-muted mt-2">
                                Token is used in-memory only and never stored or logged.
                            </p>
                        </div>

                        {/* Security Info */}
                        <div className="p-4 bg-primary/10 border border-primary/20 rounded-lg">
                            <div className="flex items-start gap-2">
                                <Lock className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                                <div className="text-xs text-text/80 space-y-1">
                                    <p className="font-medium text-text">Security Guarantees:</p>
                                    <ul className="list-disc list-inside space-y-0.5 text-muted">
                                        <li>Never stored in database</li>
                                        <li>Never logged or cached</li>
                                        <li>Cleared after each request</li>
                                        <li>Used only for API calls</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Clear Token Button */}
                        {token && (
                            <button
                                onClick={() => {
                                    onTokenChange('');
                                    setShowToken(false);
                                }}
                                className="w-full px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm font-medium transition-colors"
                            >
                                Clear Token
                            </button>
                        )}
                    </div>

                    {/* Footer Info */}
                    <div className="mt-auto pt-6 border-t border-border">
                        <p className="text-xs text-muted text-center">
                            Leave empty for public repositories
                        </p>
                    </div>
                </div>
            </div>
        </>
    );
}

