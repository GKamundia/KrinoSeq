"""
Module for generating data for sequence length visualizations.
"""

from typing import Dict, List
import numpy as np
from scipy import stats


def generate_histogram_data(lengths: List[int], bins: int = 50) -> Dict[str, List]:
    """
    Generate data for a histogram visualization of sequence lengths.
    
    Args:
        lengths: List of sequence lengths
        bins: Number of bins for the histogram
        
    Returns:
        Dictionary containing bin edges and counts
    """
    if not lengths:
        return {"bin_edges": [0], "bin_centers": [0], "counts": [0]}
    
    counts, bin_edges = np.histogram(lengths, bins=bins)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    
    return {
        "bin_edges": bin_edges.tolist(),
        "bin_centers": bin_centers.tolist(),
        "counts": counts.tolist()
    }


def generate_kde_data(lengths: List[int], points: int = 1000) -> Dict[str, List]:
    """
    Generate kernel density estimation data for sequence lengths.
    
    Args:
        lengths: List of sequence lengths
        points: Number of points to evaluate the KDE
        
    Returns:
        Dictionary containing x-values and density values
    """
    if not lengths or len(lengths) < 2:
        return {"x": [0], "density": [0]}
    
    # Apply KDE
    kde = stats.gaussian_kde(lengths)
    
    # Generate x values spanning the range of lengths
    min_x = float(min(lengths))
    max_x = float(max(lengths))
    
    # Ensure we have a decent range even with clustered data
    padding = (max_x - min_x) * 0.1
    x = np.linspace(max(0, min_x - padding), max_x + padding, points)
    
    # Calculate density values
    density = kde(x)
    
    return {
        "x": x.tolist(),
        "density": density.tolist()
    }


def generate_cumulative_distribution_data(lengths: List[int]) -> Dict[str, List]:
    """
    Generate cumulative length distribution data.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Dictionary containing sorted lengths and cumulative percentages
    """
    if not lengths:
        return {"lengths": [0], "cumulative_percent": [0]}
    
    # Sort lengths in descending order
    sorted_lengths = sorted(lengths, reverse=True)
    total_length = sum(sorted_lengths)
    
    # Calculate cumulative sum
    cumulative_sum = np.cumsum(sorted_lengths)
    
    # Convert to percentage of total
    cumulative_percent = (cumulative_sum / total_length * 100).tolist()
    
    return {
        "lengths": sorted_lengths,
        "cumulative_sum": cumulative_sum.tolist(),
        "cumulative_percent": cumulative_percent
    }
def generate_length_distribution(lengths: List[int]) -> Dict[str, Dict]:
    """
    Generate comprehensive length distribution data for visualization.
    
    This function combines histogram, KDE, and cumulative distribution data
    into a single structure expected by the frontend visualization component.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Dictionary containing histogram, kde, and cumulative distribution data
    """
    if not lengths:
        return {
            "histogram": {"bin_centers": [0], "counts": [0]},
            "kde": {"x": [0], "density": [0]},
            "cumulative": {"lengths": [0], "cumulative_percent": [0]}
        }
        
    return {
        "histogram": generate_histogram_data(lengths),
        "kde": generate_kde_data(lengths),
        "cumulative": generate_cumulative_distribution_data(lengths)
    }