"""
Configuration validation for filtering parameters.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import os


# Define valid parameter ranges for different filter methods
FILTER_METHOD_PARAMS = {
    "min_max": {
        "min_length": {"type": "int", "min": 0, "required": False},
        "max_length": {"type": "int", "min": 0, "required": False}
    },
    "iqr": {
        "k": {"type": "float", "min": 0, "max": 10, "default": 1.5}
    },
    "zscore": {
        "threshold": {"type": "float", "min": 0, "max": 10, "default": 2.5}
    },
    "adaptive": {},  # No parameters needed
    "n50_optimize": {
        "min_cutoff": {"type": "int", "min": 0, "required": False},
        "max_cutoff": {"type": "int", "min": 0, "required": False},
        "step": {"type": "int", "min": 1, "max": 1000, "default": 10}
    },
    "natural": {}  # No parameters needed
}


def validate_filter_config(method: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Validate filter configuration parameters.
    
    Args:
        method: Filter method name
        params: Parameters for the filter method
        
    Returns:
        Tuple of (is_valid, error_message, validated_params)
    """
    if method not in FILTER_METHOD_PARAMS:
        return False, f"Unknown filter method: {method}", {}
    
    method_params = FILTER_METHOD_PARAMS[method]
    validated_params = {}
    
    # Check for required parameters
    for param_name, param_config in method_params.items():
        if param_config.get("required", False) and param_name not in params:
            return False, f"Missing required parameter: {param_name}", {}
    
    # Validate all provided parameters
    for param_name, param_value in params.items():
        if param_name not in method_params:
            return False, f"Unknown parameter for method {method}: {param_name}", {}
        
        param_config = method_params[param_name]
        
        # Type validation
        if param_config.get("type") == "int":
            if not isinstance(param_value, (int, float)) or not float(param_value).is_integer():
                return False, f"Parameter {param_name} must be an integer", {}
            param_value = int(param_value)
        elif param_config.get("type") == "float":
            if not isinstance(param_value, (int, float)):
                return False, f"Parameter {param_name} must be a number", {}
            param_value = float(param_value)
        
        # Range validation
        if "min" in param_config and param_value < param_config["min"]:
            return False, f"Parameter {param_name} must be >= {param_config['min']}", {}
        if "max" in param_config and param_value > param_config["max"]:
            return False, f"Parameter {param_name} must be <= {param_config['max']}", {}
        
        validated_params[param_name] = param_value
    
    # Add defaults for missing optional parameters
    for param_name, param_config in method_params.items():
        if param_name not in validated_params and "default" in param_config:
            validated_params[param_name] = param_config["default"]
    
    return True, None, validated_params


def validate_pipeline_config(config: List[Dict[str, Any]]) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    """
    Validate the pipeline configuration.
    
    Args:
        config: List of filter stage configurations
        
    Returns:
        Tuple of (is_valid, error_message, validated_config)
    """
    validated_config = []
    
    if not config:
        return False, "Configuration cannot be empty", []
    
    allowed_methods = ["min_max", "iqr", "zscore", "adaptive", "n50_optimize", "natural"]
    
    for stage in config:
        # Check method existence and validity
        if "method" not in stage:
            return False, "Method must be specified for each stage", []
            
        method = stage["method"]
        if method not in allowed_methods:
            return False, f"Invalid method: {method}", []
        
        # Check and validate parameters
        params = stage.get("params", {})
        validated_params = {}
        
        # Method-specific validation
        if method == "min_max":
            # Validate min/max length parameters
            if "min_length" in params:
                try:
                    validated_params["min_length"] = int(params["min_length"])
                    if validated_params["min_length"] < 0:
                        return False, "min_length cannot be negative", []
                except (ValueError, TypeError):
                    return False, "min_length must be an integer", []
                    
            if "max_length" in params:
                try:
                    validated_params["max_length"] = int(params["max_length"])
                    if validated_params["max_length"] < 0:
                        return False, "max_length cannot be negative", []
                except (ValueError, TypeError):
                    return False, "max_length must be an integer", []
                    
            if "min_length" in validated_params and "max_length" in validated_params:
                if validated_params["min_length"] > validated_params["max_length"]:
                    return False, "min_length cannot be greater than max_length", []
                    
        elif method == "iqr":
            # Validate IQR multiplier
            if "k" in params:
                try:
                    validated_params["k"] = float(params["k"])
                    if validated_params["k"] <= 0:
                        return False, "k must be positive", []
                except (ValueError, TypeError):
                    return False, "k must be a number", []
            else:
                validated_params["k"] = 1.5  # Default value
                
        elif method == "zscore":
            # Validate z-score threshold
            if "threshold" in params:
                try:
                    validated_params["threshold"] = float(params["threshold"])
                    if validated_params["threshold"] <= 0:
                        return False, "threshold must be positive", []
                except (ValueError, TypeError):
                    return False, "threshold must be a number", []
            else:
                validated_params["threshold"] = 2.5  # Default value
                
        elif method == "natural":
            # Validate GMM method
            if "gmm_method" in params:
                gmm_method = params["gmm_method"]
                # ADD THIS - explicitly define the allowed GMM methods
                allowed_gmm_methods = ["midpoint", "intersection", "probability", "valley"]
                if gmm_method not in allowed_gmm_methods:
                    return False, f"Invalid GMM method: {gmm_method}. Must be one of {allowed_gmm_methods}", []
                validated_params["gmm_method"] = gmm_method
            else:
                validated_params["gmm_method"] = "midpoint"  # Default value
                
        elif method == "n50_optimize":
            # Validate N50 optimization parameters
            for param_name, param_type in [("min_cutoff", int), ("max_cutoff", int), ("step", int)]:
                if param_name in params:
                    try:
                        value = param_type(params[param_name])
                        if value <= 0:
                            return False, f"{param_name} must be positive", []
                        validated_params[param_name] = value
                    except (ValueError, TypeError):
                        return False, f"{param_name} must be a {param_type.__name__}", []
            
            if "min_cutoff" in validated_params and "max_cutoff" in validated_params:
                if validated_params["min_cutoff"] >= validated_params["max_cutoff"]:
                    return False, "min_cutoff must be less than max_cutoff", []
                    
        # Add the validated stage to the config
        validated_config.append({
            "method": method,
            "params": validated_params
        })
    
    return True, None, validated_config


def load_config_from_file(config_path: str) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    """
    Load and validate a pipeline configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration JSON file
        
    Returns:
        Tuple of (is_valid, error_message, validated_config)
    """
    if not os.path.exists(config_path):
        return False, f"Configuration file not found: {config_path}", []
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        return False, f"Error loading configuration file: {str(e)}", []
    
    return validate_pipeline_config(config)