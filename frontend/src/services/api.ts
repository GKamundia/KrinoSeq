import axios, { AxiosResponse } from 'axios';
import { FilterPipelineConfig, JobStatus, JobInfo, FilterResults } from '../types/api';

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