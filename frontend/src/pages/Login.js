import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useAuth } from '../contexts/AuthContext';
import Card from '../components/UI/Card';
import Input from '../components/UI/Input';
import Button from '../components/UI/Button';
import Alert from '../components/UI/Alert';

const PageContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
`;

const AuthContainer = styled(Card)`
  width: 100%;
  max-width: 400px;
`;

const LogoContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 2rem;
`;

const Logo = styled.h1`
  color: var(--color-primary);
  font-weight: 700;
  font-size: 1.75rem;
`;

const Title = styled.h2`
  text-align: center;
  margin-bottom: 2rem;
  font-weight: 600;
  color: var(--color-text);
`;

const Form = styled.form`
  margin-bottom: 1.5rem;
`;

const LinkText = styled.p`
  text-align: center;
  color: var(--color-text-light);
  font-size: 0.875rem;
`;

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!username || !password) {
      setError('Please fill in all fields');
      return;
    }
    
    try {
      setLoading(true);
      const result = await login(username, password);
      
      if (result.success) {
        navigate('/');
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('An unexpected error occurred');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <PageContainer>
      <AuthContainer>
        <LogoContainer>
          <Logo>Load Forecasting</Logo>
        </LogoContainer>
        <Title>Log in to your account</Title>
        
        {error && <Alert variant="error" style={{ marginBottom: '1.5rem' }}>{error}</Alert>}
        
        <Form onSubmit={handleSubmit}>
          <Input
            label="Username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          
          <Button 
            type="submit" 
            fullWidth 
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Log in'}
          </Button>
        </Form>
        
        <LinkText>
          Don't have an account? <Link to="/register">Register</Link>
        </LinkText>
      </AuthContainer>
    </PageContainer>
  );
}

export default Login;