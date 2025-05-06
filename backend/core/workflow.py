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
from ..core.quast_analysis import compare_assemblies, run_quast_analysis
from ..core.quast_parser import generate_quast_summary


class FilteringWorkflow:
    """Manager for sequence filtering workflows."""
    
    def __init__(self, input_file: str, output_dir: Optional[str] = None, 
                 run_quast: bool = True, quast_options: Optional[Dict[str, Any]] = None,
                 reference_genome: Optional[str] = None):
        """
        Initialize a filtering workflow.
        
        Args:
            input_file: Path to input FASTA file
            output_dir: Directory for output files (default: same as input)
            run_quast: Whether to run QUAST analysis after filtering
            quast_options: Options for QUAST analysis
            reference_genome: Optional path to reference genome for QUAST
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
        
        # QUAST configuration
        self.run_quast = run_quast
        self.quast_options = quast_options or {}
        self.reference_genome = reference_genome
    
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
        
        # Run QUAST analysis if enabled
        quast_results = None
        if self.run_quast and os.path.exists(output_fasta):
            try:
                # Create quast directory with standardized name
                quast_dir = os.path.join(self.output_dir, "quast")
                os.makedirs(quast_dir, exist_ok=True)
                
                # Generate assembly labels
                original_label = os.path.splitext(self.input_name)[0]
                filtered_label = f"{original_label}_filtered"
                
                # Run QUAST comparison analysis
                quast_results = compare_assemblies(
                    original_assembly=self.input_file,
                    filtered_assembly=output_fasta,
                    output_dir=quast_dir,
                    reference_genome=self.reference_genome,
                    params=self.quast_options
                )
                
                # Generate a summarized report
                quast_summary = generate_quast_summary(quast_dir)
                
                # Add QUAST results to the summary
                summary["quast"] = {
                    "success": quast_results.get("success", False),
                    "html_report": quast_results.get("html_report", ""),
                    "output_dir": quast_dir,
                    "summary": quast_summary
                }
                
                # Add key improvement metrics if available
                if "comparison" in quast_results:
                    summary["quast"]["improvements"] = quast_results["comparison"]
                
                # Update the JSON report with QUAST results
                save_results_to_json(summary, output_json)
                
            except Exception as e:
                # Log the error but continue without QUAST results
                import logging
                logging.error(f"QUAST analysis failed: {str(e)}")
                summary["quast"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Return complete results
        result = {
            "job_id": self.job_id,
            "output_file": output_fasta,
            "report_file": output_json,
            "sequences_written": sequences_written,
            "summary": summary
        }
        
        # Add QUAST results if available
        if quast_results:
            result["quast"] = quast_results
        
        return result

    def run_quast(self, original_file, filtered_file, quast_options=None):
        """
        Run QUAST analysis to compare original and filtered assemblies.
        
        Args:
            original_file: Path to original assembly FASTA
            filtered_file: Path to filtered assembly FASTA
            quast_options: Dictionary of QUAST options
            
        Returns:
            Dictionary with QUAST analysis results
        """
        import os
        import logging
        from ..utils.quast_config import QUAST_EXECUTABLE_STR
        
        # Ensure we have a quast options dict
        if quast_options is None:
            quast_options = {}
        
        # Check if quast_path is specified in options, if not, use the default from config
        if "quast_path" not in quast_options:
            quast_options["quast_path"] = QUAST_EXECUTABLE_STR
        
        logging.info(f"Using QUAST executable: {quast_options['quast_path']}")
        
        try:
            # Create quast directory with standardized name
            quast_dir = os.path.join(self.output_dir, "quast")
            os.makedirs(quast_dir, exist_ok=True)
            
            # Generate assembly labels
            original_label = os.path.basename(os.path.splitext(original_file)[0])
            filtered_label = os.path.basename(os.path.splitext(filtered_file)[0])
            
            # Run QUAST comparison analysis
            results = compare_assemblies(
                original_assembly=original_file,
                filtered_assembly=filtered_file,
                output_dir=quast_dir,
                reference_genome=self.reference_genome,
                params=quast_options
            )
            
            # Log success or error
            if results.get("success", False):
                logging.info(f"QUAST analysis completed successfully: {quast_dir}")
            else:
                logging.error(f"QUAST analysis failed: {results.get('error', 'Unknown error')}")
            
            return results
            
        except Exception as e:
            logging.error(f"Error running QUAST analysis: {str(e)}")
            return {
                "success": False,
                "error": f"Error running QUAST analysis: {str(e)}",
                "output_dir": quast_dir if 'quast_dir' in locals() else None
            }


