import { TextField } from '@mui/material';
import { styled } from '@mui/material/styles';
import { motion } from 'framer-motion';

const AnimatedContainer = styled(motion.div)`
  width: 100%;
  margin-bottom: 20px;
`;

const StyledTextField = styled(TextField)`
  width: 100%;
  
  .MuiOutlinedInput-root {
    transition: all 0.3s ease;
    
    &:hover {
      .MuiOutlinedInput-notchedOutline {
        border-color: #2196F3;
      }
    }
    
    &.Mui-focused {
      .MuiOutlinedInput-notchedOutline {
        border-color: #2196F3;
        border-width: 2px;
      }
    }
  }
  
  .MuiInputLabel-root {
    &.Mui-focused {
      color: #2196F3;
    }
  }
`;

const Input = ({ error, ...props }) => {
  return (
    <AnimatedContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <StyledTextField
        variant="outlined"
        error={Boolean(error)}
        helperText={error}
        {...props}
      />
    </AnimatedContainer>
  );
};

export default Input; 