import React from 'react';
import { Outlet } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Container, 
  Box, 
  Link, 
  Button 
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const Layout: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography 
            variant="h6" 
            component={RouterLink} 
            to="/" 
            sx={{ 
              flexGrow: 1, 
              textDecoration: 'none', 
              color: 'inherit' 
            }}
          >
            Genome Filtering Tool
          </Typography>
          <Button color="inherit" component={RouterLink} to="/">Home</Button>
          <Button color="inherit" component={RouterLink} to="/upload">Upload</Button>
          <Button color="inherit" component={RouterLink} to="/about">About</Button>
        </Toolbar>
      </AppBar>
      
      <Container 
        component="main" 
        maxWidth="lg" 
        sx={{ 
          mt: 4, 
          mb: 4, 
          flexGrow: 1, 
          display: 'flex', 
          flexDirection: 'column' 
        }}
      >
        <Outlet />
      </Container>
      
      <Box 
        component="footer" 
        sx={{ 
          py: 3, 
          px: 2, 
          mt: 'auto', 
          backgroundColor: (theme) => theme.palette.grey[200]
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            Genome Filtering Tool &copy; {new Date().getFullYear()} - 
            <Link 
              color="inherit" 
              href="https://github.com/yourusername/genome-filtering-tool"
              sx={{ ml: 1 }}
            >
              GitHub
            </Link>
          </Typography>
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;