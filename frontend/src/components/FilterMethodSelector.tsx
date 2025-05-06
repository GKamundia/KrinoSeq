import React, { useState, useRef, ChangeEvent } from 'react';
import { 
  Box, 
  Typography, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField, 
  Button,
  IconButton,
  Paper,
  Grid,
  Tooltip,
  FormHelperText,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  FormGroup,
  FormLabel,
  RadioGroup,
  Radio,
  Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import HelpIcon from '@mui/icons-material/Help';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AssessmentIcon from '@mui/icons-material/Assessment';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import { FieldArray, useFormikContext } from 'formik';
import { FilterMethod, FilterPipelineConfig, QuastOptions } from '../types/api';
import { uploadReferenceGenome } from '../services/api';

interface ExtendedFilterPipelineConfig extends FilterPipelineConfig {
  quastOptions?: QuastOptions;
  jobId?: string;
}

const methodDescriptions: Record<FilterMethod, string> = {
  [FilterMethod.MIN_MAX]: 'Simple filtering by minimum and/or maximum sequence length.',
  [FilterMethod.IQR]: 'Filter outliers based on interquartile range (IQR) statistical method.',
  [FilterMethod.ZSCORE]: 'Filter outliers based on Z-score statistical method.',
  [FilterMethod.ADAPTIVE]: 'Automatically select the best filtering method based on data characteristics.',
  [FilterMethod.N50_OPTIMIZE]: 'Optimize sequence filtering to maximize the N50 assembly metric.',
  [FilterMethod.NATURAL]: 'Identify natural breakpoints in the length distribution.'
};

const FilterMethodSelector: React.FC = () => {
  const { values, errors, touched, handleChange, setFieldValue } = useFormikContext<ExtendedFilterPipelineConfig>();
  const [referenceGenomeFile, setReferenceGenomeFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<{success?: boolean; message?: string}>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const renderMethodParameters = (method: FilterMethod, index: number) => {
    switch (method) {
      case FilterMethod.MIN_MAX:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name={`stages.${index}.params.min_length`}
                label="Minimum Length"
                type="number"
                value={values.stages[index].params?.min_length || ''}
                onChange={handleChange}
                helperText="Minimum sequence length to keep (optional)"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name={`stages.${index}.params.max_length`}
                label="Maximum Length"
                type="number"
                value={values.stages[index].params?.max_length || ''}
                onChange={handleChange}
                helperText="Maximum sequence length to keep (optional)"
              />
            </Grid>
          </Grid>
        );
        
      case FilterMethod.IQR:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name={`stages.${index}.params.k`}
                label="IQR Multiplier (k)"
                type="number"
                inputProps={{ step: 0.1, min: 0.1, max: 10 }}
                value={values.stages[index].params?.k || 1.5}
                onChange={handleChange}
                helperText="Multiplier for IQR (default: 1.5)"
              />
            </Grid>
          </Grid>
        );
        
      case FilterMethod.ZSCORE:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                name={`stages.${index}.params.threshold`}
                label="Z-score Threshold"
                type="number"
                inputProps={{ step: 0.1, min: 0.1, max: 10 }}
                value={values.stages[index].params?.threshold || 2.5}
                onChange={handleChange}
                helperText="Z-score threshold for outliers (default: 2.5)"
              />
            </Grid>
          </Grid>
        );
        
      case FilterMethod.N50_OPTIMIZE:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                name={`stages.${index}.params.min_cutoff`}
                label="Min Cutoff"
                type="number"
                value={values.stages[index].params?.min_cutoff || ''}
                onChange={handleChange}
                helperText="Minimum cutoff to consider (optional)"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                name={`stages.${index}.params.max_cutoff`}
                label="Max Cutoff"
                type="number"
                value={values.stages[index].params?.max_cutoff || ''}
                onChange={handleChange}
                helperText="Maximum cutoff to consider (optional)"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                name={`stages.${index}.params.step`}
                label="Step Size"
                type="number"
                value={values.stages[index].params?.step || 10}
                onChange={handleChange}
                helperText="Step size for search (default: 10)"
              />
            </Grid>
          </Grid>
        );
        
      case FilterMethod.NATURAL:
        return (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id={`gmm-method-label-${index}`}>GMM Cutoff Method</InputLabel>
                <Select
                  labelId={`gmm-method-label-${index}`}
                  name={`stages.${index}.params.gmm_method`}
                  value={values.stages[index].params?.gmm_method || 'midpoint'}
                  label="GMM Cutoff Method"
                  onChange={handleChange}
                >
                  <MenuItem value="midpoint">Midpoint between components</MenuItem>
                  <MenuItem value="intersection">Intersection point (weighted PDFs)</MenuItem>
                  <MenuItem value="probability">Probability threshold (0.5)</MenuItem>
                  <MenuItem value="valley">Valley finding (minimum density)</MenuItem>
                </Select>
                <FormHelperText>
                  Method to determine cutoff point between adjacent components
                </FormHelperText>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id={`transform-label-${index}`}>Transformation</InputLabel>
                <Select
                  labelId={`transform-label-${index}`}
                  name={`stages.${index}.params.transform`}
                  value={values.stages[index].params?.transform || 'box-cox'}
                  label="Transformation"
                  onChange={handleChange}
                >
                  <MenuItem value="box-cox">Box-Cox (Best for genomic data)</MenuItem>
                  <MenuItem value="log">Log Transform</MenuItem>
                  <MenuItem value="none">No transformation</MenuItem>
                </Select>
                <FormHelperText>
                  Data transformation to normalize skewed distributions
                </FormHelperText>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id={`component-method-label-${index}`}>Component Selection</InputLabel>
                <Select
                  labelId={`component-method-label-${index}`}
                  name={`stages.${index}.params.component_method`}
                  value={values.stages[index].params?.component_method || 'bic'}
                  label="Component Selection"
                  onChange={handleChange}
                >
                  <MenuItem value="bic">BIC (Bayesian Information Criterion)</MenuItem>
                  <MenuItem value="aic">AIC (Akaike Information Criterion)</MenuItem>
                  <MenuItem value="loo">PSIS-LOO (Cross-validation approximation)</MenuItem>
                  <MenuItem value="dirichlet">Dirichlet Process (Automatic)</MenuItem>
                </Select>
                <FormHelperText>
                  <strong>Note:</strong> This selects how to determine the number of clusters, 
                  not where to place the cutoff (which is set by GMM Cutoff Method)
                </FormHelperText>
              </FormControl>
            </Grid>
          </Grid>
        );
        
      default:
        return (
          <Typography variant="body2" color="text.secondary">
            No parameters required for this method.
          </Typography>
        );
    }
  };

  const handleReferenceGenomeUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files || event.target.files.length === 0) return;
    
    const file = event.target.files[0];
    setReferenceGenomeFile(file);
    
    if (values.jobId) {
      try {
        setUploadStatus({ message: "Uploading reference genome..." });
        const result = await uploadReferenceGenome(values.jobId, file);
        
        if (result) {
          setUploadStatus({ 
            success: true, 
            message: `Reference genome '${file.name}' uploaded successfully` 
          });
          setFieldValue('quastOptions.reference_genome', result.reference_genome);
        }
      } catch (error) {
        setUploadStatus({ 
          success: false, 
          message: `Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}` 
        });
      }
    } else {
      setUploadStatus({ 
        message: "Reference genome will be uploaded when filtering starts" 
      });
    }
  };

  const renderQuastOptions = () => {
    const quastOptions = values.quastOptions || {};
    
    return (
      <Accordion defaultExpanded={false} sx={{ mt: 3 }}>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="quast-options-content"
          id="quast-options-header"
        >
          <Box display="flex" alignItems="center">
            <AssessmentIcon sx={{ mr: 1 }} />
            <Typography variant="subtitle1">QUAST Quality Assessment Options</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" paragraph>
            QUAST analyzes your assemblies and provides quality metrics. Configure options below to customize the analysis.
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Reference Genome (Optional)
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12}>
              <Box display="flex" alignItems="center">
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<FileUploadIcon />}
                  size="small"
                >
                  Select Reference Genome
                  <input
                    ref={fileInputRef}
                    type="file"
                    hidden
                    accept=".fa,.fasta,.fna"
                    onChange={handleReferenceGenomeUpload}
                  />
                </Button>
                <Box ml={2}>
                  <Typography variant="body2">
                    {referenceGenomeFile 
                      ? `Selected: ${referenceGenomeFile.name}` 
                      : 'No reference genome selected'}
                  </Typography>
                </Box>
              </Box>
              
              {uploadStatus.message && (
                <Alert 
                  severity={uploadStatus.success ? "success" : "info"} 
                  sx={{ mt: 1 }}
                >
                  {uploadStatus.message}
                </Alert>
              )}
              
              <FormHelperText>
                A reference genome enables additional quality metrics like genome fraction and misassembly detection.
              </FormHelperText>
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Basic Options
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Minimum Contig Length"
                name="quastOptions.min_contig"
                type="number"
                value={quastOptions.min_contig || 500}
                onChange={handleChange}
                InputProps={{ inputProps: { min: 0 } }}
                helperText="Minimum contig length to report"
                size="small"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Thread Count"
                name="quastOptions.threads"
                type="number"
                value={quastOptions.threads || 4}
                onChange={handleChange}
                InputProps={{ inputProps: { min: 1, max: 32 } }}
                helperText="Number of threads to use"
                size="small"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Min Alignment"
                name="quastOptions.min_alignment"
                type="number"
                value={quastOptions.min_alignment || 65}
                onChange={handleChange}
                InputProps={{ inputProps: { min: 0 } }}
                helperText="Minimum alignment length"
                size="small"
              />
            </Grid>
          </Grid>
          
          <Box mt={2}>
            <FormGroup row>
              <FormControlLabel
                control={
                  <Switch
                    checked={quastOptions.gene_finding !== false}
                    onChange={(e) => setFieldValue('quastOptions.gene_finding', e.target.checked)}
                    name="quastOptions.gene_finding"
                    color="primary"
                  />
                }
                label="Gene Finding"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={quastOptions.conserved_genes_finding !== false}
                    onChange={(e) => setFieldValue('quastOptions.conserved_genes_finding', e.target.checked)}
                    name="quastOptions.conserved_genes_finding"
                    color="primary"
                  />
                }
                label="Conserved Genes Finding"
              />
            </FormGroup>
          </Box>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Genome Type
          </Typography>
          
          <FormControl component="fieldset">
            <RadioGroup 
              row 
              name="genome-type" 
              value={
                quastOptions.large_genome ? "large_genome" :
                quastOptions.eukaryote ? "eukaryote" :
                quastOptions.fungus ? "fungus" :
                quastOptions.prokaryote ? "prokaryote" :
                quastOptions.metagenome ? "metagenome" :
                "auto"
              }
              onChange={(e) => {
                setFieldValue('quastOptions.large_genome', false);
                setFieldValue('quastOptions.eukaryote', false);
                setFieldValue('quastOptions.fungus', false);
                setFieldValue('quastOptions.prokaryote', false);
                setFieldValue('quastOptions.metagenome', false);
                
                if (e.target.value !== "auto") {
                  setFieldValue(`quastOptions.${e.target.value}`, true);
                }
              }}
            >
              <FormControlLabel value="auto" control={<Radio />} label="Auto" />
              <FormControlLabel value="prokaryote" control={<Radio />} label="Prokaryote" />
              <FormControlLabel value="eukaryote" control={<Radio />} label="Eukaryote" />
              <FormControlLabel value="fungus" control={<Radio />} label="Fungus" />
              <FormControlLabel value="large_genome" control={<Radio />} label="Large Genome" />
              <FormControlLabel value="metagenome" control={<Radio />} label="Metagenome" />
            </RadioGroup>
          </FormControl>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="subtitle2" gutterBottom>
            Advanced Options
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel id="plots-format-label">Plots Format</InputLabel>
                <Select
                  labelId="plots-format-label"
                  name="quastOptions.plots_format"
                  value={quastOptions.plots_format || "png"}
                  label="Plots Format"
                  onChange={handleChange}
                >
                  <MenuItem value="png">PNG (Default)</MenuItem>
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="ps">PS</MenuItem>
                </Select>
                <FormHelperText>Format for generated plots</FormHelperText>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel id="ambiguity-usage-label">Ambiguity Usage</InputLabel>
                <Select
                  labelId="ambiguity-usage-label"
                  name="quastOptions.ambiguity_usage"
                  value={quastOptions.ambiguity_usage || "one"}
                  label="Ambiguity Usage"
                  onChange={handleChange}
                >
                  <MenuItem value="one">One (Default)</MenuItem>
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="none">None</MenuItem>
                </Select>
                <FormHelperText>How to handle sequence ambiguities</FormHelperText>
              </FormControl>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    );
  };

  return (
    <FieldArray
      name="stages"
      render={arrayHelpers => (
        <Box>
          {values.stages.map((stage, index) => (
            <Paper key={index} sx={{ p: 2, mb: 2, position: 'relative' }}>
              <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
                {values.stages.length > 1 && (
                  <IconButton 
                    size="small" 
                    onClick={() => arrayHelpers.remove(index)}
                    aria-label="Remove filter stage"
                  >
                    <DeleteIcon />
                  </IconButton>
                )}
              </Box>
              
              <Typography variant="subtitle1" gutterBottom>
                Filter Stage {index + 1}
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel id={`method-label-${index}`}>Filtering Method</InputLabel>
                    <Select
                      labelId={`method-label-${index}`}
                      name={`stages.${index}.method`}
                      value={stage.method}
                      label="Filtering Method"
                      onChange={(e) => {
                        setFieldValue(`stages.${index}.method`, e.target.value);
                        setFieldValue(`stages.${index}.params`, {});
                      }}
                    >
                      <MenuItem value={FilterMethod.ADAPTIVE}>Adaptive</MenuItem>
                      <MenuItem value={FilterMethod.MIN_MAX}>Min/Max Length</MenuItem>
                      <MenuItem value={FilterMethod.IQR}>IQR-based Outlier</MenuItem>
                      <MenuItem value={FilterMethod.ZSCORE}>Z-score Outlier</MenuItem>
                      <MenuItem value={FilterMethod.N50_OPTIMIZE}>N50 Optimization</MenuItem>
                      <MenuItem value={FilterMethod.NATURAL}>Natural Breakpoints</MenuItem>
                    </Select>
                    {errors.stages && 
                     touched.stages && 
                     errors.stages[index] && 
                     (errors.stages[index] as any)?.method && (
                      <FormHelperText error>
                        {(errors.stages[index] as any)?.method}
                      </FormHelperText>
                    )}
                  </FormControl>
                </Grid>
              </Grid>
              
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {methodDescriptions[stage.method]}
                </Typography>
                <Tooltip title="View more details about this method">
                  <IconButton size="small" sx={{ ml: 1 }}>
                    <HelpIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
              
              <Box sx={{ mt: 2 }}>
                {renderMethodParameters(stage.method, index)}
              </Box>
            </Paper>
          ))}
          
          <Box sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => arrayHelpers.push({
                method: FilterMethod.ADAPTIVE,
                params: {}
              })}
            >
              Add Another Filter Stage
            </Button>
          </Box>
          
          {renderQuastOptions()}
        </Box>
      )}
    />
  );
};

export default FilterMethodSelector;