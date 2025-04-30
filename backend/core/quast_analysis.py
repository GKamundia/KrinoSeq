"""
QUAST analysis module for evaluating genome assemblies.
Handles running QUAST through WSL, parsing its outputs, and storing results.
"""

import os
import re
import csv
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from pathlib import Path

from ..utils.wsl_path_converter import convert_windows_to_wsl_path, convert_wsl_to_windows_path
from ..utils.wsl_executor import run_wsl_command, check_command_exists, run_with_progress, WSLExecutionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define QUAST default parameters
DEFAULT_QUAST_PARAMS = {
    "min_contig": 500,
    "threads": 4,
    "gene_finding": True,
    "conserved_genes_finding": True,
    "scaffold_gap_max_size": 1000,
}

# Define key metrics to extract from QUAST reports
KEY_METRICS = [
    # Assembly size metrics
    "Total length", "Total length (>= 0 bp)", "Total length (>= 1000 bp)", 
    "Total length (>= 5000 bp)", "Total length (>= 10000 bp)", "Total length (>= 25000 bp)",
    
    # Contig count metrics
    "# contigs", "# contigs (>= 0 bp)", "# contigs (>= 1000 bp)", 
    "# contigs (>= 5000 bp)", "# contigs (>= 10000 bp)", "# contigs (>= 25000 bp)",
    
    # Assembly quality metrics
    "N50", "L50", "N75", "L75", "N90", "L90",
    
    # GC content
    "GC (%)",
    
    # Gaps and misassemblies
    "# N's per 100 kbp", "# misassemblies", "# misassembled contigs",
    
    # Reference-based metrics (if reference provided)
    "Genome fraction (%)", "Duplication ratio", "NGA50", "LGA50",
    
    # Gene metrics
    "# predicted genes (unique)", "# predicted genes", "Complete BUSCO (%)"
]


def run_quast_analysis(
    input_files: Union[str, List[str]],
    output_dir: str,
    reference_genome: Optional[str] = None,
    labels: Optional[List[str]] = None,
    params: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int], None]] = None
) -> Dict[str, Any]:
    """
    Run QUAST on one or more genome assemblies.
    
    Args:
        input_files: Path(s) to input FASTA file(s)
        output_dir: Directory to store QUAST results
        reference_genome: Optional path to reference genome
        labels: Optional list of labels for the input files
        params: Optional dictionary of QUAST parameters
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Dictionary with QUAST execution results
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if QUAST is available in WSL
    if not check_command_exists("quast.py"):
        return {
            "error": "QUAST is not available in WSL environment",
            "success": False,
            "output_dir": output_dir
        }
    
    # Convert input_files to list if it's a single string
    if isinstance(input_files, str):
        input_files = [input_files]
    
    # Convert to WSL paths
    wsl_input_files = [convert_windows_to_wsl_path(f) for f in input_files]
    wsl_output_dir = convert_windows_to_wsl_path(output_dir)
    
    # Build QUAST command
    command = ["quast.py"]
    
    # Add input files
    command.extend(wsl_input_files)
    
    # Add output directory
    command.extend(["-o", wsl_output_dir])
    
    # Add reference genome if provided
    if reference_genome:
        wsl_reference = convert_windows_to_wsl_path(reference_genome)
        command.extend(["-r", wsl_reference])
    
    # Add labels if provided
    if labels:
        if len(labels) != len(input_files):
            logger.warning("Number of labels does not match number of input files")
        else:
            # Escape commas in labels
            safe_labels = [label.replace(",", "\\,") for label in labels]
            command.extend(["--labels", ",".join(safe_labels)])
    
    # Add parameters
    merged_params = {**DEFAULT_QUAST_PARAMS, **(params or {})}
    for key, value in merged_params.items():
        if key == "gene_finding" and value:
            command.append("--gene-finding")
        elif key == "conserved_genes_finding" and value:
            command.append("--conserved-genes-finding")
        elif isinstance(value, bool):
            if value:
                command.append(f"--{key.replace('_', '-')}")
        else:
            command.append(f"--{key.replace('_', '-')}={value}")
    
    # Join command parts with spaces
    command_str = " ".join(command)
    
    # Run QUAST with progress monitoring
    if progress_callback:
        stdout, stderr, returncode = run_with_progress(
            command_str,
            timeout=3600,  # 1 hour timeout
            progress_callback=progress_callback,
            # QUAST doesn't provide clear progress percentages, so we'll use a heuristic
            progress_regex=r"Stage (\d+)/\d+"
        )
    else:
        stdout, stderr, returncode = run_wsl_command(
            command_str,
            timeout=3600,  # 1 hour timeout
        )
    
    # Check if QUAST ran successfully
    success = returncode == 0
    
    # Parse results if successful
    result = {
        "success": success,
        "output_dir": output_dir,
        "command": command_str,
        "returncode": returncode,
    }
    
    if success:
        # Parse QUAST results
        try:
            report_path = os.path.join(output_dir, "report.tsv")
            transposed_path = os.path.join(output_dir, "transposed_report.tsv")
            
            if os.path.exists(report_path):
                result["metrics"] = parse_quast_report(report_path)
                
            if os.path.exists(transposed_path):
                result["transposed_metrics"] = parse_transposed_report(transposed_path)
                
            # Extract summary metrics
            result["summary"] = extract_key_metrics(result.get("metrics", {}))
            
            # Include HTML report path for frontend reference
            result["html_report"] = os.path.join(output_dir, "report.html")
        except Exception as e:
            logger.error(f"Error parsing QUAST results: {str(e)}")
            result["parse_error"] = str(e)
    else:
        result["error"] = stderr
    
    return result


def parse_quast_report(report_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse the main QUAST report.tsv file.
    
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
                        try:
                            if "%" in value:
                                # Handle percentages
                                metrics[assembly][metric_name] = float(value.replace("%", ""))
                            elif "," in value:
                                # Handle thousands separators
                                metrics[assembly][metric_name] = float(value.replace(",", ""))
                            else:
                                metrics[assembly][metric_name] = float(value)
                        except ValueError:
                            metrics[assembly][metric_name] = value
    except Exception as e:
        logger.error(f"Error parsing QUAST report: {str(e)}")
        return {}
    
    return metrics


def parse_transposed_report(report_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse the transposed_report.tsv file from QUAST.
    
    Args:
        report_path: Path to the transposed_report.tsv file
        
    Returns:
        Dictionary of metrics organized by metric category
    """
    metrics = {}
    
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
                category = get_metric_category(metric_name)
                
                # Initialize category if needed
                if category not in metrics:
                    metrics[category] = {}
                
                # Store metric values by assembly
                metric_values = {}
                for i, value in enumerate(values):
                    if i < len(assembly_names):
                        assembly = assembly_names[i]
                        # Try to convert to numeric if possible
                        try:
                            if "%" in value:
                                # Handle percentages
                                metric_values[assembly] = float(value.replace("%", ""))
                            elif "," in value:
                                # Handle thousands separators
                                metric_values[assembly] = float(value.replace(",", ""))
                            else:
                                metric_values[assembly] = float(value)
                        except ValueError:
                            metric_values[assembly] = value
                
                metrics[category][metric_name] = metric_values
    except Exception as e:
        logger.error(f"Error parsing transposed QUAST report: {str(e)}")
        return {}
    
    return metrics


