#!/usr/bin/env python3
"""
Protein Binder Design Pipeline v2.0
BoltzGen + Boltz-2 + IPSAE

Main pipeline script for generating and scoring protein binders.
"""

import subprocess
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import shutil
from datetime import datetime
from Bio.PDB import PDBParser, MMCIFParser

__version__ = "2.0.0"

def log(msg):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def combine_boltz2_outputs(pae_file, pred_dir):
    """Combine Boltz-2 PAE and pLDDT files for IPSAE compatibility"""
    pae_basename = pae_file.stem.replace('pae_', '')
    plddt_file = pred_dir / f'plddt_{pae_basename}.npz'
    
    if not plddt_file.exists():
        return None
    
    pae_data = np.load(pae_file)
    plddt_data = np.load(plddt_file)
    
    combined_file = pred_dir / f'combined_{pae_basename}.npz'
    np.savez_compressed(combined_file,
                        pae=pae_data['pae'],
                        plddt=plddt_data['plddt'])
    return combined_file

def extract_sequences_from_cif(cif_file):
    """Extract protein sequences from CIF structure file"""
    parser = MMCIFParser(QUIET=True)
    structure = parser.get_structure('design', str(cif_file))
    
    sequences = {}
    for model in structure:
        for chain in model:
            residues = [r for r in chain if r.id[0] == ' ']
            if residues:
                from Bio.SeqUtils import seq1
                seq = ''.join([seq1(r.resname) for r in residues])
                sequences[chain.id] = seq
    
    return sequences

def run_boltzgen(config_file):
    """Execute BoltzGen design generation"""
    log("Running BoltzGen...")
    cmd = ['boltzgen', str(config_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def run_boltz2(yaml_file, output_dir, timeout=900):
    """Execute Boltz-2 structure prediction"""
    cmd = [
        'boltz', 'predict', str(yaml_file),
        '--use_msa_server',
        '--out_dir', str(output_dir),
        '--recycling_steps', '2',
        '--sampling_steps', '100',
        '--diffusion_samples', '1'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode == 0

def run_ipsae(combined_npz, cif_file, cutoff1=8, cutoff2=8, timeout=120):
    """Execute IPSAE interface scoring"""
    ipsae_script = Path.home() / 'ipsae' / 'ipsae.py'
    
    if not ipsae_script.exists():
        return None, None
    
    cmd = ['python3', str(ipsae_script), str(combined_npz), str(cif_file), 
           str(cutoff1), str(cutoff2)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    
    if result.returncode != 0:
        return None, None
    
    pred_dir = cif_file.parent
    ipsae_files = list(pred_dir.glob(f'*_{cutoff1:02d}_{cutoff2:02d}.txt'))
    
    if not ipsae_files:
        return None, None
    
    ipSAE = None
    pDockQ = None
    
    with open(ipsae_files[0]) as f:
        for line in f:
            if 'max' in line and line.strip() and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 11:
                    try:
                        ipSAE = float(parts[5])
                        pDockQ = float(parts[10])
                    except:
                        pass
                    break
    
    return ipSAE, pDockQ

def main():
    parser = argparse.ArgumentParser(
        description='Protein Binder Design Pipeline v' + __version__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--target', required=True, help='Target PDB/CIF file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--hotspots', required=True, 
                       help='Comma-separated hotspot residues (e.g., "10,15,20")')
    parser.add_argument('--num_designs', type=int, default=750,
                       help='Number of designs (fixed: 750)')
    parser.add_argument('--budget', type=int, default=375, 
                       help='Post-filtering budget (default: 375)')
    parser.add_argument('--binder_range', default=None, 
                       help='Binder length range "min,max" (auto if not specified)')
    parser.add_argument('--version', action='version', version=f'v{__version__}')
    
    args = parser.parse_args()
    
    # Validate inputs
    target = Path(args.target).absolute()
    if not target.exists():
        log(f"ERROR: Target file not found: {target}")
        return 1
    
    output_dir = Path(args.output).absolute()
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Parse structure
    if str(target).endswith('.cif'):
        parser_bio = MMCIFParser(QUIET=True)
    else:
        parser_bio = PDBParser(QUIET=True)
    
    try:
        structure = parser_bio.get_structure('target', str(target))
    except Exception as e:
        log(f"ERROR: Failed to parse structure: {e}")
        return 1
    
    # Get target size
    target_residues = [r for r in structure[0]['A'] if r.id[0] == ' ']
    target_size = len(target_residues)
    
    # Auto-determine binder range
    if args.binder_range:
        binder_range = args.binder_range
    else:
        if target_size < 100:
            binder_range = "60,120"
        elif target_size < 200:
            binder_range = "50,100"
        elif target_size < 300:
            binder_range = "40,80"
        else:
            binder_range = "60,130"
    
    try:
        binder_min, binder_max = map(int, binder_range.split(','))
    except:
        log(f"ERROR: Invalid binder_range: {binder_range}")
        return 1
    
    # Configuration
    log("=" * 80)
    log(f"PROTEIN BINDER DESIGN PIPELINE v{__version__}")
    log("=" * 80)
    log(f"Target: {target}")
    log(f"Target size: {target_size} residues")
    log(f"Output: {output_dir}")
    log(f"Designs: {args.num_designs}")
    log(f"Budget: {args.budget}")
    log(f"Binder range: {binder_min}-{binder_max} residues")
    
    # Parse hotspots
    try:
        hotspot_list = [int(x.strip()) for x in args.hotspots.split(',')]
    except:
        log(f"ERROR: Invalid hotspots: {args.hotspots}")
        return 1
    
    log(f"Hotspots: {hotspot_list}")
    
    # Create BoltzGen config
    boltzgen_yaml = output_dir / 'boltzgen_config.yaml'
    config = {
        'entities': [
            {
                'file': str(target),
                'include': [{'chain': 'A', 'binding': hotspot_list}]
            },
            {
                'protein': {'id': 'B', 'sequence': f"{binder_min}..{binder_max}"}
            }
        ],
        'designs': args.num_designs,
        'budget': args.budget,
        'output': str(output_dir / 'boltzgen_output')
    }
    
    with open(boltzgen_yaml, 'w') as f:
        yaml.dump(config, f)
    
    log(f"Config: {boltzgen_yaml}")
    
    # Run BoltzGen
    log("")
    log("=" * 80)
    log("PHASE 1: BOLTZGEN")
    log("=" * 80)
    
    if not run_boltzgen(boltzgen_yaml):
        log("ERROR: BoltzGen failed")
        return 1
    
    log("BoltzGen completed")
    
    # Cleanup intermediates
    log("Cleaning up...")
    boltzgen_out = output_dir / 'boltzgen_output'
    for int_dir in ['intermediate_designs', 'intermediate_designs_folded']:
        path = boltzgen_out / 'output' / int_dir
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    
    # Rank designs
    log("")
    log("=" * 80)
    log("PHASE 2: RANKING")
    log("=" * 80)
    
    designs_dir = boltzgen_out / 'output' / 'intermediate_designs_inverse_folded'
    npz_dir = designs_dir / 'fold_out_npz'
    
    if not npz_dir.exists():
        log(f"ERROR: Output not found: {npz_dir}")
        return 1
    
    designs = []
    for npz_file in npz_dir.glob('*.npz'):
        try:
            data = np.load(npz_file)
            designs.append({
                'design_name': npz_file.stem,
                'design_to_target_iptm': float(data.get('design_to_target_iptm', 0)),
                'iptm': float(data.get('iptm', 0)),
                'ptm': float(data.get('ptm', 0))
            })
        except Exception as e:
            log(f"Warning: {npz_file.name}: {e}")
    
    if not designs:
        log("ERROR: No designs found")
        return 1
    
    df = pd.DataFrame(designs)
    df = df.sort_values('design_to_target_iptm', ascending=False)
    
    log(f"Total designs: {len(df)}")
    log("")
    log("Top 10 by iPTM:")
    print(df.head(10)[['design_name', 'design_to_target_iptm', 'iptm', 'ptm']].to_string(index=False))
    
    # Score top 200
    log("")
    log("=" * 80)
    log("PHASE 3: BOLTZ-2 + IPSAE (TOP 200)")
    log("=" * 80)

    top_200 = df.head(200)
    boltz2_dir = output_dir / 'boltz2_scoring'
    boltz2_dir.mkdir(exist_ok=True)
    
    results = []

    for idx, row in top_200.iterrows():
        design_name = row['design_name']
        log(f"")
        log(f"[{idx+1}/200] {design_name} (iPTM={row['design_to_target_iptm']:.4f})")
        
        cif_file = designs_dir / f'{design_name}.cif'
        if not cif_file.exists():
            log(f"  Warning: CIF not found")
            continue
        
        sequences = extract_sequences_from_cif(cif_file)
        if 'B' not in sequences:
            log(f"  Warning: Chain B not found")
            continue
        
        binder_seq = sequences['B']
        target_seq = sequences['A']
        
        # Boltz-2 input
        yaml_file = boltz2_dir / f'{design_name}_input.yaml'
        with open(yaml_file, 'w') as f:
            yaml.dump({
                'sequences': [
                    {'protein': {'id': 'A', 'sequence': binder_seq}},
                    {'protein': {'id': 'B', 'sequence': target_seq}}
                ]
            }, f)
        
        # Run Boltz-2
        design_boltz_out = boltz2_dir / f'{design_name}_boltz2'
        if not run_boltz2(yaml_file, design_boltz_out):
            log(f"  Error: Boltz-2 failed")
            continue
        
        log(f"  Boltz-2 completed")
        
        # Find outputs
        pred_dir = design_boltz_out / f'boltz_results_{design_name}_input' / 'predictions' / f'{design_name}_input'
        pae_files = list(pred_dir.glob('pae_*.npz'))
        plddt_files = list(pred_dir.glob('plddt_*.npz'))
        cif_files = list(pred_dir.glob('*.cif'))
        
        if not (pae_files and plddt_files and cif_files):
            log(f"  Warning: Incomplete outputs")
            continue
        
        # Combine for IPSAE
        combined_npz = combine_boltz2_outputs(pae_files[0], pred_dir)
        if not combined_npz:
            continue
        
        # Run IPSAE
        ipSAE, pDockQ = run_ipsae(combined_npz, cif_files[0])
        
        # Calculate metrics
        pae_data = np.load(pae_files[0])
        plddt_data = np.load(plddt_files[0])
        
        pae = pae_data['pae']
        plddt = plddt_data['plddt']
        
        binder_len = len(binder_seq)
        interface_pae = pae[:binder_len, binder_len:].mean()
        avg_plddt = plddt.mean()
        
        results.append({
            'rank': idx + 1,
            'design_name': design_name,
            'binder_sequence': binder_seq,
            'binder_length': len(binder_seq),
            'interface_pae': float(interface_pae),
            'avg_plddt': float(avg_plddt),
            'ipSAE': float(ipSAE) if ipSAE else None,
            'pDockQ': float(pDockQ) if pDockQ else None,
            'design_to_target_iptm': float(row['design_to_target_iptm']),
            'iptm': float(row['iptm']),
            'ptm': float(row['ptm']),
            'structure_file': str(cif_files[0])
        })
        
        log(f"  IPSAE completed")
    
    log("")
    log("Scoring completed")
    
    # Compile results
    log("")
    log("=" * 80)
    log("PHASE 4: RESULTS")
    log("=" * 80)
    
    final_dir = output_dir / 'FINAL_RESULTS'
    final_dir.mkdir(exist_ok=True)
    
    # Copy structures
    structures_dir = final_dir / 'structures'
    structures_dir.mkdir(exist_ok=True)
    for cif_file in designs_dir.glob('*.cif'):
        shutil.copy(cif_file, structures_dir / cif_file.name)
    
    # Merge results
    results_df = pd.DataFrame(results)
    all_df = df.merge(
        results_df[['design_name', 'binder_sequence', 'binder_length', 
                   'ipSAE', 'pDockQ', 'interface_pae', 'avg_plddt']],
        on='design_name', how='left'
    )
    
    all_df['sort_score'] = all_df['ipSAE'].fillna(0)
    all_df = all_df.sort_values('sort_score', ascending=False)
    all_df = all_df.drop('sort_score', axis=1)
    
    # Save
    csv_file = final_dir / 'all_designs_complete.csv'
    all_df.to_csv(csv_file, index=False)
    
    log(f"Results: {csv_file}")
    
    # Show top designs
    scored_df = all_df[all_df['ipSAE'].notna()].head(10)
    if len(scored_df) > 0:
        log("")
        log("Top 10 scored designs:")
        print(scored_df[['rank', 'design_name', 'ipSAE', 'pDockQ', 
                         'design_to_target_iptm']].to_string(index=False))
    
    # Copy IPSAE outputs
    ipsae_dir = final_dir / 'ipsae_outputs'
    ipsae_dir.mkdir(exist_ok=True)
    for res in results:
        pred_dir = Path(res['structure_file']).parent
        for ipsae_file in pred_dir.glob('*_08_08.txt'):
            shutil.copy(ipsae_file, ipsae_dir / f"{res['design_name']}_ipsae.txt")
    
    log("")
    log("=" * 80)
    log("PIPELINE COMPLETE")
    log("=" * 80)
    log(f"Total designs: {len(df)}")
    log(f"Scored: {len(results)}")
    log(f"Results: {final_dir}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
