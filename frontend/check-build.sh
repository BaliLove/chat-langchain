#!/bin/bash
# Pre-deployment build check script
# Run this before committing to catch build errors

echo "🔍 Running pre-deployment checks..."
echo "=================================="

# Change to frontend directory
cd "$(dirname "$0")"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    yarn install
fi

# Run TypeScript check
echo "📝 Checking TypeScript..."
yarn tsc --noEmit
if [ $? -ne 0 ]; then
    echo "❌ TypeScript errors found!"
    exit 1
fi

# Run ESLint
echo "🔍 Running ESLint..."
yarn lint
if [ $? -ne 0 ]; then
    echo "❌ ESLint errors found!"
    exit 1
fi

# Run build
echo "🏗️  Running production build..."
yarn build
if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ All checks passed! Ready to deploy."