#!/usr/bin/env python3
"""
Interface Residue Detection

Identifies interface residues between protein chains in a complex.
Useful for determining hotspot residues for binder design.

Usage:
    python3 detect_interface.py structure.pdb [--cutoff 8.0]
"""

from Bio.PDB import PDBParser, MMCIFParser
import numpy as np
import argparse
import sys

def detect_interface(structure_file, cutoff=8.0):
    """Detect interface residues using C-alpha distance"""
    
    # Parse structure
    if structure_file.endswith('.cif'):
        parser = MMCIFParser(QUIET=True)
    else:
        parser = PDBParser(QUIET=True)
    
    structure = parser.get_structure('complex', structure_file)
    chains = list(structure[0])
    
    if len(chains) < 2:
        return None, chains
    
    # Detect interfaces
    interfaces = {}
    
    for i, chain_a in enumerate(chains):
        interfaces[chain_a.id] = set()
        
        for j, chain_b in enumerate(chains):
            if i >= j:
                continue
            
            for res_a in chain_a:
                if res_a.id[0] == ' ' and 'CA' in res_a:
                    for res_b in chain_b:
                        if res_b.id[0] == ' ' and 'CA' in res_b:
                            dist = np.linalg.norm(
                                res_a['CA'].coord - res_b['CA'].coord
                            )
                            if dist <= cutoff:
                                interfaces[chain_a.id].add(res_a.id[1])
                                if chain_b.id not in interfaces:
                                    interfaces[chain_b.id] = set()
                                interfaces[chain_b.id].add(res_b.id[1])
    
    return interfaces, chains

def main():
    parser = argparse.ArgumentParser(
        description='Detect interface residues in protein complex'
    )
    
    parser.add_argument('structure', help='Input PDB or CIF file')
    parser.add_argument('--cutoff', type=float, default=8.0,
                       help='C-alpha distance cutoff in Angstroms (default: 8.0)')
    
    args = parser.parse_args()
    
    print(f"\nAnalyzing: {args.structure}")
    print(f"Cutoff: {args.cutoff} Angstroms\n")
    
    interfaces, chains = detect_interface(args.structure, args.cutoff)
    
    if interfaces is None:
        print("ERROR: Single chain structure")
        print("Provide a protein complex with multiple chains")
        return 1
    
    # Display results
    print("=" * 70)
    print("STRUCTURE COMPOSITION")
    print("=" * 70)
    
    for chain in chains:
        residues = [r for r in chain if r.id[0] == ' ']
        print(f"Chain {chain.id}: {len(residues)} residues")
    
    print("\n" + "=" * 70)
    print(f"INTERFACE RESIDUES ({args.cutoff}A cutoff)")
    print("=" * 70)
    
    for chain_id, residues in sorted(interfaces.items()):
        if residues:
            residues_sorted = sorted(list(residues))
            print(f"\nChain {chain_id}: {len(residues_sorted)} interface residues")
            print(f'  Residues: {",".join(map(str, residues_sorted))}')
            print(f'\n  For pipeline:')
            print(f'  --hotspots "{",".join(map(str, residues_sorted))}"')
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print("\n1. Use ALL interface residues for maximum coverage")
    print("2. Or select 5-10 key residues based on biological knowledge")
    print("3. Consider residues with known functional importance")
    print("4. Balance specificity and design space\n")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
