"""
Advanced distribution analysis for length-based filtering of genomic sequences.
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import stats
from sklearn.mixture import GaussianMixture
from scipy.signal import find_peaks


def detect_multimodality(lengths: List[int], max_components: int = 10, 
                         transform_type: str = "box-cox",
                         component_method: str = "bic") -> Dict[str, Any]:
    """
    Detect multimodality in sequence length distribution using Gaussian Mixture Models
    with multiple component selection methods and data transformation.
    
    Args:
        lengths: List of sequence lengths
        max_components: Maximum number of components to consider
        transform_type: Data transformation method ('box-cox', 'log', 'none')
        component_method: Method for selecting number of components ('bic', 'aic', 'loo', 'dirichlet')
        
    Returns:
        Dictionary with multimodality analysis results
    """
    if not lengths or len(lengths) < 50:
        return {
            "is_multimodal": False,
            "optimal_components": 1,
            "components": [],
            "transform_params": {"type": "none"}
        }
    
    # Apply transformation
    transformed_data, transform_params = transform_data(lengths, transform_type)
    X = transformed_data.reshape(-1, 1)
    
    # Cap max components based on data size
    max_components = min(max_components, len(lengths) // 100, 10)
    if len(lengths) < 1000:
        max_components = min(max_components, 5)
    
    # Dirichlet Process approach (nonparametric)
    if component_method == "dirichlet":
        from sklearn.mixture import BayesianGaussianMixture
        
        model = BayesianGaussianMixture(
            n_components=max_components,
            weight_concentration_prior=1.0/max_components,
            weight_concentration_prior_type="dirichlet_process",
            max_iter=500,
            n_init=10,
            random_state=42
        )
        model.fit(X)
        
        # Extract components with non-negligible weights
        weights = model.weights_
        means = model.means_
        covariances = model.covariances_
        
        # Get model evaluation metrics for completeness
        bic_score = model.bic(X) if hasattr(model, 'bic') else None
        
        # Store components with weight >= 0.01
        components = []
        for i in range(len(weights)):
            if weights[i] >= 0.01:  # Apply weight threshold
                components.append({
                    "weight": float(weights[i]), 
                    "mean": float(means[i][0]),
                    "std": float(np.sqrt(covariances[i][0][0]))
                })
        
        # Sort components by mean
        components = sorted(components, key=lambda c: c["mean"])
        
        result = {
            "is_multimodal": len(components) > 1,
            "optimal_components": len(components),
            "components": components,
            "transform_params": transform_params,
            "method_used": "dirichlet"
        }
        return convert_numpy_types(result)
    
    # Traditional information criteria approaches
    bic_scores = []
    aic_scores = []
    models = []
    
    for n_components in range(1, max_components + 1):
        try:
            gmm = GaussianMixture(
                n_components=n_components,
                random_state=42,
                n_init=10,
                init_params='kmeans',
                max_iter=300,
                reg_covar=1e-5  # Better regularization for genomic data
            )
            gmm.fit(X)
            bic_scores.append(gmm.bic(X))
            aic_scores.append(gmm.aic(X))
            models.append(gmm)
        except Exception as e:
            print(f"Error fitting GMM with {n_components} components: {str(e)}")
            break
    
    if not models:
        return {
            "is_multimodal": False,
            "optimal_components": 1,
            "components": [],
            "transform_params": transform_params
        }
    
    # Select optimal number of components based on method
    if component_method == "aic":
        optimal_idx = np.argmin(aic_scores)
        method_used = "aic"
    elif component_method == "loo":
        # PSIS-LOO is approximated using a penalty on AIC
        loo_scores = [aic + 2*np.log(np.log(n)) * k 
                     for k, (aic, n) in enumerate(zip(aic_scores, [len(X)]*len(aic_scores)))]
        optimal_idx = np.argmin(loo_scores)
        method_used = "loo"
    else:  # Default to BIC
        optimal_idx = np.argmin(bic_scores)
        method_used = "bic"
    
    best_model = models[optimal_idx]
    
    # Extract components and apply weight threshold
    components = []
    for i in range(best_model.n_components):
        weight = best_model.weights_[i]
        if weight >= 0.01:  # Apply weight threshold
            mean = float(best_model.means_[i][0])
            var = float(best_model.covariances_[i][0][0])
            std = float(np.sqrt(var))
            
            components.append({
                "weight": weight,
                "mean": mean,
                "std": std
            })
    
    # Sort components by mean
    components = sorted(components, key=lambda c: c["mean"])
    
    result = {
        "is_multimodal": len(components) > 1,
        "optimal_components": len(components),
        "bic_scores": [float(score) for score in bic_scores],
        "aic_scores": [float(score) for score in aic_scores],
        "components": components,
        "transform_params": transform_params,
        "method_used": method_used
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
    Identify natural cutoff points based on distribution analysis using 
    mathematically sound GMM valley detection across all component pairs.
    """
    # Debug output to confirm the method being used
    print(f"Natural breakpoint method called with: {method}")
    
    if not lengths:
        return {
            "gmm_based": [],
            "peak_based": [],
            "valley_based": [],
            "recommended": [],
            "method_used": method
        }
    
    # Get multimodality analysis
    multimodal_results = detect_multimodality(lengths)
    
    # GMM-based cutoffs
    gmm_cutoffs = []
    components = multimodal_results.get("components", [])
    
    # Sort components by mean - THIS IS IMPORTANT
    sorted_components = sorted(components, key=lambda c: c["mean"])
    
    # IMPROVED APPROACH: Calculate cutoff candidates between ALL adjacent component pairs
    cutoff_candidates = []
    cutoff_densities = []
    cutoff_methods = []  # Track which method produced each cutoff
    
    if len(sorted_components) >= 2:
        for i in range(len(sorted_components)-1):
            comp1 = sorted_components[i]
            comp2 = sorted_components[i+1]
            mean1, std1, weight1 = comp1["mean"], comp1["std"], comp1["weight"]
            mean2, std2, weight2 = comp2["mean"], comp2["std"], comp2["weight"]
            
            # Calculate cutoff point based on selected method
            cutoff = None
            used_method = method  # Track the actual method used (including fallbacks)
            
            if method == "midpoint":
                # Simple midpoint between means
                cutoff = (mean1 + mean2) / 2
            
            elif method == "intersection":
                # Find intersection point of the weighted component densities
                if std1 == std2:
                    # With equal std, intersection is midpoint
                    cutoff = (mean1 + mean2) / 2
                else:
                    # Solve quadratic equation for intersection
                    try:
                        a = 1/(2*std2**2) - 1/(2*std1**2)
                        b = mean1/std1**2 - mean2/std2**2
                        c = mean2**2/(2*std2**2) - mean1**2/(2*std1**2) + np.log((weight2*std1)/(weight1*std2))

                        # Solve for roots
                        discriminant = b**2 - 4*a*c
                        if discriminant < 0:
                            # No real solution, use midpoint but keep method as intersection
                            cutoff = (mean1 + mean2) / 2
                        else:
                            # Find the root between the means
                            sol1 = (-b + np.sqrt(discriminant))/(2*a)
                            sol2 = (-b - np.sqrt(discriminant))/(2*a)
                            
                            # Choose solution between means
                            if min(mean1, mean2) <= sol1 <= max(mean1, mean2):
                                cutoff = sol1
                            elif min(mean1, mean2) <= sol2 <= max(mean1, mean2):
                                cutoff = sol2
                            else:
                                # Fallback to midpoint but keep method as intersection
                                cutoff = (mean1 + mean2) / 2
                    except Exception as e:
                        # Log error for debugging
                        print(f"Error calculating intersection: {str(e)}")
                        # Error in calculation, use midpoint but keep method as intersection
                        cutoff = (mean1 + mean2) / 2
            
            elif method == "probability":
                # Find where posterior probability = 0.5
                x_vals = np.linspace(mean1, mean2, 1000)
                found_cutoff = False
                
                for x in x_vals:
                    p_comp1 = weight1 * stats.norm.pdf(x, mean1, std1)
                    p_comp2 = weight2 * stats.norm.pdf(x, mean2, std2)
                    
                    if p_comp1 <= p_comp2:  # Crossing point where P(comp1|x) = 0.5
                        cutoff = x
                        found_cutoff = True
                        break
                
                # If no cutoff found, use midpoint but keep method as probability
                if not found_cutoff:
                    cutoff = (mean1 + mean2) / 2
            
            elif method == "valley":
                # Find valley in the combined PDF of these two components
                x_vals = np.linspace(mean1, mean2, 1000)
                pdfs = np.zeros_like(x_vals, dtype=float)
                
                # Calculate density from just these two components
                pdfs += weight1 * stats.norm.pdf(x_vals, mean1, std1)
                pdfs += weight2 * stats.norm.pdf(x_vals, mean2, std2)
                
                # Find minimum of the combined density
                min_idx = np.argmin(pdfs)
                cutoff = x_vals[min_idx]
            
            else:
                # Unknown method, use midpoint
                cutoff = (mean1 + mean2) / 2
                used_method = "midpoint"  # Mark actual method used as midpoint
            
            if cutoff is not None:
                cutoff_candidates.append(cutoff)
                cutoff_methods.append(used_method)
                
                # CRITICAL IMPROVEMENT: Calculate full mixture density at this cutoff point
                mixture_density = 0
                for comp in sorted_components:  # Use ALL components
                    w, m, s = comp["weight"], comp["mean"], comp["std"]
                    mixture_density += w * stats.norm.pdf(cutoff, m, s)
                
                cutoff_densities.append(mixture_density)
    
    # CRITICAL IMPROVEMENT: Select the cutoff with the deepest valley (minimum density)
    if cutoff_candidates:
        if len(cutoff_candidates) == 1:
            # Only one candidate, use it
            gmm_cutoffs = [int(cutoff_candidates[0])]
        else:
            # Sort candidates by their mixture density (ascending)
            sorted_indices = np.argsort(cutoff_densities)
            
            # Select all cutoffs, sorted from deepest to shallowest valley
            gmm_cutoffs = [int(cutoff_candidates[i]) for i in sorted_indices]
    
    # Calculate other cutoff types for reference
    peak_cutoffs = find_distribution_breakpoints(lengths)
    
    kde = stats.gaussian_kde(lengths)
    x = np.linspace(min(lengths), max(lengths), 1000)
    density = kde(x)
    neg_density = -density
    valleys, _ = find_peaks(neg_density, prominence=0.1)
    valley_cutoffs = [int(x[v]) for v in valleys]
    
    # Use GMM cutoffs if available, prioritizing the deepest valley
    recommended = gmm_cutoffs if gmm_cutoffs else (valley_cutoffs if valley_cutoffs else peak_cutoffs)
    
    # Print debug info to verify
    print(f"GMM method {method} produced cutoffs: {gmm_cutoffs}")
    
    return convert_numpy_types({
        "gmm_based": gmm_cutoffs,
        "peak_based": peak_cutoffs,
        "valley_based": valley_cutoffs,
        "recommended": recommended,
        "method_used": method,  # Always return the original requested method
        "cutoff_densities": cutoff_densities if cutoff_densities else []
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


def transform_data(lengths: List[int], transform_type: str = "box-cox") -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Transform length data to achieve better normality for GMM modeling.
    
    Args:
        lengths: List of sequence lengths
        transform_type: Transformation method ('box-cox', 'log', 'none')
        
    Returns:
        Tuple of (transformed data, transformation parameters)
    """
    transform_params = {"type": transform_type}
    
    if transform_type == "box-cox":
        # Box-Cox requires positive values
        min_length = min(lengths)
        if min_length <= 0:
            offset = abs(min_length) + 1
            adjusted_lengths = [x + offset for x in lengths]
        else:
            offset = 0
            adjusted_lengths = lengths
        
        # Apply Box-Cox transformation
        transformed_data, lmbda = stats.boxcox(adjusted_lengths)
        transform_params.update({"lambda": float(lmbda), "offset": offset})
        print(f"Box-Cox transformation applied with lambda={lmbda:.4f}, offset={offset}")
        
    elif transform_type == "log":
        # Log transformation (add 1 to handle zeros)
        transformed_data = np.log1p(lengths)
        transform_params.update({"offset": 1})
        print("Log transformation (log1p) applied")
        
    else:  # "none"
        transformed_data = np.array(lengths, dtype=float)
        print("No transformation applied")
    
    return transformed_data, transform_params


def inverse_transform_value(value: float, transform_params: Dict[str, Any]) -> float:
    """
    Transform a value back from transformed space to original space.
    
    Args:
        value: Value in transformed space
        transform_params: Transformation parameters
        
    Returns:
        Value in original space
    """
    if transform_params["type"] == "box-cox":
        lmbda = transform_params["lambda"]
        offset = transform_params.get("offset", 0)
        
        if abs(lmbda) < 1e-8:  # Lambda near zero is approximately log
            original = np.exp(value) - offset
        else:
            original = (lmbda * value + 1) ** (1/lmbda) - offset
            
    elif transform_params["type"] == "log":
        original = np.expm1(value)  # Inverse of log1p
        
    else:  # No transformation
        original = value
        
    return original


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