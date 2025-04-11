import React from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Container,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const AboutPage: React.FC = () => {
  return (
    <Container>
      <Typography variant="h4" component="h1" gutterBottom>
        About the Genome Filtering Tool
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" paragraph>
          The Genome Filtering Tool is an advanced platform for filtering genomic sequences 
          based on their length characteristics. It provides multiple sophisticated filtering 
          algorithms designed to help researchers improve the quality of their genome assemblies 
          by removing problematic sequences.
        </Typography>
        
        <Typography variant="body1" paragraph>
          This tool is particularly useful for:
        </Typography>
        
        <ul>
          <li>
            <Typography variant="body1">
              Cleaning up draft genome assemblies
            </Typography>
          </li>
          <li>
            <Typography variant="body1">
              Removing short contigs that may represent assembly artifacts
            </Typography>
          </li>
          <li>
            <Typography variant="body1">
              Improving N50 and other assembly metrics for downstream analysis
            </Typography>
          </li>
          <li>
            <Typography variant="body1">
              Identifying natural size distribution patterns in sequence data
            </Typography>
          </li>
        </ul>
      </Paper>
      
      <Typography variant="h5" gutterBottom>
        Filtering Methods Explained
      </Typography>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Adaptive Filtering</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" paragraph>
            Adaptive filtering automatically analyzes your data's characteristics and 
            applies the most appropriate filtering method. The algorithm examines the 
            distribution shape, identifies skewness and kurtosis, and selects between 
            IQR and Z-score methods with optimized parameters.
          </Typography>
          <Typography variant="body2">
            <strong>Best for:</strong> General purpose filtering when you're unsure which 
            method to choose, or for batch processing of multiple files with different 
            characteristics.
          </Typography>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Min/Max Length Filtering</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" paragraph>
            The simplest filtering approach that removes sequences shorter than a minimum 
            threshold and/or longer than a maximum threshold. You can specify either or 
            both thresholds.
          </Typography>
          <Typography variant="body2">
            <strong>Best for:</strong> Simple filtering tasks where you have specific 
            size requirements for downstream applications.
          </Typography>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">IQR-based Outlier Filtering</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" paragraph>
            Uses the Interquartile Range (IQR) statistical method to identify and remove 
            outlier sequences. Sequences with lengths below Q1 - k*IQR or above Q3 + k*IQR 
            are considered outliers, where k is a multiplier (typically 1.5).
          </Typography>
          <Typography variant="body2">
            <strong>Best for:</strong> Data with non-normal distributions or in the presence 
            of extreme outliers. More robust than Z-score for skewed distributions.
          </Typography>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Z-score Outlier Filtering</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" paragraph>
            Identifies outliers using Z-scores, which measure how many standard deviations 
            a value is from the mean. Sequences with Z-scores beyond a specified threshold 
            (typically 2.5 or 3.0) are considered outliers.
          </Typography>
          <Typography variant="body2">
            <strong>Best for:</strong> Normally distributed data where extreme values are rare.
          </Typography>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">N50 Optimization</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" paragraph>
            This method finds the minimum length cutoff that maximizes the N50 assembly metric. 
            N50 is a weighted median statistic such that 50% of the entire assembly is contained 
            in contigs longer than or equal to this value.
          </Typography>
          <Typography variant="body2">
            <strong>Best for:</strong> Optimizing genome assemblies for publication or 
            downstream analysis where N50 is an important quality metric.
          </Typography>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="subtitle1">Natural Breakpoint Detection</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" paragraph>
            Analyzes the sequence length distribution to identify natural breakpoints or 
            clusters. This method uses Gaussian Mixture Models, peak/valley detection, and 
            density analysis to find natural cutoffs in multimodal distributions.
          </Typography>
          <Typography variant="body2">
            <strong>Best for:</strong> Datasets with distinct populations of sequences, 
            such as mixed assemblies or metagenomes.
          </Typography>
        </AccordionDetails>
      </Accordion>
      
      <Box sx={{ mt: 4 }}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary" align="center">
          Genome Filtering Tool v1.0.0 - Created by Your Name/Organization
        </Typography>
      </Box>
    </Container>
  );
};

export default AboutPage;