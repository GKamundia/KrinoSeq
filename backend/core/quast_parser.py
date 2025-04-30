"""
QUAST report parser module for advanced processing of QUAST output files.
Provides specialized functions for extracting, categorizing, and summarizing metrics.
"""

import os
import csv
import json
import logging
import re
from typing import Dict, List, Tuple, Optional, Any, Union, Set
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define metric categories and their descriptions
METRIC_CATEGORIES = {
    "contig_counts": "Statistics about the number of contigs in the assembly",
    "length_stats": "Assembly size and length-based statistics",
    "assembly_quality": "N50, L50 and other assembly quality metrics",
    "composition": "GC content, Ns, and sequence composition metrics",
    "reference_based": "Metrics using the reference genome comparison",
    "gene_stats": "Gene prediction and annotation metrics",
    "accuracy": "Misassemblies and accuracy metrics",
    "other": "Other miscellaneous metrics"
}

# Define essential metrics for different analyses
ESSENTIAL_METRICS = {
    "basic": [
        "# contigs", 
        "Total length", 
        "N50", 
        "L50", 
        "GC (%)"
    ],
    "detailed": [
        "# contigs", 
        "# contigs (>= 1000 bp)",
        "Total length", 
        "Total length (>= 1000 bp)",
        "Largest contig",
        "N50", 
        "L50", 
        "N75",
        "L75",
        "GC (%)"
    ],
    "reference_based": [
        "Genome fraction (%)",
        "Duplication ratio",
        "# misassemblies",
        "# mismatches per 100 kbp",
        "# indels per 100 kbp",
        "NGA50",
        "LGA50"
    ],
    "gene_based": [
        "# predicted genes (unique)",
        "Complete BUSCO (%)",
        "Partial BUSCO (%)"
    ]
}

# Patterns for parsing QUAST report headers
CONTIG_SIZE_PATTERN = re.compile(r"# contigs \(>= (\d+) bp\)")
LENGTH_SIZE_PATTERN = re.compile(r"Total length \(>= (\d+) bp\)")


