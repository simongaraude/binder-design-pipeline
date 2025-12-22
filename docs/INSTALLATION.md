# Installation Guide

## System Requirements

### Hardware
- **GPU:** NVIDIA with 16GB+ VRAM (A10G, A100, RTX 4090)
- **RAM:** 32GB+ system memory
- **Storage:** 50GB+ free disk space
- **CPU:** Modern multi-core processor

### Software
- **OS:** Ubuntu 22.04 LTS (recommended)
- **CUDA:** Version 11.8+
- **Python:** 3.12 (installed automatically)

## Automated Installation
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/binder-design-pipeline.git
cd binder-design-pipeline

# Run installer
bash scripts/install.sh

# Restart terminal
source ~/.bashrc

# Activate environment
conda activate boltzgen

# Verify
python3 scripts/run_pipeline.py --version
```

## Manual Installation

### Step 1: Install Miniconda
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
$HOME/miniconda3/bin/conda init bash
source ~/.bashrc
```

### Step 2: Create Environment
```bash
conda create -n boltzgen python=3.12
conda activate boltzgen
```

### Step 3: Install Dependencies
```bash
# CUDA
conda install -c conda-forge cudatoolkit=11.8

# PyTorch
pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu118 \
  --break-system-packages

# Pipeline tools
pip install boltzgen --break-system-packages
pip install --upgrade boltz --break-system-packages
pip install biopython pandas numpy pyyaml --break-system-packages

# IPSAE
cd ~
git clone https://github.com/BCB-HKUST/IPSAE.git ipsae
```

## Verification
```bash
# Test GPU
python3 << 'TEST'
import torch
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
TEST

# Test tools
boltz --version
boltzgen --version
python3 ~/ipsae/ipsae.py --help
```

## Troubleshooting

### CUDA Not Available
```bash
# Check driver
nvidia-smi

# Install if needed
sudo apt-get install -y nvidia-driver-535
sudo reboot
```

### Import Errors
```bash
# Reinstall
pip uninstall torch boltzgen boltz -y
pip install torch --index-url https://download.pytorch.org/whl/cu118 --break-system-packages
pip install boltzgen boltz --break-system-packages
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues.
