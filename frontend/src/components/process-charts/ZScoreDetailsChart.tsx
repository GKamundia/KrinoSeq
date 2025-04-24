import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, LineChart, Line, ScatterChart, Scatter } from 'recharts';

interface ZScoreDetailsChartProps {
  details: any;
  outliers: any;
}

const ZScoreDetailsChart: React.FC<ZScoreDetailsChartProps> = ({ details, outliers }) => {
  if (!details || !outliers) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No Z-score details available</Typography>
      </Paper>
    );
  }
  
  // Format data for visualization
  const histogramData = details.histogram.bin_centers.map((center: number, index: number) => ({
    length: center,
    count: details.histogram.counts[index] || 0
  }));
  
  // Format normal distribution curve data
  const normalCurveData = details.normal_curve?.x.map((x: number, index: number) => ({
    length: x,
    density: details.normal_curve.y[index] || 0
  })) || [];
  
  // Format Z-score data for visualization (use first 100 for performance)
  const zScoreData = outliers.z_scores?.slice(0, 100).map((z: number, index: number) => ({
    index: index,
    z_score: z
  })) || [];
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Length Distribution with Z-score Thresholds
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
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Normal Distribution Fit
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={normalCurveData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="length" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="density" stroke="#82ca9d" dot={false} />
                  <ReferenceLine x={details.mean} stroke="blue" label={{ value: 'Mean', position: 'top', fill: 'blue' }} />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Z-score Distribution (Sample)
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="index" type="number" name="Index" />
                  <YAxis dataKey="z_score" name="Z-score" />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <ReferenceLine y={details.threshold} stroke="red" strokeDasharray="3 3" />
                  <ReferenceLine y={-details.threshold} stroke="red" strokeDasharray="3 3" />
                  <Scatter name="Z-scores" data={zScoreData} fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              Z-score Statistics
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Mean:</strong> {details.mean.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Standard Deviation:</strong> {details.std.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Z-score Threshold:</strong> {details.threshold}
              </Typography>
            </Box>
            
            <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
              Filtering Thresholds
            </Typography>
            <Typography variant="body2">
              <strong>Lower threshold:</strong> {details.lower_threshold.toLocaleString()} bp
              <br />
              <em>Calculation: Mean - (threshold × Std) = {details.mean.toLocaleString()} - ({details.threshold} × {details.std.toLocaleString()}) = {details.lower_threshold.toLocaleString()}</em>
            </Typography>
            <Typography variant="body2">
              <strong>Upper threshold:</strong> {details.upper_threshold.toLocaleString()} bp
              <br />
              <em>Calculation: Mean + (threshold × Std) = {details.mean.toLocaleString()} + ({details.threshold} × {details.std.toLocaleString()}) = {details.upper_threshold.toLocaleString()}</em>
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
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ZScoreDetailsChart;