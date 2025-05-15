# Web Application Design: Load Forecasting Agents

## 1. Architecture Overview

Based on the user requirements for a multi-page guided workflow, user authentication, project management, and a Flask backend, the proposed architecture is as follows:

*   **Web Framework:** Flask will be used for the backend logic, routing, API endpoints, and rendering frontend templates.
*   **Frontend:** Server-side rendered HTML using Flask's Jinja2 templating engine. A modern CSS framework (e.g., Bootstrap or Tailwind CSS, TBD during implementation) will be used for a minimal, clean design. JavaScript (potentially with libraries like Chart.js or Plotly.js) will be used for interactive charts and potentially asynchronous status updates.
*   **Backend Logic:** The Flask application will manage:
    *   User authentication (registration, login, session management).
    *   Project CRUD (Create, Read, Update, Delete) operations.
    *   Handling data input (CSV uploads, predefined dataset selection).
    *   Storing project metadata, data paths, and user information.
    *   Triggering the ML pipeline (data processing, modeling) as background tasks (e.g., using Flask-Executor, Celery, or simpler threading for local deployment) to avoid blocking web requests.
    *   Interacting with the existing agent logic (refactored as needed) and MLflow (for loading models, logging results).
    *   Serving results (metrics, charts, downloadable forecasts) to the frontend.
*   **Database:** A database (MySQL, as supported by the `create_flask_app` template) will store user credentials, project details, and potentially task status.
*   **ML Pipeline Integration:** The core logic from `data_processing_agent.py` and `modeling_agent.py` will be integrated into the Flask backend, callable upon user request within a specific project context.
*   **Deployment:** The application will be containerized using Docker/Docker Compose for portability and deployed using the permanent deployment tool.

## 2. User Interface Flow & Conceptual Wireframes

The application will guide the user through a multi-page process:

1.  **Login/Register Page:**
    *   **Content:** Simple forms for user login (email/password) and registration (email/password).
    *   **Action:** Submitting login/registration details.

2.  **Dashboard Page (Post-Login):**
    *   **Content:** Header with logged-in user info/logout. Main area lists existing user projects (Name, Status, Last Updated). A button/link to "Create New Project".
    *   **Action:** Click on an existing project to view details or click "Create New Project".

3.  **Project Creation Page:**
    *   **Content:** Simple form with a field for "Project Name".
    *   **Action:** Submit to create the project, redirect to the new Project View page.

4.  **Project View Page:**
    *   **Content:** Project Name. Status indicator (e.g., "No data", "Processing", "Ready"). Details of the last run (if any): Data source, Parameters, Best Model, Key Metrics. Button: "Start New Forecast Run".
    *   **Action:** Click "Start New Forecast Run".

5.  **New Run - Step 1: Data Input Page:**
    *   **Content:** Section for "Select Sample Data" with links/buttons for predefined datasets. Section for "Upload Data" with a file input for CSV. Fields to specify the "Datetime Column Name" and "Value Column Name" in the CSV.
    *   **Action:** Select sample or upload file, specify columns, click "Next: Set Parameters". Backend validates input and stores data reference.

6.  **New Run - Step 2: Parameters Page:**
    *   **Content:** Dropdown for "Forecast Horizon" (e.g., 2 days, 7 days, 10 years). Dropdown for "Forecast Granularity" (e.g., Hourly, Daily, Yearly). Dropdown for "Target Variable Unit" (e.g., kWh, Watts - maps to value column meaning).
    *   **Action:** Select parameters, click "Start Forecasting". Backend initiates the ML pipeline task.

7.  **Processing/Results Page:**
    *   **Content:** Initially shows "Processing forecast... Please wait." (May include a progress indicator or auto-refresh mechanism). Once complete:
        *   **Summary:** Best Model Name, Test MAPE, Test R2 Score.
        *   **Model Comparison:** Table listing all trained models and their test metrics (MAPE, R2, MAE).
        *   **Charts:**
            *   Interactive plot: Actual vs. Predicted values for the best model on the test set.
            *   Interactive plot: Future forecast values (with confidence intervals if available).
        *   **Download:** Button to download the forecast results as a CSV file.
    *   **Action:** View results, download forecast.

## 3. Framework Selection

Flask is confirmed as the primary backend framework, leveraging its templating for the frontend. The `create_flask_app` template will be used as a starting point, providing structure for routes, models, and the virtual environment.

## 4. Next Steps

Proceed with setting up the Flask project structure using the template and begin implementing the backend API endpoints, starting with user authentication and project management.
