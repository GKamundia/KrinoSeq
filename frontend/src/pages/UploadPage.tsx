import React from 'react';
import { 
  Typography, 
  Paper, 
  Box, 
  Container,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import FileUpload from '../components/FileUpload';

const UploadPage: React.FC = () => {
  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        Upload FASTA File
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="body1" paragraph>
          Upload a FASTA file containing your genomic sequences for analysis and filtering.
        </Typography>
        
        <Divider sx={{ my: 2 }} />
        
        <Typography variant="subtitle1" gutterBottom>
          Supported Files:
        </Typography>
        <List dense>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="FASTA files (.fasta, .fa, .fna)" 
              secondary="Files containing DNA/RNA sequences" 
            />
          </ListItem>
        </List>
        
        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
          File Requirements:
        </Typography>
        <List dense>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="Valid FASTA format" 
              secondary="Each sequence must have a header line starting with '>' followed by sequence data" 
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <CheckCircleOutlineIcon color="success" />
            </ListItemIcon>
            <ListItemText 
              primary="Maximum file size: 100MB" 
              secondary="Larger files may cause performance issues" 
            />
          </ListItem>
        </List>
      </Paper>
      
      <FileUpload />
    </Container>
  );
};

export default UploadPage;