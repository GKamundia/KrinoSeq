"""
Integration module for genomic sequence length filtering algorithms.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np

# Import filter functions from submodules
from .basic_filters import (
    filter_by_length, 
    filter_by_iqr, 
    filter_by_zscore,
    filter_by_adaptive_threshold
)

from .n50_optimization import (
    find_optimal_n50_cutoff,
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
        # Use natural breakpoints
        cutoffs = identify_natural_cutoffs(lengths)["recommended"]
        if not cutoffs:
            return seq_lengths  # No natural cutoffs found
        
        # Use the first recommended cutoff
        return filter_by_length(seq_lengths, min_length=cutoffs[0])
    
    else:
        raise ValueError(f"Unknown filtering method: {method}")