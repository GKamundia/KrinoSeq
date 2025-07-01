import React, { useState } from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  Accordion, 
  AccordionSummary, 
  AccordionDetails,
  Divider,
  Tabs,
  Tab
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import IQRDetailsChart from './process-charts/IQRDetailsChart';
import ZScoreDetailsChart from './process-charts/ZScoreDetailsChart';
import GMMDetailsChart from './process-charts/GMMDetailsChart';
import N50OptimizationChart from './process-charts/N50OptimizationChart';
import AdaptiveDetailsChart from './process-charts/AdaptiveDetailsChart';
import MinMaxDetailsChart from './process-charts/MinMaxDetailsChart';
import FilteringImpactChart from './process-charts/FilteringImpactChart';

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
      id={`filter-process-tabpanel-${index}`}
      aria-labelledby={`filter-process-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface FilteringProcessDetailsProps {
  filteringProcess: any[];
}

const FilteringProcessDetails: React.FC<FilteringProcessDetailsProps> = ({ filteringProcess }) => {
  const [expandedStage, setExpandedStage] = useState<string | false>('stage-0');
  const [activeTab, setActiveTab] = useState(0);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpandedStage(isExpanded ? panel : false);
  };
  
  if (!filteringProcess || filteringProcess.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1">No filtering process details available</Typography>
      </Paper>
    );
  }
  
  const renderFilterDetails = (stage: any, index: number) => {
    const { method, process_details } = stage;
    
    switch (method) {
      case 'iqr':
        return <IQRDetailsChart details={process_details?.iqr_details} outliers={process_details?.outliers} />;
        
      case 'zscore':
        return <ZScoreDetailsChart details={process_details?.zscore_details} outliers={process_details?.outliers} />;
        
      case 'natural':
        return <GMMDetailsChart details={process_details?.natural_breakpoint_details} />;
        
      case 'n50_optimize':
        return <N50OptimizationChart details={process_details?.n50_optimize_details} />;
        
      case 'adaptive':
        return <AdaptiveDetailsChart details={process_details?.adaptive_details} />;
        
      case 'min_max':
        return <MinMaxDetailsChart details={process_details} />;
        
      default:
        return (
          <Box sx={{ p: 2 }}>
            <Typography variant="body1">
              Detailed visualization not available for this filter method.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Method: {method}
            </Typography>
          </Box>
        );
    }
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Filtering Process Details
      </Typography>
      
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 2 }}>
        <Tab label="Stage by Stage" />
        <Tab label="Filtering Impact" />
      </Tabs>
      
      <TabPanel value={activeTab} index={0}>
        {filteringProcess.map((stage, index) => (
          <Accordion 
            key={`stage-${index}`} 
            expanded={expandedStage === `stage-${index}`}
            onChange={handleAccordionChange(`stage-${index}`)}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1">
                Stage {index + 1}: {getMethodDisplayName(stage.method)}
              </Typography>
            </AccordionSummary>
            
            <AccordionDetails>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Sequences before: {stage.sequences_before?.toLocaleString() || "0"} | 
                  Sequences after: {stage.sequences_after?.toLocaleString() || "0"} | 
                  Reduction: {(stage.reduction_percent || 0).toFixed(1)}%
                </Typography>
                
                <Divider sx={{ my: 2 }} />
                
                {renderFilterDetails(stage, index)}
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
      </TabPanel>
      
      <TabPanel value={activeTab} index={1}>
        {/* Visualization showing filtering impact across all stages */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Sequence Count Reduction Through Pipeline
          </Typography>
          <FilteringImpactChart filteringProcess={filteringProcess} />
        </Paper>
      </TabPanel>
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

export default FilteringProcessDetails;