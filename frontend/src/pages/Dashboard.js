import React from 'react';
import styled from 'styled-components';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
`;

const WelcomeSection = styled.div`
  margin-bottom: 3rem;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  color: var(--color-text-light);
  font-size: 1.125rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 1rem;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
`;

const StatCard = styled(Card)`
  padding: 1.5rem;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--color-primary);
`;

const StatLabel = styled.div`
  color: var(--color-text-light);
  font-size: 0.875rem;
`;

function Dashboard() {
  const { user } = useAuth();
  
  return (
    <div>
      <WelcomeSection>
        <Title>Welcome, {user?.username || 'User'}</Title>
        <Subtitle>Here's what's happening with your forecasting projects</Subtitle>
      </WelcomeSection>
      
      <Header>
        <SectionTitle>Dashboard</SectionTitle>
        <Button as={Link} to="/projects/new">New Project</Button>
      </Header>
      
      <Grid>
        <StatCard>
          <StatValue>5</StatValue>
          <StatLabel>Active Projects</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue>12</StatValue>
          <StatLabel>Completed Forecasts</StatLabel>
        </StatCard>
        
        <StatCard>
          <StatValue>98.2%</StatValue>
          <StatLabel>Average Accuracy</StatLabel>
        </StatCard>
      </Grid>
      
      <SectionTitle>Recent Projects</SectionTitle>
      <Card padding="0">
        <div style={{ padding: '1.5rem', textAlign: 'center' }}>
          No projects yet. <Link to="/projects/new">Create your first project</Link>
        </div>
      </Card>
    </div>
  );
}

export default Dashboard;