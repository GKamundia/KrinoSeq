"""
FastAPI application for genome filtering tool.
"""

import os
import shutil
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import json

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

# Import core and filter modules
from ..core.workflow import FilteringWorkflow
from ..core.analysis import analyze_fasta_file
from ..utils.config_validator import validate_pipeline_config

# Import API models
from .models import (
    FilterMethod, FilterParams, FilterStageConfig, FilterPipelineConfig,
    JobStatus, UploadResponse, JobStatusResponse, FilterResponse, 
    ResultSummary, FilterResultResponse
)

# Create FastAPI app
app = FastAPI(
    title="Genome Filtering API",
    description="API for advanced length-based filtering of genomic sequences",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
RESULTS_DIR = BASE_DIR / "data" / "results"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Job tracking
active_jobs = {}


def get_job_info(job_id: str) -> Dict[str, Any]:
    """Get information about a job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return active_jobs[job_id]


def setup_job_directories(job_id: str) -> Dict[str, Path]:
    """
    Create directory structure for a job including QUAST subdirectory.
    
    Args:
        job_id: The job identifier
        
    Returns:
        Dictionary with paths to job directories
    """
    # Define base directory for this job
    job_dir = RESULTS_DIR / job_id
    
    # Define subdirectories
    dirs = {
        "job": job_dir,
        "quast": job_dir / "quast",
        "plots": job_dir / "plots",
        "reports": job_dir / "reports"
    }
    
    # Create directories
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return dirs


def create_quast_metadata(job_id: str, original_file: str, filtered_file: str, 
                         quast_dir: str, reference_genome: Optional[str] = None) -> str:
    """
    Create metadata file linking QUAST results with the filtering job.
    
    Args:
        job_id: The job identifier
        original_file: Path to original assembly
        filtered_file: Path to filtered assembly
        quast_dir: Directory where QUAST results are stored
        reference_genome: Optional path to reference genome
        
    Returns:
        Path to created metadata file
    """
    metadata = {
        "job_id": job_id,
        "timestamp": datetime.now().isoformat(),
        "original_assembly": {
            "path": original_file,
            "name": os.path.basename(original_file)
        },
        "filtered_assembly": {
            "path": filtered_file,
            "name": os.path.basename(filtered_file)
        },
        "quast_directory": quast_dir,
        "reports": {
            "html": os.path.join(quast_dir, "report.html"),
            "tsv": os.path.join(quast_dir, "report.tsv"),
            "transposed_tsv": os.path.join(quast_dir, "transposed_report.tsv"),
            "pdf": os.path.join(quast_dir, "report.pdf")
        }
    }
    
    if reference_genome:
        metadata["reference_genome"] = {
            "path": reference_genome,
            "name": os.path.basename(reference_genome)
        }
    
    # Write metadata to file
    metadata_file = os.path.join(quast_dir, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata_file


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Genome Filtering API"}


@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a FASTA file for analysis and filtering
    """
    # Generate a unique job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Ensure upload directory exists
    if not UPLOAD_DIR.exists():
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save the uploaded file
    file_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"File upload failed: {str(e)}")  # Detailed logging
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    # Create job entry
    active_jobs[job_id] = {
        "job_id": job_id,
        "filename": file.filename,
        "file_path": str(file_path),
        "upload_time": datetime.now().isoformat(),
        "status": JobStatus.PENDING,
        "message": "File uploaded successfully",
        "config": None,
        "results": None
    }
    
    # Run analysis in background
    background_tasks.add_task(analyze_uploaded_file, job_id, file_path)
    
    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        status=JobStatus.PENDING,
        message="File uploaded successfully and queued for analysis"
    )


