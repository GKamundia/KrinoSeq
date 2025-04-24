import React from 'react';
import { Box, Typography, Paper, Grid, Alert } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import IQRDetailsChart from './IQRDetailsChart';
import ZScoreDetailsChart from './ZScoreDetailsChart';

interface AdaptiveDetailsChartProps {
  details: any;
}

const AdaptiveDetailsChart: React.FC<AdaptiveDetailsChartProps> = ({ details }) => {
  if (!details) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No adaptive filtering details available</Typography>
      </Paper>
    );
  }
  
  // Format data for visualization
  const histogramData = details.histogram.bin_centers.map((center: number, index: number) => ({
    length: center,
    count: details.histogram.counts[index] || 0
  }));
  
  // Create data for skewness and kurtosis visualization
  const distributionData = [
    { name: 'Skewness', value: details.skewness },
    { name: 'Kurtosis', value: details.kurtosis }
  ];
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Alert 
            severity="info" 
            sx={{ mb: 2 }}
          >
            <Typography variant="body2">
              <strong>Adaptive filtering selected:</strong> {details.selected_method.toUpperCase()} method
            </Typography>
            <Typography variant="body2">
              {details.reason}
            </Typography>
          </Alert>
        </Grid>
        
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Sequence Length Distribution
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="length" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => value.toLocaleString()} />
                  <Bar dataKey="count" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              Distribution Characteristics
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ my: 1 }}>
                <strong>Skewness:</strong> {details.skewness.toFixed(3)}
                <Typography variant="caption" display="block" color="text.secondary">
                  {Math.abs(details.skewness) < 0.5 ? 'Approximately symmetric' : 
                   Math.abs(details.skewness) < 1 ? 'Moderately skewed' : 'Highly skewed'}
                  {details.skewness > 0 ? ' (right tail)' : ' (left tail)'}
                </Typography>
              </Typography>
              
              <Typography variant="body2" sx={{ my: 1 }}>
                <strong>Kurtosis:</strong> {details.kurtosis.toFixed(3)}
                <Typography variant="caption" display="block" color="text.secondary">
                  {details.kurtosis < 0 ? 'Platykurtic (flatter than normal)' : 
                   details.kurtosis < 1 ? 'Approximately mesokurtic (normal-like)' : 'Leptokurtic (more peaked)'}
                </Typography>
              </Typography>
            </Box>
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Method Selection Logic
              </Typography>
              <Typography variant="body2">
                <strong>Selected method:</strong> {details.selected_method.toUpperCase()}
              </Typography>
              {details.selected_method === 'iqr' && (
                <Typography variant="body2">
                  <strong>IQR factor (k):</strong> {details.k_factor}
                </Typography>
              )}
              {details.selected_method === 'zscore' && (
                <Typography variant="body2">
                  <strong>Z-score threshold:</strong> {details.z_factor}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {Math.abs(details.skewness) > 2 ? 
                  'IQR selected for highly skewed distribution (robust to outliers)' : 
                  'Z-score selected for more symmetric distribution (assumes normality)'}
              </Typography>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Details of Applied {details.selected_method === 'iqr' ? 'IQR' : 'Z-score'} Method
            </Typography>
            
            {details.selected_method === 'iqr' && details.method_details && (
              <IQRDetailsChart 
                details={details.method_details.iqr_details} 
                outliers={details.method_details.outliers} 
              />
            )}
            
            {details.selected_method === 'zscore' && details.method_details && (
              <ZScoreDetailsChart 
                details={details.method_details.zscore_details} 
                outliers={details.method_details.outliers}
              />
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdaptiveDetailsChart;