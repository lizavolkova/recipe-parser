interface Recipe {
    title: string;
    source?: string;
    description?: string;
    image?: string;
    ingredients: string[];
    raw_ingredients: string[];
    raw_ingredients_detailed: Array<{
      name: string;
      quantity?: string;
      unit?: string;
      descriptors: string[];
      original: string;
      confidence: number;
      shopping_display: string;
    }>;
    instructions: string[];
    prep_time?: string;
    cook_time?: string;
    servings?: string;
    cuisine?: string;
    category?: string;
    keywords: string[];
    found_structured_data: boolean;
    used_ai: boolean;
    
    // AI categorization fields
    health_tags: string[];
    dish_type: string[];
    cuisine_type: string[];
    meal_type: string[];
    season: string[];
    ai_confidence_notes?: string;
    ai_enhanced: boolean;
    ai_model_used?: string;
  }
  
  interface RecipeCardProps {
    recipe: Recipe;
    onReCategorize?: () => void; // NEW: callback for re-categorization
    aiLoading?: boolean; // NEW: loading state for AI operations
  }
  
  export function RecipeCard({ recipe, onReCategorize, aiLoading = false }: RecipeCardProps) {
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
  
    // Function to format shopping list item with bold ingredient name
    const formatShoppingItem = (item: any): JSX.Element => {
      const display = item.shopping_display;
      const ingredientName = item.name;
      
      const regex = new RegExp(`\\b(${ingredientName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})\\b`, 'gi');
      const parts = display.split(regex);
      
      return (
        <span>
          {parts.map((part: string, index: number) => {
            if (part.toLowerCase() === ingredientName.toLowerCase()) {
              return <strong key={index} className="text-gray-900 font-bold">{part}</strong>;
            }
            return part;
          })}
        </span>
      );
    };
  
    const highlightRawIngredient = (originalIngredient: string): JSX.Element => {
      // Find the corresponding detailed ingredient
      const detailed = recipe.raw_ingredients_detailed?.find(
        d => d.original === originalIngredient
      );
      
      if (!detailed) {
        return <span>{originalIngredient}</span>;
      }
  
      // Create a case-insensitive regex to find the raw ingredient name
      const rawIngredientName = detailed.name;
      const regex = new RegExp(`\\b(${rawIngredientName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})\\b`, 'gi');
      
      // Split the text and highlight matches
      const parts = originalIngredient.split(regex);
      
      return (
        <span>
          {parts.map((part, index) => {
            if (part.toLowerCase() === rawIngredientName.toLowerCase()) {
              return <strong key={index} className="text-blue-700 font-bold">{part}</strong>;
            }
            return part;
          })}
        </span>
      );
    };
  
    // Function to copy shopping list to clipboard
    const copyShoppingList = () => {
      if (!recipe.raw_ingredients_detailed) return;
      
      const shoppingText = recipe.raw_ingredients_detailed
        .map(item => `• ${item.shopping_display}`)
        .join('\n');
      
      navigator.clipboard.writeText(`Shopping List for ${recipe.title}:\n\n${shoppingText}`);
      
      // Simple feedback (you could use a toast library instead)
      alert('Shopping list copied to clipboard!');
    };
  
    // Helper functions for AI categorization display
    const getHealthTagStyle = (tag: string) => {
      const styles: { [key: string]: string } = {
        'vegan': 'bg-green-100 text-green-800',
        'vegetarian': 'bg-green-100 text-green-700',
        'gluten free': 'bg-yellow-100 text-yellow-800',
        'dairy free': 'bg-blue-100 text-blue-800',
        'keto': 'bg-purple-100 text-purple-800',
        'paleo': 'bg-orange-100 text-orange-800',
        'healthy': 'bg-emerald-100 text-emerald-800',
      };
      return styles[tag.toLowerCase()] || 'bg-gray-100 text-gray-700';
    };
  
    const getSeasonEmoji = (season: string) => {
      const emojis: { [key: string]: string } = {
        'spring': '🌸',
        'summer': '☀️',
        'autumn': '🍂',
        'winter': '❄️'
      };
      return emojis[season.toLowerCase()] || '📅';
    };
  
    const getCuisineEmoji = (cuisine: string) => {
      const emojis: { [key: string]: string } = {
        'italian': '🇮🇹',
        'french': '🇫🇷',
        'mexican': '🇲🇽',
        'chinese': '🇨🇳',
        'japanese': '🇯🇵',
        'indian': '🇮🇳',
        'thai': '🇹🇭',
        'american': '🇺🇸',
        'mediterranean': '🌊',
        'asian': '🥢',
        'greek': '🇬🇷',
        'korean': '🇰🇷',
      };
      return emojis[cuisine.toLowerCase()] || '🌍';
    };
  
    const getMealTypeEmoji = (meal: string) => {
      const emojis: { [key: string]: string } = {
        'breakfast': '🌅',
        'brunch': '🥐',
        'lunch': '☀️',
        'dinner': '🌙',
        'snack': '🍿',
        'dessert': '🍰'
      };
      return emojis[meal.toLowerCase()] || '🍽️';
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
                <div className="flex items-center gap-2">
                  {recipe.ai_enhanced && (
                    <div className="bg-gradient-to-r from-purple-500 to-pink-500 px-3 py-1 rounded-full text-sm font-medium flex items-center">
                      🤖 AI Enhanced
                    </div>
                  )}
                  {recipe.source && (
                    <div className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-medium">
                      📍 {recipe.source}
                    </div>
                  )}
                </div>
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
                <div className="font-semibold text-gray-900">{formatTime(recipe.cook_time)}</div>
              </div>
            )}
            {recipe.servings && (
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl mb-1">🍽️</div>
                <div className="text-sm text-gray-600">Servings</div>
                <div className="font-semibold text-gray-900">{recipe.servings}</div>
              </div>
            )}
            {recipe.cuisine && (
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl mb-1">🌍</div>
                <div className="text-sm text-gray-600">Cuisine</div>
                <div className="font-semibold text-gray-900">{recipe.cuisine}</div>
              </div>
            )}
          </div>
  
          {/* NEW: AI Insights Section with Re-categorization Button */}
          {recipe.ai_enhanced && (
            <div className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6 border border-purple-100">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <h3 className="text-xl font-bold text-gray-800 flex items-center">
                    🤖 AI Recipe Insights
                    {recipe.ai_model_used && (
                      <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                        {recipe.ai_model_used}
                      </span>
                    )}
                  </h3>
                </div>
                
                {/* NEW: Refresh AI Tags Button */}
                {onReCategorize && (
                  <button
                    onClick={onReCategorize}
                    disabled={aiLoading}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2"
                  >
                    {aiLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-top-white rounded-full animate-spin"></div>
                        Re-analyzing...
                      </>
                    ) : (
                      <>
                        🔄 Refresh AI Tags
                      </>
                    )}
                  </button>
                )}
              </div>
  
              {/* Show loading overlay when re-categorizing */}
              <div className={`relative ${aiLoading ? 'opacity-50 pointer-events-none' : ''}`}>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {/* Health Tags */}
                  {recipe.health_tags && recipe.health_tags.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        💚 Dietary & Health
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {recipe.health_tags.map((tag, index) => (
                          <span
                            key={index}
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getHealthTagStyle(tag)}`}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
  
                  {/* Dish Types */}
                  {recipe.dish_type && recipe.dish_type.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        🍽️ Dish Type
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {recipe.dish_type.map((type, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium"
                          >
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
  
                  {/* Cuisine Types */}
                  {recipe.cuisine_type && recipe.cuisine_type.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        🌍 Cuisine Style
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {recipe.cuisine_type.map((cuisine, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium flex items-center"
                          >
                            {getCuisineEmoji(cuisine)} {cuisine}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
  
                  {/* Meal Types */}
                  {recipe.meal_type && recipe.meal_type.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        ⏰ Meal Timing
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {recipe.meal_type.map((meal, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded-full text-xs font-medium flex items-center"
                          >
                            {getMealTypeEmoji(meal)} {meal}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
  
                {/* Seasons - Full width section */}
                {recipe.season && recipe.season.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-purple-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                      📅 Best Seasons
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {recipe.season.map((season, index) => (
                        <span
                          key={index}
                          className="px-3 py-2 bg-gradient-to-r from-green-100 to-blue-100 text-gray-800 rounded-lg text-sm font-medium flex items-center"
                        >
                          {getSeasonEmoji(season)} {season.charAt(0).toUpperCase() + season.slice(1)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
  
                {/* AI Confidence Notes */}
                {recipe.ai_confidence_notes && (
                  <div className="mt-4 pt-4 border-t border-purple-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                      💭 AI Analysis Notes
                    </h4>
                    <p className="text-sm text-gray-600 italic leading-relaxed">
                      "{recipe.ai_confidence_notes}"
                    </p>
                  </div>
                )}
              </div>
  
              {/* Loading overlay for AI re-categorization */}
              {aiLoading && (
                <div className="absolute inset-0 bg-white/70 rounded-xl flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-8 h-8 border-4 border-purple-200 border-top-purple-500 rounded-full animate-spin mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600 font-medium">Refreshing AI insights...</p>
                  </div>
                </div>
              )}
            </div>
          )}
  
          {/* Show AI Insights placeholder for non-AI enhanced recipes */}
          {!recipe.ai_enhanced && onReCategorize && (
            <div className="mb-8 bg-gray-50 rounded-xl p-6 border border-gray-200 text-center">
              <div className="flex flex-col items-center space-y-3">
                <div className="text-4xl">🤖</div>
                <h3 className="text-lg font-semibold text-gray-700">Add AI Recipe Insights</h3>
                <p className="text-gray-600 text-sm max-w-md">
                  Get smart categorization including dietary tags, cuisine type, seasonal recommendations, and more.
                </p>
                <button
                  onClick={onReCategorize}
                  disabled={aiLoading}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 flex items-center gap-2"
                >
                  {aiLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-top-white rounded-full animate-spin"></div>
                      Analyzing with AI...
                    </>
                  ) : (
                    <>
                      ✨ Add AI Insights
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
  
          {/* Legacy Tags (if no AI categorization and no re-categorize option) */}
          {!recipe.ai_enhanced && !onReCategorize && (recipe.category || recipe.keywords.length > 0) && (
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
  
          {/* Shopping List Section */}
          {recipe.raw_ingredients_detailed && recipe.raw_ingredients_detailed.length > 0 && (
            <div className="mb-8 bg-green-50 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-800 flex items-center">
                  🛒 Shopping List
                  <span className="ml-2 text-sm font-normal text-gray-600">
                    ({recipe.raw_ingredients_detailed.length} items)
                  </span>
                </h3>
                <button
                  onClick={copyShoppingList}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  📋 Copy List
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {recipe.raw_ingredients_detailed.map((item, index) => (
                  <div key={index} className="flex items-center py-1">
                    <span className="text-green-600 mr-2">✓</span>
                    <span className="text-gray-800">{formatShoppingItem(item)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
  
          <div className="grid md:grid-cols-2 gap-8">
            {/* Ingredients */}
            <div>
              <h3 className="text-2xl font-bold mb-4 flex items-center text-gray-800">
                🥘 Ingredients
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
              <h3 className="text-2xl font-bold mb-4 flex items-center text-gray-800">
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
                {recipe.ai_enhanced && (
                  <span className="flex items-center text-purple-600">
                    ✨ AI Enhanced
                  </span>
                )}
                {recipe.raw_ingredients_detailed && (
                  <span className="flex items-center">
                    🔍 {recipe.raw_ingredients.length} Raw Ingredients
                  </span>
                )}
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
