"""
Integration module for genomic sequence length filtering algorithms.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats

from backend.core.statistics import calculate_n50
from backend.core.visualization import generate_histogram_data

# Import filter functions from submodules
from .basic_filters import (
    filter_by_length, 
    filter_by_iqr, 
    filter_by_zscore,
    filter_by_adaptive_threshold
)

from .n50_optimization import (
    find_optimal_n50_cutoff,
    simulate_min_length_filter,
    sliding_window_analysis,
    simulate_filtering_effect,
    optimize_n50_l50_tradeoff
)

from .distribution_analysis import (
    detect_multimodality,
    find_distribution_breakpoints,
    identify_natural_cutoffs,
    detect_outliers_combined
)


def apply_optimal_filter(seq_lengths: Dict[str, int], 
                        method: str = "adaptive",
                        **kwargs) -> Dict[str, int]:
    """
    Apply optimal filtering using the specified method.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        method: Filtering method to use
            - "min_max": Simple min/max thresholds
            - "iqr": IQR-based outlier filtering
            - "zscore": Z-score based outlier filtering
            - "adaptive": Automatically select best method
            - "n50_optimize": Optimize for N50
            - "natural": Use natural distribution breakpoints
        **kwargs: Additional parameters for the specific method
        
    Returns:
        Dictionary of filtered sequence IDs and their lengths
    """
    lengths = list(seq_lengths.values())
    
    if method == "min_max":
        min_length = kwargs.get("min_length")
        max_length = kwargs.get("max_length")
        return filter_by_length(seq_lengths, min_length, max_length)
    
    elif method == "iqr":
        k = kwargs.get("k", 1.5)
        return filter_by_iqr(seq_lengths, k)
    
    elif method == "zscore":
        threshold = kwargs.get("threshold", 2.5)
        return filter_by_zscore(seq_lengths, threshold)
    
    elif method == "adaptive":
        return filter_by_adaptive_threshold(seq_lengths)
    
    elif method == "n50_optimize":
        # Find optimal N50 cutoff
        min_cutoff = kwargs.get("min_cutoff")
        max_cutoff = kwargs.get("max_cutoff")
        optimal_cutoff, _ = find_optimal_n50_cutoff(lengths, min_cutoff, max_cutoff)
        return filter_by_length(seq_lengths, min_length=optimal_cutoff)
    
    elif method == "natural":
        # Use natural breakpoints with all specified parameters
        gmm_method = kwargs.get("gmm_method", "midpoint")
        transform_type = kwargs.get("transform", "box-cox")
        component_method = kwargs.get("component_method", "bic")
        
        cutoffs = identify_natural_cutoffs(
            lengths, 
            method=gmm_method,
            transform_type=transform_type,
            component_method=component_method
        )["recommended"]
        
        if not cutoffs:
            return seq_lengths  # No natural cutoffs found
        
        # Use the first recommended cutoff
        return filter_by_length(seq_lengths, min_length=cutoffs[0])
    
    else:
        raise ValueError(f"Unknown filtering method: {method}")


def apply_optimal_filter_with_details(
    seq_lengths: Dict[str, int], 
    method: str = "adaptive",
    **kwargs
) -> Tuple[Dict[str, int], Dict[str, Any]]:
    """
    Apply filtering and return both filtered sequences and detailed information
    about the filtering process.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        method: Filtering method to use
        **kwargs: Additional parameters for the filter method
        
    Returns:
        Tuple of (filtered_sequences, process_details)
    """
    lengths = list(seq_lengths.values())
    process_details = {"method": method, "params": kwargs}
    
    if method == "min_max":
        min_length = kwargs.get("min_length")
        max_length = kwargs.get("max_length")
        
        # Capture original length distribution
        process_details["length_distribution"] = {
            "histogram": generate_histogram_data(lengths),
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "thresholds": {"min": min_length, "max": max_length}
        }
        
        filtered = filter_by_length(seq_lengths, min_length, max_length)
        
        # Calculate which sequences were removed and why
        removed_too_short = [length for length in lengths if min_length is not None and length < min_length]
        removed_too_long = [length for length in lengths if max_length is not None and length > max_length]
        
        process_details["removed_sequences"] = {
            "too_short": len(removed_too_short),
            "too_short_lengths": removed_too_short[:100],  # Limit to avoid huge response
            "too_long": len(removed_too_long),
            "too_long_lengths": removed_too_long[:100]
        }
        
        return filtered, process_details
    
    elif method == "iqr":
        k = kwargs.get("k", 1.5)
        
        # Get detailed IQR information
        q1, q3 = np.percentile(lengths, [25, 75])
        iqr = q3 - q1
        lower_threshold = max(0, q1 - k * iqr)
        upper_threshold = q3 + k * iqr
        
        process_details["iqr_details"] = {
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "k": k,
            "lower_threshold": lower_threshold,
            "upper_threshold": upper_threshold,
            "histogram": generate_histogram_data(lengths),
            "box_plot_data": {
                "min": min(lengths) if lengths else 0,
                "q1": q1,
                "median": np.median(lengths),
                "q3": q3,
                "max": max(lengths) if lengths else 0
            }
        }
        
        # Identify outliers
        lower_outliers = [length for length in lengths if length < lower_threshold]
        upper_outliers = [length for length in lengths if length > upper_threshold]
        
        process_details["outliers"] = {
            "lower_count": len(lower_outliers),
            "lower_values": lower_outliers[:100],
            "upper_count": len(upper_outliers),
            "upper_values": upper_outliers[:100]
        }
        
        filtered = filter_by_iqr(seq_lengths, k)
        return filtered, process_details
        
    elif method == "zscore":
        threshold = kwargs.get("threshold", 2.5)
        
        # Get detailed Z-score information
        mean = np.mean(lengths)
        std = np.std(lengths)
        lower_threshold = max(0, mean - threshold * std)
        upper_threshold = mean + threshold * std
        
        # Calculate z-scores
        z_scores = [(x - mean) / std for x in lengths] if std > 0 else [0] * len(lengths)
        
        process_details["zscore_details"] = {
            "mean": mean,
            "std": std,
            "threshold": threshold,
            "lower_threshold": lower_threshold,
            "upper_threshold": upper_threshold,
            "histogram": generate_histogram_data(lengths),
            "normal_curve": {
                "x": list(np.linspace(mean - 4*std, mean + 4*std, 100)),
                "y": list(stats.norm.pdf(np.linspace(mean - 4*std, mean + 4*std, 100), mean, std))
            }
        }
        
        # Identify outliers
        lower_outliers = [length for length in lengths if length < lower_threshold]
        upper_outliers = [length for length in lengths if length > upper_threshold]
        
        process_details["outliers"] = {
            "lower_count": len(lower_outliers),
            "lower_values": lower_outliers[:100],
            "upper_values": upper_outliers[:100],
            "upper_count": len(upper_outliers),
            "z_scores": z_scores[:1000]  # Limit to avoid huge response
        }
        
        filtered = filter_by_zscore(seq_lengths, threshold)
        return filtered, process_details
        
    elif method == "adaptive":
        # Get distribution characteristics
        skewness = stats.skew(lengths)
        kurtosis = stats.kurtosis(lengths)
        
        process_details["adaptive_details"] = {
            "skewness": skewness,
            "kurtosis": kurtosis,
            "histogram": generate_histogram_data(lengths)
        }
        
        # Determine which method was selected
        selected_method = "iqr" if abs(skewness) > 2 else "zscore"
        k_factor = 2.0 if abs(skewness) > 4 else 1.5
        z_factor = 3.0 if abs(kurtosis) < 1 else 2.5
        
        process_details["adaptive_details"]["selected_method"] = selected_method
        process_details["adaptive_details"]["reason"] = (
            f"Selected {selected_method} because skewness={skewness:.2f} and kurtosis={kurtosis:.2f}"
        )
        
        if selected_method == "iqr":
            process_details["adaptive_details"]["k_factor"] = k_factor
            # Recursively call with IQR method to get details
            filtered, iqr_details = apply_optimal_filter_with_details(
                seq_lengths, method="iqr", k=k_factor
            )
            process_details["adaptive_details"]["method_details"] = iqr_details
        else:
            process_details["adaptive_details"]["z_factor"] = z_factor
            # Recursively call with Z-score method to get details
            filtered, zscore_details = apply_optimal_filter_with_details(
                seq_lengths, method="zscore", threshold=z_factor
            )
            process_details["adaptive_details"]["method_details"] = zscore_details
        
        return filtered, process_details
        
    elif method == "n50_optimize":
        # Capture parameters
        min_cutoff = kwargs.get("min_cutoff", max(1, min(lengths) // 10) if lengths else 1)
        max_cutoff = kwargs.get("max_cutoff", int(np.median(lengths)) if lengths else 1)
        step = kwargs.get("step", 10)
        
        # Generate N50 improvement curve
        initial_n50 = calculate_n50(lengths)
        cutoff_results = []
        
        for cutoff in range(min_cutoff, max_cutoff + 1, step):
            filtered_lengths = simulate_min_length_filter(lengths, cutoff)
            if not filtered_lengths:
                continue
                
            current_n50 = calculate_n50(filtered_lengths)
            sequences_kept = len(filtered_lengths)
            percent_kept = (sequences_kept / len(lengths)) * 100 if lengths else 0
            
            cutoff_results.append({
                "cutoff": cutoff,
                "n50": current_n50,
                "n50_change": current_n50 - initial_n50,
                "sequences_kept": sequences_kept,
                "percent_kept": percent_kept
            })
        
        # Find the optimal cutoff and its details
        optimal_cutoff, optimal_n50 = find_optimal_n50_cutoff(
            lengths, min_cutoff, max_cutoff, step
        )
        
        process_details["n50_optimize_details"] = {
            "initial_n50": initial_n50,
            "optimal_cutoff": optimal_cutoff,
            "optimal_n50": optimal_n50,
            "n50_improvement": optimal_n50 - initial_n50,
            "cutoff_results": cutoff_results,
            "min_cutoff": min_cutoff,
            "max_cutoff": max_cutoff,
            "step": step,
            "histogram": generate_histogram_data(lengths)
        }
        
        filtered = filter_by_length(seq_lengths, min_length=optimal_cutoff)
        return filtered, process_details
        
    elif method == "natural":
        # Get GMM parameters with defaults
        gmm_method = kwargs.get("gmm_method", "midpoint")
        transform_type = kwargs.get("transform", "box-cox")
        component_method = kwargs.get("component_method", "bic")
        
        print(f"Natural breakpoint using: {gmm_method}, transform={transform_type}, component={component_method}")
        
        # Use natural breakpoints with all parameters
        breakpoints = identify_natural_cutoffs(
            lengths, 
            method=gmm_method,
            transform_type=transform_type,
            component_method=component_method
        )
        
        # Get recommended cutoff
        cutoffs = breakpoints.get("recommended", [])
        
        if not cutoffs:
            print("No natural breakpoint found")
            return seq_lengths, {"natural_breakpoint_details": breakpoints}
        
        cutoff = cutoffs[0]
        filtered_seqs = {seq_id: length for seq_id, length in seq_lengths.items() 
                        if length >= cutoff}
        
        process_details["natural_breakpoint_details"] = breakpoints
        
        return filtered_seqs, process_details
    
    else:
        raise ValueError(f"Unknown filtering method: {method}")