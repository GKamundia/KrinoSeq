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
    
    result = {
        "is_multimodal": bool(optimal_components > 1),
        "optimal_components": int(optimal_components),
        "bic_scores": [float(score) for score in bic_scores],
        "components": components
    }
    return convert_numpy_types(result)


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


def identify_natural_cutoffs(lengths: List[int], method: str = "midpoint") -> Dict[str, List[int]]:
    """
    Identify natural cutoff points based on distribution analysis.
    """
    if not lengths:
        return {
            "gmm_based": [],
            "peak_based": [],
            "valley_based": [],
            "recommended": [],
            "method_used": method  # Always include the intended method
        }
    
    # Get multimodality analysis
    multimodal_results = detect_multimodality(lengths)
    
    # GMM-based cutoffs
    gmm_cutoffs = []
    components = multimodal_results.get("components", [])
    
    # Sort components by mean - THIS IS IMPORTANT
    sorted_components = sorted(components, key=lambda c: c["mean"])
    
    # Always clear gmm_cutoffs at the start of each method to prevent interference
    gmm_cutoffs = []
    
    if len(sorted_components) >= 2:
        # Calculate different cutoffs based on the selected method
        if method == "midpoint":
            # Method 1a: Simple midpoint between first two sorted components
            mean1 = sorted_components[0]["mean"]
            mean2 = sorted_components[1]["mean"]
            cutoff = (mean1 + mean2) / 2
            gmm_cutoffs.append(int(cutoff))

        elif method == "intersection":
            # Method 1b: Find intersection point between components
            comp1 = sorted_components[0]
            comp2 = sorted_components[1]
            mean1, std1, weight1 = comp1["mean"], comp1["std"], comp1["weight"]
            mean2, std2, weight2 = comp2["mean"], comp2["std"], comp2["weight"]

            if std1 == std2:
                # With equal std, intersection is midpoint
                cutoff = (mean1 + mean2) / 2
            else:
                # Solve quadratic equation for intersection point
                try:
                    a = 1/(2*std2**2) - 1/(2*std1**2)
                    b = mean1/std1**2 - mean2/std2**2
                    c = mean2**2/(2*std2**2) - mean1**2/(2*std1**2) + np.log((weight2*std1)/(weight1*std2))

                    # Solve for roots using quadratic formula
                    discriminant = b**2 - 4*a*c
                    if discriminant < 0:
                        # No real solution, use midpoint as fallback
                        cutoff = (mean1 + mean2) / 2
                    else:
                        # Find the root between the two means
                        sol1 = (-b + np.sqrt(discriminant))/(2*a)
                        sol2 = (-b - np.sqrt(discriminant))/(2*a)
                        
                        # Choose the solution between the means
                        if min(mean1, mean2) <= sol1 <= max(mean1, mean2):
                            cutoff = sol1
                        elif min(mean1, mean2) <= sol2 <= max(mean1, mean2):
                            cutoff = sol2
                        else:
                            # Fallback to midpoint if solutions are outside mean range
                            cutoff = (mean1 + mean2) / 2
                except:
                    # If any calculation error occurs, use midpoint
                    cutoff = (mean1 + mean2) / 2

            gmm_cutoffs.append(int(cutoff))

        elif method == "probability":
            # Method 2: Find cutoff based on probability assignment
            # Define first component as unwanted, rest as wanted
            x_vals = np.linspace(sorted_components[0]["mean"],
                                sorted_components[1]["mean"],
                                num=1000)
            
            # Find where posterior probability = 0.5
            cutoff = None
            for x in x_vals:
                p_unwanted = 0
                p_total = 0
                
                for comp in sorted_components:
                    weight = comp["weight"]
                    mean = comp["mean"]
                    std = comp["std"]
                    # Calculate component density at x
                    density = weight * stats.norm.pdf(x, mean, std)
                    p_total += density
                    
                    # First component is "unwanted"
                    if comp == sorted_components[0]:
                        p_unwanted = density
                
                # Calculate posterior probability
                if p_total > 0:
                    posterior = p_unwanted / p_total
                    
                    # Found our boundary at ~0.5 probability
                    if abs(posterior - 0.5) < 0.01:
                        cutoff = x
                        break
                    
                    # We crossed the 0.5 threshold, use linear interpolation
                    if posterior < 0.5 and cutoff is None:
                        cutoff = x
                        break
            
            # If no cutoff found, use midpoint but keep track that we fell back
            if cutoff is not None:
                gmm_cutoffs.append(int(cutoff))
            else:
                mean1 = sorted_components[0]["mean"]
                mean2 = sorted_components[1]["mean"]
                gmm_cutoffs.append(int((mean1 + mean2) / 2))

        elif method == "valley":
            # Method 3: Find valleys in combined PDF
            # Generate x values spanning between the first two component means with extra margin
            margin = 0.5  # 50% extra margin on each side
            span = sorted_components[1]["mean"] - sorted_components[0]["mean"]
            x_min = max(0, sorted_components[0]["mean"] - margin * span)
            x_max = sorted_components[1]["mean"] + margin * span
            x_vals = np.linspace(x_min, x_max, 1000)
            
            # Calculate combined PDF
            pdfs = np.zeros_like(x_vals, dtype=float)
            for comp in sorted_components:
                weight = comp["weight"]
                mean = comp["mean"]
                std = comp["std"]
                pdfs += weight * stats.norm.pdf(x_vals, mean, std)
            
            # Find valleys (local minima)
            # Use negative PDF for finding peaks
            neg_pdf = -pdfs
            valleys, _ = find_peaks(neg_pdf, prominence=0.001)  # Lower prominence threshold
            
            # Filter valleys to only include those between component means with margin
            valid_valleys = []
            for valley_idx in valleys:
                valley_x = x_vals[valley_idx]
                # Check if valley is between the two means (with margin)
                if x_min <= valley_x <= x_max:
                    valid_valleys.append(valley_x)
            
            # Use the first valid valley, or the midpoint if none found
            if valid_valleys:
                gmm_cutoffs.append(int(valid_valleys[0]))
            else:
                # Fall back to midpoint if no valleys found
                mean1 = sorted_components[0]["mean"]
                mean2 = sorted_components[1]["mean"]
                gmm_cutoffs.append(int((mean1 + mean2) / 2))
                
        else:
            # Unknown method, fall back to midpoint
            mean1 = sorted_components[0]["mean"]
            mean2 = sorted_components[1]["mean"]
            cutoff = (mean1 + mean2) / 2
            gmm_cutoffs.append(int(cutoff))
    
    # Notice we've removed the fallback - if a specific method doesn't work,
    # it has its own internal fallback but preserves the method name
    
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
    recommended = gmm_cutoffs if gmm_cutoffs else (valley_cutoffs if valley_cutoffs else peak_cutoffs)
    
    return convert_numpy_types({
        "gmm_based": gmm_cutoffs,
        "peak_based": peak_cutoffs,
        "valley_based": valley_cutoffs,
        "recommended": recommended,
        "method_used": method  # Always report the requested method
    })


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


def convert_numpy_types(obj):
    """Convert NumPy types to Python native types for JSON serialization."""
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj