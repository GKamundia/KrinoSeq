import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  Stepper, 
  Step, 
  StepLabel,
  Button,
  Divider,
  Container,
  CircularProgress,
  Grid
} from '@mui/material';
import { Formik, Form } from 'formik';
import * as Yup from 'yup';
import { getJobStatus, configureFilter, executeFilter } from '../services/api';
import { FilterMethod, JobStatus, FilterPipelineConfig } from '../types/api';
import StatusAlert from '../components/StatusAlert';
import SequenceStatsCard from '../components/SequenceStatsCard';
import LengthDistributionChart from '../components/LengthDistributionChart';
import FilterMethodSelector from '../components/FilterMethodSelector';

const ConfigurePage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [jobInfo, setJobInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobStatus = async () => {
      if (!jobId) return;
      
      try {
        setLoading(true);
        const data = await getJobStatus(jobId);
        setJobInfo(data);
        
        // If the job is completed, move to step 1
        if (data.status === JobStatus.COMPLETED) {
          setActiveStep(1);
        }
      } catch (err) {
        console.error('Error fetching job status:', err);
        setError('Failed to load job information');
      } finally {
        setLoading(false);
      }
    };

    fetchJobStatus();
    
    // Poll for job status updates if the job is pending or processing
    const intervalId = setInterval(() => {
      if (jobInfo?.status === JobStatus.PENDING || jobInfo?.status === JobStatus.PROCESSING) {
        fetchJobStatus();
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [jobId, jobInfo?.status]);

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmitConfig = async (values: FilterPipelineConfig) => {
    if (!jobId) return;
    
    try {
      setLoading(true);
      await configureFilter(jobId, values);
      handleNext();
    } catch (err) {
      console.error('Error configuring filter:', err);
      setError('Failed to configure filter');
    } finally {
      setLoading(false);
    }
  };

  const handleStartFiltering = async () => {
    if (!jobId) return;
    
    try {
      setLoading(true);
      await executeFilter(jobId);
      navigate(`/results/${jobId}`);
    } catch (err) {
      console.error('Error executing filter:', err);
      setError('Failed to start filtering process');
      setLoading(false);
    }
  };

  const steps = ['File Analysis', 'Configure Filters', 'Review & Execute'];

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
      </Box>
    );
  }

  return (
    <Container>
      <Typography variant="h4" component="h1" gutterBottom>
        Configure Filtering
      </Typography>
      
      {jobInfo && jobInfo.status !== JobStatus.COMPLETED && (
        <StatusAlert 
          status={jobInfo.status} 
          message={jobInfo.message} 
          progress={jobInfo.progress} 
        />
      )}
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        <Divider sx={{ my: 2 }} />
        
        {activeStep === 0 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              File Analysis
            </Typography>
            <Typography paragraph>
              Your file is being analyzed. This may take a few moments for large files.
            </Typography>
          </Box>
        )}
        
        {activeStep === 1 && jobInfo?.file_info && (
          <Box>
            <Typography variant="h6" gutterBottom>
              File Analysis Results
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <SequenceStatsCard 
                  title="Sequence Statistics"
                  sequenceCount={jobInfo.file_info.sequence_count}
                  basicStats={jobInfo.file_info.basic_stats}
                  assemblyStats={jobInfo.file_info.assembly_stats}
                />
              </Grid>
              
              <Grid item xs={12}>
                <LengthDistributionChart 
                  data={jobInfo.file_info.visualization_data}
                  title="Sequence Length Distribution"
                />
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              Configure Filtering Methods
            </Typography>
            
            <Formik
              initialValues={{
                stages: [
                  {
                    method: FilterMethod.ADAPTIVE,
                    params: {}
                  }
                ]
              }}
              validationSchema={Yup.object({
                stages: Yup.array().of(
                  Yup.object({
                    method: Yup.string().required('Method is required'),
                    params: Yup.object().when('method', (methodValue, schema) => {
                      // Handle the case where method is passed as an array
                      const method = Array.isArray(methodValue) ? methodValue[0] : methodValue;
                      
                      if (method === FilterMethod.MIN_MAX) {
                        return Yup.object({
                          min_length: Yup.number().nullable(),
                          max_length: Yup.number().nullable(),
                        });
                      }
                      
                      if (method === FilterMethod.IQR) {
                        return Yup.object({
                          k: Yup.number().default(1.5).min(0.1).max(10),
                        });
                      }
                      
                      if (method === FilterMethod.ZSCORE) {
                        return Yup.object({
                          threshold: Yup.number().default(2.5).min(0.1).max(10),
                        });
                      }
                      
                      // Default return the original schema
                      return schema;
                    })
                  })
                ).min(1, 'At least one filtering method is required')
              })}
              onSubmit={handleSubmitConfig}
            >
              {({ isSubmitting }) => (
                <Form>
                  <FilterMethodSelector />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                    <Button
                      onClick={handleBack}
                      sx={{ mr: 1 }}
                    >
                      Back
                    </Button>
                    <Button
                      variant="contained"
                      color="primary"
                      type="submit"
                      disabled={isSubmitting}
                    >
                      Next
                    </Button>
                  </Box>
                </Form>
              )}
            </Formik>
          </Box>
        )}
        
        {activeStep === 2 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review and Execute
            </Typography>
            
            <Typography paragraph>
              Your filtering configuration is ready. Click the button below to start the filtering process.
            </Typography>
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
              <Button
                onClick={handleBack}
                sx={{ mr: 1 }}
              >
                Back
              </Button>
              <Button
                variant="contained"
                color="primary"
                onClick={handleStartFiltering}
                disabled={loading}
              >
                Start Filtering
              </Button>
            </Box>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default ConfigurePage;