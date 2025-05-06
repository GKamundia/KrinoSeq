import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import modules to test
from ..utils.wsl_executor import run_wsl_command, check_command_exists, get_quast_version
from ..utils.wsl_path_converter import convert_windows_to_wsl_path, convert_wsl_to_windows_path
from ..core.quast_analysis import run_quast_analysis, compare_assemblies, calculate_comparison_metrics
from ..core.quast_parser import parse_quast_report_file, generate_quast_summary, extract_essential_metrics
from ..core.workflow import FilteringWorkflow
from ..utils.config_validator import validate_quast_options


# Test fixtures
@pytest.fixture
def sample_quast_report():
    """Create a sample QUAST report file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
        f.write("Assembly\toriginal\tfiltered\n")
        f.write("# contigs\t100\t80\n")
        f.write("Total length\t5000000\t4800000\n")
        f.write("N50\t50000\t60000\n")
        f.write("L50\t30\t25\n")
        f.write("GC (%)\t45.2\t45.3\n")
        f.write("# misassemblies\t5\t3\n")
        f.write("Genome fraction (%)\t98.5\t98.2\n")
        return f.name


@pytest.fixture
def sample_transposed_report():
    """Create a sample transposed QUAST report file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
        f.write("Assembly\toriginal\tfiltered\n")
        f.write("# contigs\t100\t80\n")
        f.write("# contigs (>= 1000 bp)\t90\t75\n")
        f.write("Total length\t5000000\t4800000\n")
        f.write("Total length (>= 1000 bp)\t4950000\t4770000\n")
        f.write("N50\t50000\t60000\n")
        f.write("L50\t30\t25\n")
        return f.name


