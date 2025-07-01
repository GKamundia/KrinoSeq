# Genome Filtering Tool

A full-stack web application for advanced length-based filtering of genomic sequences.

## Features

- Upload FASTA files for analysis
- Advanced filtering with multiple algorithms
- Real-time progress tracking
- Statistical analysis and visualization
- Download filtered results

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React with TypeScript and Material-UI
- **Data Processing**: BioPython, NumPy, Pandas
- **Visualization**: Matplotlib, Recharts

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -r ../requirements.txt
python -m uvicorn api.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Deployment

This application is configured for easy deployment on platforms like Railway, Render, or Heroku.

### Railway Deployment

1. Push your code to GitHub
2. Connect your repository to Railway
3. Railway will automatically detect and deploy your FastAPI application

### Environment Variables

- `PORT`: Server port (automatically set by hosting platforms)
- `ENVIRONMENT`: Set to "production" for production deployment

## API Documentation

Once deployed, visit `/docs` for interactive API documentation.

## License

MIT License
