# KrinoSeq - Genome Sequence Filtering Tool

KrinoSeq is a bioinformatics tool for advanced length-based filtering of genomic sequences with quality assessment using QUAST (Quality Assessment Tool for Genome Assemblies).

## Cross-Platform Support

KrinoSeq now supports multiple operating systems:

- **Windows**: Uses WSL (Windows Subsystem for Linux) for running QUAST
- **macOS**: Uses native execution (no WSL required)
- **Linux**: Uses native execution (no WSL required)

## Quick Answer: Do I need WSL on macOS?

**No, you do not need WSL when working on a MacBook Pro M2.** WSL (Windows Subsystem for Linux) is a Windows-specific technology that allows running Linux environments on Windows systems. On macOS, which is already Unix-based, you can run bioinformatics tools like QUAST natively.

## Platform-Specific Setup

### macOS Setup (MacBook Pro M2)

1. **Install Python and pip** (if not already installed):
   ```bash
   # Using Homebrew (recommended)
   brew install python3
   
   # Or download from python.org
   ```

2. **Install QUAST** (choose one method):
   
   **Option A: Using pip**
   ```bash
   pip install quast
   ```
   
   **Option B: Using conda**
   ```bash
   conda install -c bioconda quast
   ```
   
   **Option C: Using Homebrew**
   ```bash
   brew install quast
   ```

3. **Verify QUAST installation**:
   ```bash
   quast.py --version
   ```

4. **Install Node.js** (for the frontend):
   ```bash
   brew install node
   ```

5. **Set up the project**:
   ```bash
   # Clone the repository
   git clone https://github.com/GKamundia/KrinoSeq.git
   cd KrinoSeq
   
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd frontend
   npm install
   ```

### Windows Setup

1. **Install WSL2**:
   ```cmd
   wsl --install
   ```

2. **Install QUAST in WSL**:
   ```bash
   # Open WSL terminal
   wsl
   
   # Install QUAST
   pip install quast
   # or
   conda install -c bioconda quast
   ```

3. **Verify QUAST installation**:
   ```bash
   quast.py --version
   ```

4. **Continue with Python and Node.js setup** as described in the macOS section.

### Linux Setup

1. **Install QUAST** (choose one method):
   ```bash
   # Using pip
   pip install quast
   
   # Using conda
   conda install -c bioconda quast
   
   # Using apt (Ubuntu/Debian)
   sudo apt update
   sudo apt install quast
   ```

2. **Verify installation and continue** as described in the macOS section.

## Running the Application

### Backend (API Server)

```bash
cd backend
python -m uvicorn api.main:app --reload --port 8000
```

### Frontend (React App)

```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Checking Platform Status

You can check your platform compatibility and QUAST installation status by visiting:
```
http://localhost:8000/platform
```

This endpoint will show:
- Current operating system information
- Whether WSL is required for your platform
- QUAST installation status
- Platform-specific setup recommendations

## Architecture

- **Frontend**: React/TypeScript application for the user interface
- **Backend**: Python FastAPI application for processing and analysis
- **Cross-platform execution**: Automatically detects your operating system and uses the appropriate execution method (WSL on Windows, native on macOS/Linux)

## Key Features

- **Length-based filtering** of genomic sequences
- **QUAST integration** for quality assessment
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Web-based interface** for easy interaction
- **RESTful API** for programmatic access

## Troubleshooting

### QUAST Not Found

If you get an error that QUAST is not found:

1. Verify QUAST is installed: `quast.py --version`
2. Check if it's in your PATH: `which quast.py`
3. Install QUAST using one of the methods above
4. Restart the backend server after installation

### Platform Detection Issues

If the application doesn't correctly detect your platform:

1. Check the platform status endpoint: `GET /platform`
2. Ensure you're using a supported Python version (3.7+)
3. Check the application logs for detailed error messages

### WSL Issues (Windows only)

If you encounter WSL-related issues on Windows:

1. Ensure WSL2 is installed and updated: `wsl --update`
2. Verify your Linux distribution is running: `wsl -l -v`
3. Test QUAST directly in WSL: `wsl quast.py --version`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on your platform
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.