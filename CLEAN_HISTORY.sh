#!/bin/bash
# Script to clean git history and remove .env file

echo "⚠️  WARNING: This will rewrite git history!"
echo ""
echo "Before running this:"
echo "1. Rotate your OpenAI API key at https://platform.openai.com/api-keys"
echo "2. Update your local .env file with the new key"
echo ""
read -p "Have you rotated your API key? (yes/no): " answer

if [ "$answer" != "yes" ]; then
    echo "Please rotate your API key first, then run this script again."
    exit 1
fi

echo ""
echo "Starting clean history process..."

# Remove git history
rm -rf .git

# Initialize fresh repo
git init
git branch -M main

# Add all files (except .env which is ignored)
git add .

# Create initial commit
git commit -m "Initial commit - CV Formatter web app"

echo ""
echo "✅ Clean history created!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with the new API key"
echo "2. Run: git remote add origin https://github.com/taisy03/cv-formatter.git"
echo "3. Run: git push -u origin main --force"
echo ""
echo "⚠️  The --force flag will replace everything on GitHub with clean history"

