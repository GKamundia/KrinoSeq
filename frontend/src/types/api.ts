// API Types matching backend models

export enum FilterMethod {
  MIN_MAX = "min_max",
  IQR = "iqr",
  ZSCORE = "zscore",
  ADAPTIVE = "adaptive",
  N50_OPTIMIZE = "n50_optimize",
  NATURAL = "natural"
}

export enum JobStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface FilterParams {
  min_length?: number;
  max_length?: number;
  k?: number;
  threshold?: number;
  min_cutoff?: number;
  max_cutoff?: number;
  step?: number;
}

export interface FilterStageConfig {
  method: FilterMethod;
  params?: FilterParams;
}

export interface FilterPipelineConfig {
  stages: FilterStageConfig[];
}

export interface BasicStats {
  min: number;
  max: number;
  mean: number;
  median: number;
  std_dev: number;
  total: number;
  count: number;
}

export interface QuartileStats {
  q1: number;
  q2: number;
  q3: number;
  iqr: number;
}

export interface AssemblyStats {
  n50: number;
  l50: number;
}

export interface VisualizationData {
  histogram: {
    bin_edges: number[];
    bin_centers: number[];
    counts: number[];
  };
  kde: {
    x: number[];
    density: number[];
  };
  cumulative: {
    lengths: number[];
    cumulative_sum: number[];
    cumulative_percent: number[];
  };
}

export interface FileInfo {
  path: string;
  name: string;
  size_bytes: number;
  sequence_count: number;
  basic_stats: BasicStats;
  assembly_stats: AssemblyStats;
}

export interface JobInfo {
  job_id: string;
  status: JobStatus;
  progress?: number;
  message: string;
  file_info?: {
    sequence_count: number;
    basic_stats: BasicStats;
    quartile_stats: QuartileStats;
    assembly_stats: AssemblyStats;
    visualization_data: VisualizationData;
  };
}

export interface FilteringSummary {
  input_file: FileInfo;
  output_file: FileInfo;
  filtering: {
    sequences_removed: number;
    length_removed: number;
    percent_sequences_kept: number;
    percent_length_kept: number;
    n50_change: number;
    l50_change: number;
  };
  timestamp: string;
}

export interface FilterProcessStage {
  method: string;
  params: any;
  sequences_before: number;
  sequences_after: number;
  reduction_percent: number;
  process_details: any;
}

export interface FilterResults {
  job_id: string;
  status: JobStatus;
  summary?: FilteringSummary;
  download_url?: string;
  visualization_data?: {
    before: VisualizationData;
    after: VisualizationData;
  };
  filtering_process?: FilterProcessStage[];
  message?: string;
}