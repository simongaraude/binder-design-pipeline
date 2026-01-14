# Protein Binder Design Pipeline

A production-ready pipeline for computational design of protein binders using BoltzGen, Boltz-2, and IPSAE scoring.

## Overview

This pipeline generates de novo protein binders against a target protein of interest. The workflow consists of:

1. **BoltzGen** - Generates diverse binder designs
2. **Boltz-2** - Predicts 3D structures with high accuracy
3. **IPSAE** - Scores binding interfaces

### Key Features

- Automated end-to-end workflow
- GPU-accelerated structure prediction
- Comprehensive interface scoring (ipSAE, pDockQ, iPTM)
- Generates 750 designs, refines top 200
- Production-ready with error handling and logging

## Requirements

### Hardware
- NVIDIA GPU with 16GB+ VRAM (A10G, A100, or equivalent)
- 50GB+ disk space
- 32GB+ RAM

### Software
- Ubuntu 22.04 LTS (or compatible Linux)
- CUDA 11.8+
- Miniconda/Anaconda

## Installation

### Quick Start
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/binder-design-pipeline.git
cd binder-design-pipeline

# Run automated installation
bash scripts/install.sh

# Activate environment
conda activate boltzgen
```

### Manual Installation

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.

## Usage

### Basic Usage
```bash
python3 scripts/run_pipeline.py \
  --target /path/to/target.pdb \
  --output ./results \
  --hotspots "10,15,20,25,30" \
  --num_designs 100 \
  --budget 50
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--target` | Yes | - | Path to target PDB/CIF file |
| `--output` | Yes | - | Output directory path |
| `--hotspots` | Yes | - | Comma-separated residue numbers (chain A) |
| `--num_designs` | No | 750 | Number of binder designs to generate (fixed: 750) |
| `--budget` | No | 375 | Post-filtering budget (typically half of num_designs) |
| `--binder_range` | No | Auto | Binder length range (e.g., "60,130") |

### Example
```bash
# Generate 750 binder designs for your target
python3 scripts/run_pipeline.py \
  --target examples/target_protein.pdb \
  --output ./my_binders \
  --hotspots "45,48,52,89,93" \
  --num_designs 750 \
  --budget 375
```

## Identifying Hotspot Residues

### Option 1: Known Binding Site

If you know the binding site from literature or experimental data, use those residue numbers directly.

### Option 2: Automated Detection

For protein complexes with known binding partners:
```bash
python3 scripts/detect_interface.py your_complex.pdb
```

This outputs interface residues between chains that you can use as hotspots.

### Option 3: Computational Prediction

Use tools like:
- PyMOL with surface/pocket detection
- FTMap (https://ftmap.bu.edu/)
- P2Rank (https://github.com/rdk/p2rank)

## Output

### Directory Structure
```
output_folder/
├── FINAL_RESULTS/
│   ├── all_designs_complete.csv    # Complete results with scores
│   ├── structures/                 # All design structures (CIF)
│   │   ├── design_000.cif
│   │   ├── design_001.cif
│   │   └── ...
│   └── ipsae_outputs/             # Detailed scores for top 200
│       ├── design_XXX_ipsae.txt
│       └── ...
└── boltzgen_output/               # Intermediate files
```

### Results CSV Columns

| Column | Description | Good Values |
|--------|-------------|-------------|
| `design_name` | Unique design identifier | - |
| `binder_sequence` | Amino acid sequence | - |
| `binder_length` | Sequence length in residues | 50-130 |
| `ipSAE` | Interface predicted Surface-Accessible Exposed area | >0.5 good, >0.8 excellent |
| `pDockQ` | Predicted DockQ score | >0.23 acceptable, >0.5 good |
| `design_to_target_iptm` | Interface predicted TM-score | >0.4 good, >0.6 excellent |
| `iptm` | Overall interface pTM | Higher is better |
| `ptm` | Predicted TM-score | >0.5 good structure |

### Quality Tiers

**Excellent (Priority for experimental validation)**
- ipSAE > 0.8
- pDockQ > 0.6
- design_to_target_iptm > 0.6

**Good (Worth testing)**
- ipSAE > 0.5
- pDockQ > 0.4
- design_to_target_iptm > 0.5

**Moderate (Backup candidates)**
- ipSAE > 0.3
- pDockQ > 0.23
- design_to_target_iptm > 0.4

## Runtime Estimates

| Designs | GPU | Time | Cost (AWS g5.2xlarge) |
|---------|-----|------|-----------------------|
| 50 | A10G | 8-10 hours | $10-12 |
| 100 | A10G | 12-15 hours | $15-18 |
| 200 | A10G | 24-30 hours | $30-36 |
| 500 | A10G | 3-4 days | $90-120 |
| 750 | A10G | 4-5 days | $120-150 |

## AWS Deployment

See [docs/AWS_SETUP.md](docs/AWS_SETUP.md) for instructions on running the pipeline on AWS EC2.

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

## Citation

If you use this pipeline in your research, please cite:

**BoltzGen:**
```bibtex
@article{wohlwend2024boltzgen,
  title={Generative design of de novo proteins based on secondary structure constraints using an attention-based diffusion model},
  author={Wohlwend, Jeremy and others},
  journal={bioRxiv},
  year={2024}
}
```

**Boltz:**
```bibtex
@article{wohlwend2024boltz,
  title={Boltz-1: Democratizing biomolecular interaction modeling},
  author={Wohlwend, Jeremy and others},
  year={2024}
}
```

**IPSAE:**
```bibtex
@article{zhang2023ipsae,
  title={Protein-protein docking with interface residue restraints},
  author={Zhang, Y and Sanner, MF},
  journal={Bioinformatics},
  year={2023}
}
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- **Issues:** Use GitHub Issues for bug reports and feature requests
- **Discussions:** Use GitHub Discussions for questions and help

## Acknowledgments

This pipeline integrates:
- BoltzGen (https://github.com/jwohlwend/boltzgen)
- Boltz-2 (https://github.com/jwohlwend/boltz)
- IPSAE (https://github.com/DunbrackLab/IPSAE)
