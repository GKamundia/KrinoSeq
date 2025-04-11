"""
Example usage of the filtering workflow.
"""

from backend.core.workflow import FilteringWorkflow

# Configure and run a simple filtering workflow
workflow = FilteringWorkflow(
    input_file="c:/Users/Anarchy/Documents/Data_Science/genome_work/genome_filtering_tool/cholera/18_23_scaffolds.fasta",
    output_dir="c:/Users/Anarchy/Documents/Data_Science/genome_work/genome_filtering_tool/results"
)

# Configure pipeline with multiple filter stages
config = [
    {
        "method": "adaptive",
        "params": {}
    },
    {
        "method": "n50_optimize",
        "params": {"step": 100}
    }
]

success, error = workflow.configure_from_dict(config)
if not success:
    print(f"Configuration error: {error}")
else:
    results = workflow.run()
    print(f"Filtering complete: {results['output_file']}")
    print(f"Report: {results['report_file']}")
    print(f"Sequences kept: {results['sequences_written']}/{results['summary']['input_file']['sequence_count']}")
    print(f"N50 improvement: {results['summary']['filtering']['n50_change']}")