"""
N50/L50-based optimization filters for genomic sequences.
"""

from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
from ..core.statistics import calculate_n50, calculate_l50


def simulate_min_length_filter(lengths: List[int], min_length: int) -> List[int]:
    """
    Simulate applying a minimum length filter.
    
    Args:
        lengths: List of sequence lengths
        min_length: Minimum length threshold
        
    Returns:
        List of sequence lengths that pass the filter
    """
    return [length for length in lengths if length >= min_length]


def calculate_n50_after_filtering(lengths: List[int], min_length: int) -> float:
    """
    Calculate N50 after applying a minimum length filter.
    
    Args:
        lengths: List of sequence lengths
        min_length: Minimum length threshold
        
    Returns:
        N50 value after filtering
    """
    filtered_lengths = simulate_min_length_filter(lengths, min_length)
    if not filtered_lengths:
        return 0.0
    
    return calculate_n50(filtered_lengths)


def find_optimal_n50_cutoff(lengths: List[int], 
                           min_cutoff: Optional[int] = None,
                           max_cutoff: Optional[int] = None,
                           step: int = 10) -> Tuple[int, float]:
    """
    Find the minimum length cutoff that maximizes the N50 value.
    
    Args:
        lengths: List of sequence lengths
        min_cutoff: Minimum cutoff to consider (default: min length / 10)
        max_cutoff: Maximum cutoff to consider (default: median length)
        step: Step size for cutoff values
        
    Returns:
        Tuple of (optimal_cutoff, optimal_n50)
    """
    if not lengths:
        return (0, 0.0)
    
    if min_cutoff is None:
        min_cutoff = max(1, min(lengths) // 10)
    
    if max_cutoff is None:
        max_cutoff = int(np.median(lengths))
    
    best_cutoff = 0
    best_n50 = calculate_n50(lengths)  # Initial N50 without filtering
    
    # Try different cutoffs and find the one that maximizes N50
    for cutoff in range(min_cutoff, max_cutoff + 1, step):
        current_n50 = calculate_n50_after_filtering(lengths, cutoff)
        
        # Keep the new cutoff if it improves N50 or gives the same N50 with fewer sequences
        if current_n50 > best_n50:
            best_n50 = current_n50
            best_cutoff = cutoff
    
    return (best_cutoff, best_n50)


def sliding_window_analysis(lengths: List[int], window_size: int = 100, 
                           metric: str = "n50") -> List[Tuple[int, float]]:
    """
    Perform sliding window analysis to find how filter cutoffs affect metrics.
    
    Args:
        lengths: List of sequence lengths
        window_size: Size of the sliding window
        metric: Metric to track, either "n50" or "l50"
        
    Returns:
        List of tuples (cutoff, metric_value) showing the effect of each cutoff
    """
    if not lengths:
        return []
    
    min_len = min(lengths)
    max_len = max(lengths)
    
    # Define evaluation points (cutoffs to analyze)
    cutoffs = list(range(min_len, max_len, window_size))
    results = []
    
    for cutoff in cutoffs:
        filtered_lengths = simulate_min_length_filter(lengths, cutoff)
        
        if not filtered_lengths:
            # No sequences left after filtering
            metric_value = 0.0 if metric == "n50" else 0
            results.append((cutoff, metric_value))
            continue
        
        if metric == "n50":
            metric_value = calculate_n50(filtered_lengths)
        else:  # l50
            metric_value = calculate_l50(filtered_lengths)
            
        results.append((cutoff, float(metric_value)))
    
    return results


def simulate_filtering_effect(seq_lengths: Dict[str, int], cutoffs: List[int]) -> Dict[int, Dict[str, float]]:
    """
    Simulate the effect of different minimum length cutoffs on assembly metrics.
    
    Args:
        seq_lengths: Dictionary mapping sequence IDs to their lengths
        cutoffs: List of minimum length cutoffs to simulate
        
    Returns:
        Dictionary mapping cutoffs to metrics (n50, l50, sequence_count, total_length)
    """
    lengths = list(seq_lengths.values())
    results = {}
    
    for cutoff in cutoffs:
        filtered_lengths = simulate_min_length_filter(lengths, cutoff)
        
        if not filtered_lengths:
            results[cutoff] = {
                "n50": 0.0,
                "l50": 0,
                "sequence_count": 0,
                "total_length": 0,
                "percent_sequences_kept": 0.0,
                "percent_total_length_kept": 0.0
            }
            continue
        
        n50 = calculate_n50(filtered_lengths)
        l50 = calculate_l50(filtered_lengths)
        
        # Calculate percentages
        pct_seqs = (len(filtered_lengths) / len(lengths)) * 100 if lengths else 0
        pct_length = (sum(filtered_lengths) / sum(lengths)) * 100 if sum(lengths) else 0
        
        results[cutoff] = {
            "n50": n50,
            "l50": l50,
            "sequence_count": len(filtered_lengths),
            "total_length": sum(filtered_lengths),
            "percent_sequences_kept": pct_seqs,
            "percent_total_length_kept": pct_length
        }
    
    return results


def optimize_n50_l50_tradeoff(lengths: List[int], 
                             min_sequence_pct: float = 50.0,
                             min_length_pct: float = 95.0) -> int:
    """
    Find optimal cutoff balancing N50 improvement with sequence retention.
    
    This finds the cutoff that maximizes N50 while keeping at least min_sequence_pct
    of sequences and min_length_pct of the total assembly length.
    
    Args:
        lengths: List of sequence lengths
        min_sequence_pct: Minimum percentage of sequences to retain
        min_length_pct: Minimum percentage of total length to retain
        
    Returns:
        Optimal minimum length cutoff value
    """
    if not lengths:
        return 0
    
    total_seqs = len(lengths)
    total_length = sum(lengths)
    min_seqs = int(total_seqs * min_sequence_pct / 100)
    min_len = int(total_length * min_length_pct / 100)
    
    # Start with min length and increase gradually
    cutoff = 0
    best_n50 = calculate_n50(lengths)
    best_cutoff = 0
    
    # Try different cutoffs, up to the point where we'd filter too much
    for trial_cutoff in range(0, int(np.median(lengths)), 10):
        filtered_lengths = simulate_min_length_filter(lengths, trial_cutoff)
        
        if len(filtered_lengths) < min_seqs or sum(filtered_lengths) < min_len:
            break  # This cutoff removes too much
        
        current_n50 = calculate_n50(filtered_lengths)
        if current_n50 > best_n50:
            best_n50 = current_n50
            best_cutoff = trial_cutoff
    
    return best_cutoff