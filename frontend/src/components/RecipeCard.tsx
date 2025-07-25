interface Recipe {
    title: string;
    source?: string;
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
  
  interface RecipeCardProps {
    recipe: Recipe;
  }
  
  export function RecipeCard({ recipe }: RecipeCardProps) {
    const formatTime = (time?: string) => {
      if (!time) return null;
      // Handle ISO 8601 duration format (PT30M) or plain text
      if (time.startsWith('PT')) {
        const match = time.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
        if (match) {
          const hours = match[1] ? parseInt(match[1]) : 0;
          const minutes = match[2] ? parseInt(match[2]) : 0;
          if (hours && minutes) return `${hours}h ${minutes}m`;
          if (hours) return `${hours}h`;
          if (minutes) return `${minutes}m`;
        }
      }
      return time;
    };
  
    return (
      <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header with Image */}
        <div className="relative h-64 bg-gradient-to-r from-blue-500 to-purple-600">
          {recipe.image ? (
            <img
              src={recipe.image}
              alt={recipe.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                // Hide image on error and show gradient background
                e.currentTarget.style.display = 'none';
              }}
            />
          ) : null}
          <div className="absolute inset-0 bg-black/20 flex items-end">
          <div className="p-6 text-white">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-3xl font-bold">{recipe.title}</h2>
              {recipe.source && (
                <div className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-medium">
                  📍 {recipe.source}
                </div>
              )}
            </div>
            {recipe.description && (
              <p className="text-white/90">{recipe.description}</p>
            )}
          </div>
        </div>
      </div>
  
        <div className="p-8">
          {/* Recipe Meta */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {recipe.prep_time && (
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl mb-1">⏱️</div>
                <div className="text-sm text-gray-600">Prep Time</div>
                <div className="font-semibold text-gray-900">{formatTime(recipe.prep_time)}</div>
              </div>
            )}
            {recipe.cook_time && (
              <div className="text-center p-3 bg-orange-50 rounded-lg">
                <div className="text-2xl mb-1">🔥</div>
                <div className="text-sm text-gray-600">Cook Time</div>
                <div className="font-semibold text-gray-600">{formatTime(recipe.cook_time)}</div>
              </div>
            )}
            {recipe.servings && (
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl mb-1">🍽️</div>
                <div className="text-sm text-gray-600">Servings</div>
                <div className="font-semibold text-gray-600">{recipe.servings}</div>
              </div>
            )}
            {recipe.cuisine && (
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl mb-1">🌍</div>
                <div className="text-sm text-gray-600">Cuisine</div>
                <div className="font-semibold text-gray-600">{recipe.cuisine}</div>
              </div>
            )}
          </div>
  
          {/* Tags */}
          {(recipe.category || recipe.keywords.length > 0) && (
            <div className="mb-8">
              <div className="flex flex-wrap gap-2">
                {recipe.category && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {recipe.category}
                  </span>
                )}
                {recipe.keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
  
          <div className="grid md:grid-cols-2 gap-8">
            {/* Ingredients */}
            <div>
              <h3 className="text-2xl font-bold mb-4 flex items-center text-gray-600">
                🛒 Ingredients
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({recipe.ingredients.length})
                </span>
              </h3>
              <ul className="space-y-2">
                {recipe.ingredients.map((ingredient, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-blue-500 mr-2 mt-1">•</span>
                    <span className="text-gray-700">{ingredient}</span>
                  </li>
                ))}
              </ul>
            </div>
  
            {/* Instructions */}
            <div>
              <h3 className="text-2xl font-bold mb-4 flex items-center text-gray-600">
                📝 Instructions
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({recipe.instructions.length} steps)
                </span>
              </h3>
              <ol className="space-y-4">
                {recipe.instructions.map((instruction, index) => (
                  <li key={index} className="flex items-start">
                    <span className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-3 mt-1">
                      {index + 1}
                    </span>
                    <p className="text-gray-700 leading-relaxed">{instruction}</p>
                  </li>
                ))}
              </ol>
            </div>
          </div>
  
          {/* Parser Info */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <div className="flex items-center space-x-4">
                <span className="flex items-center">
                  {recipe.found_structured_data ? '✅' : '❌'} Structured Data
                </span>
                <span className="flex items-center">
                  {recipe.used_ai ? '🤖' : '📊'} {recipe.used_ai ? 'AI Parsed' : 'Data Extracted'}
                </span>
              </div>
              <button
                onClick={() => window.print()}
                className="text-blue-600 hover:text-blue-800 flex items-center"
              >
                🖨️ Print Recipe
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
