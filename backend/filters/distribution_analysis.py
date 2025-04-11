"""
Advanced distribution analysis for length-based filtering of genomic sequences.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats
from sklearn.mixture import GaussianMixture
from scipy.signal import find_peaks


def detect_multimodality(lengths: List[int], max_components: int = 5) -> Dict[str, Any]:
    """
    Detect multimodality in sequence length distribution using Gaussian Mixture Models.
    
    Args:
        lengths: List of sequence lengths
        max_components: Maximum number of components to consider
        
    Returns:
        Dictionary with multimodality analysis results
    """
    if not lengths or len(lengths) < max_components * 2:
        return {
            "is_multimodal": False,
            "optimal_components": 1,
            "bic_scores": [],
            "components": []
        }
    
    # Reshape data for sklearn
    X = np.array(lengths).reshape(-1, 1)
    
    # Find optimal number of components using BIC
    bic_scores = []
    models = []
    
    for n_components in range(1, min(max_components + 1, len(lengths) // 2)):
        gmm = GaussianMixture(n_components=n_components, random_state=42)
        gmm.fit(X)
        bic_scores.append(gmm.bic(X))
        models.append(gmm)
    
    # Find optimal number of components
    optimal_idx = np.argmin(bic_scores) if bic_scores else 0
    optimal_components = optimal_idx + 1 if bic_scores else 1
    
    # Extract component details if we have a model
    components = []
    if optimal_components > 0 and models:
        best_model = models[optimal_idx]
        for i in range(optimal_components):
            weight = best_model.weights_[i]
            mean = float(best_model.means_[i][0])
            var = float(best_model.covariances_[i][0][0])
            std = float(np.sqrt(var))
            
            components.append({
                "weight": weight,
                "mean": mean,
                "std": std
            })
    
    return {
        "is_multimodal": optimal_components > 1,
        "optimal_components": optimal_components,
        "bic_scores": bic_scores,
        "components": components
    }


def find_distribution_breakpoints(lengths: List[int], 
                                 prominence: float = 0.1, 
                                 width: Optional[int] = None) -> List[int]:
    """
    Find natural breakpoints in the length distribution using peak detection.
    
    Args:
        lengths: List of sequence lengths
        prominence: Relative prominence of peaks
        width: Minimum width of peaks
        
    Returns:
        List of breakpoint values
    """
    if not lengths or len(lengths) < 3:
        return []
    
    # Create histogram data
    counts, bin_edges = np.histogram(lengths, bins='auto')
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    
    # Normalize counts
    normalized_counts = counts / np.max(counts)
    
    # Find peaks
    width_param = width if width is not None else len(counts) // 10
    peaks, _ = find_peaks(normalized_counts, prominence=prominence, width=width_param)
    
    # Convert peak indices to length values
    breakpoints = [int(bin_centers[p]) for p in peaks]
    
    return sorted(breakpoints)


def identify_natural_cutoffs(lengths: List[int]) -> Dict[str, List[int]]:
    """
    Identify natural cutoff points based on distribution analysis.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Dictionary with different recommended cutoffs
    """
    if not lengths:
        return {
            "gmm_based": [],
            "peak_based": [],
            "valley_based": [],
            "recommended": []
        }
    
    # Get multimodality analysis
    multimodal_results = detect_multimodality(lengths)
    
    # GMM-based cutoffs
    gmm_cutoffs = []
    components = multimodal_results.get("components", [])
    for i in range(len(components) - 1):
        # Find intersection between adjacent components
        mean1 = components[i]["mean"]
        std1 = components[i]["std"]
        mean2 = components[i + 1]["mean"]
        std2 = components[i + 1]["std"]
        
        # Simplified intersection point
        cutoff = (mean1 + mean2) / 2
        gmm_cutoffs.append(int(cutoff))
    
    # Peak-based cutoffs
    peak_cutoffs = find_distribution_breakpoints(lengths)
    
    # Valley-based cutoffs (minima in the density)
    kde = stats.gaussian_kde(lengths)
    x = np.linspace(min(lengths), max(lengths), 1000)
    density = kde(x)
    
    # Find valleys as negative peaks
    neg_density = -density
    valleys, _ = find_peaks(neg_density, prominence=0.1)
    valley_cutoffs = [int(x[v]) for v in valleys]
    
    # Determine recommended cutoffs
    recommended = []
    
    # If multimodal, use GMM cutoffs
    if multimodal_results["is_multimodal"] and gmm_cutoffs:
        recommended = gmm_cutoffs
    # Otherwise, use valley cutoffs if available
    elif valley_cutoffs:
        recommended = valley_cutoffs
    # Otherwise, try peak cutoffs
    elif peak_cutoffs:
        recommended = peak_cutoffs
    
    return {
        "gmm_based": gmm_cutoffs,
        "peak_based": peak_cutoffs,
        "valley_based": valley_cutoffs,
        "recommended": recommended
    }


def detect_outliers_zscore(lengths: List[int], threshold: float = 3.0) -> Tuple[List[int], List[int]]:
    """
    Detect outliers using Z-score method.
    
    Args:
        lengths: List of sequence lengths
        threshold: Z-score threshold for outlier detection
        
    Returns:
        Tuple of (lower_outliers, upper_outliers)
    """
    if not lengths or len(lengths) < 2:
        return ([], [])
    
    mean = np.mean(lengths)
    std = np.std(lengths)
    
    if std == 0:  # All values are the same
        return ([], [])
    
    z_scores = [(x - mean) / std for x in lengths]
    
    lower_outliers = [lengths[i] for i, z in enumerate(z_scores) if z < -threshold]
    upper_outliers = [lengths[i] for i, z in enumerate(z_scores) if z > threshold]
    
    return (lower_outliers, upper_outliers)


def detect_outliers_combined(lengths: List[int]) -> Tuple[List[int], List[int]]:
    """
    Detect outliers using a combination of methods for better accuracy.
    
    Args:
        lengths: List of sequence lengths
        
    Returns:
        Tuple of (lower_outliers, upper_outliers)
    """
    from ..core.statistics import detect_outliers_iqr
    
    if not lengths or len(lengths) < 4:
        return ([], [])
    
    # Get outliers from both methods
    iqr_lower, iqr_upper = detect_outliers_iqr(lengths, k=1.5)
    zscore_lower, zscore_upper = detect_outliers_zscore(lengths, threshold=2.5)
    
    # Combine results - only consider as outliers if detected by both methods
    lower_outliers = list(set(iqr_lower).intersection(set(zscore_lower)))
    upper_outliers = list(set(iqr_upper).intersection(set(zscore_upper)))
    
    return (lower_outliers, upper_outliers)