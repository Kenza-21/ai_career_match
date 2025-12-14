import pytest
from fastapi.testclient import TestClient

from main import app
from services.assistant import career_assistant
import routes.search_routes as search_routes
import routes.job_routes as job_routes


class FakeJobMatcher:
    def __init__(self):
        self.jobs = [
            {
                "job_id": 1,
                "job_title": "Développeur Backend Python",
                "category": "Tech",
                "description": "API et microservices",
                "required_skills": "python backend api",
                "recommended_courses": "",
                "avg_salary_mad": "8000",
                "demand_level": "High",
            },
            {
                "job_id": 2,
                "job_title": "Data Analyst",
                "category": "Tech",
                "description": "SQL et dashboards",
                "required_skills": "sql bi tableau",
                "recommended_courses": "",
                "avg_salary_mad": "7000",
                "demand_level": "Medium",
            },
        ]

    def search_jobs(self, query: str, top_k: int = 5):
        query_lower = query.lower()
        scored = []
        for idx, job in enumerate(self.jobs):
            score = 0.0
            for token in query_lower.split():
                if token in job["job_title"].lower() or token in job["required_skills"].lower():
                    score += 1
            if score > 0:
                scored.append((idx, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_job_by_index(self, index: int):
        return self.jobs[index]


@pytest.fixture(autouse=True)
def override_dependencies():
    fake = FakeJobMatcher()
    search_routes.job_matcher = fake
    job_routes.job_matcher = fake
    career_assistant.sessions.clear()
    yield
    search_routes.job_matcher = fake
    job_routes.job_matcher = fake


@pytest.fixture
def client():
    return TestClient(app)


def test_clear_query_returns_searches_and_results(client):
    resp = client.post("/api/search", json={"query": "python backend developer", "session_id": "s1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["clarify"] is False
    assert len(body["search_queries"]) >= 5
    assert all("query" in q and "google_link" in q and "indeed_link" in q for q in body["search_queries"])
    assert body["results"]["summary"]["total_matches"] >= 1


def test_vague_query_triggers_clarification(client):
    resp = client.post("/api/search", json={"query": "help with my project", "session_id": "s2"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["clarify"] is True
    assert "question" in body


def test_clarify_flow_returns_results(client):
    session_id = "s3"
    first = client.post("/api/search", json={"query": "need help", "session_id": session_id}).json()
    assert first["clarify"] is True

    clarified = client.post("/api/clarify", json={"session_id": session_id, "answer": "backend python"}).json()
    assert clarified["clarify"] is False
    assert clarified["results"]["summary"]["total_matches"] >= 1

