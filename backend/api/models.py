"""
Pydantic models for API request and response validation.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field


class FilterMethod(str, Enum):
    """Available filter methods"""
    MIN_MAX = "min_max"
    IQR = "iqr"
    ZSCORE = "zscore"
    ADAPTIVE = "adaptive"
    N50_OPTIMIZE = "n50_optimize"
    NATURAL = "natural"


class FilterParams(BaseModel):
    """Parameters for filter methods"""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    k: Optional[float] = None
    threshold: Optional[float] = None
    min_cutoff: Optional[int] = None
    max_cutoff: Optional[int] = None
    step: Optional[int] = None
    gmm_method: Optional[str] = None
    transform: Optional[str] = None
    component_method: Optional[str] = None


class FilterStageConfig(BaseModel):
    """Configuration for a single filter stage"""
    method: FilterMethod
    params: Optional[FilterParams] = Field(default_factory=FilterParams)


class FilterPipelineConfig(BaseModel):
    """Configuration for the complete filter pipeline"""
    stages: List[FilterStageConfig]


class JobStatus(str, Enum):
    """Job status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response for file upload endpoint"""
    job_id: str
    filename: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Response for job status endpoint"""
    job_id: str
    status: JobStatus
    progress: Optional[float] = None
    message: str
    file_info: Optional[Dict[str, Any]] = None


class FilterResponse(BaseModel):
    """Response for filter execution endpoint"""
    job_id: str
    status: JobStatus
    message: str


class ResultSummary(BaseModel):
    """Summary of filtering results"""
    input_file: Dict[str, Any]
    output_file: Dict[str, Any]
    filtering: Dict[str, Any]
    timestamp: str


# New QUAST-related models

class QuastOptions(BaseModel):
    """Configuration options for QUAST analysis"""
    min_contig: Optional[int] = Field(default=500, description="Minimum contig length to report")
    threads: Optional[int] = Field(default=4, description="Number of threads to use")
    gene_finding: Optional[bool] = Field(default=True, description="Enable gene finding")
    conserved_genes_finding: Optional[bool] = Field(default=True, description="Enable conserved genes finding")
    scaffold_gap_max_size: Optional[int] = Field(default=1000, description="Maximum size of scaffold gaps")
    reference_genome: Optional[str] = Field(None, description="Path to reference genome for comparison")
    labels: Optional[List[str]] = Field(None, description="Custom labels for assemblies")
    large_genome: Optional[bool] = Field(default=False, description="Enable large genome mode")
    eukaryote: Optional[bool] = Field(default=False, description="Enable eukaryote mode")
    fungus: Optional[bool] = Field(default=False, description="Enable fungus mode")
    prokaryote: Optional[bool] = Field(default=False, description="Enable prokaryote mode")
    metagenome: Optional[bool] = Field(default=False, description="Enable metagenome mode")
    plots_format: Optional[str] = Field(default="png", description="Format for plots (png, pdf, ps)")
    min_alignment: Optional[int] = Field(default=65, description="Minimum alignment length")
    ambiguity_usage: Optional[str] = Field(default="one", description="Ambiguity usage mode")


class QuastMetric(BaseModel):
    """Individual QUAST quality metric"""
    name: str
    value: Union[float, int, str]
    is_better: Optional[bool] = None  # Whether this metric is better than the original


class QuastAssemblyResult(BaseModel):
    """QUAST results for a single assembly"""
    name: str
    metrics: Dict[str, Union[float, int, str]]
    contig_counts: Dict[str, int]
    length_stats: Dict[str, Union[float, int]]
    assembly_quality: Dict[str, Union[float, int]]
    reference_metrics: Optional[Dict[str, Union[float, int]]] = None
    gene_metrics: Optional[Dict[str, Union[float, int]]] = None


class QuastComparisonResult(BaseModel):
    """Comparison between original and filtered assemblies"""
    absolute_change: Dict[str, float]
    percent_change: Dict[str, float] 
    improvements: Dict[str, bool]
    overall_improvement_score: float
    overall_improved: bool
    positive_metric_count: int
    negative_metric_count: int
    total_evaluated_metrics: int


class QuastResults(BaseModel):
    """Complete QUAST analysis results"""
    success: bool
    html_report_path: str
    output_directory: str
    assemblies: List[QuastAssemblyResult]
    comparison: Optional[QuastComparisonResult] = None
    has_reference: bool = False
    has_gene_prediction: bool = False
    basic_metrics: Dict[str, Dict[str, Any]]
    quality_metrics: Dict[str, Dict[str, Any]]
    reference_metrics: Optional[Dict[str, Dict[str, Any]]] = None
    gene_metrics: Optional[Dict[str, Dict[str, Any]]] = None
    command_line: Optional[str] = None
    error_message: Optional[str] = None


class FilteringProcessDetails(BaseModel):
    """Detailed information about the filtering process"""
    method: str
    params: Dict[str, Any]
    process_details: Dict[str, Any]


class FilterResultResponse(BaseModel):
    """Response for filter results endpoint"""
    job_id: str
    status: JobStatus
    summary: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    visualization_data: Optional[Dict[str, Any]] = None
    filtering_process: Optional[List[FilteringProcessDetails]] = None
    message: Optional[str] = None
    # New QUAST-related fields
    quast_results: Optional[QuastResults] = None
    quast_report_url: Optional[str] = None
    quast_metrics_summary: Optional[Dict[str, Any]] = None
    quast_improvement: Optional[Dict[str, Any]] = None


class ReferenceGenomeUpload(BaseModel):
    """Request model for reference genome upload"""
    job_id: str
    use_for_quast: bool = True