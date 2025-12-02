import React, { useState } from "react";
import { Sparkles, Github, Info } from "lucide-react";
import { About } from "./About";

export function Layout({ children }) {
    const [showAbout, setShowAbout] = useState(false);

    return (
        <div className="min-h-screen text-text flex flex-col items-center justify-center py-10 sm:py-14 px-4 sm:px-6 lg:px-8 pb-20 relative z-10">
            <div className="absolute top-6 left-6 sm:top-8 sm:left-8 flex items-center gap-4">
                <a
                    href="https://github.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted hover:text-text transition-colors duration-300"
                >
                    <Github className="w-6 h-6 sm:w-8 sm:h-8" />
                </a>
                <button
                    onClick={() => setShowAbout(true)}
                    className="text-muted hover:text-text transition-colors duration-300"
                    aria-label="About"
                >
                    <Info className="w-6 h-6 sm:w-8 sm:h-8" />
                </button>
            </div>

            {showAbout && <About onClose={() => setShowAbout(false)} />}

            <div className="w-full max-w-5xl mx-auto flex flex-col items-center">

                {/* HERO HEADER */}
                <div className="flex flex-col items-center text-center space-y-6 mb-10">
                    <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight">
                        <span className="bg-gradient-to-r from-white via-blue-100 to-purple-200 bg-clip-text text-transparent drop-shadow-lg">
                            Merge X
                        </span>
                    </h1>

                    <p className="text-xl sm:text-2xl italic text-muted">
                        Automated GitHub PR Review Agent
                    </p>

                    {/* AI Badge */}
                    <div className="inline-flex items-center justify-center gap-2 px-5 py-2 rounded-full glass border border-primary/25">
                        <Sparkles className="w-5 h-5 text-primary animate-pulse" />
                        <p className="text-sm font-medium text-primary">
                            Multi-Agent AI • Lightning-fast Code Analysis
                        </p>
                    </div>
                </div>

                {/* MAIN CONTENT */}
                <main className="w-full flex flex-col items-center justify-center">
                    {children}
                </main>

                {/* FOOTER */}
                <footer className="text-center text-sm text-muted pt-20 pb-6">
                    <p className="flex items-center justify-center gap-1">
                        Built with <span className="text-red-400">♥</span> using React, FastAPI & LangGraph
                    </p>
                    <p className="text-xs opacity-60 mt-2">
                        © 2025 Merge X • Automated PR Review Intelligence
                    </p>
                </footer>
            </div>

            {/* Disclaimer - Fixed at bottom */}
            <div className="fixed bottom-0 left-0 right-0 z-10 py-3 px-4 bg-background/80 backdrop-blur-sm border-t border-border/50">
                <p className="text-center text-xs text-muted/70 max-w-4xl mx-auto">
                    <span className="text-yellow-400/80">⚠️</span> Merge X can make mistakes. Please cross-check accordingly.
                </p>
            </div>
        </div>
    );
}
