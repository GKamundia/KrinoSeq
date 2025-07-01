import React from 'react';
import { Card, CardContent, Typography, Grid, Divider } from '@mui/material';
import { BasicStats, AssemblyStats } from '../types/api';

interface SequenceStatsCardProps {
  title: string;
  sequenceCount?: number;
  basicStats?: BasicStats;
  assemblyStats?: AssemblyStats;
}

const SequenceStatsCard: React.FC<SequenceStatsCardProps> = ({
  title,
  sequenceCount = 0,
  basicStats,
  assemblyStats
}) => {
  // Create safe versions of the stats objects with defaults
  const stats = basicStats || {
    min: 0,
    max: 0,
    mean: 0,
    median: 0,
    std_dev: 0,
    total: 0,
    count: 0
  };
  
  const assembly = assemblyStats || {
    n50: 0,
    l50: 0
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Contig Count</Typography>
            <Typography variant="body1">{sequenceCount.toLocaleString()}</Typography>
            
            <Divider sx={{ my: 1 }} />
            
            <Typography variant="subtitle2">Length Statistics</Typography>
            <Typography variant="body2">
              Total Length: {stats.total.toLocaleString()} bp
            </Typography>
            <Typography variant="body2">
              Min: {stats.min.toLocaleString()} bp
            </Typography>
            <Typography variant="body2">
              Max: {stats.max.toLocaleString()} bp
            </Typography>
            <Typography variant="body2">
              Mean: {stats.mean.toFixed(2)} bp
            </Typography>
            <Typography variant="body2">
              Median: {stats.median.toLocaleString()} bp
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Assembly Statistics</Typography>
            <Typography variant="body2">
              N50: {assembly.n50.toLocaleString()} bp
            </Typography>
            <Typography variant="body2">
              L50: {assembly.l50.toLocaleString()} contigs
            </Typography>
            
            <Divider sx={{ my: 1 }} />
            
            <Typography variant="subtitle2">Variability</Typography>
            <Typography variant="body2">
              Std Dev: {stats.std_dev.toFixed(2)} bp
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SequenceStatsCard;