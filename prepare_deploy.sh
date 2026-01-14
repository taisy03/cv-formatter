#!/bin/bash
# Deployment Preparation Script

echo "🚀 CV Formatter - Deployment Preparation"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "server.py" ]; then
    echo "❌ Error: server.py not found. Run this script from the project root."
    exit 1
fi

echo "✅ Checking required files..."

# Check required files
missing_files=()

[ ! -f "server.py" ] && missing_files+=("server.py")
[ ! -f "requirements.txt" ] && missing_files+=("requirements.txt")
[ ! -f "frontend/index.html" ] && missing_files+=("frontend/index.html")
[ ! -f "frontend/style.css" ] && missing_files+=("frontend/style.css")
[ ! -f "frontend/app.js" ] && missing_files+=("frontend/app.js")
[ ! -f "template/template.docx" ] && missing_files+=("template/template.docx")

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ Missing files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo "✅ All required files present"
echo ""

# Create deployment package info
echo "📦 Files to upload:"
echo "   - server.py"
echo "   - requirements.txt"
echo "   - frontend/ (folder)"
echo "   - template/ (folder)"
echo ""

# Check file sizes
echo "📊 File sizes:"
du -sh server.py requirements.txt frontend/ template/ 2>/dev/null | awk '{print "   " $2 ": " $1}'
echo ""

# Check Python version
echo "🐍 Python version check:"
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "   ⚠️  Python3 not found in PATH"
fi
echo ""

# Check if dependencies are installed locally
echo "📚 Checking dependencies..."
if [ -d "venv" ] || [ -d ".venv" ]; then
    echo "   ✅ Virtual environment found"
else
    echo "   ℹ️  No virtual environment found (this is OK for deployment)"
fi
echo ""

echo "✅ Ready for deployment!"
echo ""
echo "Next steps:"
echo "1. Read DEPLOY_STEPS.md for detailed instructions"
echo "2. Upload all files to your Hostinger server"
echo "3. Install dependencies on the server"
echo "4. Start the application"
echo ""