async def analyze_uploaded_file(job_id: str, file_path: Path):
    """Background task to analyze an uploaded file"""
    if job_id not in active_jobs:
        print(f"Job ID {job_id} not found in active_jobs")
        return
    
    job_info = active_jobs[job_id]
    job_info["status"] = JobStatus.PROCESSING
    job_info["message"] = "Analyzing file..."
    
    try:
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} does not exist")
            
        # Analyze the file
        analysis_results = analyze_fasta_file(str(file_path))
        
        # Update job info
        job_info["status"] = JobStatus.COMPLETED
        job_info["message"] = "Analysis completed"
        job_info["file_info"] = {
            "sequence_count": analysis_results["sequence_count"],
            "basic_stats": analysis_results["basic_stats"],
            "quartile_stats": analysis_results["quartile_stats"],
            "assembly_stats": analysis_results["assembly_stats"],
            "visualization_data": analysis_results["visualization_data"]
        }
    except Exception as e:
        import traceback
        print(f"Analysis failed: {str(e)}")
        print(traceback.format_exc())  # Print stack trace
        job_info["status"] = JobStatus.FAILED
        job_info["message"] = f"Analysis failed: {str(e)}"


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a job
    """
    job_info = get_job_info(job_id)
    
    return JobStatusResponse(
        job_id=job_id,
        status=job_info["status"],
        progress=job_info.get("progress", None),
        message=job_info["message"],
        file_info=job_info.get("file_info", None)
    )


@app.post("/configure/{job_id}", response_model=FilterResponse)
async def configure_filter(job_id: str, config: FilterPipelineConfig):
    """
    Configure the filter pipeline for a job
    """
    job_info = get_job_info(job_id)
    
    if job_info["status"] not in [JobStatus.COMPLETED, JobStatus.PENDING]:
        raise HTTPException(
            status_code=400, 
            detail=f"Job must be in 'completed' or 'pending' status to configure filters"
        )
    
    # Convert the Pydantic model to a dictionary compatible with our backend
    pipeline_config = []
    for stage in config.stages:
        stage_dict = {
            "method": stage.method,
            "params": stage.params.dict(exclude_none=True)
        }
        pipeline_config.append(stage_dict)
    
    # Log before validation
    for stage in pipeline_config:
        if stage["method"] == "natural":
            print(f"BEFORE VALIDATION - Natural breakpoint params: {stage.get('params', {})}")
            
    # Validate the configuration
    is_valid, error_message, validated_config = validate_pipeline_config(pipeline_config)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {error_message}")
    
    # After validation
    for stage in validated_config:
        if stage["method"] == "natural":
            print(f"AFTER VALIDATION - Natural breakpoint params: {stage['params']}")
    
    # Store the validated configuration in the job info
    job_info["config"] = validated_config
    job_info["message"] = "Filter configuration validated and stored"
    
    return FilterResponse(
        job_id=job_id,
        status=job_info["status"],
        message="Filter configuration applied successfully"
    )


@app.post("/filter/{job_id}", response_model=FilterResponse)
async def execute_filter(
    job_id: str, 
    background_tasks: BackgroundTasks
):
    """
    Execute the configured filter pipeline on the uploaded file
    """
    job_info = get_job_info(job_id)
    
    if job_info["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail="Analysis must be completed before filtering"
        )
    
    if not job_info.get("config"):
        raise HTTPException(
            status_code=400, 
            detail="Filter must be configured before execution"
        )
    
    # Update job status
    job_info["status"] = JobStatus.PROCESSING
    job_info["message"] = "Filter execution started"
    job_info["progress"] = 0.0
    
    # Execute filtering in background
    background_tasks.add_task(run_filter_job, job_id)
    
    return FilterResponse(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        message="Filter execution started"
    )


async def run_filter_job(job_id: str):
    """Background task to run the filtering workflow"""
    if job_id not in active_jobs:
        return
    
    job_info = active_jobs[job_id]
    
    try:
        # Create job directories including QUAST subdirectory
        job_dirs = setup_job_directories(job_id)
        
        # Determine if reference genome is provided
        reference_genome = None
        if "reference_genome" in job_info:
            reference_genome = job_info["reference_genome"]
        
        # Create workflow with QUAST enabled
        workflow = FilteringWorkflow(
            input_file=job_info["file_path"],
            output_dir=str(job_dirs["job"]),  # Use job directory for output
            run_quast=True,  # Enable QUAST
            quast_options={"threads": 4, "gene_finding": True},
            reference_genome=reference_genome
        )
        
        # Configure workflow
        success, error = workflow.configure_from_dict(job_info["config"])
        if not success:
            job_info["status"] = JobStatus.FAILED
            job_info["message"] = f"Configuration error: {error}"
            return
        
        # Update progress
        job_info["progress"] = 25.0
        
        # Run workflow
        results = workflow.run()
        
        # Update progress
        job_info["progress"] = 100.0
        
        if "error" in results:
            job_info["status"] = JobStatus.FAILED
            job_info["message"] = results["error"]
            return
        
        # If QUAST was run successfully, create metadata and organize results
        if "quast" in results and results["quast"].get("success", False):
            # Create metadata file
            quast_dir = results["quast"]["output_dir"]
            
            # If QUAST output is not in the standard quast directory, copy it there
            if os.path.normpath(quast_dir) != os.path.normpath(str(job_dirs["quast"])):
                # Copy QUAST results to the standard location
                for file in os.listdir(quast_dir):
                    src_file = os.path.join(quast_dir, file)
                    dst_file = os.path.join(job_dirs["quast"], file)
                    
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, dst_file)
                    elif os.path.isdir(src_file):
                        shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
                
                # Update the quast directory in results
                results["quast"]["output_dir"] = str(job_dirs["quast"])
            
            # Create metadata file
            create_quast_metadata(
                job_id=job_id,
                original_file=job_info["file_path"],
                filtered_file=results["output_file"],
                quast_dir=str(job_dirs["quast"]),
                reference_genome=reference_genome
            )
        
        # Store results
        job_info["status"] = JobStatus.COMPLETED
        job_info["message"] = "Filtering completed successfully"
        job_info["results"] = results  # This should include all data from workflow.run()
        
    except Exception as e:
        job_info["status"] = JobStatus.FAILED
        job_info["message"] = f"Filtering failed: {str(e)}"


@app.get("/results/{job_id}", response_model=FilterResultResponse)
async def get_filter_results(job_id: str):
    """
    Get the results of a completed filter job
    """
    job_info = get_job_info(job_id)
    
    if job_info["status"] != JobStatus.COMPLETED or not job_info.get("results"):
        return FilterResultResponse(
            job_id=job_id,
            status=job_info["status"],
            message=job_info["message"],
        )
    
    results = job_info["results"]
    
    # Generate download URL for filtered FASTA
    output_file_name = Path(results["output_file"]).name
    download_url = f"/download/{job_id}/{output_file_name}"
    
    # Prepare visualization data
    if "summary" in results:
        # Extract filtering process details from pipeline stages
        filtering_process = []
        if "summary" in results and "pipeline_report" in results["summary"]:
            if "stages" in results["summary"]["pipeline_report"]:
                # Extract the stages
                pipeline_stages = results["summary"]["pipeline_report"]["stages"]
                
                # For each stage, ensure we preserve the GMM method
                for stage in pipeline_stages:
                    if stage["method"] == "natural" and "process_details" in stage:
                        if "natural_breakpoint_details" in stage["process_details"]:
                            details = stage["process_details"]["natural_breakpoint_details"]
                            
                            # Make sure the original method is used, not the default
                            if "method_used" in details:
                                stage["method_used"] = details["method_used"]
                                # Add this line to preserve the method throughout the pipeline
                                print(f"Preserving GMM method: {details['method_used']}")
                
                filtering_process = pipeline_stages
        
        return FilterResultResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            summary=results["summary"],
            download_url=download_url,
            visualization_data={
                "before": job_info.get("file_info", {}).get("visualization_data", {}),
                "after": results.get("summary", {}).get("output_file", {}).get("visualization_data", {})
            },
            filtering_process=filtering_process,  # Include detailed filtering process information
            message="Filtering completed successfully"
        )
    else:
        return FilterResultResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            download_url=download_url,
            message="Filtering completed but summary not available"
        )


@app.get("/download/{job_id}/{file_name}")
async def download_file(job_id: str, file_name: str):
    """
    Download a filtered FASTA file
    """
    job_info = get_job_info(job_id)
    
    if not job_info.get("results"):
        raise HTTPException(status_code=404, detail="No results available for this job")
    
    output_file = job_info["results"]["output_file"]
    
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        path=output_file,
        filename=Path(output_file).name,
        media_type="application/octet-stream"
    )


@app.get("/quast/{job_id}/{report_name}")
async def get_quast_report(job_id: str, report_name: str):
    """
    Get a QUAST report file for a specific job.
    
    Args:
        job_id: The job identifier
        report_name: Name of the report file (html, tsv, pdf)
    
    Returns:
        The requested QUAST report file
    """
    job_info = get_job_info(job_id)
    
    if job_info["status"] != JobStatus.COMPLETED or "results" not in job_info:
        raise HTTPException(
            status_code=404,
            detail="Job not completed or results not available"
        )
    
    # Define allowed report types
    allowed_reports = {
        "report.html": "text/html",
        "report.tsv": "text/tab-separated-values",
        "transposed_report.tsv": "text/tab-separated-values",
        "report.pdf": "application/pdf",
        "icarus.html": "text/html"
    }
    
    # Check if requested report is allowed
    if report_name not in allowed_reports:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {list(allowed_reports.keys())}"
        )
    
    # Get QUAST directory
    quast_dir = job_info["results"].get("quast", {}).get("output_dir")
    if not quast_dir or not os.path.exists(quast_dir):
        # Try standard location
        quast_dir = os.path.join(str(RESULTS_DIR), job_id, "quast")
        if not os.path.exists(quast_dir):
            raise HTTPException(
                status_code=404,
                detail="QUAST results not found"
            )
    
    # Get report path
    report_path = os.path.join(quast_dir, report_name)
    if not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail=f"Report {report_name} not found"
        )
    
    # Return the report file
    return FileResponse(
        path=report_path,
        media_type=allowed_reports[report_name],
        filename=report_name
    )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its associated files
    """
    job_info = get_job_info(job_id)
    
    # Delete uploaded file
    if "file_path" in job_info and os.path.exists(job_info["file_path"]):
        os.remove(job_info["file_path"])
    
    # Delete result files if they exist
    if "results" in job_info and job_info["results"]:
        if "output_file" in job_info["results"] and os.path.exists(job_info["results"]["output_file"]):
            os.remove(job_info["results"]["output_file"])
        if "report_file" in job_info["results"] and os.path.exists(job_info["results"]["report_file"]):
            os.remove(job_info["results"]["report_file"])
    
    # Remove job from active jobs
    del active_jobs[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}


# Mount static files for documentation
@app.get("/docs")
async def get_docs():
    """Redirect to API documentation"""
    return {"message": "API documentation available at /docs"}


# Serve static files from the results directory
app.mount("/static", StaticFiles(directory=str(RESULTS_DIR)), name="static")