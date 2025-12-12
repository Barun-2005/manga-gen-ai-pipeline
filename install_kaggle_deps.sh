#!/bin/bash
# ============================================
# MangaGen - Kaggle Dependencies Installer
# ============================================
# Run this FIRST in a Kaggle notebook cell:
#   !bash install_kaggle_deps.sh
#
# This script handles tricky dependencies that fail to build from source:
# - insightface (needs pre-compiled onnxruntime)
# - opencv fixes for headless environments
# ============================================

set -e  # Exit on any error

echo "🎨 MangaGen Kaggle Setup Starting..."
echo "========================================"

# ============================================
# Step 1: Upgrade pip and install build tools
# ============================================
echo "📦 Step 1/5: Upgrading pip and build tools..."
pip install --upgrade pip wheel setuptools --quiet

# ============================================
# Step 2: Install PyTorch (Kaggle usually has it, but ensure correct version)
# ============================================
echo "🔥 Step 2/5: Verifying PyTorch..."
python -c "import torch; print(f'PyTorch {torch.__version__} - CUDA: {torch.cuda.is_available()}')"

# ============================================
# Step 3: Install core requirements
# ============================================
echo "📚 Step 3/5: Installing core requirements..."

# CRITICAL: Downgrade numpy first to avoid compatibility issues
echo "   📌 Fixing numpy version..."
pip install --quiet "numpy<2.0.0"

# Install diffusers ecosystem FIRST (order matters!)
echo "   📌 Installing diffusers ecosystem..."
pip install --quiet --upgrade \
    diffusers==0.27.2 \
    transformers==4.40.2 \
    accelerate==0.29.3 \
    safetensors==0.4.3

# Install other dependencies
echo "   📌 Installing other dependencies..."
pip install --quiet \
    controlnet-aux==0.0.9 \
    google-generativeai>=0.5.0 \
    "pydantic>=2.0.0,<2.12" \
    opencv-python-headless>=4.8.0 \
    Pillow>=10.0.0 \
    reportlab>=4.0.0 \
    python-dotenv>=1.0.0 \
    huggingface-hub>=0.21.0 \
    tqdm>=4.65.0

# Skip mediapipe as it causes numpy conflicts
echo "   ⏭️ Skipping mediapipe (optional, causes numpy conflicts)"

# ============================================
# Step 4: Install ONNX Runtime GPU (required for insightface)
# ============================================
echo "⚡ Step 4/5: Installing ONNX Runtime GPU..."
pip install --quiet onnxruntime-gpu==1.17.1

# ============================================
# Step 5: Install InsightFace (using pre-compiled wheel)
# ============================================
echo "👤 Step 5/5: Installing InsightFace..."

# Try installing from PyPI first (works on most Kaggle environments)
if pip install insightface --quiet 2>/dev/null; then
    echo "✅ InsightFace installed from PyPI"
else
    echo "⚠️ PyPI install failed, trying alternative method..."
    
    # Alternative: Install build dependencies and compile
    apt-get update -qq && apt-get install -qq -y cmake libgl1-mesa-glx
    pip install cython numpy --quiet
    pip install --no-build-isolation insightface --quiet
    
    echo "✅ InsightFace installed from source"
fi

# ============================================
# Verify installations
# ============================================
echo ""
echo "========================================"
echo "🔍 Verifying installations..."
echo "========================================"

python -c "
import sys
packages = [
    ('diffusers', '0.27.2'),
    ('transformers', '4.40.2'),
    ('accelerate', '0.29.3'),
    ('google.generativeai', None),
    ('cv2', None),
    ('PIL', None),
    ('reportlab', None),
]

all_ok = True
for pkg, expected_ver in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, '__version__', 'installed')
        status = '✅'
        if expected_ver and ver != expected_ver:
            status = '⚠️ '
            ver = f'{ver} (expected {expected_ver})'
    except ImportError:
        status = '❌'
        ver = 'NOT FOUND'
        all_ok = False
    print(f'{status} {pkg}: {ver}')

# Check InsightFace separately
try:
    import insightface
    print(f'✅ insightface: {insightface.__version__}')
except ImportError:
    print('⚠️ insightface: Not installed (IP-Adapter FaceID will use fallback)')

if all_ok:
    print()
    print('🎉 All core dependencies installed successfully!')
else:
    print()
    print('⚠️ Some packages missing - check errors above')
    sys.exit(1)
"

echo ""
echo "========================================"
echo "🎨 MangaGen Kaggle Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Add your GEMINI_API_KEY to Kaggle Secrets"
echo "  2. Run the pipeline notebook cells"
echo ""