def get_metric_category(metric_name: str) -> str:
    """
    Determine the category for a QUAST metric.
    
    Args:
        metric_name: Name of the metric
        
    Returns:
        Category name
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


def extract_key_metrics(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extract key metrics from the full QUAST report.
    
    Args:
        metrics: Dictionary of all metrics from parse_quast_report
        
    Returns:
        Dictionary containing only key metrics
    """
    key_metrics = {}
    
    for assembly_name, assembly_metrics in metrics.items():
        key_metrics[assembly_name] = {}
        
        # Extract metrics that are in our KEY_METRICS list
        for metric_name, value in assembly_metrics.items():
            if metric_name in KEY_METRICS:
                key_metrics[assembly_name][metric_name] = value
        
        # Calculate additional derived metrics
        if "# contigs" in assembly_metrics and "# contigs (>= 1000 bp)" in assembly_metrics:
            try:
                small_contigs = assembly_metrics["# contigs"] - assembly_metrics["# contigs (>= 1000 bp)"]
                key_metrics[assembly_name]["# small contigs (< 1000 bp)"] = small_contigs
                key_metrics[assembly_name]["% large contigs (>= 1000 bp)"] = (
                    assembly_metrics["# contigs (>= 1000 bp)"] / assembly_metrics["# contigs"] * 100
                    if assembly_metrics["# contigs"] > 0 else 0
                )
            except (TypeError, ValueError):
                pass
    
    return key_metrics


def compare_assemblies(
    original_assembly: str,
    filtered_assembly: str,
    output_dir: str,
    reference_genome: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int], None]] = None
) -> Dict[str, Any]:
    """
    Compare original and filtered assemblies using QUAST.
    
    Args:
        original_assembly: Path to the original assembly FASTA
        filtered_assembly: Path to the filtered assembly FASTA
        output_dir: Directory to store comparison results
        reference_genome: Optional path to reference genome
        params: Optional dictionary of QUAST parameters
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Dictionary with comparison results
    """
    # Generate labels based on filenames
    orig_label = os.path.splitext(os.path.basename(original_assembly))[0]
    filt_label = os.path.splitext(os.path.basename(filtered_assembly))[0]
    
    # Add 'original' and 'filtered' tags to labels for clarity
    labels = [f"{orig_label}_original", f"{filt_label}_filtered"]
    
    # Run QUAST on both assemblies
    result = run_quast_analysis(
        input_files=[original_assembly, filtered_assembly],
        output_dir=output_dir,
        reference_genome=reference_genome,
        labels=labels,
        params=params,
        progress_callback=progress_callback
    )
    
    # Add comparison metrics
    if result.get("success") and "metrics" in result:
        result["comparison"] = calculate_comparison_metrics(result["metrics"], labels[0], labels[1])
    
    return result


