import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend, ComposedChart, Area } from 'recharts';

interface FilteringImpactChartProps {
  filteringProcess: any[];
}

const FilteringImpactChart: React.FC<FilteringImpactChartProps> = ({ filteringProcess }) => {
  if (!filteringProcess || filteringProcess.length === 0) {
    return (
      <Paper sx={{ p: 2 }}>
        <Typography>No filtering process data available</Typography>
      </Paper>
    );
  }
  
  // Generate data for sequence count reduction through the pipeline
  const sequenceCountData = filteringProcess.reduce((acc: any[], stage: any, index: number) => {
    // If it's the first stage, add the "before" state
    if (index === 0) {
      acc.push({
        stage: 'Original',
        sequences: stage.sequences_before,
        reduction: 0
      });
    }
    
    // Add current stage's data
    acc.push({
      stage: `Stage ${index + 1}`,
      sequences: stage.sequences_after,
      reduction: ((stage.sequences_before - stage.sequences_after) / stage.sequences_before * 100).toFixed(1),
      method: getMethodDisplayName(stage.method)
    });
    
    return acc;
  }, []);
  
  // Generate summary data with method-specific stats
  const summaryByMethod = filteringProcess.reduce((acc: any, stage: any) => {
    const methodName = stage.method;
    const sequencesBefore = stage.sequences_before;
    const sequencesAfter = stage.sequences_after;
    const reduction = sequencesBefore - sequencesAfter;
    const reductionPercent = (reduction / sequencesBefore * 100).toFixed(1);
    
    acc.push({
      method: getMethodDisplayName(methodName),
      sequencesBefore,
      sequencesAfter,
      reduction,
      reductionPercent
    });
    
    return acc;
  }, []);
  
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Sequence Count Through Pipeline Stages
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={sequenceCountData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="stage" />
                  <YAxis 
                    yAxisId="left"
                    label={{ value: 'Sequence Count', angle: -90, position: 'insideLeft' }}
                  />
                  <YAxis 
                    yAxisId="right" 
                    orientation="right" 
                    domain={[0, 100]}
                    label={{ value: 'Reduction %', angle: 90, position: 'insideRight' }}
                  />
                  <Tooltip formatter={(value: any) => typeof value === 'number' ? value.toLocaleString() : value} />
                  <Legend />
                  <Bar 
                    yAxisId="left"
                    dataKey="sequences" 
                    fill="#8884d8" 
                    name="Sequences"
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="reduction" 
                    stroke="#ff7300" 
                    name="Reduction %"
                    connectNulls
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Impact by Filtering Method
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summaryByMethod} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="method" type="category" width={120} />
                  <Tooltip formatter={(value: any) => typeof value === 'number' ? value.toLocaleString() : value} />
                  <Legend />
                  <Bar dataKey="reduction" fill="#82ca9d" name="Sequences Removed" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Filtering Efficiency Comparison
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summaryByMethod}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="method" />
                  <YAxis domain={[0, 100]} label={{ value: 'Percentage', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value: any) => `${value}%`} />
                  <Legend />
                  <Bar dataKey="reductionPercent" fill="#ff8042" name="Reduction %" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

// Helper function to get a display-friendly method name
function getMethodDisplayName(method: string): string {
  switch (method) {
    case 'min_max': return 'Min/Max Length Filter';
    case 'iqr': return 'IQR-based Outlier Filter';
    case 'zscore': return 'Z-score Outlier Filter';
    case 'adaptive': return 'Adaptive Filter';
    case 'n50_optimize': return 'N50 Optimization Filter';
    case 'natural': return 'Natural Breakpoint Filter';
    default: return method;
  }
}

export default FilteringImpactChart;