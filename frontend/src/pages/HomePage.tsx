import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Container,
  Grid,
  Card,
  CardContent,
  CardActions,
  Divider
} from '@mui/material';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import TuneIcon from '@mui/icons-material/Tune';
import BarChartIcon from '@mui/icons-material/BarChart';
import InfoIcon from '@mui/icons-material/Info';

const HomePage: React.FC = () => {
  return (
    <Container>
      <Box sx={{ 
        textAlign: 'center', 
        py: 8,
        background: 'linear-gradient(120deg, #e0f7fa 0%, #bbdefb 100%)',
        borderRadius: 2,
        mb: 4
      }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Genome Filtering Tool
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Advanced length-based filtering for genomic sequences
        </Typography>
        <Button
          component={RouterLink}
          to="/upload"
          variant="contained"
          size="large"
          startIcon={<FileUploadIcon />}
          sx={{ mt: 2 }}
        >
          Upload FASTA File
        </Button>
      </Box>
      
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        How It Works
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <FileUploadIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                1. Upload
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upload your FASTA file containing genomic sequences. The system will analyze 
                sequence length distributions and prepare statistics.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={RouterLink} to="/upload">
                Upload File
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <TuneIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                2. Configure
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Choose from multiple filtering methods including statistical 
                outlier detection, N50 optimization, and natural breakpoint analysis.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ textAlign: 'center', mb: 2 }}>
                <BarChartIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              </Box>
              <Typography variant="h6" gutterBottom>
                3. Analyze Results
              </Typography>
              <Typography variant="body2" color="text.secondary">
                View comprehensive before/after statistics, visualize length 
                distributions, and download your filtered sequences in FASTA format.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Available Filtering Methods
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>Adaptive Filtering</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Automatically selects the best filtering method based on your data's characteristics.
            </Typography>
            
            <Typography variant="subtitle1" gutterBottom>
              <strong>Min/Max Filtering</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Simple filtering by minimum and maximum sequence lengths.
            </Typography>
            
            <Typography variant="subtitle1" gutterBottom>
              <strong>Statistical Outlier Detection</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Removes outliers using IQR or Z-score methods.
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              <strong>N50 Optimization</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Finds the optimal length cutoff that maximizes the N50 assembly metric.
            </Typography>
            
            <Typography variant="subtitle1" gutterBottom>
              <strong>Natural Breakpoint Detection</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Identifies natural breakpoints in sequence length distribution.
            </Typography>
            
            <Typography variant="subtitle1" gutterBottom>
              <strong>Multi-stage Filtering</strong>
            </Typography>
            <Typography variant="body2" paragraph>
              Combine multiple filtering methods in sequence for advanced filtering.
            </Typography>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
          <Button 
            variant="outlined" 
            component={RouterLink} 
            to="/about"
            startIcon={<InfoIcon />}
          >
            Learn More About Filtering Methods
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default HomePage;