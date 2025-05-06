import React, { useState, useEffect } from 'react';
import { 
  Grid, 
  Typography, 
  Paper, 
  Box, 
  Tab, 
  Tabs,
  Button,
  Divider,
  CircularProgress,
  Alert,
  AlertTitle,
  Chip,
  Card,
  CardContent
} from '@mui/material';
import { FilterResults, QuastResults, QuastResultsResponse } from '../types/api';
import { 
  openQuastHtmlReport, 
  fetchQuastResults, 
  getQuastReportUrl,
  hasQuastResults
} from '../services/api';
import QuastMetricsCard from './QuastMetricsCard';
import QuastComparisonChart from './QuastComparisonChart';
import LaunchIcon from '@mui/icons-material/Launch';
import GetAppIcon from '@mui/icons-material/GetApp';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index} id={`tabpanel-${index}`}>
    {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
  </div>
);

interface QuastResultsTabProps {
  jobId: string;
  filterResults?: FilterResults;
  onError?: (message: string) => void;
}

const QuastResultsTab: React.FC<QuastResultsTabProps> = ({ 
  jobId,
  filterResults,
  onError
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [detailedResults, setDetailedResults] = useState<QuastResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Get the high-level QUAST results from the filter results
  const quastResults = filterResults?.quast_results;
  const quastMetrics = filterResults?.quast_metrics_summary;
  const quastImprovement = filterResults?.quast_improvement;
  
  // Check if we have any QUAST results
  const hasQuast = hasQuastResults(filterResults);
  
  // Fetch detailed QUAST results when the tab is active
  useEffect(() => {
    const loadDetailedResults = async () => {
      if (jobId && hasQuast && !detailedResults && !loading) {
        setLoading(true);
        setError(null);
        
        try {
          const data = await fetchQuastResults(jobId);
          setDetailedResults(data);
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Failed to fetch QUAST results';
          setError(message);
          if (onError) onError(message);
        } finally {
          setLoading(false);
        }
      }
    };
    
    loadDetailedResults();
  }, [jobId, hasQuast, detailedResults, loading, onError]);
  
  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // Open QUAST report in a new tab
  const handleOpenReport = () => {
    openQuastHtmlReport(jobId);
  };
  
  // Get assembly names
  const originalAssemblyName = detailedResults?.assemblies?.[0] || 'Original Assembly';
  const filteredAssemblyName = detailedResults?.assemblies?.[1] || 'Filtered Assembly';
  
  // Extract key metrics for comparison
  const keyMetrics = [
    '# contigs', 
    'Total length', 
    'N50', 
    'L50', 
    'Largest contig',
    'GC (%)'
  ];
  
  // Add reference-based metrics if available
  if (detailedResults?.has_reference) {
    keyMetrics.push('Genome fraction (%)', 'Duplication ratio', 'NGA50', 'LGA50');
  }
  
  // Add gene prediction metrics if available
  if (detailedResults?.has_gene_prediction) {
    keyMetrics.push('# predicted genes (unique)', 'Complete BUSCO (%)');
  }
  
  // Prepare assembly data for comparison
  const originalAssembly = {
    name: originalAssemblyName,
    metrics: detailedResults?.basic_metrics?.[originalAssemblyName] || {}
  };
  
  const filteredAssembly = {
    name: filteredAssemblyName,
    metrics: detailedResults?.basic_metrics?.[filteredAssemblyName] || {}
  };
  
  // Check if enough data is available for comparison
  const canCompare = 
    Object.keys(originalAssembly.metrics).length > 0 && 
    Object.keys(filteredAssembly.metrics).length > 0;
  
  // Group metrics by category
  const metricGroups = [
    { 
      title: 'Assembly Statistics', 
      keys: ['# contigs', 'Total length', 'Largest contig', 'GC (%)'] 
    },
    { 
      title: 'Quality Metrics', 
      keys: ['N50', 'L50', 'N75', 'L75'] 
    }
  ];
  
  if (detailedResults?.has_reference) {
    metricGroups.push({
      title: 'Reference-based Metrics',
      keys: ['Genome fraction (%)', 'Duplication ratio', 'NGA50', 'LGA50', '# misassemblies', '# mismatches per 100 kbp']
    });
  }
  
  if (detailedResults?.has_gene_prediction) {
    metricGroups.push({
      title: 'Gene Prediction',
      keys: ['# predicted genes (unique)', 'Complete BUSCO (%)', '# predicted genes (>= 300 bp)']
    });
  }
  
  if (!hasQuast) {
    return (
      <Alert severity="info">
        <AlertTitle>No QUAST results available</AlertTitle>
        Quality assessment was not performed for this job. QUAST analysis provides detailed metrics 
        about assembly quality.
      </Alert>
    );
  }
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">QUAST Quality Assessment</Typography>
        <Box>
          <Button 
            startIcon={<LaunchIcon />} 
            variant="outlined" 
            onClick={handleOpenReport}
            size="small"
            sx={{ mr: 1 }}
          >
            Open Report
          </Button>
          <Button
            startIcon={<GetAppIcon />}
            variant="outlined"
            href={getQuastReportUrl(jobId, 'html')}
            download
            size="small"
          >
            Download
          </Button>
        </Box>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Error loading QUAST results</AlertTitle>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Paper sx={{ mb: 3 }}>
            <Tabs
              value={activeTab}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="fullWidth"
            >
              <Tab label="Summary" />
              <Tab label="Detailed Metrics" />
              <Tab label="Comparison" />
            </Tabs>
            
            <TabPanel value={activeTab} index={0}>
              <Box mb={3}>
                <Typography variant="subtitle1" gutterBottom>
                  Assembly Quality Assessment
                </Typography>
                <Typography variant="body2" paragraph>
                  QUAST has evaluated the quality of your original and filtered assemblies. 
                  {quastImprovement?.overall_improved 
                    ? " The filtering has improved overall assembly quality." 
                    : " The filtering has changed assembly characteristics, but may not have improved all quality metrics."}
                </Typography>
                
                {quastImprovement && (
                  <Box mt={2} mb={3} display="flex" alignItems="center">
                    <Chip 
                      icon={quastImprovement.overall_improved ? <CompareArrowsIcon /> : undefined}
                      label={
                        quastImprovement.overall_improved 
                          ? `Overall Quality Improved (${(quastImprovement.overall_score * 100).toFixed(0)}%)` 
                          : `Quality Changes Mixed (${(quastImprovement.overall_score * 100).toFixed(0)}%)`
                      }
                      color={quastImprovement.overall_improved ? "success" : "warning"}
                      variant="outlined"
                    />
                  </Box>
                )}
              </Box>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  {canCompare && (
                    <QuastComparisonChart
                      title="Key Metrics Comparison"
                      originalAssembly={originalAssembly}
                      filteredAssembly={filteredAssembly}
                      comparison={quastResults?.comparison}
                      metricKeys={keyMetrics.filter(key => 
                        originalAssembly.metrics[key] !== undefined &&
                        filteredAssembly.metrics[key] !== undefined
                      )}
                    />
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  {canCompare && (
                    <QuastComparisonChart
                      title="Percent Change in Key Metrics"
                      originalAssembly={originalAssembly}
                      filteredAssembly={filteredAssembly}
                      comparison={quastResults?.comparison}
                      metricKeys={keyMetrics.filter(key => 
                        originalAssembly.metrics[key] !== undefined &&
                        filteredAssembly.metrics[key] !== undefined
                      )}
                      showPercent
                    />
                  )}
                </Grid>
              </Grid>
            </TabPanel>
            
            <TabPanel value={activeTab} index={1}>
              <Grid container spacing={3}>
                {detailedResults?.assemblies?.map((assemblyName) => {
                  const metrics = detailedResults?.basic_metrics?.[assemblyName] || {};
                  
                  // Convert metrics for each group to the expected format
                  const groupsWithMetrics = metricGroups.map(group => ({
                    title: group.title,
                    metrics: group.keys
                      .filter(key => metrics[key] !== undefined)
                      .map(key => ({
                        name: key,
                        value: metrics[key]
                      }))
                  })).filter(group => group.metrics.length > 0);
                  
                  return (
                    <Grid item xs={12} md={6} key={assemblyName}>
                      <QuastMetricsCard
                        title="Assembly Quality Metrics"
                        assemblyName={assemblyName}
                        metricGroups={groupsWithMetrics}
                      />
                    </Grid>
                  );
                })}
              </Grid>
            </TabPanel>
            
            <TabPanel value={activeTab} index={2}>
              {quastResults?.comparison ? (
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <QuastMetricsCard
                      title="Metric Changes"
                      comparison
                      metrics={quastResults.comparison.percent_change}
                      improved={quastResults.comparison.improvements}
                      percentChange={quastResults.comparison.percent_change}
                      description="Positive percentages indicate increases, negative indicate decreases"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>Improvement Summary</Typography>
                        <Divider sx={{ mb: 2 }} />
                        
                        <Box mb={2}>
                          <Typography variant="subtitle2" gutterBottom>Overall Assessment</Typography>
                          <Typography variant="body2">
                            {quastResults.comparison.overall_improved 
                              ? "Filtering has improved overall assembly quality." 
                              : "Filtering has altered assembly characteristics but may not have improved all quality aspects."}
                          </Typography>
                        </Box>
                        
                        <Box mb={2}>
                          <Typography variant="subtitle2" gutterBottom>Improvement Score</Typography>
                          <Typography variant="body1" color={
                            quastResults.comparison.overall_improvement_score > 0 ? "success.main" : "error.main"
                          }>
                            {(quastResults.comparison.overall_improvement_score * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                        
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light' }}>
                              <Typography variant="h5" align="center">
                                {quastResults.comparison.positive_metric_count}
                              </Typography>
                              <Typography variant="body2" align="center">
                                Improved Metrics
                              </Typography>
                            </Paper>
                          </Grid>
                          
                          <Grid item xs={6}>
                            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'error.light' }}>
                              <Typography variant="h5" align="center">
                                {quastResults.comparison.negative_metric_count}
                              </Typography>
                              <Typography variant="body2" align="center">
                                Degraded Metrics
                              </Typography>
                            </Paper>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              ) : (
                <Box textAlign="center" py={4}>
                  <Typography variant="body1" color="text.secondary">
                    Comparison data is not available.
                  </Typography>
                </Box>
              )}
            </TabPanel>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default QuastResultsTab;