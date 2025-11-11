import { Button as MuiButton } from '@mui/material';
import { styled } from '@mui/material/styles';
import { motion } from 'framer-motion';

const AnimatedButton = styled(motion.div)`
  display: inline-block;
`;

const StyledButton = styled(MuiButton)`
  background: linear-gradient(45deg, #2196F3 30%, #21CBF3 90%);
  border-radius: 3px;
  border: 0;
  color: white;
  height: 48px;
  padding: 0 30px;
  box-shadow: 0 3px 5px 2px rgba(33, 203, 243, .3);
  transition: all 0.3s ease;

  &:hover {
    background: linear-gradient(45deg, #21CBF3 30%, #2196F3 90%);
    transform: translateY(-2px);
    box-shadow: 0 6px 10px 2px rgba(33, 203, 243, .3);
  }
`;

const Button = ({ children, ...props }) => {
  return (
    <AnimatedButton
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <StyledButton {...props}>
        {children}
      </StyledButton>
    </AnimatedButton>
  );
};

export default Button; 