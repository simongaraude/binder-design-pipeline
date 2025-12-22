# Examples

## Example Target

Download example structure:
```bash
wget https://files.rcsb.org/download/6M0J.pdb -O example_target.pdb
```

## Example Run
```bash
# Detect hotspots
python3 ../scripts/detect_interface.py example_target.pdb

# Run pipeline
python3 ../scripts/run_pipeline.py \
  --target example_target.pdb \
  --output ./example_results \
  --hotspots "45,48,52,89,93" \
  --num_designs 100 \
  --budget 50
```

## Expected Output

After 12-15 hours:
- 100 binder designs
- Top 20 scored with Boltz-2 + IPSAE
- Complete CSV with metrics
- Structure files (CIF format)
