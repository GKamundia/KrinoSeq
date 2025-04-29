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
  const histogramData = details?.histogram?.bin_centers?.map((center: number, index: number) => ({
    length: center,
    count: details.histogram.counts[index] || 0
  })) || [];

  // Add a fallback for empty histogram data
  if (histogramData.length === 0 && details) {
    console.log("Missing histogram data in GMM details:", details);
  }
  
  // Format BIC scores for chart
  const bicScores = details.bic_scores?.map((score: number, index: number) => ({
    components: index + 1,
    bic: score
  })) || [];
  
  // Process component curves data for visualization
  const combinedData = details.component_curves?.length > 0 
    ? details.component_curves[0].x.map((x: number, i: number) => {
        const point: any = { length: x };
        
        // Add each component's density at this point
        details.component_curves.forEach((curve: any, componentIndex: number) => {
          point[`component_${componentIndex}`] = curve.y[i] || 0;
        });
        
        return point;
      }) 
    : [];
  
  // Colors for components
  const componentColors = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#0088fe'];
  
  // Use either sorted_components or components
  const componentData = details.sorted_components || details.components || [];
  
  // Override is_multimodal based on component count if needed
  const isMultimodal = details.is_multimodal !== undefined 
    ? details.is_multimodal 
    : (componentData.length > 1);
    
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
                  {details.gmm_based?.map((cutoff: number, index: number) => (
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
              {combinedData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={combinedData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="length" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {componentData.map((component: any, index: number) => (
                      <Line
                        key={`component-${index}`}
                        type="monotone"
                        dataKey={`component_${index}`}
                        name={`Component ${index + 1} (${Math.round(component.weight * 100)}%)`}
                        stroke={componentColors[index % componentColors.length]}
                        dot={false}
                      />
                    ))}
                    {details.selected_cutoff && (
                      <ReferenceLine
                        x={details.selected_cutoff}
                        stroke="#ff8042"
                        strokeWidth={2}
                        label={{ value: 'Cutoff', position: 'top', fill: '#ff8042', fontSize: 12 }}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" sx={{ pt: 10, textAlign: 'center' }}>
                  No component curve data available. This may happen if there is only one component
                  or if the GMM analysis failed to identify clear components.
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              BIC Scores by Component Count
            </Typography>
            <Box sx={{ height: 250 }}>
              {bicScores.length > 0 ? (
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
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ pt: 5, textAlign: 'center' }}>
                  BIC scores are not available. This may be because:
                  <ul>
                    <li>Only one component was detected</li>
                    <li>You're using Dirichlet method which doesn't provide BIC</li>
                    <li>Component method is set incorrectly</li>
                  </ul>
                  Try changing the Component Selection method to "bic" in filter settings.
                </Typography>
              )}
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
                <strong>Is Multimodal:</strong> {isMultimodal ? 'Yes' : 'No'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Optimal Number of Components:</strong> {details.optimal_components}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Selected Cutoff:</strong> {details.selected_cutoff?.toLocaleString() || details.gmm_based?.[0]?.toLocaleString() || 'None'} bp
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Cutoff Method:</strong> {details.method_used || 'midpoint'}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Transform Type:</strong> {details.transform_params?.type || 'none'}
                {details.transform_params?.type === 'box-cox' && details.transform_params?.lambda && (
                  <span> (λ = {details.transform_params.lambda.toFixed(4)})</span>
                )}
              </Typography>
              <Typography variant="body2" gutterBottom>
                <strong>Component Selection Method:</strong> {details.component_selection_method || 'bic'}
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Component Details
              </Typography>
              
              <Stack spacing={1}>
                {componentData.map((component: any, index: number) => (
                  <Box key={`comp-details-${index}`} sx={{ p: 1, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                    <Typography variant="body2">
                      <strong>Component {index + 1}:</strong> Weight: {(component.weight * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">
                      {component.mean_original ? (
                        <>Mean (orig): {component.mean_original.toLocaleString()} bp, Std (orig): {component.std_original.toLocaleString()} bp</>
                      ) : (
                        <>Mean: {component.mean.toLocaleString()} bp, Std Dev: {component.std.toLocaleString()} bp</>
                      )}
                    </Typography>
                    {component.mean_transformed && (
                      <Typography variant="body2" fontSize="0.75rem" color="text.secondary">
                        Mean (transformed space): {component.mean_transformed.toFixed(3)}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Stack>
              
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Available Cutoff Types
              </Typography>
              
              <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
                {details.gmm_based?.length > 0 && (
                  <Chip label={`GMM Cutoffs: ${details.gmm_based.length}`} color="primary" size="small" />
                )}
                {details.peak_cutoffs?.length > 0 && (
                  <Chip label={`Peak Cutoffs: ${details.peak_cutoffs.length}`} color="secondary" size="small" />
                )}
                {details.valley_cutoffs?.length > 0 && (
                  <Chip label={`Valley Cutoffs: ${details.valley_cutoffs.length}`} color="success" size="small" />
                )}
              </Stack>

              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Method Diagnostic Information
              </Typography>

              <Box sx={{ mt: 1 }}>
                <Typography variant="body2">
                  <strong>Method Used:</strong> {details.method_used || 'midpoint'}
                </Typography>
                <Typography variant="body2">
                  <strong>GMM Cutoffs:</strong> {details.gmm_based?.map((c: number) => c.toLocaleString()).join(', ') || 'None'}
                </Typography>
                <Typography variant="body2">
                  <strong>Valley Cutoffs:</strong> {details.valley_cutoffs?.map((c: number) => c.toLocaleString()).join(', ') || 'None'} 
                </Typography>
                <Typography variant="body2">
                  <strong>Peak Cutoffs:</strong> {details.peak_cutoffs?.map((c: number) => c.toLocaleString()).join(', ') || 'None'}
                </Typography>
                <Typography variant="body2">
                  <strong>Recommended Cutoffs:</strong> {(details.recommended_cutoffs || details.recommended)?.map((c: number) => c.toLocaleString()).join(', ') || 'None'}
                </Typography>
              </Box>

              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Transformation Details
              </Typography>

              <Box sx={{ mt: 1 }}>
                <Typography variant="body2">
                  <strong>Transform Type:</strong> {details.transform_params?.type || 'none'}
                </Typography>
                {details.transform_params?.type === 'box-cox' && (
                  <Typography variant="body2">
                    <strong>Lambda:</strong> {details.transform_params?.lambda?.toFixed(4)}
                    <strong> Offset:</strong> {details.transform_params?.offset || 0}
                  </Typography>
                )}
              </Box>

              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Filtering Impact
              </Typography>

              <Box sx={{ mt: 1 }}>
                {details.filtering_stats && (
                  <>
                    <Typography variant="body2">
                      <strong>Cutoff Value:</strong> {details.filtering_stats.cutoff?.toLocaleString()} bp
                    </Typography>
                    <Typography variant="body2">
                      <strong>Contigs Retained:</strong> {details.filtering_stats.retained_contigs?.toLocaleString()} 
                      ({details.filtering_stats.retained_contigs_percent?.toFixed(1)}%)
                    </Typography>
                    <Typography variant="body2">
                      <strong>Base Pairs Retained:</strong> {details.filtering_stats.retained_bp?.toLocaleString()} 
                      ({details.filtering_stats.retained_bp_percent?.toFixed(1)}%)
                    </Typography>
                  </>
                )}
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default GMMDetailsChart;