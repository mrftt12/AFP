import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';
import Card from '../components/UI/Card';
import Button from '../components/UI/Button';
import Alert from '../components/UI/Alert';

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  font-size: 2rem;
`;

const ProjectsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
`;

const ProjectCard = styled(Card)`
  display: flex;
  flex-direction: column;
  height: 100%;
`;

const ProjectHeader = styled.div`
  padding: 1.5rem 1.5rem 0.75rem 1.5rem;
`;

const ProjectTitle = styled.h3`
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
`;

const ProjectDescription = styled.p`
  color: var(--color-text-light);
  font-size: 0.875rem;
  margin-bottom: 1rem;
`;

const ProjectMeta = styled.div`
  font-size: 0.75rem;
  color: var(--color-text-light);
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--color-border);
  padding: 0.75rem 1.5rem;
  margin-top: auto;
`;

const Status = styled.span`
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  
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

const EmptyState = styled(Card)`
  text-align: center;
  padding: 3rem 1.5rem;
`;

function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await axios.get('/api/projects/');
        setProjects(response.data.projects || []);
      } catch (err) {
        console.error('Error fetching projects:', err);
        setError('Failed to load projects. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchProjects();
  }, []);
  
  if (loading) {
    return <div>Loading projects...</div>;
  }
  
  return (
    <div>
      <Header>
        <Title>Projects</Title>
        <Button as={Link} to="/projects/new">New Project</Button>
      </Header>
      
      {error && <Alert variant="error" style={{ marginBottom: '2rem' }}>{error}</Alert>}
      
      {projects.length === 0 ? (
        <EmptyState>
          <h3 style={{ marginBottom: '1rem' }}>No projects yet</h3>
          <p style={{ marginBottom: '1.5rem', color: 'var(--color-text-light)' }}>
            Create your first load forecasting project to get started.
          </p>
          <Button as={Link} to="/projects/new">Create Project</Button>
        </EmptyState>
      ) : (
        <ProjectsGrid>
          {projects.map(project => (
            <ProjectCard key={project.id}>
              <ProjectHeader>
                <ProjectTitle>{project.name}</ProjectTitle>
                <ProjectDescription>
                  {project.description || 'No description provided'}
                </ProjectDescription>
                <Status status={project.status}>{project.status}</Status>
              </ProjectHeader>
              <ProjectMeta>
                <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
                <Button as={Link} to={`/projects/${project.id}`} variant="text" size="small">
                  View
                </Button>
              </ProjectMeta>
            </ProjectCard>
          ))}
        </ProjectsGrid>
      )}
    </div>
  );
}

export default Projects;