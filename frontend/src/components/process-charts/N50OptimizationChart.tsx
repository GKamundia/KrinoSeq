import React from 'react';
import { Box, Typography, Paper, Grid, Divider } from '@mui/material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend, ComposedChart, Area } from 'recharts';

interface N50OptimizationChartProps {
  details: any;
}

const N50OptimizationChart: React.FC<N50OptimizationChartProps> = ({ details }) => {
  if (!details) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No N50 optimization details available</Typography>
      </Paper>
    );
  }
  
  // Format original length histogram for visualization
  const histogramData = details.histogram.bin_centers.map((center: number, index: number) => ({
    length: center,
    count: details.histogram.counts[index] || 0
  }));
  
  // Format N50 curve data
  const n50Data = details.cutoff_results?.map((result: any) => ({
    cutoff: result.cutoff,
    n50: result.n50,
    n50_change: result.n50_change,
    sequences_kept: result.sequences_kept,
    percent_kept: result.percent_kept
  })) || [];
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              N50 vs. Cutoff Length
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={n50Data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="cutoff" 
                    label={{ value: 'Minimum Length Cutoff (bp)', position: 'insideBottom', offset: -5 }}
                  />
                  <YAxis 
                    yAxisId="left"
                    label={{ value: 'N50 (bp)', angle: -90, position: 'insideLeft' }}
                  />
                  <YAxis 
                    yAxisId="right" 
                    orientation="right"
                    label={{ value: 'Sequences Kept (%)', angle: 90, position: 'insideRight' }}
                  />
                  <Tooltip formatter={(value: any) => value.toLocaleString()} />
                  <Legend />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="n50" 
                    stroke="#8884d8" 
                    name="N50"
                    dot={false}
                    activeDot={{ r: 5 }}
                  />
                  <Area 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="percent_kept" 
                    stroke="#82ca9d"
                    fill="#82ca9d"
                    fillOpacity={0.3} 
                    name="Sequences Kept (%)"
                  />
                  <ReferenceLine
                    x={details.optimal_cutoff}
                    stroke="red"
                    strokeDasharray="3 3"
                    label={{ value: 'Optimal Cutoff', position: 'insideBottomRight', fill: 'red' }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              N50 Optimization Results
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Initial N50:</strong> {details.initial_n50.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Optimal N50:</strong> {details.optimal_n50.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>N50 Improvement:</strong> {details.n50_improvement.toLocaleString()} bp
                ({((details.n50_improvement / details.initial_n50) * 100).toFixed(1)}%)
              </Typography>
            </Box>
            
            <Divider />
            
            <Box sx={{ my: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Optimal Filtering Parameters
              </Typography>
              <Typography variant="body2">
                <strong>Optimal Length Cutoff:</strong> {details.optimal_cutoff.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Search Range:</strong> {details.min_cutoff.toLocaleString()} bp - {details.max_cutoff.toLocaleString()} bp
              </Typography>
              <Typography variant="body2">
                <strong>Step Size:</strong> {details.step.toLocaleString()} bp
              </Typography>
            </Box>
            
            <Divider />
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Sequences at Optimal Cutoff
              </Typography>
              {n50Data.length > 0 && details.optimal_cutoff && (() => {
                const optimalResult = n50Data.find((d: any) => d.cutoff === details.optimal_cutoff);
                if (optimalResult) {
                  return (
                    <>
                      <Typography variant="body2">
                        <strong>Sequences kept:</strong> {optimalResult.sequences_kept.toLocaleString()}
                        ({optimalResult.percent_kept.toFixed(1)}%)
                      </Typography>
                      <Typography variant="body2">
                        <strong>Sequences removed:</strong> {
                          (n50Data[0]?.sequences_kept - optimalResult.sequences_kept).toLocaleString()
                        } ({(100 - optimalResult.percent_kept).toFixed(1)}%)
                      </Typography>
                    </>
                  );
                }
                return null;
              })()}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Original Length Distribution with Optimal Cutoff
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
                    x={details.optimal_cutoff}
                    stroke="red"
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    label={{ value: 'Optimal Cutoff', position: 'insideBottomRight', fill: 'red' }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default N50OptimizationChart;