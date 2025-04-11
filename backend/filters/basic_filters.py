"""
Basic length-based filtering functions for genomic sequences.
"""

from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
from scipy import stats


def filter_by_length(seq_lengths: Dict[str, int], min_length: Optional[int] = None, 
                     max_length: Optional[int] = None) -> Dict[str, int]:
    """
    Filter sequences by minimum and/or maximum length.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        min_length: Minimum length threshold (inclusive), or None for no minimum
        max_length: Maximum length threshold (inclusive), or None for no maximum
        
    Returns:
        Dictionary of filtered sequence IDs and their lengths
    """
    filtered_lengths = {}
    
    for seq_id, length in seq_lengths.items():
        if (min_length is None or length >= min_length) and \
           (max_length is None or length <= max_length):
            filtered_lengths[seq_id] = length
            
    return filtered_lengths


def calculate_iqr_thresholds(lengths: List[int], k: float = 1.5) -> Tuple[float, float]:
    """
    Calculate length thresholds based on interquartile range (IQR).
    
    Args:
        lengths: List of sequence lengths
        k: Multiplier for IQR (typically 1.5)
        
    Returns:
        Tuple containing (lower_threshold, upper_threshold)
    """
    if not lengths or len(lengths) < 4:  # Need at least a few points for quartiles
        return (0, float('inf'))
    
    q1, q3 = np.percentile(lengths, [25, 75])
    iqr = q3 - q1
    
    lower_threshold = max(0, q1 - k * iqr)
    upper_threshold = q3 + k * iqr
    
    return (lower_threshold, upper_threshold)


def filter_by_iqr(seq_lengths: Dict[str, int], k: float = 1.5) -> Dict[str, int]:
    """
    Filter sequences by removing outliers based on IQR method.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        k: Multiplier for IQR (typically 1.5)
        
    Returns:
        Dictionary of filtered sequence IDs and their lengths
    """
    lengths = list(seq_lengths.values())
    lower_threshold, upper_threshold = calculate_iqr_thresholds(lengths, k)
    
    return filter_by_length(seq_lengths, min_length=int(lower_threshold), 
                           max_length=int(upper_threshold))


def calculate_zscore_thresholds(lengths: List[int], z_threshold: float = 2.5) -> Tuple[float, float]:
    """
    Calculate length thresholds based on Z-scores.
    
    Args:
        lengths: List of sequence lengths
        z_threshold: Z-score threshold for considering a value as an outlier
        
    Returns:
        Tuple containing (lower_threshold, upper_threshold)
    """
    if not lengths or len(lengths) < 2:
        return (0, float('inf'))
    
    mean = np.mean(lengths)
    std = np.std(lengths)
    
    if std == 0:  # All values are the same
        return (mean, mean)
    
    lower_threshold = max(0, mean - z_threshold * std)
    upper_threshold = mean + z_threshold * std
    
    return (lower_threshold, upper_threshold)


def filter_by_zscore(seq_lengths: Dict[str, int], z_threshold: float = 2.5) -> Dict[str, int]:
    """
    Filter sequences by removing outliers based on Z-score method.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        z_threshold: Z-score threshold for considering a value as an outlier
        
    Returns:
        Dictionary of filtered sequence IDs and their lengths
    """
    lengths = list(seq_lengths.values())
    lower_threshold, upper_threshold = calculate_zscore_thresholds(lengths, z_threshold)
    
    return filter_by_length(seq_lengths, min_length=int(lower_threshold), 
                           max_length=int(upper_threshold))


def adaptive_threshold_calculator(lengths: List[int]) -> Tuple[float, float]:
    """
    Calculate adaptive thresholds based on dataset characteristics.
    
    This function analyzes the distribution and selects the most appropriate
    thresholding method automatically.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Tuple containing (min_length, max_length)
    """
    if not lengths:
        return (0, float('inf'))
    
    # Check distribution shape
    skewness = stats.skew(lengths)
    kurtosis = stats.kurtosis(lengths)
    
    # For highly skewed distributions, IQR method works better
    if abs(skewness) > 2:
        k_factor = 2.0 if abs(skewness) > 4 else 1.5
        return calculate_iqr_thresholds(lengths, k=k_factor)
    
    # For more normal-like distributions, Z-score works better
    else:
        z_factor = 3.0 if abs(kurtosis) < 1 else 2.5
        return calculate_zscore_thresholds(lengths, z_threshold=z_factor)


def filter_by_adaptive_threshold(seq_lengths: Dict[str, int]) -> Dict[str, int]:
    """
    Filter sequences using automatically selected thresholding method.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        
    Returns:
        Dictionary of filtered sequence IDs and their lengths
    """
    lengths = list(seq_lengths.values())
    min_length, max_length = adaptive_threshold_calculator(lengths)
    
    return filter_by_length(seq_lengths, min_length=int(min_length), 
                           max_length=int(max_length))