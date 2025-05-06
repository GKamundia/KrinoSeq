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
  gmm_method?: string;
  transform?: string;
  component_method?: string;
}

export interface FilterStageConfig {
  method: FilterMethod;
  params?: FilterParams;
}

export interface FilterPipelineConfig {
  stages: FilterStageConfig[];
  quastOptions?: QuastOptions;
  jobId?: string;
}

// Ensure the QuastOptions interface matches the backend model
export interface QuastOptions {
  min_contig?: number;
  threads?: number;
  gene_finding?: boolean;
  conserved_genes_finding?: boolean;
  scaffold_gap_max_size?: number;
  reference_genome?: string;
  labels?: string[];
  large_genome?: boolean;
  eukaryote?: boolean;
  fungus?: boolean;
  prokaryote?: boolean;
  metagenome?: boolean;
  plots_format?: string;
  min_alignment?: number;
  ambiguity_usage?: string;
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
    before?: VisualizationData;
    after?: VisualizationData;
  };
  filtering_process?: FilterProcessStage[];
  message?: string;
  quast_results?: QuastResults;
  quast_report_url?: string;
  quast_metrics_summary?: QuastMetricsSummary;
  quast_improvement?: QuastImprovement;
}

/**
 * Individual QUAST quality metric with improvement indicator
 */
export interface QuastMetric {
  name: string;
  value: number | string;
  is_better?: boolean;  // Whether this metric is better than the original
}

/**
 * QUAST results for a single assembly
 */
export interface QuastAssemblyResult {
  name: string;
  metrics: Record<string, number | string>;
  contig_counts: Record<string, number>;
  length_stats: Record<string, number>;
  assembly_quality: Record<string, number>;
  reference_metrics?: Record<string, number>;
  gene_metrics?: Record<string, number>;
}

/**
 * Comparison between original and filtered assemblies
 */
export interface QuastComparisonResult {
  absolute_change: Record<string, number>;
  percent_change: Record<string, number>;
  improvements: Record<string, boolean>;
  overall_improvement_score: number;
  overall_improved: boolean;
  positive_metric_count: number;
  negative_metric_count: number;
  total_evaluated_metrics: number;
}

/**
 * Complete QUAST analysis results
 */
export interface QuastResults {
  success: boolean;
  html_report_path: string;
  output_directory: string;
  assemblies: QuastAssemblyResult[];
  comparison?: QuastComparisonResult;
  has_reference: boolean;
  has_gene_prediction: boolean;
  basic_metrics: Record<string, Record<string, any>>;
  quality_metrics: Record<string, Record<string, any>>;
  reference_metrics?: Record<string, Record<string, any>>;
  gene_metrics?: Record<string, Record<string, any>>;
  command_line?: string;
  error_message?: string;
}

/**
 * Simple QUAST metrics summary for quick display
 */
export interface QuastMetricsSummary {
  has_reference: boolean;
  has_gene_prediction: boolean;
  assemblies: string[];
  basic_metrics: Record<string, Record<string, any>>;
}

/**
 * QUAST improvement summary
 */
export interface QuastImprovement {
  overall_improved: boolean;
  overall_score: number;
}

/**
 * Report URLs for QUAST analysis
 */
export interface QuastReportUrls {
  html: string;
  tsv: string;
  transposed_tsv: string;
  icarus: string;
}

/**
 * Response from the detailed QUAST results endpoint
 */
export interface QuastResultsResponse {
  assemblies: string[];
  has_reference: boolean;
  has_gene_prediction: boolean;
  basic_metrics: Record<string, Record<string, any>>;
  contig_distribution: Record<string, any>;
  quality_metrics: Record<string, Record<string, any>>;
  reference_metrics?: Record<string, Record<string, any>>;
  gene_metrics?: Record<string, Record<string, any>>;
  report_path: string;
  transposed_report_path?: string;
  html_report_path: string;
  report_urls: QuastReportUrls;
}