@pytest.fixture
def sample_quast_dir(sample_quast_report, sample_transposed_report):
    """Create a sample QUAST output directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Copy sample files to the temp dir
    report_path = os.path.join(temp_dir, "report.tsv")
    transposed_path = os.path.join(temp_dir, "transposed_report.tsv")
    
    with open(sample_quast_report, 'r') as src, open(report_path, 'w') as dest:
        dest.write(src.read())
    
    with open(sample_transposed_report, 'r') as src, open(transposed_path, 'w') as dest:
        dest.write(src.read())
    
    # Create empty HTML report
    with open(os.path.join(temp_dir, "report.html"), 'w') as f:
        f.write("<html><body>QUAST Report</body></html>")
        
    return temp_dir


@pytest.fixture
def sample_fasta_files():
    """Create sample FASTA files for testing."""
    original_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta')
    original_file.write(">contig1\nACGTACGTACGT\n>contig2\nACGTACGTACGT\n")
    original_file.close()
    
    filtered_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta')
    filtered_file.write(">contig1\nACGTACGTACGT\n")
    filtered_file.close()
    
    return original_file.name, filtered_file.name


# Test WSL command execution
@patch('subprocess.run')
def test_run_wsl_command(mock_run):
    """Test running a command in WSL."""
    # Setup mock
    process_mock = MagicMock()
    process_mock.stdout = b'output'
    process_mock.stderr = b'error'
    process_mock.returncode = 0
    mock_run.return_value = process_mock
    
    # Test the function
    stdout, stderr, returncode = run_wsl_command('echo "Hello WSL"')
    
    # Assertions
    mock_run.assert_called_once()
    assert stdout == 'output'
    assert stderr == 'error'
    assert returncode == 0


@patch('subprocess.run')
def test_check_command_exists(mock_run):
    """Test checking if a command exists in WSL."""
    # Test command exists
    process_mock = MagicMock()
    process_mock.returncode = 0
    mock_run.return_value = process_mock
    
    assert check_command_exists('ls') is True
    
    # Test command does not exist
    process_mock.returncode = 127  # Command not found
    mock_run.return_value = process_mock
    
    assert check_command_exists('nonexistent_command') is False


@patch('subprocess.run')
def test_get_quast_version(mock_run):
    """Test getting QUAST version."""
    # Mock successful version fetch
    process_mock = MagicMock()
    process_mock.stdout = b'QUAST v5.0.2'
    process_mock.returncode = 0
    mock_run.return_value = process_mock
    
    assert get_quast_version() == 'QUAST v5.0.2'
    
    # Mock failed version fetch
    process_mock.returncode = 1
    mock_run.return_value = process_mock
    
    assert get_quast_version() is None


# Test path conversion
def test_convert_windows_to_wsl_path():
    """Test converting Windows paths to WSL paths."""
    win_path = r'C:\Users\Test\file.txt'
    wsl_path = convert_windows_to_wsl_path(win_path)
    assert wsl_path == '/mnt/c/Users/Test/file.txt'
    
    win_path = r'D:\Data\genome.fa'
    wsl_path = convert_windows_to_wsl_path(win_path)
    assert wsl_path == '/mnt/d/Data/genome.fa'


def test_convert_wsl_to_windows_path():
    """Test converting WSL paths to Windows paths."""
    wsl_path = '/mnt/c/Users/Test/file.txt'
    win_path = convert_wsl_to_windows_path(wsl_path)
    assert win_path == r'C:\Users\Test\file.txt'
    
    wsl_path = '/mnt/d/Data/genome.fa'
    win_path = convert_wsl_to_windows_path(wsl_path)
    assert win_path == r'D:\Data\genome.fa'


# Test QUAST result parsing
def test_parse_quast_report_file(sample_quast_report):
    """Test parsing a QUAST report file."""
    metrics = parse_quast_report_file(sample_quast_report)
    
    # Check if metrics were parsed correctly
    assert "original" in metrics
    assert "filtered" in metrics
    
    assert metrics["original"]["# contigs"] == 100
    assert metrics["original"]["N50"] == 50000
    assert metrics["filtered"]["# contigs"] == 80
    assert metrics["filtered"]["N50"] == 60000


def test_extract_essential_metrics(sample_quast_report):
    """Test extracting essential metrics from a QUAST report."""
    metrics = parse_quast_report_file(sample_quast_report)
    essential = extract_essential_metrics(metrics, "basic")
    
    assert "original" in essential
    assert "filtered" in essential
    
    assert "# contigs" in essential["original"]
    assert "N50" in essential["original"]
    assert "L50" in essential["original"]


def test_generate_quast_summary(sample_quast_dir):
    """Test generating a comprehensive QUAST summary."""
    summary = generate_quast_summary(sample_quast_dir)
    
    assert "assemblies" in summary
    assert "basic_metrics" in summary
    assert "has_reference" in summary
    assert "has_gene_prediction" in summary


def test_calculate_comparison_metrics():
    """Test calculating comparison metrics between assemblies."""
    metrics = {
        "original": {
            "# contigs": 100,
            "N50": 50000,
            "L50": 30,
            "Total length": 5000000
        },
        "filtered": {
            "# contigs": 80,
            "N50": 60000,
            "L50": 25,
            "Total length": 4800000
        }
    }
    
    comparison = calculate_comparison_metrics(metrics, "original", "filtered")
    
    assert "change_summary" in comparison
    assert "percent_change" in comparison
    assert "improvement" in comparison
    assert "overall_improvement_score" in comparison
    
    # Check specific changes
    assert comparison["change_summary"]["# contigs"] == -20  # Reduction in contigs
    assert comparison["change_summary"]["N50"] == 10000  # Increase in N50
    assert comparison["percent_change"]["# contigs"] == -20.0
    
    # Check improvement determinations
    assert comparison["improvement"]["# contigs"] is True  # Fewer contigs is better
    assert comparison["improvement"]["N50"] is True  # Higher N50 is better


@patch('backend.utils.wsl_executor.run_wsl_command')
def test_run_quast_analysis(mock_run, sample_fasta_files, sample_quast_dir):
    """Test running QUAST analysis."""
    # Setup mock
    mock_run.return_value = ('QUAST output', '', 0)
    
    # Mock quast.py call to use sample data
    original_file, filtered_file = sample_fasta_files
    temp_output_dir = tempfile.mkdtemp()
    
    # Mock successful execution
    with patch('backend.core.quast_analysis.parse_quast_report', return_value={"original": {"# contigs": 100}}), \
         patch('backend.core.quast_analysis.extract_key_metrics', return_value={"original": {"# contigs": 100}}):
        
        result = run_quast_analysis(
            input_files=[original_file],
            output_dir=temp_output_dir,
        )
        
        assert result["success"] is True
        mock_run.assert_called_once()


@patch('backend.core.quast_analysis.run_quast_analysis')
def test_compare_assemblies(mock_run_quast, sample_fasta_files):
    """Test comparing assemblies with QUAST."""
    original_file, filtered_file = sample_fasta_files
    
    # Mock successful execution
    mock_run_quast.return_value = {
        "success": True,
        "metrics": {
            "original_original": {"# contigs": 100, "N50": 50000},
            "filtered_filtered": {"# contigs": 80, "N50": 60000}
        }
    }
    
    result = compare_assemblies(
        original_assembly=original_file,
        filtered_assembly=filtered_file,
        output_dir=tempfile.mkdtemp()
    )
    
    assert result["success"] is True
    assert "comparison" in result
    mock_run_quast.assert_called_once()


# Test integration with workflow
@patch('backend.core.quast_analysis.compare_assemblies')
def test_workflow_with_quast(mock_compare, sample_fasta_files):
    """Test integration of QUAST with the filtering workflow."""
    original_file, filtered_file = sample_fasta_files
    
    # Mock comparison result
    mock_compare.return_value = {
        "success": True,
        "metrics": {
            "original_original": {"# contigs": 100, "N50": 50000},
            "filtered_filtered": {"# contigs": 80, "N50": 60000}
        },
        "comparison": {
            "overall_improved": True,
            "overall_improvement_score": 0.75
        }
    }
    
    # Create a workflow instance and test QUAST integration
    with patch('backend.core.workflow.FilteringWorkflow.run_filter', return_value=filtered_file), \
         patch('backend.core.workflow.FilteringWorkflow._update_status'):
             
        workflow = FilteringWorkflow(job_id="test_job", input_file=original_file)
        
        # Test run_quast method
        quast_result = workflow.run_quast(
            original_file=original_file, 
            filtered_file=filtered_file,
            quast_options={"min_contig": 500, "gene_finding": True}
        )
        
        assert quast_result["success"] is True
        assert "comparison" in quast_result
        mock_compare.assert_called_once()


# Test QUAST options validation
def test_validate_quast_options():
    """Test validation of QUAST options."""
    # Test valid options
    options = {
        "min_contig": 500,
        "threads": 4,
        "gene_finding": True,
        "conserved_genes_finding": True,
        "large_genome": False
    }
    
    is_valid, error, validated = validate_quast_options(options)
    assert is_valid is True
    assert error is None
    assert validated["min_contig"] == 500
    assert validated["threads"] == 4
    
    # Test invalid option (out of range)
    options = {
        "min_contig": -100,  # Invalid: negative
        "threads": 4
    }
    
    is_valid, error, validated = validate_quast_options(options)
    assert is_valid is False
    assert error is not None
    
    # Test invalid option (wrong type)
    options = {
        "min_contig": "500",  # Should be converted to int
        "threads": 4
    }
    
    is_valid, error, validated = validate_quast_options(options)
    assert is_valid is True
    assert validated["min_contig"] == 500  # Should be properly converted
    
    # Test with reference genome
    with patch('os.path.exists', return_value=False):
        options = {
            "min_contig": 500,
            "reference_genome": "/path/to/reference.fa"  # Non-existent but valid path format
        }
        
        is_valid, error, validated = validate_quast_options(options)
        assert is_valid is True  # Should not fail, just log warning


# Clean up temporary files
@pytest.fixture(autouse=True)
def cleanup(request, sample_quast_report, sample_transposed_report, sample_fasta_files):
    """Clean up temporary files after tests."""
    def finalizer():
        try:
            os.unlink(sample_quast_report)
            os.unlink(sample_transposed_report)
            os.unlink(sample_fasta_files[0])
            os.unlink(sample_fasta_files[1])
        except:
            pass
    
    request.addfinalizer(finalizer)