def parse_quast_report_file(report_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse a QUAST report.tsv file directly from disk.
    
    Args:
        report_path: Path to the report.tsv file
        
    Returns:
        Dictionary of metrics organized by assembly
    """
    metrics = {}
    
    try:
        with open(report_path, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)  # First row is headers
            
            # First column is the metric name, other columns are assembly names
            assembly_names = headers[1:]
            
            # Initialize dictionaries for each assembly
            for name in assembly_names:
                metrics[name] = {}
            
            # Read metric rows
            for row in reader:
                if not row:
                    continue
                    
                metric_name = row[0]
                values = row[1:]
                
                # Store values for each assembly
                for i, value in enumerate(values):
                    if i < len(assembly_names):
                        assembly = assembly_names[i]
                        # Try to convert to numeric if possible
                        metrics[assembly][metric_name] = normalize_value(value)
    except Exception as e:
        logger.error(f"Error parsing QUAST report: {str(e)}")
        return {}
    
    return metrics


def parse_transposed_report_file(report_path: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Parse a QUAST transposed_report.tsv file directly from disk.
    
    Args:
        report_path: Path to the transposed_report.tsv file
        
    Returns:
        Dictionary of metrics organized by category and then by metric
    """
    metrics = {}
    assembly_names = []
    
    try:
        with open(report_path, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            
            # Read all rows
            for row in reader:
                if not row or len(row) < 2:
                    continue
                    
                metric_name = row[0]
                values = row[1:]
                
                # Skip the headers row
                if metric_name == "Assembly":
                    assembly_names = values
                    continue
                
                # Determine metric category
                category = categorize_metric(metric_name)
                
                # Initialize category if needed
                if category not in metrics:
                    metrics[category] = {}
                
                # Store metric values by assembly
                metric_values = {}
                for i, value in enumerate(values):
                    if i < len(assembly_names):
                        assembly = assembly_names[i]
                        metric_values[assembly] = normalize_value(value)
                
                metrics[category][metric_name] = metric_values
    except Exception as e:
        logger.error(f"Error parsing transposed QUAST report: {str(e)}")
        return {}
    
    return metrics


def normalize_value(value: str) -> Union[float, int, str]:
    """
    Convert string values to appropriate numeric types when possible.
    
    Args:
        value: String value from QUAST report
        
    Returns:
        Normalized value (float, int, or string)
    """
    try:
        # Handle percentages
        if "%" in value:
            return float(value.replace("%", ""))
        
        # Handle thousands separators
        if "," in value:
            return float(value.replace(",", ""))
        
        # Try to convert to numeric
        float_val = float(value)
        
        # If it's an integer, convert to int
        if float_val.is_integer():
            return int(float_val)
        
        return float_val
    except (ValueError, TypeError):
        # Return as string if conversion fails
        return value


def categorize_metric(metric_name: str) -> str:
    """
    Categorize a QUAST metric based on its name.
    
    Args:
        metric_name: Name of the metric
        
    Returns:
        Category name from METRIC_CATEGORIES
    """
    # Map metrics to categories
    if any(keyword in metric_name.lower() for keyword in ["# contigs", "contig count"]):
        return "contig_counts"
    elif any(keyword in metric_name.lower() for keyword in ["length", "total", "largest", "shortest"]):
        return "length_stats"
    elif any(keyword in metric_name.lower() for keyword in ["n50", "l50", "n75", "l75", "n90", "l90"]):
        return "assembly_quality"
    elif any(keyword in metric_name.lower() for keyword in ["gc", "n's", "gap"]):
        return "composition"
    elif any(keyword in metric_name.lower() for keyword in ["genome fraction", "duplication", "nga", "lga", "align", "reference"]):
        return "reference_based"
    elif any(keyword in metric_name.lower() for keyword in ["gene", "busco", "predicted"]):
        return "gene_stats"
    elif any(keyword in metric_name.lower() for keyword in ["misassembl", "mismatch", "indel"]):
        return "accuracy"
    else:
        return "other"


def extract_essential_metrics(
    metrics: Dict[str, Dict[str, Any]], 
    metric_set: str = "basic"
) -> Dict[str, Dict[str, Any]]:
    """
    Extract essential metrics based on the specified set.
    
    Args:
        metrics: Dictionary of all metrics from parse_quast_report
        metric_set: Which set of metrics to extract ('basic', 'detailed', 
                   'reference_based', 'gene_based')
        
    Returns:
        Dictionary containing only essential metrics
    """
    essential = {}
    
    # Get the list of metrics for this set
    essential_list = ESSENTIAL_METRICS.get(metric_set, ESSENTIAL_METRICS["basic"])
    
    # Extract metrics for each assembly
    for assembly_name, assembly_metrics in metrics.items():
        essential[assembly_name] = {}
        
        # Extract specified metrics
        for metric_name, value in assembly_metrics.items():
            if metric_name in essential_list:
                essential[assembly_name][metric_name] = value
    
    return essential


def has_reference_metrics(metrics: Dict[str, Dict[str, Any]]) -> bool:
    """
    Check if the metrics include reference-based analysis.
    
    Args:
        metrics: Dictionary of metrics from parse_quast_report
        
    Returns:
        True if reference-based metrics are present
    """
    # Check if any assembly has reference-based metrics
    for assembly_metrics in metrics.values():
        if any(ref_metric in assembly_metrics for ref_metric in ESSENTIAL_METRICS["reference_based"]):
            return True
    
    return False


def has_gene_metrics(metrics: Dict[str, Dict[str, Any]]) -> bool:
    """
    Check if the metrics include gene prediction metrics.
    
    Args:
        metrics: Dictionary of metrics from parse_quast_report
        
    Returns:
        True if gene prediction metrics are present
    """
    # Check if any assembly has gene prediction metrics
    for assembly_metrics in metrics.values():
        if any(gene_metric in assembly_metrics for gene_metric in ESSENTIAL_METRICS["gene_based"]):
            return True
    
    return False


def calculate_contig_size_distribution(
    metrics: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Dict[str, int]]]:
    """
    Calculate contig size distribution statistics from metrics.
    
    Args:
        metrics: Dictionary of metrics from parse_quast_report
        
    Returns:
        Dictionary with contig counts in different size ranges
    """
    distribution = {}
    
    for assembly_name, assembly_metrics in metrics.items():
        distribution[assembly_name] = {"counts": {}, "percentages": {}}
        
        # Find contig count metrics of different sizes
        contig_counts = {}
        total_contigs = None
        
        # First find the total number of contigs
        if "# contigs" in assembly_metrics:
            total_contigs = assembly_metrics["# contigs"]
            contig_counts["all"] = total_contigs
        
        # Find size-based metrics
        for metric in assembly_metrics:
            size_match = CONTIG_SIZE_PATTERN.match(metric)
            if size_match:
                size = int(size_match.group(1))
                contig_counts[size] = assembly_metrics[metric]
        
        # Calculate contigs in each size range
        sizes = sorted(contig_counts.keys())
        for i in range(len(sizes) - 1):
            lower = sizes[i]
            upper = sizes[i+1]
            
            # Skip the "all" category
            if lower == "all":
                continue
                
            # Calculate contigs in this range
            range_key = f"{lower}-{upper}"
            count = contig_counts[lower] - contig_counts[upper]
            distribution[assembly_name]["counts"][range_key] = count
            
            # Calculate percentage if total is available
            if total_contigs:
                distribution[assembly_name]["percentages"][range_key] = (count / total_contigs) * 100
        
        # Add the largest size range
        if sizes and sizes[-1] != "all":
            largest_size = sizes[-1]
            count = contig_counts[largest_size]
            range_key = f"≥{largest_size}"
            distribution[assembly_name]["counts"][range_key] = count
            
            # Calculate percentage if total is available
            if total_contigs:
                distribution[assembly_name]["percentages"][range_key] = (count / total_contigs) * 100
    
    return distribution


def get_assembly_improvement_metrics(
    original_metrics: Dict[str, Any],
    filtered_metrics: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate improvement metrics between original and filtered assemblies.
    
    Args:
        original_metrics: Metrics for the original assembly
        filtered_metrics: Metrics for the filtered assembly
        
    Returns:
        Dictionary with improvement statistics
    """
    improvements = {
        "absolute_change": {},
        "percent_change": {},
        "is_improvement": {}
    }
    
    # Metrics where higher values are better
    higher_better = {
        "N50", "NGA50", "Genome fraction (%)", "Complete BUSCO (%)", "Largest contig"
    }
    
    # Metrics where lower values are better
    lower_better = {
        "L50", "LGA50", "# misassemblies", "# contigs", "# indels per 100 kbp", 
        "# mismatches per 100 kbp", "Duplication ratio"
    }
    
    # Calculate changes for each metric present in both
    for metric, orig_value in original_metrics.items():
        if metric in filtered_metrics:
            filt_value = filtered_metrics[metric]
            
            # Skip non-numeric values
            if not isinstance(orig_value, (int, float)) or not isinstance(filt_value, (int, float)):
                continue
            
            # Calculate absolute change
            change = filt_value - orig_value
            improvements["absolute_change"][metric] = change
            
            # Calculate percent change (avoid division by zero)
            if orig_value != 0:
                pct_change = (change / orig_value) * 100
                improvements["percent_change"][metric] = pct_change
            else:
                improvements["percent_change"][metric] = 0
            
            # Determine if it's an improvement
            if metric in higher_better:
                improvements["is_improvement"][metric] = change > 0
            elif metric in lower_better:
                improvements["is_improvement"][metric] = change < 0
            else:
                improvements["is_improvement"][metric] = None
    
    # Calculate overall improvement score
    positive_changes = sum(1 for imp in improvements["is_improvement"].values() if imp is True)
    negative_changes = sum(1 for imp in improvements["is_improvement"].values() if imp is False)
    total_evaluated = sum(1 for imp in improvements["is_improvement"].values() if imp is not None)
    
    if total_evaluated > 0:
        improvements["improvement_score"] = (positive_changes - negative_changes) / total_evaluated
    else:
        improvements["improvement_score"] = 0
    
    improvements["is_overall_improved"] = improvements["improvement_score"] > 0
    improvements["positive_metric_count"] = positive_changes
    improvements["negative_metric_count"] = negative_changes
    improvements["total_evaluated_metrics"] = total_evaluated
    
    return improvements


def generate_quast_summary(quast_results_dir: str) -> Dict[str, Any]:
    """
    Generate a comprehensive summary of QUAST results.
    
    Args:
        quast_results_dir: Directory containing QUAST results
        
    Returns:
        Dictionary with summary statistics and categorized metrics
    """
    summary = {
        "assemblies": [],
        "has_reference": False,
        "has_gene_prediction": False,
        "basic_metrics": {},
        "contig_distribution": {},
        "quality_metrics": {},
        "reference_metrics": {},
        "gene_metrics": {}
    }
    
    # Parse the report files
    report_path = os.path.join(quast_results_dir, "report.tsv")
    transposed_path = os.path.join(quast_results_dir, "transposed_report.tsv")
    
    if not os.path.exists(report_path):
        logger.error(f"QUAST report not found at {report_path}")
        return summary
    
    # Parse the main report
    metrics = parse_quast_report_file(report_path)
    if not metrics:
        logger.error("Failed to parse QUAST report")
        return summary
    
    # Get list of assemblies
    summary["assemblies"] = list(metrics.keys())
    
    # Check if reference-based or gene metrics are present
    summary["has_reference"] = has_reference_metrics(metrics)
    summary["has_gene_prediction"] = has_gene_metrics(metrics)
    
    # Extract metrics by category
    summary["basic_metrics"] = extract_essential_metrics(metrics, "basic")
    summary["quality_metrics"] = extract_essential_metrics(metrics, "detailed")
    
    if summary["has_reference"]:
        summary["reference_metrics"] = extract_essential_metrics(metrics, "reference_based")
    
    if summary["has_gene_prediction"]:
        summary["gene_metrics"] = extract_essential_metrics(metrics, "gene_based")
    
    # Calculate contig size distribution
    summary["contig_distribution"] = calculate_contig_size_distribution(metrics)
    
    # Add report paths
    summary["report_path"] = report_path
    summary["transposed_report_path"] = transposed_path if os.path.exists(transposed_path) else None
    summary["html_report_path"] = os.path.join(quast_results_dir, "report.html")
    
    return summary


def format_metrics_for_display(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format metrics for more user-friendly display.
    
    Args:
        metrics: Dictionary of metrics
        
    Returns:
        Dictionary with formatted metrics
    """
    display_metrics = {}
    
    # Format values for display
    for metric, value in metrics.items():
        if isinstance(value, float):
            # Format percentages with 2 decimal places
            if "%" in metric:
                display_metrics[metric] = f"{value:.2f}%"
            # Format other floats with 2 decimal places
            else:
                display_metrics[metric] = f"{value:.2f}"
        elif isinstance(value, int):
            # Format large integers with commas
            if value > 1000:
                display_metrics[metric] = f"{value:,}"
            else:
                display_metrics[metric] = str(value)
        else:
            # Keep other values as-is
            display_metrics[metric] = str(value)
    
    return display_metrics


def get_reference_alignment_stats(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extract alignment statistics for assemblies aligned to a reference.
    
    Args:
        metrics: Dictionary of metrics from parse_quast_report
        
    Returns:
        Dictionary with alignment statistics
    """
    alignment_stats = {}
    
    for assembly_name, assembly_metrics in metrics.items():
        # Skip if no alignment metrics
        if "Genome fraction (%)" not in assembly_metrics:
            continue
        
        alignment_stats[assembly_name] = {
            "genome_fraction": assembly_metrics.get("Genome fraction (%)", 0),
            "duplication_ratio": assembly_metrics.get("Duplication ratio", 1.0),
            "aligned_bases": assembly_metrics.get("Aligned bases", 0),
            "unaligned_bases": assembly_metrics.get("Unaligned bases", 0),
            "misassemblies": assembly_metrics.get("# misassemblies", 0),
            "mismatches_per_100kbp": assembly_metrics.get("# mismatches per 100 kbp", 0),
            "indels_per_100kbp": assembly_metrics.get("# indels per 100 kbp", 0),
            "nga50": assembly_metrics.get("NGA50", 0),
            "lga50": assembly_metrics.get("LGA50", 0)
        }
        
        # Calculate percent of aligned bases
        total_length = assembly_metrics.get("Total length", 0)
        aligned_bases = alignment_stats[assembly_name]["aligned_bases"]
        
        if total_length > 0:
            alignment_stats[assembly_name]["percent_aligned"] = (aligned_bases / total_length) * 100
        else:
            alignment_stats[assembly_name]["percent_aligned"] = 0
    
    return alignment_stats