import React from 'react';
import { Box, Typography, Paper, Grid, Divider } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

interface MinMaxDetailsChartProps {
  details: any;
}

const MinMaxDetailsChart: React.FC<MinMaxDetailsChartProps> = ({ details }) => {
  if (!details || !details.length_distribution) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No min/max filtering details available</Typography>
      </Paper>
    );
  }
  
  // Format data for visualization
  const histogramData = details.length_distribution.histogram.bin_centers.map(
    (center: number, index: number) => ({
      length: center,
      count: details.length_distribution.histogram.counts[index] || 0
    })
  );
  
  // Get threshold values
  const minLength = details.params?.min_length;
  const maxLength = details.params?.max_length;
  
  // Get removed sequence counts
  const tooShortCount = details.removed_sequences?.too_short || 0;
  const tooLongCount = details.removed_sequences?.too_long || 0;
  
  // Create sample data for removed sequences
  const shortLengths = details.removed_sequences?.too_short_lengths || [];
  const longLengths = details.removed_sequences?.too_long_lengths || [];
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Length Distribution with Min/Max Thresholds
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogramData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="length" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => value.toLocaleString()} />
                  <Bar dataKey="count" fill="#1976d2" />
                  {minLength && (
                    <ReferenceLine
                      x={minLength}
                      stroke="red"
                      strokeDasharray="3 3"
                      label={{ value: 'Min Length', position: 'insideBottomRight', fill: 'red', fontSize: 10 }}
                    />
                  )}
                  {maxLength && (
                    <ReferenceLine
                      x={maxLength}
                      stroke="red"
                      strokeDasharray="3 3"
                      label={{ value: 'Max Length', position: 'insideBottomRight', fill: 'red', fontSize: 10 }}
                    />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle2" gutterBottom>
              Min/Max Filter Parameters
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Minimum Length:</strong> {minLength ? `${minLength.toLocaleString()} bp` : 'Not specified'}
              </Typography>
              <Typography variant="body2">
                <strong>Maximum Length:</strong> {maxLength ? `${maxLength.toLocaleString()} bp` : 'Not specified'}
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Original Data Range
            </Typography>
            <Typography variant="body2">
              <strong>Min value:</strong> {details.length_distribution.min.toLocaleString()} bp
            </Typography>
            <Typography variant="body2">
              <strong>Max value:</strong> {details.length_distribution.max.toLocaleString()} bp
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Filtering Results
            </Typography>
            <Typography variant="body2">
              <strong>Sequences below minimum:</strong> {tooShortCount.toLocaleString()}
              {tooShortCount > 0 && shortLengths.length > 0 && (
                <Typography variant="caption" display="block" color="text.secondary">
                  Example lengths: {shortLengths.slice(0, 5).map((l: number) => l.toLocaleString()).join(', ')}
                  {shortLengths.length > 5 ? '...' : ''}
                </Typography>
              )}
            </Typography>
            
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Sequences above maximum:</strong> {tooLongCount.toLocaleString()}
              {tooLongCount > 0 && longLengths.length > 0 && (
                <Typography variant="caption" display="block" color="text.secondary">
                  Example lengths: {longLengths.slice(0, 5).map((l: number) => l.toLocaleString()).join(', ')}
                  {longLengths.length > 5 ? '...' : ''}
                </Typography>
              )}
            </Typography>
            
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Total sequences removed:</strong> {(tooShortCount + tooLongCount).toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MinMaxDetailsChart;