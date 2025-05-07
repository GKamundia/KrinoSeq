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
from ..utils.wsl_executor import check_command_exists
from ..utils.quast_config import get_wsl_quast_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define QUAST default parameters
DEFAULT_QUAST_PARAMS = {
    "min_contig": 0, # Minimum contig length to report
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
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert input_files to list if it's a single string
    if isinstance(input_files, str):
        input_files = [input_files]
    
    # Convert to WSL paths
    wsl_input_files = [convert_windows_to_wsl_path(f) for f in input_files]
    wsl_output_dir = convert_windows_to_wsl_path(output_dir)
    
    # Use a simple command with proper quoting
    command = "wsl"
    args = ["quast.py"]  # Directly use QUAST from the WSL path
    
    # Add input files
    for input_file in wsl_input_files:
        args.append(input_file)
    
    # Add output directory
    args.extend(["-o", wsl_output_dir])
    
    # Add reference genome if provided
    if reference_genome:
        wsl_reference = convert_windows_to_wsl_path(reference_genome)
        args.extend(["-r", wsl_reference])
    
    # Add labels if provided
    if labels:
        if len(labels) != len(input_files):
            logger.warning("Number of labels does not match number of input files")
        else:
            # Escape commas in labels
            safe_labels = [label.replace(",", "\\,") for label in labels]
            label_str = ",".join(safe_labels)
            args.extend(["--labels", label_str])
    
    # Add parameters
    merged_params = {**DEFAULT_QUAST_PARAMS, **(params or {})}
    for key, value in merged_params.items():
        # Skip the quast_path parameter as we're handling that separately
        if key == "quast_path":
            continue
        elif key == "gene_finding" and value:
            args.append("--gene-finding")
        elif key == "conserved_genes_finding" and value:
            args.append("--conserved-genes-finding")
        elif isinstance(value, bool):
            if value:
                args.append(f"--{key.replace('_', '-')}")
        else:
            args.append(f"--{key.replace('_', '-')}={value}")
    
    # Format the full command for logging
    full_command = command + " " + " ".join(args)
    logger.info(f"Running QUAST command: {full_command}")
    
    # Run QUAST using subprocess to avoid WSL execution issues
    import subprocess
    try:
        # Run the command directly with subprocess
        process = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        stdout = process.stdout
        stderr = process.stderr
        returncode = process.returncode
        
        # Check if QUAST ran successfully
        success = returncode == 0
        
        # Log the results for debugging
        logger.info(f"QUAST return code: {returncode}")
        if stderr:
            logger.warning(f"QUAST stderr: {stderr}")
        
        # Parse results if successful
        result = {
            "success": success,
            "output_dir": output_dir,
            "command": full_command,
            "returncode": returncode,
        }
        
        # Check if report files were actually created
        from ..core.quast_parser import find_quast_report_path
        report_path = find_quast_report_path(output_dir)
        
        if success and not report_path:
            logger.error(f"QUAST did not generate report file in directory: {output_dir}")
            result["success"] = False
            result["error"] = "QUAST report files not generated"
            return result
        
        if success:
            # Parse QUAST results
            try:
                # Use the found report path
                result_dir = os.path.dirname(report_path)
                transposed_path = os.path.join(result_dir, "transposed_report.tsv")
                
                if os.path.exists(report_path):
                    result["metrics"] = parse_quast_report(report_path)
                    
                if os.path.exists(transposed_path):
                    result["transposed_metrics"] = parse_transposed_report(transposed_path)
                    
                # Extract summary metrics
                result["summary"] = extract_key_metrics(result.get("metrics", {}))
                
                # Include HTML report path for frontend reference
                result["html_report"] = os.path.join(result_dir, "report.html")
            except Exception as e:
                logger.error(f"Error parsing QUAST results: {str(e)}")
                result["parse_error"] = str(e)
        else:
            result["error"] = stderr
        
        return result
    except Exception as e:
        logger.error(f"Exception running QUAST: {str(e)}")
        return {
            "success": False,
            "output_dir": output_dir,
            "error": f"Error executing QUAST: {str(e)}",
            "command": full_command
        }


def parse_quast_report(report_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse the main QUAST report.tsv file.
    Args:
        report_path: Path to the report.tsv file
    Returns:
        Dictionary of metrics organized by assembly
    """
    import re
    metrics = {}
    try:
        with open(report_path, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)
            assembly_names = headers[1:]
            for name in assembly_names:
                metrics[name] = {}
            for row in reader:
                if not row:
                    continue
                metric_name = row[0]
                values = row[1:]
                for i, value in enumerate(values):
                    if i < len(assembly_names):
                        assembly = assembly_names[i]
                        try:
                            value_str = str(value).strip()
                            if "%" in value_str:
                                metrics[assembly][metric_name] = float(value_str.replace("%", ""))
                            elif "," in value_str:
                                metrics[assembly][metric_name] = float(value_str.replace(",", ""))
                            elif " + " in value_str or "+" in value_str:
                                # Extract first number only for metrics like "3713 + 17 part"
                                matches = re.findall(r'\d+', value_str)
                                if matches:
                                    metrics[assembly][metric_name] = float(matches[0])
                                else:
                                    metrics[assembly][metric_name] = value_str
                            else:
                                metrics[assembly][metric_name] = float(value_str)
                        except (ValueError, TypeError):
                            metrics[assembly][metric_name] = value_str
                            logger.debug(f"Stored non-numeric value for {metric_name}: {value}")
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
    # Import modules at the beginning of the function
    import os  # Explicitly import os here
    import re  # Import re for regex pattern matching
    
    metrics = {}
    assembly_names = []  # Initialize this to avoid reference errors
    
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
                            # Ensure value is a string and strip whitespace
                            value_str = str(value).strip()
                            
                            # Handle various formats
                            if "%" in value_str:
                                # Handle percentages
                                metric_values[assembly] = float(value_str.replace("%", "").strip())
                            elif "," in value_str:
                                # Handle thousands separators
                                metric_values[assembly] = float(value_str.replace(",", "").strip())
                            elif " + " in value_str or "+" in value_str:
                                # Handle values like "3713 + 17 part" or "3713+17 part"
                                # Extract and use only the first number
                                matches = re.findall(r'\d+', value_str)
                                if matches:
                                    metric_values[assembly] = float(matches[0])
                                else:
                                    metric_values[assembly] = value_str
                            else:
                                # Try to convert to float
                                metric_values[assembly] = float(value_str)
                        except (ValueError, TypeError) as e:
                            # If conversion fails, store as string
                            metric_values[assembly] = str(value)
                            logger.debug(f"Stored non-numeric value for {metric_name}: {value}, error: {e}")
                
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
    # Import os explicitly here to ensure it's available in this scope
    import os # This import is fine as it's local to the function if needed, or rely on module-level
    
    key_metrics = {}
    
    for assembly_name, assembly_metrics in metrics.items():
        key_metrics[assembly_name] = {}
        
        # Extract metrics that are in our KEY_METRICS list
        for metric_name, value in assembly_metrics.items():
            if metric_name in KEY_METRICS:
                # Only include if it's a numeric value
                if isinstance(value, (int, float)):
                    key_metrics[assembly_name][metric_name] = value
                else:
                    logger.debug(f"Skipping non-numeric value for key metric {metric_name} in assembly {assembly_name}: {value}")
        
        # Calculate additional derived metrics
        # Check if base metrics exist AND are numeric before proceeding
        contigs_val = assembly_metrics.get("# contigs")
        contigs_1000bp_val = assembly_metrics.get("# contigs (>= 1000 bp)")

        if isinstance(contigs_val, (int, float)) and isinstance(contigs_1000bp_val, (int, float)):
            try:
                # Now it's safe to perform operations
                small_contigs = contigs_val - contigs_1000bp_val
                key_metrics[assembly_name]["# small contigs (< 1000 bp)"] = small_contigs

                if contigs_val > 0: # This comparison is now safe
                    key_metrics[assembly_name]["% large contigs (>= 1000 bp)"] = (contigs_1000bp_val / contigs_val) * 100
                else:
                    key_metrics[assembly_name]["% large contigs (>= 1000 bp)"] = 0.0 # Ensure float for consistency
            except (TypeError, ValueError) as e: # Should be rare if isinstance checks pass
                logger.warning(f"Error calculating derived contig metrics for {assembly_name} despite initial checks: {str(e)}")
        elif ("# contigs" in assembly_metrics or "# contigs (>= 1000 bp)" in assembly_metrics): # Log if keys exist but types are wrong
            logger.debug(
                f"Skipping derived contig metrics for {assembly_name}: base metrics are not numeric. "
                f"Type of '# contigs': {type(contigs_val)}, "
                f"Type of '# contigs (>= 1000 bp)': {type(contigs_1000bp_val)}"
            )
            # Optionally, set derived metrics to None or a placeholder if they are expected in the schema
            key_metrics[assembly_name]["# small contigs (< 1000 bp)"] = None
            key_metrics[assembly_name]["% large contigs (>= 1000 bp)"] = None


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
    """
    # Local import to ensure os is available in this scope
    import os
    
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
    """
    comparison = {
        "change_summary": {},
        "percent_change": {},
        "improvement": {}
    }
    
    if original_label not in metrics or filtered_label not in metrics:
        return comparison
        
    original_metrics = metrics[original_label]
    filtered_metrics = metrics[filtered_label]
    
    # First pass - pre-process any string values that should be numeric
    for metric_name in set(original_metrics.keys()) & set(filtered_metrics.keys()):
        try:
            # Ensure both values are numeric if possible
            for metrics_dict, label in [(original_metrics, original_label), (filtered_metrics, filtered_label)]:
                val = metrics_dict.get(metric_name)
                if isinstance(val, str):
                    try:
                        if val.replace('.', '', 1).isdigit():  # Simple float check
                            metrics_dict[metric_name] = float(val)
                        elif "+" in val:
                            # Extract first number for gene metrics like "3713 + 17 part"
                            import re
                            matches = re.findall(r'\d+', val)
                            if matches:
                                metrics_dict[metric_name] = float(matches[0])
                    except (ValueError, TypeError):
                        pass  # Keep as string if conversion fails
        except Exception as e:
            logger.debug(f"Error pre-processing metric {metric_name}: {str(e)}")
    
    # Now process metrics for comparison
    for metric in KEY_METRICS:
        try:
            if metric in original_metrics and metric in filtered_metrics:
                orig_val = original_metrics[metric]
                filt_val = filtered_metrics[metric]
                
                # Only compare if both are numeric
                if not isinstance(orig_val, (int, float)) or not isinstance(filt_val, (int, float)):
                    logger.debug(f"Skipping non-numeric values for metric {metric}: {orig_val} ({type(orig_val).__name__}), {filt_val} ({type(filt_val).__name__})")
                    continue
                
                # Now safe to perform numeric operations
                change = filt_val - orig_val
                comparison["change_summary"][metric] = change
                
                # Calculate percent change (avoid division by zero)
                if orig_val != 0:
                    pct_change = (change / orig_val) * 100
                    comparison["percent_change"][metric] = pct_change
                else:
                    comparison["percent_change"][metric] = 0
                
                # Determine if change is an improvement
                if any(keyword in metric.lower() for keyword in ["n50", "nga50", "genome fraction", "busco", "complete"]):
                    comparison["improvement"][metric] = change > 0
                elif any(keyword in metric.lower() for keyword in ["l50", "lga50", "misassemblies", "# contigs"]):
                    comparison["improvement"][metric] = change < 0
                else:
                    comparison["improvement"][metric] = None
        except Exception as e:
            logger.error(f"Error calculating comparison for metric {metric}: {str(e)}")
            continue
    
    try:
        positive_changes = sum(1 for imp in comparison["improvement"].values() if imp is True)
        negative_changes = sum(1 for imp in comparison["improvement"].values() if imp is False)
        total_changes = sum(1 for imp in comparison["improvement"].values() if imp is not None)
        
        if total_changes > 0:
            comparison["overall_improvement_score"] = (positive_changes - negative_changes) / total_changes
            comparison["overall_improved"] = comparison["overall_improvement_score"] > 0
        else:
            comparison["overall_improvement_score"] = 0
            comparison["overall_improved"] = False
            
        # Add detailed counts to match the API model
        comparison["positive_metric_count"] = positive_changes
        comparison["negative_metric_count"] = negative_changes
        comparison["total_evaluated_metrics"] = total_changes
    except Exception as e:
        logger.error(f"Error calculating overall assessment: {str(e)}")
        comparison["overall_improvement_score"] = 0
        comparison["overall_improved"] = False
        comparison["positive_metric_count"] = 0
        comparison["negative_metric_count"] = 0
        comparison["total_evaluated_metrics"] = 0
    
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
    # Local import to ensure os is available in this scope
    import os
    
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