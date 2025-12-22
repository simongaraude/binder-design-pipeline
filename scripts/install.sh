#!/bin/bash
# Automated Installation Script for Binder Design Pipeline
# Compatible with Ubuntu 22.04 and similar Linux distributions

set -e

echo "=========================================="
echo "Binder Design Pipeline Installation"
echo "=========================================="

# Check GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "WARNING: nvidia-smi not found"
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo ""
echo "[1/7] Updating system..."
sudo apt-get update -qq
sudo apt-get install -y wget git build-essential curl

# Install Miniconda
echo ""
echo "[2/7] Installing Miniconda..."
if [ ! -d "$HOME/miniconda3" ]; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3.sh
    bash ~/miniconda3.sh -b -p $HOME/miniconda3
    rm ~/miniconda3.sh
    echo "Miniconda installed"
else
    echo "Miniconda already installed"
fi

# Initialize conda
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"
$HOME/miniconda3/bin/conda init bash

# Create environment
echo ""
echo "[3/7] Creating environment..."
conda create -y -n boltzgen python=3.12

# Activate and install
conda activate boltzgen

echo ""
echo "[4/7] Installing CUDA..."
conda install -y -c conda-forge cudatoolkit=11.8

echo ""
echo "[5/7] Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --break-system-packages

echo ""
echo "[6/7] Installing pipeline tools..."
pip install boltzgen --break-system-packages
pip install --upgrade boltz --break-system-packages
pip install biopython pandas numpy pyyaml --break-system-packages

echo ""
echo "[7/7] Installing IPSAE..."
cd ~
if [ ! -d "ipsae" ]; then
    git clone https://github.com/BCB-HKUST/IPSAE.git ipsae
    echo "IPSAE installed"
else
    echo "IPSAE already installed"
fi

# Verify
echo ""
echo "=========================================="
echo "Verifying Installation"
echo "=========================================="

python3 << 'VERIFY'
import torch
import sys
print("Python:", sys.version.split()[0])
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
VERIFY

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart terminal: exit"
echo "  2. Activate: conda activate boltzgen"
echo "  3. Test: python3 scripts/run_pipeline.py --help"
