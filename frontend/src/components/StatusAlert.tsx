import React from 'react';
import { Alert, AlertTitle, CircularProgress, Box, LinearProgress, Typography } from '@mui/material';
import { JobStatus } from '../types/api';

interface StatusAlertProps {
  status: JobStatus;
  message?: string;
  progress?: number;
}

const StatusAlert: React.FC<StatusAlertProps> = ({ status, message, progress }) => {
  switch (status) {
    case JobStatus.PENDING:
      return (
        <Alert severity="info" icon={<CircularProgress size={24} />}>
          <AlertTitle>Pending</AlertTitle>
          {message || 'Your request is pending...'}
        </Alert>
      );
    case JobStatus.PROCESSING:
      return (
        <Alert severity="info" icon={<CircularProgress size={24} />}>
          <AlertTitle>Processing</AlertTitle>
          {message || 'Processing your request...'}
          {progress !== undefined && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <Box sx={{ width: '100%', mr: 1 }}>
                <LinearProgress variant="determinate" value={progress * 100} />
              </Box>
              <Box sx={{ minWidth: 35 }}>
                <Typography variant="body2" color="text.secondary">
                  {Math.round(progress * 100)}%
                </Typography>
              </Box>
            </Box>
          )}
        </Alert>
      );
    case JobStatus.COMPLETED:
      return (
        <Alert severity="success">
          <AlertTitle>Completed</AlertTitle>
          {message || 'Your request has been completed successfully.'}
        </Alert>
      );
    case JobStatus.FAILED:
      return (
        <Alert severity="error">
          <AlertTitle>Failed</AlertTitle>
          {message || 'Your request has failed. Please try again.'}
        </Alert>
      );
    default:
      return null;
  }
};

export default StatusAlert;