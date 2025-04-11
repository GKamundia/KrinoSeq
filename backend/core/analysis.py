"""
Integrated sequence analysis utilities.
"""

from typing import Dict, List, Any, Optional
import os
import glob
from .parser import get_sequence_lengths
from .statistics import calculate_basic_stats, calculate_quartiles, calculate_n50, calculate_l50
from .visualization import generate_histogram_data, generate_kde_data, generate_cumulative_distribution_data


def analyze_fasta_file(file_path: str) -> Dict[str, Any]:
    """
    Perform complete analysis of a FASTA file.
    
    Args:
        file_path: Path to the FASTA file
        
    Returns:
        Dictionary containing all analysis results
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get sequence lengths
    seq_lengths_dict = get_sequence_lengths(file_path)
    seq_lengths = list(seq_lengths_dict.values())
    
    # Calculate statistics
    basic_stats = calculate_basic_stats(seq_lengths)
    quartile_stats = calculate_quartiles(seq_lengths)
    n50 = calculate_n50(seq_lengths)
    l50 = calculate_l50(seq_lengths)
    
    # Generate visualization data
    histogram_data = generate_histogram_data(seq_lengths)
    kde_data = generate_kde_data(seq_lengths)
    cumulative_data = generate_cumulative_distribution_data(seq_lengths)
    
    # Combine all results
    return {
        "file_info": {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size_bytes": os.path.getsize(file_path)
        },
        "sequence_count": len(seq_lengths),
        "basic_stats": basic_stats,
        "quartile_stats": quartile_stats,
        "assembly_stats": {
            "n50": n50,
            "l50": l50
        },
        "visualization_data": {
            "histogram": histogram_data,
            "kde": kde_data,
            "cumulative": cumulative_data
        }
    }


def analyze_multiple_fasta_files(file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple FASTA files and return results for each.
    
    Args:
        file_paths: List of paths to FASTA files
        
    Returns:
        Dictionary mapping file names to their analysis results
    """
    results = {}
    
    for file_path in file_paths:
        try:
            file_name = os.path.basename(file_path)
            results[file_name] = analyze_fasta_file(file_path)
        except Exception as e:
            results[os.path.basename(file_path)] = {"error": str(e)}
    
    return results


def analyze_directory(directory_path: str, pattern: str = "*.fasta") -> Dict[str, Dict[str, Any]]:
    """
    Analyze all FASTA files in a directory matching the given pattern.
    
    Args:
        directory_path: Path to directory containing FASTA files
        pattern: Glob pattern to match FASTA files (default: "*.fasta")
        
    Returns:
        Dictionary mapping file names to their analysis results
    """
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Get all matching files in the directory
    file_paths = glob.glob(os.path.join(directory_path, pattern))
    
    if not file_paths:
        return {"warning": f"No files matching '{pattern}' found in {directory_path}"}
    
    return analyze_multiple_fasta_files(file_paths)


def compare_fasta_files(file_paths: List[str], metric: str = "n50") -> Dict[str, Any]:
    """
    Compare multiple FASTA files based on a specific metric.
    
    Args:
        file_paths: List of paths to FASTA files
        metric: Metric to compare (default: "n50")
        
    Returns:
        Dictionary with comparison results
    """
    valid_metrics = ["n50", "l50", "mean", "median", "min", "max", "sequence_count"]
    
    if metric not in valid_metrics:
        raise ValueError(f"Invalid metric: {metric}. Must be one of {valid_metrics}")
    
    results = analyze_multiple_fasta_files(file_paths)
    comparison = {"metric": metric, "values": {}}
    
    for file_name, analysis in results.items():
        if "error" in analysis:
            comparison["values"][file_name] = None
            continue
            
        if metric in ["n50", "l50"]:
            comparison["values"][file_name] = analysis["assembly_stats"][metric]
        elif metric in ["mean", "median", "min", "max"]:
            comparison["values"][file_name] = analysis["basic_stats"][metric]
        elif metric == "sequence_count":
            comparison["values"][file_name] = analysis["sequence_count"]
    
    # Add ranking
    sorted_files = sorted(
        comparison["values"].keys(),
        key=lambda k: (comparison["values"][k] is not None, comparison["values"][k] or 0),
        reverse=(metric != "l50")  # For L50, lower is better
    )
    
    comparison["ranking"] = {file_name: idx+1 for idx, file_name in enumerate(sorted_files)}
    
    return comparison