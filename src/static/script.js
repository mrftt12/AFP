// script.js - Client-side functionality

document.addEventListener('DOMContentLoaded', function() {
    // Handle login form submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Form validation
            if (!username || !password) {
                showAlert('Please fill in all fields', 'danger');
                return;
            }
            
            // Submit login request
            fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert(data.error, 'danger');
                } else {
                    // Redirect to dashboard
                    window.location.href = '/dashboard.html';
                }
            })
            .catch(error => {
                showAlert('Error: ' + error.message, 'danger');
            });
        });
    }
    
    // Handle registration form submission
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            
            // Form validation
            if (!username || !email || !password || !confirmPassword) {
                showAlert('Please fill in all fields', 'danger');
                return;
            }
            
            if (password !== confirmPassword) {
                showAlert('Passwords do not match', 'danger');
                return;
            }
            
            // Submit registration request
            fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert(data.error, 'danger');
                } else {
                    // Redirect to dashboard
                    window.location.href = '/dashboard.html';
                }
            })
            .catch(error => {
                showAlert('Error: ' + error.message, 'danger');
            });
        });
    }
    
    // Load user projects on dashboard
    const projectsList = document.getElementById('projects-list');
    if (projectsList) {
        loadProjects();
    }
    
    // Project creation form
    const createProjectForm = document.getElementById('create-project-form');
    if (createProjectForm) {
        createProjectForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const projectName = document.getElementById('project-name').value;
            const projectDescription = document.getElementById('project-description').value;
            const dataSource = document.getElementById('data-source').value;
            
            // Form validation
            if (!projectName) {
                showAlert('Project name is required', 'danger');
                return;
            }
            
            // Submit project creation request
            fetch('/api/projects/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: projectName,
                    description: projectDescription,
                    data_source: dataSource
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showAlert(data.error, 'danger');
                } else {
                    // Redirect to project page
                    window.location.href = '/project.html?id=' + data.project.id;
                }
            })
            .catch(error => {
                showAlert('Error: ' + error.message, 'danger');
            });
        });
    }
    
    // Handle logout
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/api/auth/logout', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                window.location.href = '/login.html';
            })
            .catch(error => {
                showAlert('Error: ' + error.message, 'danger');
            });
        });
    }
});

// Helper function to show alerts
function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        // Clear existing alerts
        alertContainer.innerHTML = '';
        alertContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Load user projects
function loadProjects() {
    const projectsList = document.getElementById('projects-list');
    if (!projectsList) return;
    
    fetch('/api/projects/')
        .then(response => {
            if (!response.ok) {
                // If not authenticated, redirect to login
                if (response.status === 401) {
                    window.location.href = '/login.html';
                    return;
                }
                throw new Error('Failed to load projects');
            }
            return response.json();
        })
        .then(data => {
            if (data.projects && data.projects.length > 0) {
                projectsList.innerHTML = '';
                
                data.projects.forEach(project => {
                    const projectCard = document.createElement('div');
                    projectCard.className = 'card project-card';
                    projectCard.innerHTML = `
                        <div class="card-header">${project.name}</div>
                        <div class="card-body">
                            <p>${project.description || 'No description'}</p>
                            <p><strong>Status:</strong> ${project.status}</p>
                            <p><strong>Created:</strong> ${new Date(project.created_at).toLocaleDateString()}</p>
                            <a href="/project.html?id=${project.id}" class="btn btn-primary">View Project</a>
                        </div>
                    `;
                    projectsList.appendChild(projectCard);
                });
            } else {
                projectsList.innerHTML = '<p>No projects yet. Create a new project to get started.</p>';
            }
        })
        .catch(error => {
            showAlert('Error: ' + error.message, 'danger');
        });
}