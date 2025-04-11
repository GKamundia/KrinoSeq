"""
FASTA sequence parsing module with support for large files.
"""

from Bio import SeqIO
from typing import Dict, Generator, List, Tuple
import os


def parse_fasta(file_path: str) -> Generator[Tuple[str, str], None, None]:
    """
    Parse FASTA file and yield sequence identifier and sequence as a generator.
    
    Args:
        file_path: Path to the FASTA file
        
    Yields:
        Tuple containing (sequence_id, sequence)
    """
    with open(file_path, "r") as handle:
        for record in SeqIO.parse(handle, "fasta"):
            yield record.id, str(record.seq)


def get_sequence_lengths(file_path: str) -> Dict[str, int]:
    """
    Get a dictionary of sequence identifiers and their lengths.
    
    Args:
        file_path: Path to the FASTA file
        
    Returns:
        Dictionary mapping sequence identifiers to their lengths
    """
    sequence_lengths = {}
    for seq_id, sequence in parse_fasta(file_path):
        sequence_lengths[seq_id] = len(sequence)
    return sequence_lengths


def get_total_sequences(file_path: str) -> int:
    """
    Count the total number of sequences in a FASTA file.
    
    Args:
        file_path: Path to the FASTA file
        
    Returns:
        Number of sequences in the file
    """
    return sum(1 for _ in parse_fasta(file_path))


def is_large_file(file_path: str, threshold_mb: int = 100) -> bool:
    """
    Check if a file is considered large (exceeds threshold).
    
    Args:
        file_path: Path to the FASTA file
        threshold_mb: Size threshold in megabytes
        
    Returns:
        True if file exceeds threshold, False otherwise
    """
    threshold_bytes = threshold_mb * 1024 * 1024
    return os.path.getsize(file_path) > threshold_bytes


def parse_fasta_chunked(file_path: str, chunk_size: int = 1000) -> Generator[List[Tuple[str, str]], None, None]:
    """
    Parse large FASTA files in chunks to avoid memory issues.
    
    Args:
        file_path: Path to the FASTA file
        chunk_size: Number of sequences to process in each chunk
        
    Yields:
        List of tuples containing (sequence_id, sequence) for each chunk
    """
    chunk = []
    count = 0
    
    for seq_id, sequence in parse_fasta(file_path):
        chunk.append((seq_id, sequence))
        count += 1
        
        if count >= chunk_size:
            yield chunk
            chunk = []
            count = 0
    
    if chunk:
        yield chunk