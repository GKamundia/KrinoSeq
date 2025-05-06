import React from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  Typography, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Box,
  Tooltip,
  Chip,
  IconButton
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { QuastMetric } from '../types/api';

interface MetricsGroupData {
  title: string;
  metrics: QuastMetric[];
}

interface QuastMetricsCardProps {
  title: string;
  assemblyName?: string;
  metrics?: Record<string, any>;
  metricGroups?: MetricsGroupData[];
  comparison?: boolean;
  description?: string;
  improved?: Record<string, boolean>;
  percentChange?: Record<string, number>;
}

const formatMetricValue = (value: any): string => {
  if (typeof value === 'number') {
    // Format percentage with 2 decimal places
    if (value > 0 && value < 1) {
      return (value * 100).toFixed(2) + '%';
    }
    // Format large numbers with commas
    else if (Math.abs(value) >= 10000) {
      return value.toLocaleString();
    }
    // Format floating point numbers with 2 decimal places
    else if (value % 1 !== 0) {
      return value.toFixed(2);
    }
    // Return integers as is
    return value.toString();
  }
  return value?.toString() || '-';
};

const QuastMetricsCard: React.FC<QuastMetricsCardProps> = ({
  title,
  assemblyName,
  metrics,
  metricGroups,
  comparison = false,
  description,
  improved,
  percentChange
}) => {
  // If we have raw metrics, convert them to groups
  const metricGroupsToRender = metricGroups || (metrics ? 
    [{
      title: 'Metrics',
      metrics: Object.entries(metrics).map(([key, value]) => ({
        name: key,
        value,
        is_better: improved ? improved[key] : undefined
      }))
    }] : []);

  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardHeader 
        title={title}
        subheader={assemblyName && <Typography variant="body2" color="text.secondary">{assemblyName}</Typography>}
        titleTypographyProps={{ variant: 'h6' }}
        action={
          description && (
            <Tooltip title={description}>
              <IconButton size="small">
                <InfoOutlinedIcon />
              </IconButton>
            </Tooltip>
          )
        }
      />
      <CardContent>
        {metricGroupsToRender.length > 0 ? (
          metricGroupsToRender.map((group, groupIndex) => (
            <Box key={`group-${groupIndex}`} mb={groupIndex < metricGroupsToRender.length - 1 ? 3 : 0}>
              {group.title !== 'Metrics' && (
                <Typography variant="subtitle2" gutterBottom color="text.secondary">
                  {group.title}
                </Typography>
              )}
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell align="right">Value</TableCell>
                      {comparison && <TableCell align="right">Change</TableCell>}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {group.metrics.map((metric, idx) => {
                      const pctChange = percentChange?.[metric.name];
                      const isImproved = metric.is_better;
                      
                      return (
                        <TableRow key={`metric-${idx}`} hover>
                          <TableCell 
                            component="th" 
                            scope="row"
                            sx={{ 
                              maxWidth: '180px', 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            <Tooltip title={metric.name}>
                              <span>{metric.name}</span>
                            </Tooltip>
                          </TableCell>
                          <TableCell align="right">
                            {formatMetricValue(metric.value)}
                          </TableCell>
                          {comparison && (
                            <TableCell align="right">
                              {pctChange !== undefined && (
                                <Box display="flex" alignItems="center" justifyContent="flex-end">
                                  {isImproved === true && <TrendingUpIcon color="success" fontSize="small" />}
                                  {isImproved === false && <TrendingDownIcon color="error" fontSize="small" />}
                                  {isImproved === undefined && <TrendingFlatIcon color="action" fontSize="small" />}
                                  <Typography 
                                    variant="body2" 
                                    color={
                                      isImproved === true ? 'success.main' : 
                                      isImproved === false ? 'error.main' : 
                                      'text.secondary'
                                    }
                                    ml={0.5}
                                  >
                                    {pctChange >= 0 ? '+' : ''}{pctChange.toFixed(1)}%
                                  </Typography>
                                </Box>
                              )}
                            </TableCell>
                          )}
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">
            No metrics available
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default QuastMetricsCard;