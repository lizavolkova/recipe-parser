'use client';

import { useState } from 'react';
import { RecipeCard } from '@/components/RecipeCard';
import { LoadingSpinner } from '@/components/LoadingSpinner';

interface Recipe {
  title: string;
  description?: string;
  image?: string;
  ingredients: string[];
  instructions: string[];
  prep_time?: string;
  cook_time?: string;
  servings?: string;
  cuisine?: string;
  category?: string;
  keywords: string[];
  found_structured_data: boolean;
  used_ai: boolean;
}

export default function Home() {
  const [url, setUrl] = useState('');
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseRecipe = async () => {
    if (!url.trim()) {
      setError('Please enter a recipe URL');
      return;
    }

    setLoading(true);
    setError(null);
    setRecipe(null);

    try {
      const response = await fetch('http://localhost:8000/parse-recipe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: Recipe = await response.json();
      setRecipe(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse recipe');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    parseRecipe();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-5xl font-bold text-white mb-4">
            🍳 Recipe Parser
          </h1>
          <p className="text-xl text-white/90">
            Paste any recipe URL and get clean, structured recipe data
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="url" className="block text-lg font-semibold text-gray-700 mb-2">
                Recipe URL
              </label>
              <input
                id="url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/recipe-page"
                className="w-full p-4 text-lg border-2 border-gray-300 rounded-xl focus:border-blue-500 focus:outline-none transition-colors text-gray-600"
                disabled={loading}
              />
            </div>
            
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white text-lg font-semibold py-4 px-6 rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02]"
            >
              {loading ? 'Parsing Recipe...' : 'Parse Recipe'}
            </button>
          </form>

          {/* Quick Examples */}
          <div className="mt-6 p-4 bg-gray-50 rounded-xl">
            <p className="text-sm text-gray-600 mb-2">Try these example URLs:</p>
            <div className="space-y-1">
              <button
                onClick={() => setUrl('https://www.loveandlemons.com/grilled-ratatouille-tartines/')}
                className="block text-blue-600 hover:text-blue-800 text-sm underline"
                disabled={loading}
              >
                Love and Lemons - Grilled Ratatouille
              </button>
              <button
                onClick={() => setUrl('https://asianinspirations.com.au/recipes/braised-chicken-with-radish/')}
                className="block text-blue-600 hover:text-blue-800 text-sm underline"
                disabled={loading}
              >
                Asian Inspirations - Braised Chicken
              </button>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && <LoadingSpinner />}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <div className="flex items-center">
              <span className="text-2xl mr-3">❌</span>
              <div>
                <h3 className="text-lg font-semibold text-red-800">Error</h3>
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Recipe Result */}
        {recipe && <RecipeCard recipe={recipe} />}
      </div>
    </div>
  );
}
