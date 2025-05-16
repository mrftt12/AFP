import React from 'react';
import styled from 'styled-components';

const StyledCard = styled.div`
  background-color: var(--color-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: ${props => props.padding || '1.5rem'};
`;

const Card = ({ children, ...props }) => {
  return <StyledCard {...props}>{children}</StyledCard>;
};

export default Card;