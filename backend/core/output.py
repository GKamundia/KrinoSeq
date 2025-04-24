"""
Output generation utilities for filtered sequences.
"""

from typing import Dict, List, Set, Any, Optional
import os
import json
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from datetime import datetime

from .analysis import analyze_fasta_file


def filter_sequences_from_fasta(input_file: str, seq_ids_to_keep: Set[str], output_file: str) -> int:
    """
    Filter sequences from a FASTA file based on sequence IDs.
    
    Args:
        input_file: Path to input FASTA file
        seq_ids_to_keep: Set of sequence IDs to keep
        output_file: Path to output FASTA file
        
    Returns:
        Number of sequences written to output file
    """
    count = 0
    
    with open(output_file, 'w') as out_handle:
        for record in SeqIO.parse(input_file, "fasta"):
            if record.id in seq_ids_to_keep:
                SeqIO.write(record, out_handle, "fasta")
                count += 1
    
    return count


def generate_results_summary(input_file: str, 
                            output_file: str, 
                            pipeline_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a detailed summary of filtering results.
    
    Args:
        input_file: Path to input FASTA file
        output_file: Path to output FASTA file
        pipeline_report: Filter pipeline report
        
    Returns:
        Dictionary with summary information
    """
    # Analyze before and after files
    try:
        before_stats = analyze_fasta_file(input_file)
        after_stats = analyze_fasta_file(output_file)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "input_file": {
                "path": input_file,
                "name": os.path.basename(input_file),
                "sequence_count": before_stats["sequence_count"],
                "total_length": before_stats["basic_stats"]["total"],
                "min_length": before_stats["basic_stats"]["min"],
                "max_length": before_stats["basic_stats"]["max"],
                "mean_length": before_stats["basic_stats"]["mean"],
                "median_length": before_stats["basic_stats"]["median"],
                "std_dev": before_stats["basic_stats"]["std_dev"],
                "n50": before_stats["assembly_stats"]["n50"],
                "l50": before_stats["assembly_stats"]["l50"],
                "visualization_data": before_stats["visualization_data"]
            },
            "output_file": {
                "path": output_file,
                "name": os.path.basename(output_file),
                "sequence_count": after_stats["sequence_count"],
                "total_length": after_stats["basic_stats"]["total"],
                "min_length": after_stats["basic_stats"]["min"],
                "max_length": after_stats["basic_stats"]["max"],
                "mean_length": after_stats["basic_stats"]["mean"],
                "median_length": after_stats["basic_stats"]["median"],
                "std_dev": after_stats["basic_stats"]["std_dev"],
                "n50": after_stats["assembly_stats"]["n50"],
                "l50": after_stats["assembly_stats"]["l50"],
                "visualization_data": after_stats["visualization_data"]
            },
            "filtering": {
                "sequences_removed": before_stats["sequence_count"] - after_stats["sequence_count"],
                "length_removed": before_stats["basic_stats"]["total"] - after_stats["basic_stats"]["total"],
                "percent_sequences_kept": (
                    after_stats["sequence_count"] / before_stats["sequence_count"] * 100
                    if before_stats["sequence_count"] > 0 else 0
                ),
                "percent_length_kept": (
                    after_stats["basic_stats"]["total"] / before_stats["basic_stats"]["total"] * 100
                    if before_stats["basic_stats"]["total"] > 0 else 0
                ),
                "n50_change": after_stats["assembly_stats"]["n50"] - before_stats["assembly_stats"]["n50"],
                "l50_change": after_stats["assembly_stats"]["l50"] - before_stats["assembly_stats"]["l50"]
            },
            "pipeline_report": pipeline_report,
            "pipeline_stages": pipeline_report.get("stages", [])
        }
        
        return summary
    
    except Exception as e:
        return {
            "error": f"Error generating summary: {str(e)}",
            "pipeline_report": pipeline_report
        }


def save_results_to_json(summary: Dict[str, Any], output_json: str) -> None:
    """
    Save results summary to a JSON file.
    
    Args:
        summary: Results summary dictionary
        output_json: Path to output JSON file
    """
    with open(output_json, 'w') as f:
        json.dump(summary, f, indent=2)