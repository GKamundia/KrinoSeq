import React, { useMemo } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent, 
  Typography, 
  Box, 
  Chip,
  useTheme,
  Divider
} from '@mui/material';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell, TooltipProps 
} from 'recharts';
import { QuastComparisonResult } from '../types/api';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

interface ChartData {
  name: string;
  original: number;
  filtered: number;
  percentChange: number;
  improved: boolean | undefined;
  formattedOriginal: string;
  formattedFiltered: string;
}

interface QuastComparisonChartProps {
  title?: string;
  originalAssembly: {
    name: string;
    metrics: Record<string, number | string>;
  };
  filteredAssembly: {
    name: string;
    metrics: Record<string, number | string>;
  };
  comparison?: QuastComparisonResult;
  metricKeys?: string[];
  showPercent?: boolean;
}

const formatLargeNumber = (value: number | string): string => {
  if (typeof value !== 'number') return String(value);
  
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toString();
};

const formatValue = (value: number | string): string => {
  if (typeof value === 'number') {
    if (value >= 10000) {
      return value.toLocaleString();
    }
    if (value % 1 !== 0) {
      return value.toFixed(2);
    }
  }
  return String(value);
};

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload as ChartData;
    
    return (
      <Box sx={{ bgcolor: 'background.paper', p: 2, boxShadow: 3, borderRadius: 1 }}>
        <Typography variant="subtitle2">{label}</Typography>
        <Divider sx={{ my: 1 }} />
        
        <Box display="flex" justifyContent="space-between" mb={0.5}>
          <Typography variant="body2" color="text.secondary">Original:</Typography>
          <Typography variant="body2">{data.formattedOriginal}</Typography>
        </Box>
        
        <Box display="flex" justifyContent="space-between" mb={0.5}>
          <Typography variant="body2" color="text.secondary">Filtered:</Typography>
          <Typography variant="body2">{data.formattedFiltered}</Typography>
        </Box>
        
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="body2" color="text.secondary">Change:</Typography>
          <Box display="flex" alignItems="center">
            {data.improved !== undefined && (
              data.improved ? 
                <CheckCircleOutlineIcon color="success" fontSize="small" sx={{ mr: 0.5 }} /> : 
                <ErrorOutlineIcon color="error" fontSize="small" sx={{ mr: 0.5 }} />
            )}
            <Typography 
              variant="body2" 
              color={
                data.improved === true ? 'success.main' : 
                data.improved === false ? 'error.main' : 
                'text.secondary'
              }
            >
              {data.percentChange >= 0 ? '+' : ''}{data.percentChange.toFixed(2)}%
            </Typography>
          </Box>
        </Box>
      </Box>
    );
  }
  return null;
};

// Custom tick component that handles text wrapping
const CustomYAxisTick = (props: any) => {
  const { x, y, payload } = props;
  
  // Split long text into multiple lines (adjust width as needed)
  const maxCharsPerLine = 20;
  const text = payload.value;
  
  // Simple word wrap logic
  const words = text.split(' ');
  const lines = [];
  let currentLine = '';
  
  words.forEach((word: string) => {
    if ((currentLine + ' ' + word).length <= maxCharsPerLine) {
      currentLine = currentLine ? currentLine + ' ' + word : word;
    } else {
      lines.push(currentLine);
      currentLine = word;
    }
  });
  
  if (currentLine) {
    lines.push(currentLine);
  }
  
  return (
    <g transform={`translate(${x},${y})`}>
      {lines.map((line, i) => (
        <text 
          key={i}
          x={-10} 
          y={i * 12} 
          dy={5}
          textAnchor="end"
          fontSize={10}
          fill="#666"
        >
          {line}
        </text>
      ))}
    </g>
  );
};

const QuastComparisonChart: React.FC<QuastComparisonChartProps> = ({ 
  title = "Assembly Comparison",
  originalAssembly, 
  filteredAssembly,
  comparison,
  metricKeys = ['# contigs', 'Total length', 'N50', 'L50'],
  showPercent = false
}) => {
  const theme = useTheme();
  
  // Prepare chart data from the metrics
  const chartData: ChartData[] = useMemo(() => {
    return metricKeys
      .filter(key => {
        const originalValue = originalAssembly.metrics[key];
        const filteredValue = filteredAssembly.metrics[key];
        return (
          originalValue !== undefined && 
          filteredValue !== undefined &&
          typeof originalValue === 'number' &&
          typeof filteredValue === 'number'
        );
      })
      .map(key => {
        const originalValue = originalAssembly.metrics[key] as number;
        const filteredValue = filteredAssembly.metrics[key] as number;
        const percentChange = originalValue !== 0 
          ? ((filteredValue - originalValue) / Math.abs(originalValue)) * 100 
          : 0;
          
        // Determine if the change is an improvement
        // Generally, higher N50 is better, but higher L50 is worse
        let improved: boolean | undefined;
        if (key.includes('N50') || key.includes('Genome fraction')) {
          improved = percentChange > 0;
        } else if (key.includes('L50') || key.includes('# contigs') || key.includes('misassembl')) {
          improved = percentChange < 0;
        } else {
          improved = comparison?.improvements?.[key];
        }
        
        return {
          name: key,
          original: originalValue,
          filtered: filteredValue,
          percentChange,
          improved,
          formattedOriginal: formatValue(originalValue),
          formattedFiltered: formatValue(filteredValue)
        };
      });
  }, [originalAssembly, filteredAssembly, metricKeys, comparison]);
  
  // Calculate overall improvement score
  const hasImprovementData = comparison?.overall_improvement_score !== undefined;
  const improvementScore = comparison?.overall_improvement_score || 0;
  const isOverallImproved = comparison?.overall_improved || false;
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader 
        title={title} 
        titleTypographyProps={{ variant: 'h6' }}
        action={
          hasImprovementData && (
            <Chip 
              icon={isOverallImproved ? <CheckCircleOutlineIcon /> : <ErrorOutlineIcon />}
              label={`Overall ${isOverallImproved ? 'Improved' : 'Degraded'}`}
              color={isOverallImproved ? 'success' : 'error'}
              variant="outlined"
            />
          )
        }
      />
      <CardContent>
        {hasImprovementData && (
          <Box mb={2} display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="body2" color="text.secondary">
              Improvement score: {(improvementScore * 100).toFixed(1)}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {comparison?.positive_metric_count} improved / {comparison?.negative_metric_count} degraded
            </Typography>
          </Box>
        )}
        
        <Box height={350}>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                barSize={30}
                layout="vertical"
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis
                  type="number"
                  tickFormatter={showPercent ? (value) => `${value}%` : formatLargeNumber}
                />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={120}
                  tick={<CustomYAxisTick />} // Use custom tick component instead of wordWrap
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {showPercent ? (
                  <Bar 
                    dataKey="percentChange" 
                    name="Percent Change" 
                    fill={theme.palette.primary.main}
                  >
                    {chartData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={
                          entry.improved === true ? theme.palette.success.main : 
                          entry.improved === false ? theme.palette.error.main : 
                          theme.palette.grey[500]
                        }
                      />
                    ))}
                  </Bar>
                ) : (
                  <>
                    <Bar dataKey="original" name={originalAssembly.name} fill={theme.palette.info.main} />
                    <Bar dataKey="filtered" name={filteredAssembly.name} fill={theme.palette.success.main} />
                  </>
                )}
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <Box display="flex" alignItems="center" justifyContent="center" height="100%">
              <Typography variant="body2" color="text.secondary">
                No comparable metrics available
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default QuastComparisonChart;