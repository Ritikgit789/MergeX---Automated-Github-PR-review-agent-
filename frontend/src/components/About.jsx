import React from 'react';
import { Shield, Lock, Key, Github, Info, CheckCircle } from 'lucide-react';

export function About({ onClose }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Overlay */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal Content */}
            <div className="relative glass-strong rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-border">
                <div className="p-8">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-3xl font-bold text-text flex items-center gap-3">
                            <Info className="w-8 h-8 text-primary" />
                            About Merge X
                        </h2>
                        <button
                            onClick={onClose}
                            className="text-muted hover:text-text transition-colors text-2xl"
                        >
                            ✕
                        </button>
                    </div>

                    {/* Content */}
                    <div className="space-y-6 text-text/90">
                        {/* Introduction */}
                        <section>
                            <h3 className="text-xl font-semibold text-text mb-3">
                                What is Merge X?
                            </h3>
                            <p className="leading-relaxed">
                                Merge X is an automated GitHub Pull Request review agent powered by multi-agent AI.
                                It analyzes your code changes for logic errors, security vulnerabilities, performance issues,
                                and readability concerns, providing comprehensive feedback in seconds.
                            </p>
                        </section>

                        {/* Token Section */}
                        <section className="p-6 bg-primary/10 border border-primary/20 rounded-xl">
                            <div className="flex items-start gap-3 mb-4">
                                <Key className="w-6 h-6 text-primary flex-shrink-0 mt-0.5" />
                                <div>
                                    <h3 className="text-xl font-semibold text-text mb-2">
                                        GitHub Personal Access Token (PAT)
                                    </h3>
                                    <p className="text-sm text-text/80 mb-4">
                                        For private repositories, you'll need to provide a GitHub Personal Access Token.
                                    </p>
                                </div>
                            </div>

                            {/* How to Get Token */}
                            <div className="space-y-4">
                                <div>
                                    <h4 className="font-semibold text-text mb-2 flex items-center gap-2">
                                        <Github className="w-5 h-5" />
                                        How to Create a PAT:
                                    </h4>
                                    <ol className="list-decimal list-inside space-y-2 text-sm text-text/80 ml-2">
                                        <li>Go to GitHub → Settings → Developer settings</li>
                                        <li>Click "Personal access tokens" → "Tokens (classic)"</li>
                                        <li>Click "Generate new token (classic)"</li>
                                        <li>Select scopes:
                                            <ul className="list-disc list-inside ml-6 mt-1 space-y-1">
                                                <li><code className="bg-background/50 px-1 rounded">repo</code> - For private repos</li>
                                                <li><code className="bg-background/50 px-1 rounded">public_repo</code> - For public repos only</li>
                                            </ul>
                                        </li>
                                        <li>Copy the token and paste it in the sidebar settings</li>
                                    </ol>
                                </div>

                                {/* Security Guarantees */}
                                <div className="mt-6 p-4 bg-background/50 border border-border rounded-lg">
                                    <h4 className="font-semibold text-text mb-3 flex items-center gap-2">
                                        <Shield className="w-5 h-5 text-green-400" />
                                        Security Guarantees
                                    </h4>
                                    <div className="space-y-2">
                                        {[
                                            'Token is used in-memory only for API calls',
                                            'Never stored in database or files',
                                            'Never logged or cached',
                                            'Automatically cleared after each request',
                                            'Not shared with any third parties',
                                            'You must provide token again after page reload'
                                        ].map((item, index) => (
                                            <div key={index} className="flex items-start gap-2 text-sm text-text/80">
                                                <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                                                <span>{item}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Privacy Note */}
                                <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                                    <div className="flex items-start gap-2">
                                        <Lock className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                                        <div className="text-sm text-text/90">
                                            <p className="font-medium text-text mb-1">Privacy Note:</p>
                                            <p className="text-text/80">
                                                Your token is only used to authenticate with GitHub's API to fetch PR data.
                                                It's never stored, logged, or shared. After your request completes, the token
                                                is completely removed from memory. You'll need to provide it again for the next request.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Usage */}
                        <section>
                            <h3 className="text-xl font-semibold text-text mb-3">
                                How to Use
                            </h3>
                            <ol className="list-decimal list-inside space-y-2 text-sm text-text/80 ml-2">
                                <li>For <strong>public repositories</strong>: Just paste the PR URL and click "Review PR"</li>
                                <li>For <strong>private repositories</strong>:
                                    <ul className="list-disc list-inside ml-6 mt-1 space-y-1">
                                        <li>Open the sidebar (Settings icon in top-right)</li>
                                        <li>Paste your GitHub token</li>
                                        <li>Paste the PR URL and click "Review PR"</li>
                                    </ul>
                                </li>
                                <li>Review results will appear below with detailed feedback</li>
                            </ol>
                        </section>

                        {/* Features */}
                        <section>
                            <h3 className="text-xl font-semibold text-text mb-3">
                                Review Categories
                            </h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {[
                                    { name: 'Logic', desc: 'Logical errors and edge cases' },
                                    { name: 'Security', desc: 'Security vulnerabilities' },
                                    { name: 'Performance', desc: 'Performance optimizations' },
                                    { name: 'Readability', desc: 'Code style and maintainability' }
                                ].map((cat, index) => (
                                    <div key={index} className="p-3 bg-background/50 border border-border rounded-lg">
                                        <p className="font-medium text-text">{cat.name}</p>
                                        <p className="text-xs text-muted mt-1">{cat.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>

                    {/* Footer */}
                    <div className="mt-8 pt-6 border-t border-border text-center">
                        <p className="text-sm text-muted">
                            Built with ❤️ using React, FastAPI & LangGraph
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

