import React from 'react';
import { Box, Typography, Paper, Grid, Chip, Stack } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, LineChart, Line, Legend } from 'recharts';

interface GMMDetailsChartProps {
  details: any;
}

const GMMDetailsChart: React.FC<GMMDetailsChartProps> = ({ details }) => {
  if (!details) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No GMM details available</Typography>
      </Paper>
    );
  }
  
  // Format data for visualization
  const histogramData = details.histogram.bin_centers.map((center: number, index: number) => ({
    length: center,
    count: details.histogram.counts[index] || 0
  }));
  
  // Format BIC scores for chart
  const bicScores = details.bic_scores?.map((score: number, index: number) => ({
    components: index + 1,
    bic: score
  })) || [];
  
  // Combine all component curves for overlay
  const combinedData = details.component_curves?.[0].x.map((x: number, i: number) => {
    const point: any = { length: x };
    
    // Add each component's density at this point
    details.component_curves.forEach((curve: any, componentIndex: number) => {
      point[`component_${componentIndex}`] = curve.y[i] || 0;
    });
    
    return point;
  }) || [];
  
  // Colors for components
  const componentColors = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088fe'];
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Sequence Length Distribution with GMM Components
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="length" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => value.toLocaleString()} />
                  <Bar dataKey="count" fill="#1976d2" fillOpacity={0.6} />
                  {details.gmm_cutoffs?.map((cutoff: number, index: number) => (
                    <ReferenceLine
                      key={`cutoff-${index}`}
                      x={cutoff}
                      stroke="red"
                      strokeDasharray="3 3"
                      label={{ value: `Cutoff ${index + 1}`, position: 'insideBottomRight', fill: 'red', fontSize: 10 }}
                    />
                  ))}
                  {details.selected_cutoff && (
                    <ReferenceLine
                      x={details.selected_cutoff}
                      stroke="#ff8042"
                      strokeWidth={2}
                      label={{ value: 'Selected Cutoff', position: 'insideBottomRight', fill: '#ff8042', fontSize: 12 }}
                    />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              GMM Component Curves
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={combinedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="length" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  {details.component_curves?.map((curve: any, index: number) => (
                    <Line
                      key={`component-${index}`}
                      type="monotone"
                      dataKey={`component_${index}`}
                      name={`Component ${index + 1}`}
                      stroke={componentColors[index % componentColors.length]}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              BIC Scores by Component Count
            </Typography>
            <Box sx={{ height: 250 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={bicScores}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="components" label={{ value: 'Number of Components', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'BIC Score', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value: any) => value.toLocaleString()} />
                  <Bar dataKey="bic" fill="#82ca9d" />
                  <ReferenceLine
                    x={details.optimal_components}
                    stroke="red"
                    strokeDasharray="3 3"
                    label={{ value: 'Optimal', position: 'insideTopRight', fill: 'red' }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              GMM Model Information
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                <strong>Is Multimodal:</strong> {details.is_multimodal ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Optimal Number of Components:</strong> {details.optimal_components}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Selected Cutoff:</strong> {details.selected_cutoff?.toLocaleString() || 'None'} bp
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Component Details
              </Typography>
              
              <Stack spacing={1}>
                {details.components?.map((component: any, index: number) => (
                  <Box key={`comp-details-${index}`} sx={{ p: 1, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                    <Typography variant="body2">
                      <strong>Component {index + 1}:</strong> Weight: {(component.weight * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      Mean: {component.mean.toLocaleString()} bp,  Std Dev: {component.std.toLocaleString()} bp
                    </Typography>
                  </Box>
                ))}
              </Stack>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Available Cutoff Types
              </Typography>
              
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
                {details.gmm_cutoffs?.length > 0 && (
                  <Chip label={`GMM Cutoffs: ${details.gmm_cutoffs.length}`} color="primary" size="small" />
                )}
                {details.peak_cutoffs?.length > 0 && (
                  <Chip label={`Peak Cutoffs: ${details.peak_cutoffs.length}`} color="secondary" size="small" />
                )}
                {details.valley_cutoffs?.length > 0 && (
                  <Chip label={`Valley Cutoffs: ${details.valley_cutoffs.length}`} color="success" size="small" />
                )}
              </Stack>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default GMMDetailsChart;