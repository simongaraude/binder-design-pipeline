# Troubleshooting Guide

## Common Issues

### CUDA Out of Memory

**Symptom:** `RuntimeError: CUDA out of memory`

**Solutions:**
```bash
# Reduce binder length
--binder_range "40,80"

# Reduce designs
--num_designs 100

# Upgrade GPU instance
```

### Disk Space Full

**Symptom:** `OSError: No space left on device`

**Solutions:**
```bash
# Check space
df -h /

# Clean conda
conda clean --all -y

# Remove temp files
rm -rf /tmp/* ~/.cache/*
```

### Pipeline Crashes

**Check logs:**
```bash
tail -100 output/pipeline.log
```

**Check GPU:**
```bash
nvidia-smi
```

**Check memory:**
```bash
free -h
```

### BoltzGen Fails

**Verify input:**
```bash
python3 << 'TEST'
from Bio.PDB import PDBParser
parser = PDBParser()
structure = parser.get_structure('test', 'target.pdb')
print("Chains:", [c.id for c in structure[0]])
TEST
```

### Invalid Hotspots

**Correct format:**
- `"10,15,20"` - Correct
- `"10, 15"` - Wrong (spaces)
- `"A10,A15"` - Wrong (chain IDs)

## Performance Issues

**Expected times per design:**
- BoltzGen: 1-2 minutes
- Boltz-2: 5-6 minutes
- IPSAE: 30 seconds

**If slower, check:**
```bash
# GPU utilization
watch -n 1 nvidia-smi

# CPU usage
htop

# Network (for MSA)
speedtest-cli
```

## Getting Help

Include when reporting:
```bash
# System info
uname -a

# GPU info
nvidia-smi

# Environment
conda list

# Logs
tail -100 pipeline.log
```

Submit to GitHub Issues with this information.
