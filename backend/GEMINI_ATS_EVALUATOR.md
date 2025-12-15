# Google Gemini ATS Resume Evaluator

## Overview
This service uses Google Gemini 1.5 Pro to perform comprehensive ATS (Applicant Tracking System) resume evaluation. It analyzes resumes across 14 categories and provides an ATS score from 0-100.

## Features
- **Comprehensive Analysis**: Evaluates resumes across 14 mandatory categories
- **ATS Score Calculation**: Provides a 0-100 score based on ATS heuristics
- **Structured JSON Output**: Returns machine-parsable JSON with positives and negatives for each category
- **Google Gemini Integration**: Uses Gemini 1.5 Pro with reasoning capabilities

## API Endpoint

### POST `/api/ats_evaluate`

Evaluate a resume using Google Gemini ATS evaluator.

#### Parameters
- `cv_file` (optional): UploadFile - CV file (PDF, DOCX, TXT)
- `cv_text` (optional): str - Resume text (if no file provided)
- `session_id` (optional): str - Session ID for result persistence

#### Response
```json
{
  "success": true,
  "ats_score": 75,
  "evaluation": {
    "ATS_Score": 75,
    "Contact Information": {
      "Positives": ["Email address present", "Phone number included"],
      "Negatives": ["LinkedIn profile missing"]
    },
    "Spelling & Grammar": {
      "Positives": ["No spelling errors detected"],
      "Negatives": ["Grammar issue in line 5: 'I have lead' should be 'I have led'"]
    },
    // ... all 14 categories
  },
  "metadata": {
    "source": "google_gemini",
    "model": "gemini-1.5-pro",
    "timestamp": "2024-01-01T12:00:00",
    "resume_length": 2500
  }
}
```

## Analysis Categories

The evaluator analyzes resumes across these 14 categories:

1. **Contact Information** - Email, phone, LinkedIn, address
2. **Spelling & Grammar** - Errors, typos, grammatical issues
3. **Personal Pronoun Usage** - Use of "I", "me", "my" (should be minimal)
4. **Skills & Keyword Targeting** - Relevant keywords, skill density
5. **Complex or Long Sentences** - Sentence length and complexity
6. **Generic or Weak Phrases** - Clichés, weak action verbs
7. **Passive Voice Usage** - Passive vs active voice
8. **Quantified Achievements** - Numbers, metrics, measurable results
9. **Required Resume Sections** - All standard sections present
10. **AI-Generated Language Detection** - Overly polished, generic AI language
11. **Repeated Action Verbs** - Variety in action verbs
12. **Visual Formatting or Readability** - Text structure, organization
13. **Personal Information / Bias Triggers** - Unnecessary personal info
14. **Other Strengths and Weaknesses** - Additional observations

## ATS Score Calculation

The ATS_Score (0-100) is calculated based on:
- Keyword relevance
- Structure and section coverage
- Clarity and conciseness
- ATS compatibility
- Measurable impact
- Professional resume best practices

## Usage Examples

### Python
```python
import requests

# With file upload
files = {"cv_file": open("resume.pdf", "rb")}
response = requests.post(
    "http://localhost:8000/api/ats_evaluate",
    files=files
)
result = response.json()

# With text
data = {
    "cv_text": "John Doe\nSoftware Engineer\n...",
    "session_id": "session123"
}
response = requests.post(
    "http://localhost:8000/api/ats_evaluate",
    data=data
)
result = response.json()
```

### cURL
```bash
# With file
curl -X POST "http://localhost:8000/api/ats_evaluate" \
  -F "cv_file=@resume.pdf" \
  -F "session_id=session123"

# With text
curl -X POST "http://localhost:8000/api/ats_evaluate" \
  -F "cv_text=John Doe\nSoftware Engineer..." \
  -F "session_id=session123"
```

## Service Implementation

The service is implemented in:
- `backend/services/gemini_ats_evaluator.py` - Gemini ATS evaluator service
- `backend/routes/ats_routes.py` - API endpoint

## Configuration

The API key is configured in `gemini_ats_evaluator.py`:
```python
GEMINI_API_KEY = "AIzaSyA1vogI-pn8-rLWtLwwpW1iJH78tk-b14U"
```

## Dependencies

- `google-generativeai==0.3.2` - Google Gemini API client

## Error Handling

The service handles:
- Empty or invalid resume text
- JSON parsing errors (with fallback extraction)
- API errors from Google Gemini
- Structure validation to ensure all categories are present

## Output Format

The output is strictly JSON with:
- All keys and string values use double quotes
- No trailing commas
- No markdown formatting
- Every category has both "Positives" and "Negatives" arrays
- Empty arrays `[]` if no feedback for a category
