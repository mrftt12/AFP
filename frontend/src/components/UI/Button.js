import React from 'react';
import styled, { css } from 'styled-components';

const ButtonStyles = css`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: ${props => props.size === 'small' ? '0.5rem 1rem' : props.size === 'large' ? '0.75rem 1.75rem' : '0.625rem 1.25rem'};
  font-size: ${props => props.size === 'small' ? '0.875rem' : props.size === 'large' ? '1.125rem' : '1rem'};
  font-weight: 500;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  text-decoration: none;
  
  ${props => props.fullWidth && css`
    width: 100%;
  `}
  
  ${props => props.variant === 'primary' && css`
    background-color: var(--color-primary);
    color: white;
    
    &:hover {
      background-color: var(--color-primary-dark);
    }
  `}
  
  ${props => props.variant === 'secondary' && css`
    background-color: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
    
    &:hover {
      background-color: rgba(37, 99, 235, 0.05);
    }
  `}
  
  ${props => props.variant === 'text' && css`
    background-color: transparent;
    color: var(--color-primary);
    padding-left: 0;
    padding-right: 0;
    
    &:hover {
      background-color: transparent;
      text-decoration: underline;
    }
  `}
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const StyledButton = styled.button`
  ${ButtonStyles}
`;

const StyledLink = styled.a`
  ${ButtonStyles}
`;

const Button = ({ 
  children, 
  variant = 'primary',
  size = 'medium',
  fullWidth = false,
  href,
  ...props 
}) => {
  if (href) {
    return (
      <StyledLink
        href={href}
        variant={variant}
        size={size}
        fullWidth={fullWidth}
        {...props}
      >
        {children}
      </StyledLink>
    );
  }
  
  return (
    <StyledButton
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      {...props}
    >
      {children}
    </StyledButton>
  );
};

export default Button;