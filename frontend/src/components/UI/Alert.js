import React from 'react';
import styled from 'styled-components';

const StyledAlert = styled.div`
  padding: 1rem;
  margin-bottom: 1.5rem;
  border-radius: var(--radius-md);
  font-weight: 500;
  
  ${props => props.variant === 'success' && `
    background-color: #ecfdf5;
    color: #047857;
    border: 1px solid #a7f3d0;
  `}
  
  ${props => props.variant === 'error' && `
    background-color: #fef2f2;
    color: #b91c1c;
    border: 1px solid #fecaca;
  `}
  
  ${props => props.variant === 'info' && `
    background-color: #eff6ff;
    color: #1e40af;
    border: 1px solid #bfdbfe;
  `}
  
  ${props => props.variant === 'warning' && `
    background-color: #fffbeb;
    color: #b45309;
    border: 1px solid #fef3c7;
  `}
`;

const Alert = ({ 
  children, 
  variant = 'info',
  ...props 
}) => {
  return (
    <StyledAlert variant={variant} {...props}>
      {children}
    </StyledAlert>
  );
};

export default Alert;