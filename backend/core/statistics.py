"""
Module for calculating statistics on sequence length data.
"""

from typing import Dict, List, Tuple
import numpy as np
from scipy import stats


def calculate_basic_stats(lengths: List[int]) -> Dict[str, float]:
    """
    Calculate basic statistics from a list of sequence lengths.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Dictionary containing min, max, mean, median, and standard deviation
    """
    if not lengths:
        return {
            "min": 0,
            "max": 0,
            "mean": 0,
            "median": 0,
            "std_dev": 0,
            "total": 0,
            "count": 0
        }
    
    return {
        "min": float(min(lengths)),
        "max": float(max(lengths)),
        "mean": float(np.mean(lengths)),
        "median": float(np.median(lengths)),
        "std_dev": float(np.std(lengths)),
        "total": float(sum(lengths)),
        "count": len(lengths)
    }


def calculate_quartiles(lengths: List[int]) -> Dict[str, float]:
    """
    Calculate quartiles and interquartile range from a list of sequence lengths.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Dictionary containing Q1, Q2 (median), Q3, and IQR
    """
    if not lengths:
        return {
            "q1": 0,
            "q2": 0,
            "q3": 0,
            "iqr": 0
        }
    
    q1, q2, q3 = np.percentile(lengths, [25, 50, 75])
    iqr = q3 - q1
    
    return {
        "q1": float(q1),
        "q2": float(q2),
        "q3": float(q3),
        "iqr": float(iqr)
    }


def calculate_n50(lengths: List[int]) -> float:
    """
    Calculate N50 statistic.
    
    N50 is the sequence length such that 50% of the total assembly 
    length is contained in sequences >= N50 length.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        N50 value
    """
    if not lengths:
        return 0.0
    
    sorted_lengths = sorted(lengths, reverse=True)
    total_length = sum(sorted_lengths)
    
    running_sum = 0
    for length in sorted_lengths:
        running_sum += length
        if running_sum >= total_length / 2:
            return float(length)
    
    return float(sorted_lengths[-1])


def calculate_l50(lengths: List[int]) -> int:
    """
    Calculate L50 statistic.
    
    L50 is the number of sequences with length >= N50 length.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        L50 value
    """
    if not lengths:
        return 0
    
    sorted_lengths = sorted(lengths, reverse=True)
    total_length = sum(sorted_lengths)
    
    running_sum = 0
    for i, length in enumerate(sorted_lengths, 1):
        running_sum += length
        if running_sum >= total_length / 2:
            return i
    
    return len(sorted_lengths)


def detect_outliers_iqr(lengths: List[int], k: float = 1.5) -> Tuple[List[int], List[int]]:
    """
    Detect outliers using the IQR method.
    
    Args:
        lengths: List of sequence lengths
        k: Multiplier for IQR (typically 1.5)
        
    Returns:
        Tuple containing (lower_outliers, upper_outliers)
    """
    if not lengths:
        return ([], [])
    
    q1, q3 = np.percentile(lengths, [25, 75])
    iqr = q3 - q1
    
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    
    lower_outliers = [x for x in lengths if x < lower_bound]
    upper_outliers = [x for x in lengths if x > upper_bound]
    
    return (lower_outliers, upper_outliers)