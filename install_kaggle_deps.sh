#!/bin/bash
# ============================================
# MangaGen - Kaggle Dependencies Installer
# ============================================
# Run this FIRST in a Kaggle notebook cell:
#   !bash install_kaggle_deps.sh
# ============================================

set -e  # Exit on any error

echo "🎨 MangaGen Kaggle Setup Starting..."
echo "========================================"

# ============================================
# Step 1: Upgrade pip
# ============================================
echo "📦 Step 1/4: Upgrading pip..."
pip install --upgrade pip --quiet

# ============================================
# Step 2: Install diffusers with COMPATIBLE versions
# ============================================
echo "🎨 Step 2/4: Installing diffusers ecosystem..."
echo "   (This may take a minute...)"

# Use newer diffusers that works with Kaggle's huggingface_hub
pip install --quiet --upgrade \
    "diffusers>=0.29.0,<0.31.0" \
    "transformers>=4.41.0,<4.46.0" \
    "accelerate>=0.30.0" \
    "safetensors>=0.4.0"

# ============================================
# Step 3: Install other dependencies
# ============================================
echo "📚 Step 3/4: Installing other dependencies..."
pip install --quiet \
    "google-generativeai>=0.5.0" \
    "pydantic>=2.0.0,<2.12" \
    "opencv-python-headless>=4.8.0" \
    "Pillow>=10.0.0" \
    "reportlab>=4.0.0" \
    "python-dotenv>=1.0.0" \
    "tqdm>=4.65.0"

# ============================================
# Step 4: Verify installations
# ============================================
echo ""
echo "========================================"
echo "🔍 Step 4/4: Verifying installations..."
echo "========================================"

python << 'EOF'
import sys

packages = [
    ('diffusers', None),
    ('transformers', None),
    ('accelerate', None),
    ('torch', None),
    ('PIL', None),
    ('cv2', None),
    ('reportlab', None),
    ('google.generativeai', None),
]

all_ok = True
for pkg, _ in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, '__version__', '✓')
        print(f'✅ {pkg}: {ver}')
    except ImportError:
        print(f'❌ {pkg}: NOT FOUND')
        all_ok = False

# Check CUDA
import torch
if torch.cuda.is_available():
    print(f'✅ CUDA: {torch.cuda.get_device_name(0)}')
else:
    print('⚠️ CUDA: Not available (will use CPU)')

if all_ok:
    print()
    print('🎉 All dependencies installed successfully!')
else:
    print()
    print('⚠️ Some packages missing - check above')
    sys.exit(1)
EOF

echo ""
echo "========================================"
echo "🎨 MangaGen Setup Complete!"
echo "========================================"
