# Frontend - Assistant++ Career Match

Professional Streamlit frontend application for job search, CV analysis, and ATS optimization.

## Structure

```
frontend/
├── app.py                 # Main entry point
├── pages/                 # Streamlit pages (auto-detected)
│   ├── 1_Job_Search.py   # Job search functionality
│   ├── 2_CV_Analyzer.py  # CV vs Job matching
│   └── 3_ATS_Optimizer.py # ATS CV optimization
├── components/            # Reusable UI components
│   ├── layout.py         # Layout and navigation
│   ├── job_results.py    # Job results display
│   ├── cv_analysis.py    # CV analysis display
│   └── ats_optimizer.py  # ATS optimizer display
├── services/              # API and business logic
│   └── api_client.py     # Backend API client
└── utils/                 # Utility functions
    └── session_manager.py # Session management
```

## Running the Application

1. Make sure the backend is running on `http://localhost:8000`
2. Install dependencies:
   ```bash
   pip install streamlit requests
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## Environment Variables

- `ASSISTANT_API_URL`: Backend API URL (default: `http://localhost:8000`)

## Features

- **Job Search**: Natural language job search with clarification flow
- **CV Analyzer**: Analyze CV against job descriptions with matching scores
- **ATS Optimizer**: Generate ATS-compliant LaTeX CVs

## Architecture

- **Separation of Concerns**: Each page handles a single responsibility
- **Reusable Components**: UI components are modular and reusable
- **API Service Layer**: Centralized API communication
- **Session Management**: Persistent user sessions across pages

