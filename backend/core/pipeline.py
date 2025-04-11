"""
Filter pipeline architecture for chaining multiple filtering methods.
"""

from typing import Dict, List, Any, Optional, Callable
import copy
from ..filters import apply_optimal_filter
from .visualization import generate_length_distribution


class FilterStage:
    """A single stage in the filtering pipeline."""
    
    def __init__(self, method: str, **params):
        """
        Initialize a filter stage.
        
        Args:
            method: Filtering method to use
            **params: Parameters for the filter method
        """
        self.method = method
        self.params = params
        self.filtered_count = 0
        self.original_count = 0
    
    def apply(self, seq_lengths: Dict[str, int]) -> Dict[str, int]:
        """Apply this filter stage to the sequences."""
        self.original_count = len(seq_lengths)
        result = apply_optimal_filter(seq_lengths, method=self.method, **self.params)
        self.filtered_count = len(result)
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about this filter stage."""
        return {
            "method": self.method,
            "params": self.params,
            "sequences_before": self.original_count,
            "sequences_after": self.filtered_count,
            "reduction_percent": (
                (self.original_count - self.filtered_count) / self.original_count * 100
                if self.original_count > 0 else 0
            )
        }


class FilterPipeline:
    """Pipeline for applying multiple filters in sequence."""
    
    def __init__(self):
        """Initialize an empty filter pipeline."""
        self.stages: List[FilterStage] = []
        self.input_sequences: Optional[Dict[str, int]] = None
        self.result_sequences: Optional[Dict[str, int]] = None
    
    def add_stage(self, method: str, **params) -> 'FilterPipeline':
        """
        Add a filter stage to the pipeline.
        
        Args:
            method: Filtering method to use
            **params: Parameters for the filter method
            
        Returns:
            Self for method chaining
        """
        self.stages.append(FilterStage(method, **params))
        return self
    
    def run(self, seq_lengths: Dict[str, int]) -> Dict[str, int]:
        """
        Run the full pipeline on the input sequences.
        
        Args:
            seq_lengths: Dictionary mapping sequence IDs to their lengths
            
        Returns:
            Filtered sequence lengths dictionary
        """
        self.input_sequences = copy.deepcopy(seq_lengths)
        result = copy.deepcopy(seq_lengths)
        
        for stage in self.stages:
            result = stage.apply(result)
        
        self.result_sequences = result
        return result
    
    def get_report(self) -> Dict[str, Any]:
        """
        Generate a report of the filtering pipeline results.
        
        Returns:
            Dictionary with pipeline statistics
        """
        if self.input_sequences is None or self.result_sequences is None:
            return {"error": "Pipeline has not been run yet"}
        
        stage_reports = [stage.get_stats() for stage in self.stages]
        
        # Get lengths before filtering
        before_lengths = list(self.input_sequences.values())
        before_viz = generate_length_distribution(before_lengths)

        # Get lengths after filtering
        after_lengths = list(self.result_sequences.values())
        after_viz = generate_length_distribution(after_lengths)

        # Include both in results
        return {
            "input_sequence_count": len(self.input_sequences),
            "output_sequence_count": len(self.result_sequences),
            "total_reduction_percent": (
                (len(self.input_sequences) - len(self.result_sequences)) / len(self.input_sequences) * 100
                if len(self.input_sequences) > 0 else 0
            ),
            "stages": stage_reports,
            "visualization_data": {
                "before": before_viz,
                "after": after_viz  # Make sure this is included
            }
        }