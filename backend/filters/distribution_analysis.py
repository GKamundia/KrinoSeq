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
    # Add debug output at the beginning
    print(f"Running GMM with component_method={component_method}, transform_type={transform_type}")

    if not lengths or len(lengths) < 50:
        print(f"Not enough data points for GMM: {len(lengths)} < 50")
        return {
            "is_multimodal": False,
            "optimal_components": 1,
            "components": [],
            "transform_params": {"type": "none"}
        }
    
    # Apply transformation
    transformed_data, transform_params = transform_data(lengths, transform_type)
    X = transformed_data.reshape(-1, 1)
    
    # Cap the maximum number of components based on the size of the data
    # Ensure at least 2 components and limit to a maximum of 10
    max_components = min(max_components, max(2, len(lengths) // 100), 10)
    
    # Further restrict the maximum components for smaller datasets
    # If the dataset has fewer than 1000 data points, limit to a maximum of 5 components
    if len(lengths) < 1000:
        max_components = max(2, min(max_components, 5))
    
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
            "method_used": "dirichlet",
            "weight_concentrations": [float(w) for w in model.weights_],
            "weight_concentration_prior": float(1.0/max_components)
        }
        print(f"Selected {len(components)} components using dirichlet method")
        print(f"Dirichlet Process found {len(components)} components with weights: {[c['weight'] for c in components]}")
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
    
    # Add calculated LOO scores if they were computed
    if component_method == "loo":
        result["loo_scores"] = [float(score) for score in loo_scores]
    
    print(f"Selected {len(components)} components using {method_used} method")
    if component_method == "bic":
        print(f"BIC scores: {bic_scores}")
    elif component_method == "aic":
        print(f"AIC scores: {aic_scores}")
    elif component_method == "loo":
        print(f"LOO scores: {loo_scores}")
    
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


def identify_natural_cutoffs(lengths: List[int], method: str = "midpoint",
                           transform_type: str = "box-cox", 
                           component_method: str = "bic") -> Dict[str, Any]:
    """
    Identify natural cutoff points with data transformation and improved component selection.
    """
    print(f"Natural breakpoint with: method={method}, transform={transform_type}, component={component_method}")
    
    if not lengths:
        return {
            "gmm_based": [],
            "recommended": [],
            "recommended_cutoffs": [],  # Add this for frontend compatibility
            "method_used": method,
            "transform_params": {"type": "none"},
            "is_multimodal": False
        }
    
    # Get multimodality analysis with transformation
    multimodal_results = detect_multimodality(
        lengths, 
        transform_type=transform_type,
        component_method=component_method
    )
    
    # Add this line to get the actual method used from the results
    # This ensures we use what was actually applied, not just what was requested
    used_component_method = multimodal_results.get("method_used", component_method)
    
    transform_params = multimodal_results.get("transform_params", {"type": "none"})
    components = multimodal_results.get("components", [])
    
    # Store both transformed and original versions of components
    orig_components = []
    for comp in components:
        # Create a copy to avoid modifying the original
        orig_comp = comp.copy()
        # Add original space values
        orig_comp["mean_original"] = inverse_transform_value(comp["mean"], transform_params)
        orig_comp["std_original"] = abs(inverse_transform_value(comp["mean"] + comp["std"], transform_params) - 
                                      inverse_transform_value(comp["mean"], transform_params))
        # Keep transformed values too
        orig_comp["mean_transformed"] = comp["mean"]
        orig_comp["std_transformed"] = comp["std"]
        orig_components.append(orig_comp)
    
    # Fix the multimodal flag - we are multimodal if we have multiple components
    is_multimodal = len(components) > 1
    
    # If we have fewer than 2 components, we can't calculate a cutoff
    if len(components) < 2:
        print("Insufficient components to calculate cutoff")
        from ..core.visualization import generate_histogram_data
        histogram_data = generate_histogram_data(lengths)
        
        # Even if no cutoff, still generate component curves if available
        component_curves = generate_component_curves(components, transform_params, lengths)
        
        return {
            "gmm_based": [],
            "recommended": [],
            "recommended_cutoffs": [],  # Add these for frontend compatibility
            "method_used": method,
            "component_selection_method": used_component_method,  # Use the method that was actually applied
            "transform_params": transform_params,
            "component_count": len(components),
            "is_multimodal": is_multimodal,
            "components": orig_components,
            "sorted_components": orig_components,  # Add sorted_components for frontend
            "histogram": histogram_data,
            "component_curves": component_curves,
            "bic_scores": multimodal_results.get("bic_scores", []),
            "aic_scores": multimodal_results.get("aic_scores", []),
            "loo_scores": multimodal_results.get("loo_scores", []),
            "weight_concentrations": multimodal_results.get("weight_concentrations", []),
            "optimal_components": len(components)
        }
    
    # Focus on the first two components for cutoff calculation
    comp1 = components[0]
    comp2 = components[1]
    mean1, std1, weight1 = comp1["mean"], comp1["std"], comp1["weight"]
    mean2, std2, weight2 = comp2["mean"], comp2["std"], comp2["weight"]
    
    # Calculate cutoff in transformed space using selected method
    cutoff = None
    
    if method == "midpoint":
        cutoff = (mean1 + mean2) / 2
    
    elif method == "intersection":
        if std1 == std2:
            cutoff = (mean1 + mean2) / 2
        else:
            try:
                a = 1/(2*std2**2) - 1/(2*std1**2)
                b = mean1/std1**2 - mean2/std2**2
                c = mean2**2/(2*std2**2) - mean1**2/(2*std1**2) + np.log((weight2*std1)/(weight1*std2))

                discriminant = b**2 - 4*a*c
                if discriminant < 0:
                    cutoff = (mean1 + mean2) / 2
                else:
                    sol1 = (-b + np.sqrt(discriminant))/(2*a)
                    sol2 = (-b - np.sqrt(discriminant))/(2*a)
                    
                    if min(mean1, mean2) <= sol1 <= max(mean1, mean2):
                        cutoff = sol1
                    elif min(mean1, mean2) <= sol2 <= max(mean1, mean2):
                        cutoff = sol2
                    else:
                        cutoff = (mean1 + mean2) / 2
            except Exception as e:
                print(f"Error calculating intersection: {str(e)}")
                cutoff = (mean1 + mean2) / 2
    
    elif method == "probability":
        x_vals = np.linspace(mean1, mean2, 1000)
        for x in x_vals:
            p_comp1 = weight1 * stats.norm.pdf(x, mean1, std1)
            p_comp2 = weight2 * stats.norm.pdf(x, mean2, std2)
            
            if p_comp1 <= p_comp2:
                cutoff = x
                break
        
        if cutoff is None:
            cutoff = (mean1 + mean2) / 2
    
    elif method == "valley":
        x_vals = np.linspace(mean1, mean2, 1000)
        pdfs = (weight1 * stats.norm.pdf(x_vals, mean1, std1) + 
                weight2 * stats.norm.pdf(x_vals, mean2, std2))
        min_idx = np.argmin(pdfs)
        cutoff = x_vals[min_idx]
    
    else:
        cutoff = (mean1 + mean2) / 2
        method = "midpoint"
    
    # Transform cutoff back to original space
    if cutoff is not None:
        original_cutoff = inverse_transform_value(cutoff, transform_params)
        
        # Ensure it's a reasonable value for genomic data
        original_cutoff = max(original_cutoff, 100)  # Minimum reasonable contig length
        original_cutoff = min(original_cutoff, 5000)  # Maximum reasonable cutoff
        
        # Round to nearest integer
        gmm_cutoffs = [int(round(original_cutoff))]
        print(f"GMM cutoff (transformed back): {gmm_cutoffs[0]}")
    else:
        gmm_cutoffs = []
    
    # Calculate statistics on filtered results
    if gmm_cutoffs:
        filtered_lengths = [l for l in lengths if l >= gmm_cutoffs[0]]
        retained_count = len(filtered_lengths)
        retained_percent = (retained_count / len(lengths)) * 100
        retained_bp = sum(filtered_lengths)
        total_bp = sum(lengths)
        retained_bp_percent = (retained_bp / total_bp) * 100
        
        filtering_stats = {
            "cutoff": gmm_cutoffs[0],
            "total_contigs": len(lengths),
            "retained_contigs": retained_count,
            "retained_contigs_percent": retained_percent,
            "total_bp": total_bp,
            "retained_bp": retained_bp,
            "retained_bp_percent": retained_bp_percent
        }
    else:
        filtering_stats = {}
    
    # Generate histogram data for visualization
    from ..core.visualization import generate_histogram_data
    histogram_data = generate_histogram_data(lengths)
    
    # Generate component curves data for frontend visualization
    component_curves = generate_component_curves(components, transform_params, lengths)
    
    # Find candidate cutoffs for reference
    peak_cutoffs = find_distribution_breakpoints(lengths)
    
    # Calculate KDE for valley detection
    kde = stats.gaussian_kde(lengths)
    x = np.linspace(min(lengths), max(lengths), 1000)
    density = kde(x)
    neg_density = -density
    valleys, _ = find_peaks(neg_density, prominence=0.1)
    valley_cutoffs = [int(x[v]) for v in valleys]
    
    result = {
        "gmm_based": gmm_cutoffs,
        "recommended": gmm_cutoffs,
        "recommended_cutoffs": gmm_cutoffs,  # Add this for frontend compatibility
        "selected_cutoff": gmm_cutoffs[0] if gmm_cutoffs else None,
        "method_used": method,
        "component_selection_method": used_component_method,  # Use the method that was actually applied
        "transform_params": transform_params,
        "component_count": len(components),
        "is_multimodal": is_multimodal,  # Fixed multimodal flag
        "filtering_stats": filtering_stats,
        "components": orig_components,  # Components with original space values
        "sorted_components": orig_components,  # Add sorted_components for frontend
        "histogram": histogram_data,
        "component_curves": component_curves,  # Add component curves for visualization
        "peak_cutoffs": peak_cutoffs,
        "valley_cutoffs": valley_cutoffs,
        "bic_scores": multimodal_results.get("bic_scores", []),
        "aic_scores": multimodal_results.get("aic_scores", []),
        "loo_scores": multimodal_results.get("loo_scores", []),
        "weight_concentrations": multimodal_results.get("weight_concentrations", []),
        "optimal_components": len(components)
    }
    
    return convert_numpy_types(result)


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
    """
    transform_params = {"type": transform_type}
    
    if transform_type == "box-cox":
        try:
            # Box-Cox requires positive values
            min_length = min(lengths)
            if min_length <= 0:
                offset = abs(min_length) + 1
                adjusted_lengths = [x + offset for x in lengths]
            else:
                offset = 0
                adjusted_lengths = lengths
            
            # Apply Box-Cox transformation with bounded lambda
            # This avoids extreme transformations that can cause issues
            transformed_data, lmbda = stats.boxcox(adjusted_lengths, lmbda=None)
            
            # Limit lambda to a reasonable range
            if abs(lmbda) > 3:
                print(f"Box-Cox lambda {lmbda:.4f} is extreme, limiting transformation")
                lmbda = 0 if lmbda < 0 else 0.5
                transformed_data = np.log1p(adjusted_lengths) if lmbda < 0.01 else np.power(adjusted_lengths, lmbda)
            
            transform_params.update({"lambda": float(lmbda), "offset": offset})
            print(f"Box-Cox transformation applied with lambda={lmbda:.4f}, offset={offset}")
            
        except Exception as e:
            print(f"Box-Cox transformation failed: {str(e)}, falling back to log transform")
            # Fallback to log transform
            transformed_data = np.log1p(lengths)
            transform_params = {"type": "log", "offset": 1}
    
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


def generate_component_curves(components: List[Dict], transform_params: Dict, lengths: List[int]) -> List[Dict]:
    """
    Generate component curve data in the original space for visualization.
    
    Args:
        components: List of component parameters (weight, mean, std) in transformed space
        transform_params: Transformation parameters
        lengths: Original length values for determining proper range
        
    Returns:
        List of component curves with x and y values in original space
    """
    if not components:
        return []
    
    curves = []
    
    # Determine appropriate range for curve generation (both in transformed and original space)
    min_length = min(lengths)
    max_length = max(lengths)
    
    # Generate 200 points in original space
    original_x = np.linspace(min_length, max_length, 200)
    
    # Transform these points to transformed space
    if transform_params["type"] == "box-cox":
        lmbda = transform_params.get("lambda", 0)
        offset = transform_params.get("offset", 0)
        
        if abs(lmbda) < 1e-8:  # Lambda near zero is approximately log
            transformed_x = np.log(original_x + offset)
        else:
            transformed_x = ((original_x + offset) ** lmbda - 1) / lmbda
    
    elif transform_params["type"] == "log":
        transformed_x = np.log1p(original_x)
    
    else:  # No transformation
        transformed_x = original_x
    
    # For each component, calculate its density in transformed space and keep x in original space
    for i, comp in enumerate(components):
        mean_t = comp["mean"]  # Mean in transformed space
        std_t = comp["std"]    # Std in transformed space
        weight = comp["weight"]
        
        # Calculate density in transformed space
        density_t = weight * stats.norm.pdf(transformed_x, mean_t, std_t)
        
        # Store curve with x in original space
        curve = {
            "x": original_x.tolist(),
            "y": density_t.tolist(),
            "component_index": i,
            "weight": weight,
            "mean_transformed": mean_t,
            "std_transformed": std_t,
            "mean_original": inverse_transform_value(mean_t, transform_params),
            "std_original": abs(inverse_transform_value(mean_t + std_t, transform_params) - 
                              inverse_transform_value(mean_t, transform_params))
        }
        curves.append(curve)
    
    return curves


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