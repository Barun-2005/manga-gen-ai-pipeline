#!/bin/bash
# ============================================
# MangaGen - Kaggle Dependencies Installer
# ============================================
# Run this FIRST in a Kaggle notebook cell:
#   !pip install "numpy<2.0.0" --quiet --force-reinstall
#   # Then restart kernel, then run:
#   !bash install_kaggle_deps.sh
# ============================================

set -e  # Exit on any error

echo "🎨 MangaGen Kaggle Setup Starting..."
echo "========================================"

# ============================================
# Step 1: Fix numpy and matplotlib FIRST
# ============================================
echo "🔧 Step 1/4: Fixing numpy + matplotlib compatibility..."

# Force numpy 1.x
pip install "numpy>=1.24.0,<2.0.0" --quiet --force-reinstall

# CRITICAL: Reinstall matplotlib to get numpy 1.x compatible binaries
echo "   Reinstalling matplotlib for numpy 1.x compatibility..."
pip uninstall matplotlib -y --quiet 2>/dev/null || true
pip install "matplotlib>=3.7.0,<3.9.0" --quiet --force-reinstall --no-cache-dir

# Also fix opencv
pip install "opencv-python-headless>=4.8.0,<4.11.0" --quiet --force-reinstall --no-cache-dir

echo "   ✅ numpy + matplotlib fixed"

# ============================================
# Step 2: Install diffusers ecosystem
# ============================================
echo "🎨 Step 2/4: Installing diffusers ecosystem..."

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

# Check numpy version FIRST
import numpy as np
numpy_ver = np.__version__
print(f'✅ numpy: {numpy_ver}')
if numpy_ver.startswith('2'):
    print('❌ CRITICAL: numpy 2.x detected! This will cause issues.')
    print('   Run: pip install "numpy<2.0.0" --force-reinstall')
    print('   Then restart the kernel and try again.')
    sys.exit(1)

# Check matplotlib works
try:
    import matplotlib
    print(f'✅ matplotlib: {matplotlib.__version__}')
except Exception as e:
    print(f'❌ matplotlib broken: {e}')
    sys.exit(1)

# Check other packages
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
    except ImportError as e:
        print(f'❌ {pkg}: NOT FOUND - {e}')
        all_ok = False

# Check CUDA
import torch
if torch.cuda.is_available():
    print(f'✅ CUDA: {torch.cuda.get_device_name(0)}')
else:
    print('⚠️ CUDA: Not available (will use CPU)')

# Try importing SDXL pipeline (the critical test!)
print('')
print('🧪 Testing SDXL pipeline import...')
try:
    from diffusers import StableDiffusionXLPipeline
    print('✅ StableDiffusionXLPipeline: can import!')
except Exception as e:
    print(f'❌ StableDiffusionXLPipeline: {e}')
    all_ok = False

if all_ok:
    print()
    print('🎉 All dependencies installed successfully!')
    print('🚀 GPU image generation should work!')
else:
    print()
    print('⚠️ Some packages missing - check above')
    sys.exit(1)
EOF

echo ""
echo "========================================"
echo "🎨 MangaGen Setup Complete!"
echo "========================================"
