import React from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper,
  Chip,
  Divider,
  LinearProgress,
  Tooltip
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';

interface FilteringResultsSummaryProps {
  summary: any;
}

const FilteringResultsSummary: React.FC<FilteringResultsSummaryProps> = ({ summary }) => {
  if (!summary) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography>No filtering summary available</Typography>
      </Paper>
    );
  }

  // Safe access to nested properties with fallbacks
  const inputFile = summary.input_file || {};
  const outputFile = summary.output_file || {};
  const filtering = summary.filtering || {};
  
  // Safe access with fallbacks for all values
  const inputSequenceCount = inputFile.sequence_count || 0;
  const outputSequenceCount = outputFile.sequence_count || 0;
  const inputTotalLength = inputFile.total_length || 0;
  const outputTotalLength = outputFile.total_length || 0;
  
  const percentSequencesKept = filtering.percent_sequences_kept || 0;
  const percentLengthKept = filtering.percent_length_kept || 0;
  const n50Change = filtering.n50_change || 0;
  const l50Change = filtering.l50_change || 0;
  const sequencesRemoved = filtering.sequences_removed || 0;
  const lengthRemoved = filtering.length_removed || 0;
  
  const formattedDate = summary.timestamp 
    ? new Date(summary.timestamp).toLocaleString() 
    : new Date().toLocaleString();

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Filtering Summary
      </Typography>
      <Typography variant="caption" display="block" color="text.secondary" gutterBottom>
        Completed on {formattedDate}
      </Typography>
      
      <Divider sx={{ my: 2 }} />
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Contigs Retained
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box sx={{ flexGrow: 1, mr: 1 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={percentSequencesKept} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {percentSequencesKept.toFixed(1)}%
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {outputSequenceCount.toLocaleString()} / {inputSequenceCount.toLocaleString()} contigs kept
            </Typography>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Total Length Retained
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box sx={{ flexGrow: 1, mr: 1 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={percentLengthKept} 
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {percentLengthKept.toFixed(1)}%
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {outputTotalLength.toLocaleString()} / {inputTotalLength.toLocaleString()} bp kept
            </Typography>
          </Box>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="subtitle2" gutterBottom>
            Assembly Metrics Impact
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Tooltip title="N50 is a measure of assembly quality - higher is better">
              <Chip 
                icon={n50Change >= 0 ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />}
                label={`N50: ${n50Change >= 0 ? '+' : ''}${n50Change.toLocaleString()} bp`}
                color={n50Change >= 0 ? "success" : "error"}
                variant="outlined"
              />
            </Tooltip>
            
            <Tooltip title="L50 is the number of contigs needed to reach N50 - lower is better">
              <Chip 
                icon={l50Change <= 0 ? <ArrowUpwardIcon /> : <ArrowDownwardIcon />}
                label={`L50: ${l50Change >= 0 ? '+' : ''}${l50Change.toLocaleString()}`}
                color={l50Change <= 0 ? "success" : "error"}
                variant="outlined"
              />
            </Tooltip>
          </Box>
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Removed Data
            </Typography>
            <Typography variant="body2">
              <strong>{sequencesRemoved.toLocaleString()}</strong> contigs removed
            </Typography>
            <Typography variant="body2">
              <strong>{lengthRemoved.toLocaleString()}</strong> bp removed
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default FilteringResultsSummary;