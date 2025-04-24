import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface IQRDetailsChartProps {
  details: any;
  outliers: any;
}

const IQRDetailsChart: React.FC<IQRDetailsChartProps> = ({ details, outliers }) => {
  if (!details || !outliers) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No IQR details available</Typography>
      </Paper>
    );
  }
  
  // Format data for visualization
  const histogramData = details.histogram.bin_centers.map((center: number, index: number) => ({
    length: center,
    count: details.histogram.counts[index] || 0
  }));
  
  // Generate box plot data
  const boxPlotData = [details.box_plot_data];
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Length Distribution with IQR Thresholds
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="length" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => value.toLocaleString()} />
                  <Bar dataKey="count" fill="#1976d2" />
                  <ReferenceLine
                    x={details.lower_threshold}
                    stroke="red"
                    strokeDasharray="3 3"
                    label={{ value: 'Lower Threshold', position: 'insideBottomRight', fill: 'red', fontSize: 10 }}
                  />
                  <ReferenceLine
                    x={details.upper_threshold}
                    stroke="red"
                    strokeDasharray="3 3"
                    label={{ value: 'Upper Threshold', position: 'insideBottomRight', fill: 'red', fontSize: 10 }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              IQR Statistics
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Q1 (25th percentile):</strong> {details.q1.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Median (50th percentile):</strong> {details.box_plot_data.median.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Q3 (75th percentile):</strong> {details.q3.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>IQR (Q3-Q1):</strong> {details.iqr.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>k-factor used:</strong> {details.k}
              </Typography>
            </Box>
            
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Filtering Thresholds
            </Typography>
            <Typography variant="body2">
              <strong>Lower threshold:</strong> {details.lower_threshold.toLocaleString()} bp
              <br />
              <em>Calculation: Q1 - (k × IQR) = {details.q1.toLocaleString()} - ({details.k} × {details.iqr.toLocaleString()}) = {details.lower_threshold.toLocaleString()}</em>
            </Typography>
            <Typography variant="body2">
              <strong>Upper threshold:</strong> {details.upper_threshold.toLocaleString()} bp
              <br />
              <em>Calculation: Q3 + (k × IQR) = {details.q3.toLocaleString()} + ({details.k} × {details.iqr.toLocaleString()}) = {details.upper_threshold.toLocaleString()}</em>
            </Typography>
            
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Detected Outliers
            </Typography>
            <Typography variant="body2">
              <strong>Lower outliers:</strong> {outliers.lower_count.toLocaleString()} sequences
            </Typography>
            <Typography variant="body2">
              <strong>Upper outliers:</strong> {outliers.upper_count.toLocaleString()} sequences
            </Typography>
            <Typography variant="body2">
              <strong>Total outliers removed:</strong> {(outliers.lower_count + outliers.upper_count).toLocaleString()} sequences
              ({((outliers.lower_count + outliers.upper_count) / (details.box_plot_data.count || 1) * 100).toFixed(1)}% of total)
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default IQRDetailsChart;