def calculate_comparison_metrics(
    metrics: Dict[str, Dict[str, Any]],
    original_label: str,
    filtered_label: str
) -> Dict[str, Any]:
    """
    Calculate metrics comparing original and filtered assemblies.
    
    Args:
        metrics: Dictionary of metrics from QUAST
        original_label: Label for the original assembly
        filtered_label: Label for the filtered assembly
    
    Returns:
        Dictionary of comparison metrics
    """
    comparison = {
        "change_summary": {},
        "percent_change": {},
        "improvement": {}
    }
    
    # Check if both labels exist in the metrics
    if original_label not in metrics or filtered_label not in metrics:
        return comparison
    
    original_metrics = metrics[original_label]
    filtered_metrics = metrics[filtered_label]
    
    # Calculate absolute changes
    for metric in KEY_METRICS:
        if metric in original_metrics and metric in filtered_metrics:
            orig_val = original_metrics[metric]
            filt_val = filtered_metrics[metric]
            
            # Skip non-numeric values
            if not isinstance(orig_val, (int, float)) or not isinstance(filt_val, (int, float)):
                continue
            
            # Calculate change
            change = filt_val - orig_val
            comparison["change_summary"][metric] = change
            
            # Calculate percent change (avoid division by zero)
            if orig_val != 0:
                pct_change = (change / orig_val) * 100
                comparison["percent_change"][metric] = pct_change
            else:
                comparison["percent_change"][metric] = 0
            
            # Determine if the change is an improvement
            # For metrics where higher is better
            if any(keyword in metric.lower() for keyword in ["n50", "genome fraction", "busco", "complete"]):
                comparison["improvement"][metric] = change > 0
            # For metrics where lower is better
            elif any(keyword in metric.lower() for keyword in ["l50", "misassemblies", "# contigs"]):
                comparison["improvement"][metric] = change < 0
            # For other metrics, don't make a judgment
            else:
                comparison["improvement"][metric] = None
    
    # Add overall assessment
    positive_changes = sum(1 for imp in comparison["improvement"].values() if imp is True)
    negative_changes = sum(1 for imp in comparison["improvement"].values() if imp is False)
    total_changes = sum(1 for imp in comparison["improvement"].values() if imp is not None)
    
    if total_changes > 0:
        comparison["overall_improvement_score"] = (positive_changes - negative_changes) / total_changes
        comparison["overall_improved"] = comparison["overall_improvement_score"] > 0
    else:
        comparison["overall_improvement_score"] = 0
        comparison["overall_improved"] = False
    
    return comparison


def get_quast_report_path(job_id: str, report_type: str = "html") -> str:
    """
    Get the path to a QUAST report file for a specific job.
    
    Args:
        job_id: Job ID
        report_type: Type of report (html, tsv, pdf, etc.)
    
    Returns:
        Path to the report file
    """
    base_dir = os.path.join("data", "jobs", job_id, "quast")
    
    # Map report types to filenames
    report_files = {
        "html": "report.html",
        "tsv": "report.tsv",
        "transposed_tsv": "transposed_report.tsv",
        "pdf": "report.pdf",
        "json": "report.json"
    }
    
    filename = report_files.get(report_type, "report.html")
    return os.path.join(base_dir, filename)


def get_quast_result_schema() -> Dict[str, Any]:
    """
    Get the schema definition for QUAST results.
    
    Returns:
        Dictionary describing the QUAST results schema
    """
    return {
        "title": "QUAST Analysis Results",
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "output_dir": {"type": "string"},
            "command": {"type": "string"},
            "returncode": {"type": "integer"},
            "metrics": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "additionalProperties": {"type": ["number", "string", "null"]}
                }
            },
            "transposed_metrics": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": {"type": ["number", "string", "null"]}
                    }
                }
            },
            "summary": {
                "type": "object",
                "additionalProperties": {
                    "type": "object",
                    "additionalProperties": {"type": ["number", "string", "null"]}
                }
            },
            "html_report": {"type": "string"},
            "comparison": {
                "type": "object",
                "properties": {
                    "change_summary": {
                        "type": "object",
                        "additionalProperties": {"type": "number"}
                    },
                    "percent_change": {
                        "type": "object",
                        "additionalProperties": {"type": "number"}
                    },
                    "improvement": {
                        "type": "object",
                        "additionalProperties": {"type": ["boolean", "null"]}
                    },
                    "overall_improvement_score": {"type": "number"},
                    "overall_improved": {"type": "boolean"}
                }
            }
        },
        "required": ["success", "output_dir"]
    }