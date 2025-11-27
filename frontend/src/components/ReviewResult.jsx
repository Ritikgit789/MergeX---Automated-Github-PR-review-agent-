import { motion, animate, useMotionValue, useTransform } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { AlertCircle, CheckCircle, Info, XCircle, FileCode, Shield, Zap, BookOpen, Bot } from 'lucide-react';
import { clsx } from 'clsx';

const severityIcons = {
    critical: <XCircle className="w-5 h-5 text-red-500" />,
    error: <XCircle className="w-5 h-5 text-red-400" />,
    warning: <AlertCircle className="w-5 h-5 text-yellow-400" />,
    info: <Info className="w-5 h-5 text-blue-400" />,
};

const categoryIcons = {
    logic: <FileCode className="w-4 h-4" />,
    security: <Shield className="w-4 h-4" />,
    performance: <Zap className="w-4 h-4" />,
    readability: <BookOpen className="w-4 h-4" />,
};

const categoryColors = {
    logic: "text-purple-400 bg-purple-400/10 border-purple-400/20",
    security: "text-red-400 bg-red-400/10 border-red-400/20",
    performance: "text-orange-400 bg-orange-400/10 border-orange-400/20",
    readability: "text-blue-400 bg-blue-400/10 border-blue-400/20",
};

function Counter({ value }) {
    const ref = useRef(null);

    useEffect(() => {
        const node = ref.current;
        if (!node) return;

        const safeValue = Number(value) || 0;

        const controls = animate(0, safeValue, {
            duration: 1.5,
            ease: "easeOut",
            onUpdate(val) {
                node.textContent = Math.round(val);
            }
        });

        return () => controls.stop();
    }, [value]);

    return <span ref={ref} />;
}

export function ReviewResult({ data }) {
    // Safety check: if data is null/undefined, don't render or render fallback
    if (!data) return null;

    const { total_issues = 0, summary = '', comments = [] } = data;

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const item = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 }
    };

    return (
        <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="space-y-6 w-full max-w-4xl mx-auto"
        >
            {/* Summary Section */}
            <motion.div
                variants={item}
                className="glass-strong rounded-xl p-8 border border-primary/20 shadow-2xl shadow-primary/10 text-center"
            >
                <div className="flex flex-col items-center justify-center mb-6 gap-4">
                    <div className="p-3 bg-primary/10 rounded-full">
                        <CheckCircle className="w-8 h-8 text-primary" />
                    </div>

                    <div className="space-y-2">
                        <h3 className="text-2xl font-bold text-text">Review Complete</h3>
                        <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-background/50 rounded-full border border-border/50">
                            <span className="text-sm font-medium text-muted">
                                <span className="text-primary font-bold text-lg mr-1">
                                    <Counter value={total_issues} />
                                </span>
                                Issues Found
                            </span>
                        </div>
                    </div>
                </div>
                <p className="text-text/80 leading-relaxed whitespace-pre-wrap max-w-2xl mx-auto">{summary}</p>
            </motion.div>

            {/* Comments List */}
            <div className="space-y-4">
                {Array.isArray(comments) && comments.map((comment, index) => {
                    // Safety checks for icons/colors
                    const severityIcon = severityIcons[comment.severity] || severityIcons.info;
                    const categoryIcon = categoryIcons[comment.category] || categoryIcons.logic;
                    const categoryColor = categoryColors[comment.category] || categoryColors.logic;

                    return (
                        <motion.div
                            key={index}
                            variants={item}
                            className="bg-surface border border-border rounded-lg p-5 hover:border-primary/30 transition-colors group"
                        >
                            <div className="flex items-start gap-4">
                                <div className="mt-1 flex-shrink-0">
                                    {severityIcon}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                                        <span className="font-mono text-sm text-primary bg-primary/10 px-2 py-0.5 rounded border border-primary/20">
                                            {comment.file_path}:{comment.line_number}
                                        </span>
                                        <span className={clsx(
                                            "flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded border uppercase tracking-wider",
                                            categoryColor
                                        )}>
                                            {categoryIcon}
                                            {comment.category || 'Unknown'}
                                        </span>
                                        {comment.source_agent && (
                                            <span className="flex items-center gap-1 text-xs text-muted bg-border/50 px-2 py-0.5 rounded border border-border ml-auto">
                                                <Bot className="w-3 h-3" />
                                                {comment.source_agent}
                                            </span>
                                        )}
                                    </div>

                                    <p className="text-text mb-3">{comment.message}</p>

                                    {comment.suggestion && (
                                        <div className="bg-background rounded border border-border p-3 mt-3">
                                            <p className="text-xs text-muted mb-1 font-medium uppercase tracking-wider">Suggestion</p>
                                            <code className="text-sm font-mono text-green-400 block overflow-x-auto">
                                                {comment.suggestion}
                                            </code>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </motion.div>
    );
}
