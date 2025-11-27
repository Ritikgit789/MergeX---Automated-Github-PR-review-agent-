import React, { useState } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';

export function PRInput({ onSubmit, isLoading }) {
    const [url, setUrl] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (url.trim()) {
            onSubmit(url.trim());
        }
    };

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-8xl mx-auto flex flex-col items-center">
            <div className="relative group w-full">
                {/* Animated gradient border */}
                <div className="absolute -inset-1 bg-gradient-to-r from-primary via-purple-500 to-secondary rounded-xl blur-lg opacity-30 group-hover:opacity-60 group-focus-within:opacity-60 transition duration-500"></div>

                {/* Input container with glassmorphism */}
                <div className="relative glass-strong rounded-xl shadow-lg shadow-primary/5">
                    <div className="flex items-center p-2">
                        <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 ml-2">
                            <Search className="w-5 h-5 text-primary" />
                        </div>

                        <input
                            type="text"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            placeholder="https://github.com/owner/repo/pull/123"
                            className="flex-1 bg-transparent border-none focus:ring-0 text-text placeholder-muted px-4 py-3 text-base outline-none w-full"
                            disabled={isLoading}
                        />

                        <button
                            type="submit"
                            disabled={isLoading || !url.trim()}
                            className={clsx(
                                "relative px-8 py-3 rounded-lg font-semibold text-sm sm:text-base transition-all duration-300 mr-2 overflow-hidden group/btn",
                                isLoading || !url.trim()
                                    ? "bg-border text-muted cursor-not-allowed"
                                    : "bg-gradient-to-r from-primary to-blue-600 hover:from-blue-600 hover:to-primary text-white shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:scale-105"
                            )}
                        >
                            {isLoading ? (
                                <div className="flex items-center space-x-2">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Analyzing...</span>
                                </div>
                            ) : (
                                <div className="flex items-center space-x-2">
                                    <Sparkles className="w-4 h-4" />
                                    <span>Review PR</span>
                                </div>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </form>
    );
}
