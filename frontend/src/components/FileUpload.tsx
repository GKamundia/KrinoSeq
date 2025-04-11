import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Box, 
  CircularProgress, 
  Paper, 
  Typography, 
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Button
} from '@mui/material';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import DeleteIcon from '@mui/icons-material/Delete';
import { uploadFasta } from '../services/api';
import { useNavigate } from 'react-router-dom';

const FileUpload: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Only keep FASTA files
    const fastaFiles = acceptedFiles.filter(file => 
      file.name.endsWith('.fasta') || 
      file.name.endsWith('.fa') || 
      file.name.endsWith('.fna')
    );

    if (fastaFiles.length === 0) {
      setError('Please upload FASTA files (.fasta, .fa, or .fna)');
      return;
    }

    setError(null);
    setFiles(fastaFiles);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/fasta': ['.fasta', '.fa', '.fna']
    },
    maxFiles: 1
  });

  const handleRemoveFile = (index: number) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select a file to upload');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const response = await uploadFasta(files[0]);
      // Navigate to the configuration page with the job ID
      navigate(`/configure/${response.job_id}`);
    } catch (err: any) {
      console.error('Upload error:', err);
      // More detailed error message
      if (err.response && err.response.data) {
        setError(`Upload failed: ${err.response.data.detail || 'Server error'}`);
      } else {
        setError('An error occurred during upload. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ width: '100%', mt: 3 }}>
      <Paper
        {...getRootProps()}
        sx={{
          p: 3,
          textAlign: 'center',
          borderStyle: 'dashed',
          borderWidth: 2,
          borderColor: theme => isDragActive ? theme.palette.primary.main : theme.palette.grey[300],
          bgcolor: theme => isDragActive ? 'rgba(25, 118, 210, 0.08)' : 'background.paper',
          cursor: 'pointer',
          '&:hover': {
            borderColor: theme => theme.palette.primary.main,
            bgcolor: 'rgba(25, 118, 210, 0.04)'
          }
        }}
      >
        <input {...getInputProps()} />
        <FileUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop the files here...' : 'Drag & drop FASTA files here'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          or click to select files (.fasta, .fa, .fna)
        </Typography>
      </Paper>

      {files.length > 0 && (
        <List sx={{ mt: 2 }}>
          {files.map((file, index) => (
            <ListItem
              key={index}
              secondaryAction={
                <IconButton 
                  edge="end" 
                  aria-label="delete"
                  onClick={() => handleRemoveFile(index)}
                  disabled={uploading}
                >
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemIcon>
                <InsertDriveFileIcon />
              </ListItemIcon>
              <ListItemText
                primary={file.name}
                secondary={`${(file.size / 1024 / 1024).toFixed(2)} MB`}
              />
            </ListItem>
          ))}
        </List>
      )}

      {error && (
        <Typography color="error" sx={{ mt: 2 }}>
          {error}
        </Typography>
      )}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={files.length === 0 || uploading}
          startIcon={<FileUploadIcon />}
          size="large"
        >
          Upload
        </Button>
      </Box>
    </Box>
  );
};

export default FileUpload;