import axios, { AxiosResponse } from 'axios';
import { 
  FilterPipelineConfig, 
  JobStatus, 
  JobInfo, 
  FilterResults, 
  QuastResultsResponse, 
  QuastReportUrls 
} from '../types/api';

// Create axios instance with base configuration
const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',  // Make sure this matches your backend URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
API.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || 'An unexpected error occurred';
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

// API functions
export const uploadFasta = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await API.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const getJobStatus = async (jobId: string): Promise<JobInfo> => {
  const response = await API.get(`/jobs/${jobId}`);
  return response.data;
};

export const configureFilter = async (jobId: string, config: FilterPipelineConfig) => {
  const response = await API.post(`/configure/${jobId}`, config);
  return response.data;
};

export const executeFilter = async (jobId: string) => {
  const response = await API.post(`/filter/${jobId}`);
  return response.data;
};

export const getFilterResults = async (jobId: string): Promise<FilterResults> => {
  const response = await API.get(`/results/${jobId}`);
  return response.data;
};

export const getDownloadUrl = (jobId: string, fileName: string): string => {
  return `${API.defaults.baseURL}/download/${jobId}/${fileName}`;
};

export const deleteJob = async (jobId: string) => {
  const response = await API.delete(`/jobs/${jobId}`);
  return response.data;
};

/**
 * Fetch detailed QUAST analysis results
 * 
 * @param jobId The job identifier
 * @returns Detailed QUAST analysis results
 */
export async function fetchQuastResults(jobId: string): Promise<QuastResultsResponse> {
  try {
    const response = await fetch(`/api/quast-results/${jobId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Error fetching QUAST results: ${response.statusText}`);
    }
    
    return await response.json() as QuastResultsResponse;
  } catch (error) {
    console.error('Failed to fetch QUAST results:', error);
    throw error;
  }
}

/**
 * Get URL for a specific QUAST report
 * 
 * @param jobId The job identifier
 * @param reportType The type of report (html, tsv, transposed_tsv, icarus)
 * @returns URL to access the QUAST report
 */
export function getQuastReportUrl(jobId: string, reportType: keyof QuastReportUrls): string {
  const reportFileNames: Record<keyof QuastReportUrls, string> = {
    html: 'report.html',
    tsv: 'report.tsv',
    transposed_tsv: 'transposed_report.tsv',
    icarus: 'icarus.html'
  };
  
  return `/quast/${jobId}/${reportFileNames[reportType]}`;
}

/**
 * Upload a reference genome for QUAST analysis
 * 
 * @param jobId The job identifier
 * @param file The reference genome file
 * @param useForQuast Whether to use this genome for QUAST analysis
 * @returns Response with details about the uploaded reference genome
 */
export async function uploadReferenceGenome(
  jobId: string, 
  file: File, 
  useForQuast: boolean = true
): Promise<{job_id: string; reference_genome: string; filename: string; use_for_quast: boolean}> {
  try {
    const formData = new FormData();
    formData.append('reference_file', file);
    formData.append('use_for_quast', useForQuast.toString());
    
    const response = await fetch(`/api/reference-genome/${jobId}`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Error uploading reference genome: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Failed to upload reference genome:', error);
    throw error;
  }
}

/**
 * Opens the QUAST HTML report in a new browser tab
 * 
 * @param jobId The job identifier
 */
export function openQuastHtmlReport(jobId: string): void {
  const reportUrl = getQuastReportUrl(jobId, 'html');
  window.open(reportUrl, '_blank');
}

/**
 * Check if QUAST results are available for a job
 * 
 * @param results The filter results object
 * @returns boolean indicating if QUAST results are available
 */
export function hasQuastResults(results?: FilterResults): boolean {
  return Boolean(
    results?.quast_results?.success || 
    results?.quast_metrics_summary
  );
}