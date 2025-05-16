import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import Alert from '../components/UI/Alert';

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  color: var(--color-text-light);
  margin-bottom: 1rem;
`;

const Status = styled.span`
  display: inline-block;
  padding: 0.25rem 0.75rem;
  margin-left: 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  vertical-align: middle;
  
  ${props => props.status === 'completed' && `
    background-color: #ecfdf5;
    color: #047857;
  `}
  
  ${props => props.status === 'processing' && `
    background-color: #eff6ff;
    color: #1e40af;
  `}
  
  ${props => props.status === 'created' && `
    background-color: #f3f4f6;
    color: #374151;
  `}
`;

const MetaGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const MetaCard = styled(Card)`
  padding: 1.25rem;
`;

const MetaTitle = styled.h3`
  font-size: 0.875rem;
  color: var(--color-text-light);
  margin-bottom: 0.5rem;
`;

const MetaValue = styled.div`
  font-size: 1rem;
  font-weight: 500;
`;

const SectionTitle = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  margin-top: 2.5rem;
`;

const EmptyCard = styled(Card)`
  padding: 2rem;
  text-align: center;
  color: var(--color-text-light);
`;

function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await axios.get(`/api/projects/${projectId}`);
        setProject(response.data.project);
      } catch (err) {
        console.error('Error fetching project:', err);
        setError('Failed to load project details');
      } finally {
        setLoading(false);
      }
    };
    
    fetchProject();
  }, [projectId]);
  
  if (loading) {
    return <div>Loading project details...</div>;
  }
  
  if (error) {
    return (
      <Alert variant="error">
        {error}. <Link to="/projects">Back to projects</Link>
      </Alert>
    );
  }
  
  if (!project) {
    return (
      <Alert variant="error">
        Project not found. <Link to="/projects">Back to projects</Link>
      </Alert>
    );
  }
  
  return (
    <div>
      <Header>
        <div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Title>{project.name}</Title>
            <Status status={project.status}>{project.status}</Status>
          </div>
          <Subtitle>
            Created on {new Date(project.created_at).toLocaleDateString()}
          </Subtitle>
        </div>
        <Button variant="secondary" onClick={() => navigate('/projects')}>
          Back to Projects
        </Button>
      </Header>
      
      <MetaGrid>
        <MetaCard>
          <MetaTitle>Data Source</MetaTitle>
          <MetaValue>{project.data_source || 'Not specified'}</MetaValue>
        </MetaCard>
        
        <MetaCard>
          <MetaTitle>Status</MetaTitle>
          <MetaValue>{project.status}</MetaValue>
        </MetaCard>
      </MetaGrid>
      
      <Card>
        <h3 style={{ marginBottom: '1rem' }}>Description</h3>
        <p>{project.description || 'No description provided'}</p>
      </Card>
      
      <SectionTitle>Forecasting Results</SectionTitle>
      
      <EmptyCard>
        No forecasting results available yet.
        {project.status === 'created' && (
          <div style={{ marginTop: '1rem' }}>
            <Button>Start Forecasting</Button>
          </div>
        )}
      </EmptyCard>
    </div>
  );
}

export default ProjectDetail;