import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import styled from 'styled-components';

const Header = styled.header`
  background-color: var(--color-card);
  box-shadow: var(--shadow-sm);
  padding: 1rem 0;
`;

const HeaderContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
`;

const Logo = styled.div`
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-primary);
`;

const Nav = styled.nav`
  display: flex;
  align-items: center;
  gap: 1.5rem;
`;

const NavItem = styled(NavLink)`
  color: var(--color-text-light);
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 0;
  border-bottom: 2px solid transparent;
  transition: color 0.2s, border-color 0.2s;

  &:hover {
    color: var(--color-primary);
    text-decoration: none;
  }

  &.active {
    color: var(--color-primary);
    border-bottom: 2px solid var(--color-primary);
  }
`;

const LogoutButton = styled.button`
  background: none;
  border: none;
  color: var(--color-text-light);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;

  &:hover {
    color: var(--color-primary);
    background: none;
  }
`;

const Main = styled.main`
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 1.5rem;
`;

function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    const result = await logout();
    if (result.success) {
      navigate('/login');
    }
  };

  return (
    <>
      <Header>
        <HeaderContainer>
          <Logo>Load Forecasting</Logo>
          <Nav>
            <NavItem to="/" end>Dashboard</NavItem>
            <NavItem to="/projects">Projects</NavItem>
            {user && (
              <LogoutButton onClick={handleLogout}>Logout</LogoutButton>
            )}
          </Nav>
        </HeaderContainer>
      </Header>
      <Main>
        <Outlet />
      </Main>
    </>
  );
}

export default Layout;