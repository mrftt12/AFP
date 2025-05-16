import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import axios from 'axios';
import Card from '../components/UI/Card';
import Input from '../components/UI/Input';
import Button from '../components/UI/Button';
import Alert from '../components/UI/Alert';

const Title = styled.h1`
  font-size: 2rem;
  margin-bottom: 2rem;
`;

const FormCard = styled(Card)`
  max-width: 600px;
`;

const FormFooter = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
  gap: 1rem;
`;

const TextArea = styled.textarea`
  font-family: inherit;
  font-size: 1rem;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-card);
  color: var(--color-text);
  width: 100%;
  min-height: 100px;
  resize: vertical;
  transition: border-color 0.2s;

  &:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }
`;

function CreateProject() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [dataSource, setDataSource] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!name) {
      setError('Project name is required');
      return;
    }
    
    try {
      setLoading(true);
      const response = await axios.post('/api/projects/', {
        name,
        description,
        data_source: dataSource,
      });
      
      navigate(`/projects/${response.data.project.id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create project');
      console.error('Error creating project:', err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <Title>Create New Project</Title>
      
      {error && <Alert variant="error" style={{ marginBottom: '2rem' }}>{error}</Alert>}
      
      <FormCard>
        <form onSubmit={handleSubmit}>
          <Input
            label="Project Name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          
          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="description"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontWeight: '500',
              }}
            >
              Description
            </label>
            <TextArea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter project description"
            />
          </div>
          
          <Input
            label="Data Source"
            type="text"
            value={dataSource}
            onChange={(e) => setDataSource(e.target.value)}
            placeholder="URL or file path to load data"
          />
          
          <FormFooter>
            <Button 
              type="button" 
              variant="secondary" 
              onClick={() => navigate('/projects')}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Project'}
            </Button>
          </FormFooter>
        </form>
      </FormCard>
    </div>
  );
}

export default CreateProject;