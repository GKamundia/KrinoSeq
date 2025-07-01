import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area
} from 'recharts';
import { Card, CardContent, Typography, Box, Tabs, Tab, Paper } from '@mui/material';
import { VisualizationData } from '../types/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index, ...other }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`chart-tabpanel-${index}`}
      aria-labelledby={`chart-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 2 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface LengthDistributionChartProps {
  data: VisualizationData;
  title?: string;
}

const LengthDistributionChart: React.FC<LengthDistributionChartProps> = ({ 
  data,
  title = 'Contig Length Distribution'
}) => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Add comprehensive null checking
  if (!data || !data.histogram || !data.histogram.bin_centers || !data.histogram.counts || data.histogram.bin_centers.length === 0) {
    return (
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6">{title}</Typography>
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            No distribution data available
          </Typography>
        </Box>
      </Paper>
    );
  }

  // Prepare data for histogram
  const histogramData = data.histogram.bin_centers.map((center, index) => ({
    length: center,
    count: data.histogram.counts[index] || 0  // Add fallback for missing counts
  }));

  // Prepare data for density plot
  const kdeData = data.kde.x.map((x, index) => ({
    length: x,
    density: data.kde.density[index]
  }));

  // Prepare data for cumulative plot
  const cumulativeData = data.cumulative.lengths.map((length, index) => ({
    length,
    percent: data.cumulative.cumulative_percent[index]
  })).filter((_, i) => i % 10 === 0); // Reduce points for better performance

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>{title}</Typography>
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="distribution charts">
            <Tab label="Histogram" id="chart-tab-0" aria-controls="chart-tabpanel-0" />
            <Tab label="Density" id="chart-tab-1" aria-controls="chart-tabpanel-1" />
            <Tab label="Cumulative" id="chart-tab-2" aria-controls="chart-tabpanel-2" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={histogramData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="length" 
                label={{ value: 'Contig Length (bp)', position: 'insideBottom', offset: -5 }} 
              />
              <YAxis 
                label={{ value: 'Count', angle: -90, position: 'insideLeft' }} 
              />
              <Tooltip formatter={(value: number) => [value.toLocaleString(), 'Contig']} labelFormatter={(label: number) => `Length: ${label.toLocaleString()} bp`} />
              <Legend />
              <Bar dataKey="count" fill="#1976d2" />
            </BarChart>
          </ResponsiveContainer>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={kdeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="length" 
                label={{ value: 'Contige Length (bp)', position: 'insideBottom', offset: -5 }} 
              />
              <YAxis 
                label={{ value: 'Density', angle: -90, position: 'insideLeft' }} 
              />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="density" 
                stroke="#82ca9d" 
                dot={false} 
                name="Density" 
              />
            </LineChart>
          </ResponsiveContainer>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={cumulativeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="length" 
                label={{ value: 'Contig Length (bp)', position: 'insideBottom', offset: -5 }} 
              />
              <YAxis 
                label={{ value: 'Cumulative %', angle: -90, position: 'insideLeft' }} 
              />
              <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="percent" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.3} 
                name="Cumulative %" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </TabPanel>
      </CardContent>
    </Card>
  );
};

export default LengthDistributionChart;