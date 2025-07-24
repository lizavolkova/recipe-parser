import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Recipe Parser | Extract Recipes from Any URL',
  description: 'Parse recipes from any website URL and get clean, structured recipe data including ingredients, instructions, and metadata.',
  keywords: 'recipe parser, recipe extractor, cooking, ingredients, instructions',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <main>{children}</main>
        <footer className="bg-gray-900 text-white py-8">
          <div className="container mx-auto px-4 text-center">
            <p className="text-gray-400">
              Built with ❤️ using Next.js and FastAPI
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports recipe-scrapers, structured data extraction, and AI parsing
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}
