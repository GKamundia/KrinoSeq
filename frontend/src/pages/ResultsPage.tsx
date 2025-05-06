import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  Container,
  Button,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Tabs,
  Tab
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import AssessmentIcon from '@mui/icons-material/Assessment'; // New icon for QUAST tab
import { getFilterResults, getJobStatus, hasQuastResults } from '../services/api'; // Added hasQuastResults
import { JobStatus, FilterResults } from '../types/api';
import StatusAlert from '../components/StatusAlert';
import SequenceStatsCard from '../components/SequenceStatsCard';
import LengthDistributionChart from '../components/LengthDistributionChart';
import FilteringResultsSummary from '../components/FilteringResultsSummary';
import FilteringProcessDetails from '../components/FilteringProcessDetails';
import QuastResultsTab from '../components/QuastResultsTab'; // Add import for QUAST tab

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`results-tabpanel-${index}`}
      aria-labelledby={`results-tab-${index}`}
      {...other }
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Define interfaces for our data structure
interface SummaryData {
  input_file?: {
    sequence_count?: number;
    total_length?: number;
    n50?: number;
    l50?: number;
    min_length?: number;
    max_length?: number;
    mean_length?: number;
    median_length?: number;
    std_dev?: number;
  };
  output_file?: {
    sequence_count?: number;
    total_length?: number;
    n50?: number;
    l50?: number;
    min_length?: number;
    max_length?: number;
    mean_length?: number;
    median_length?: number;
    std_dev?: number;
  };
}

interface VisualizationDataType {
  before?: any;
  after?: any;
}

const ResultsPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const [results, setResults] = useState<FilterResults | null>(null);
  const [jobInfo, setJobInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    const fetchResults = async () => {
      if (!jobId) return;
      
      try {
        setLoading(true);
        
        const status = await getJobStatus(jobId);
        setJobInfo(status);
        
        if (status.status === JobStatus.COMPLETED) {
          const filterResults = await getFilterResults(jobId);
          setResults(filterResults);
        }
      } catch (err) {
        console.error('Error fetching results:', err);
        setError('Failed to load filtering results');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
    
    const intervalId = setInterval(() => {
      if (jobInfo?.status === JobStatus.PROCESSING) {
        fetchResults();
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [jobId, jobInfo?.status]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    // If trying to navigate to tab 4 (QUAST) but QUAST results aren't available,
    // don't change the tab value
    if (newValue === 4 && !hasQuastResults(results)) {
      return;
    }
    setTabValue(newValue);
  };

  if (loading && !jobInfo) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <StatusAlert status={JobStatus.FAILED} message={error} />
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button
            component={RouterLink}
            to="/upload"
            variant="contained"
          >
            Upload New File
          </Button>
        </Box>
      </Box>
    );
  }

  const summary = (results?.summary || {}) as SummaryData;
  const inputFile = summary.input_file || {};
  const outputFile = summary.output_file || {};
  const visualizationData = (results?.visualization_data || {}) as VisualizationDataType;

  return (
    <Container>
      <Typography variant="h4" component="h1" gutterBottom>
        Filtering Results
      </Typography>
      
      {jobInfo && jobInfo.status !== JobStatus.COMPLETED && (
        <StatusAlert 
          status={jobInfo.status} 
          message={jobInfo.message || 'Processing your filtering request...'} 
          progress={jobInfo.progress} 
        />
      )}
      
      {results && results.status === JobStatus.COMPLETED && (
        <Box>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FilteringResultsSummary summary={summary} />
              </Grid>
              
              {results.download_url && (
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      component="a"
                      href={results.download_url}
                      startIcon={<DownloadIcon />}
                      sx={{ mr: 2 }}
                    >
                      Download Filtered FASTA
                    </Button>
                    <Button
                      variant="outlined"
                      component={RouterLink}
                      to="/upload"
                      sx={{ ml: 2 }}
                    >
                      Upload New File
                    </Button>
                  </Box>
                </Grid>
              )}
            </Grid>
          </Paper>
          
          <Card sx={{ mb: 4 }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange} 
                aria-label="Results tabs"
                centered
              >
                <Tab label="Before/After Comparison" id="results-tab-0" />
                <Tab label="Original Contigs" id="results-tab-1" />
                <Tab label="Filtered Contigs" id="results-tab-2" />
                <Tab label="Filtering Process" id="results-tab-3" />
                {/* Add QUAST Analysis tab only if results are available */}
                {hasQuastResults(results) && (
                  <Tab 
                    label="QUAST Analysis" 
                    id="results-tab-4" 
                    icon={<AssessmentIcon fontSize="small" />} 
                    iconPosition="start"
                  />
                )}
              </Tabs>
            </Box>
            
            <CardContent>
              <TabPanel value={tabValue} index={0}>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                      <CompareArrowsIcon sx={{ mr: 1 }} /> Comparison
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <SequenceStatsCard 
                          title="Original File"
                          sequenceCount={inputFile.sequence_count || 0}
                          basicStats={{
                            total: inputFile.total_length || 0,
                            min: inputFile.min_length || 0,
                            max: inputFile.max_length || 0,
                            mean: inputFile.mean_length || 0,
                            median: inputFile.median_length || 0,
                            std_dev: inputFile.std_dev || 0,
                            count: inputFile.sequence_count || 0
                          }}
                          assemblyStats={{
                            n50: inputFile.n50 || 0,
                            l50: inputFile.l50 || 0
                          }}
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <SequenceStatsCard 
                          title="Filtered File"
                          sequenceCount={outputFile.sequence_count || 0}
                          basicStats={{
                            total: outputFile.total_length || 0,
                            min: outputFile.min_length || 0,
                            max: outputFile.max_length || 0,
                            mean: outputFile.mean_length || 0,
                            median: outputFile.median_length || 0,
                            std_dev: outputFile.std_dev || 0,
                            count: outputFile.sequence_count || 0
                          }}
                          assemblyStats={{
                            n50: outputFile.n50 || 0,
                            l50: outputFile.l50 || 0
                          }}
                        />
                      </Grid>
                    </Grid>
                    
                    {hasQuastResults(results) && (
                      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          QUAST Quality Assessment Available
                        </Typography>
                        <Typography variant="body2">
                          Detailed assembly quality metrics are available in the QUAST Analysis tab.
                          These metrics provide insights into the impact of filtering on assembly quality.
                        </Typography>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          sx={{ mt: 1 }}
                          onClick={() => setTabValue(4)}
                        >
                          View QUAST Analysis
                        </Button>
                      </Box>
                    )}
                  </Grid>
                </Grid>
              </TabPanel>
              
              <TabPanel value={tabValue} index={1}>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Original Contig Statistics
                    </Typography>
                    
                    <SequenceStatsCard 
                      title="Original File"
                      sequenceCount={inputFile.sequence_count || 0}
                      basicStats={{
                        total: inputFile.total_length || 0,
                        min: inputFile.min_length || 0,
                        max: inputFile.max_length || 0,
                        mean: inputFile.mean_length || 0,
                        median: inputFile.median_length || 0,
                        std_dev: inputFile.std_dev || 0,
                        count: inputFile.sequence_count || 0
                      }}
                      assemblyStats={{
                        n50: inputFile.n50 || 0,
                        l50: inputFile.l50 || 0
                      }}
                    />
                  </Grid>
                  
                  {visualizationData?.before && (
                    <Grid item xs={12}>
                      <LengthDistributionChart 
                        data={visualizationData.before}
                        title="Original Length Distribution"
                      />
                    </Grid>
                  )}
                </Grid>
              </TabPanel>
              
              <TabPanel value={tabValue} index={2}>
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <Typography variant="h6" gutterBottom>
                      Filtered Contig Statistics
                    </Typography>
                    
                    <SequenceStatsCard 
                      title="Filtered File"
                      sequenceCount={outputFile.sequence_count || 0}
                      basicStats={{
                        total: outputFile.total_length || 0,
                        min: outputFile.min_length || 0,
                        max: outputFile.max_length || 0,
                        mean: outputFile.mean_length || 0,
                        median: outputFile.median_length || 0,
                        std_dev: outputFile.std_dev || 0,
                        count: outputFile.sequence_count || 0
                      }}
                      assemblyStats={{
                        n50: outputFile.n50 || 0,
                        l50: outputFile.l50 || 0
                      }}
                    />
                  </Grid>
                  
                  {visualizationData?.after && (
                    <Grid item xs={12}>
                      <LengthDistributionChart 
                        data={visualizationData.after}
                        title="Filtered Length Distribution"
                      />
                    </Grid>
                  )}
                </Grid>
              </TabPanel>

              <TabPanel value={tabValue} index={3}>
                <FilteringProcessDetails filteringProcess={results?.filtering_process || []} />
              </TabPanel>

              {/* Add new TabPanel for QUAST Analysis */}
              {hasQuastResults(results) && (
                <TabPanel value={tabValue} index={4}>
                  <QuastResultsTab 
                    jobId={jobId!} 
                    filterResults={results}
                    onError={(message) => {
                      // Handle errors, could set a state variable if needed
                      console.error("QUAST error:", message);
                    }} 
                  />
                </TabPanel>
              )}
            </CardContent>
          </Card>
        </Box>
      )}
    </Container>
  );
};

export default ResultsPage;