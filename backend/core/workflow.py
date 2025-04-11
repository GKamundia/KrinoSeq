"""
Workflow manager for sequence filtering operations.
"""

from typing import Dict, List, Set, Any, Optional, Tuple
import os
import uuid
from datetime import datetime

from ..core.parser import get_sequence_lengths
from ..core.pipeline import FilterPipeline
from ..core.output import filter_sequences_from_fasta, generate_results_summary, save_results_to_json
from ..utils.config_validator import validate_pipeline_config


class FilteringWorkflow:
    """Manager for sequence filtering workflows."""
    
    def __init__(self, input_file: str, output_dir: Optional[str] = None):
        """
        Initialize a filtering workflow.
        
        Args:
            input_file: Path to input FASTA file
            output_dir: Directory for output files (default: same as input)
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        self.input_file = input_file
        self.input_name = os.path.basename(input_file)
        self.input_dir = os.path.dirname(input_file)
        
        self.output_dir = output_dir if output_dir else self.input_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.job_id = str(uuid.uuid4())[:8]
        self.pipeline = FilterPipeline()
        self.seq_lengths: Dict[str, int] = {}
        self.filtered_seq_lengths: Dict[str, int] = {}
    
    def configure_from_dict(self, config: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Configure the pipeline from a dictionary.
        
        Args:
            config: List of filter stage configurations
            
        Returns:
            Tuple of (success, error_message)
        """
        is_valid, error, validated_config = validate_pipeline_config(config)
        if not is_valid:
            return False, error
        
        # Reset pipeline and add validated stages
        self.pipeline = FilterPipeline()
        for stage in validated_config:
            self.pipeline.add_stage(stage["method"], **stage["params"])
        
        return True, None
    
    def run(self) -> Dict[str, Any]:
        """
        Run the filtering workflow.
        
        Returns:
            Dictionary with workflow results
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_prefix = f"{os.path.splitext(self.input_name)[0]}_filtered_{self.job_id}"
        output_fasta = os.path.join(self.output_dir, f"{output_prefix}.fasta")
        output_json = os.path.join(self.output_dir, f"{output_prefix}_report.json")
        
        # Get sequence lengths from input file
        try:
            self.seq_lengths = get_sequence_lengths(self.input_file)
        except Exception as e:
            return {"error": f"Error reading input file: {str(e)}"}
        
        # Run the pipeline
        try:
            self.filtered_seq_lengths = self.pipeline.run(self.seq_lengths)
        except Exception as e:
            return {"error": f"Error running filter pipeline: {str(e)}"}
        
        # Generate filtered FASTA file
        try:
            seq_ids_to_keep = set(self.filtered_seq_lengths.keys())
            sequences_written = filter_sequences_from_fasta(
                self.input_file, seq_ids_to_keep, output_fasta)
        except Exception as e:
            return {"error": f"Error generating output file: {str(e)}"}
        
        # Generate summary
        try:
            pipeline_report = self.pipeline.get_report()
            summary = generate_results_summary(self.input_file, output_fasta, pipeline_report)
            save_results_to_json(summary, output_json)
        except Exception as e:
            return {
                "error": f"Error generating summary: {str(e)}",
                "output_file": output_fasta,
                "sequences_written": sequences_written
            }
        
        return {
            "job_id": self.job_id,
            "output_file": output_fasta,
            "report_file": output_json,
            "sequences_written": sequences_written,
            "summary": summary
        }


