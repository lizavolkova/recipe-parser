export function LoadingSpinner() {
    return (
      <div className="bg-white rounded-2xl shadow-2xl p-8 text-center">
        <div className="flex flex-col items-center space-y-4">
          {/* Animated cooking icons */}
          <div className="flex space-x-2 mb-4">
            <span className="text-4xl animate-bounce" style={{ animationDelay: '0ms' }}>🍳</span>
            <span className="text-4xl animate-bounce" style={{ animationDelay: '150ms' }}>🥄</span>
            <span className="text-4xl animate-bounce" style={{ animationDelay: '300ms' }}>📖</span>
          </div>
          
          {/* Loading spinner */}
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 border-top-blue-500 rounded-full animate-spin"></div>
          </div>
          
          {/* Loading text */}
          <div className="text-center">
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              Parsing your recipe...
            </h3>
            <p className="text-gray-500">
              Extracting ingredients, instructions, and metadata
            </p>
          </div>
          
          {/* Loading steps */}
          <div className="w-full max-w-md">
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>🔍 Analyzing webpage...</span>
                <span className="text-blue-500">✓</span>
              </div>
              <div className="flex items-center justify-between">
                <span>📊 Extracting structured data...</span>
                <div className="w-4 h-4 border-2 border-blue-500 border-top-transparent rounded-full animate-spin"></div>
              </div>
              <div className="flex items-center justify-between opacity-50">
                <span>🤖 AI parsing (if needed)...</span>
                <span>⏳</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
