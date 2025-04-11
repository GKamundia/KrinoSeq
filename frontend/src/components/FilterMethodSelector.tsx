import React from 'react';
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
  FormHelperText
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import HelpIcon from '@mui/icons-material/Help';
import { FieldArray, useFormikContext } from 'formik';
import { FilterMethod, FilterPipelineConfig } from '../types/api';

const methodDescriptions: Record<FilterMethod, string> = {
  [FilterMethod.MIN_MAX]: 'Simple filtering by minimum and/or maximum sequence length.',
  [FilterMethod.IQR]: 'Filter outliers based on interquartile range (IQR) statistical method.',
  [FilterMethod.ZSCORE]: 'Filter outliers based on Z-score statistical method.',
  [FilterMethod.ADAPTIVE]: 'Automatically select the best filtering method based on data characteristics.',
  [FilterMethod.N50_OPTIMIZE]: 'Optimize sequence filtering to maximize the N50 assembly metric.',
  [FilterMethod.NATURAL]: 'Identify natural breakpoints in the length distribution.'
};

const FilterMethodSelector: React.FC = () => {
  const { values, errors, touched, handleChange, setFieldValue } = useFormikContext<FilterPipelineConfig>();

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
        
      // ADAPTIVE and NATURAL don't have parameters
      default:
        return (
          <Typography variant="body2" color="text.secondary">
            No parameters required for this method.
          </Typography>
        );
    }
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
                        // Reset params when changing method
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
        </Box>
      )}
    />
  );
};

export default FilterMethodSelector;