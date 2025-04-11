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
    Validate a complete filter pipeline configuration.
    
    Args:
        config: List of filter stage configurations
        
    Returns:
        Tuple of (is_valid, error_message, validated_config)
    """
    if not isinstance(config, list):
        return False, "Pipeline configuration must be a list", []
    
    validated_config = []
    
    for i, stage_config in enumerate(config):
        if not isinstance(stage_config, dict):
            return False, f"Stage {i} configuration must be a dictionary", []
        
        if "method" not in stage_config:
            return False, f"Stage {i} is missing the required 'method' field", []
        
        method = stage_config["method"]
        params = stage_config.get("params", {})
        
        is_valid, error, validated_params = validate_filter_config(method, params)
        if not is_valid:
            return False, f"Stage {i}: {error}", []
        
        validated_config.append({"method": method, "params": validated_params})
    
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