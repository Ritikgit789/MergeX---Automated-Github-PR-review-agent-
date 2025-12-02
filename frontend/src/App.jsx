import { useState } from 'react';
import axios from 'axios';
import { Layout } from './components/Layout';
import { PRInput } from './components/PRInput';
import { ReviewResult } from './components/ReviewResult';
import { Sidebar } from './components/Sidebar';
import { AlertCircle } from 'lucide-react';

// API Base URL - deployed backend on Render
const API_BASE_URL = 'https://mergex-d3c1.onrender.com/api/v1';

function App() {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [githubToken, setGithubToken] = useState('');

    const handleReview = async (url) => {
        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            // Build request payload
            const payload = {
                pr_url: url
            };
            
            // Add token only if provided (for private repos)
            if (githubToken && githubToken.trim()) {
                payload.github_token = githubToken.trim();
            }

            const response = await axios.post(`${API_BASE_URL}/review/github`, payload);
            setResult(response.data);
        } catch (err) {
            console.error('Review failed:', err);
            setError(
                err.response?.data?.detail ||
                err.message ||
                "Failed to review PR. Please check if the backend is running."
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Layout>
            {/* Sidebar for token input */}
            <Sidebar token={githubToken} onTokenChange={setGithubToken} />

            <div className="w-full flex flex-col items-center gap-12">

                {/* PR Input */}
                <PRInput onSubmit={handleReview} isLoading={isLoading} />

                {/* Error box */}
                {error && (
                    <div className="glass-strong rounded-xl p-5 flex items-start gap-3 text-red-400 shadow-2xl shadow-red-500/10 border-red-500/30 w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                        <p className="text-sm">{error}</p>
                    </div>
                )}

                {/* Results Section */}
                {result && <ReviewResult data={result} />}
            </div>
        </Layout>
    );
}

export default App;
