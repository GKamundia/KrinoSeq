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
    filtering_process: Optional[List[FilteringProcessDetails]] = None  # Added field
    message: Optional[str] = None