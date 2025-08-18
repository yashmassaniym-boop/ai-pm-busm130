import os, sys
# ensure repo root is on import path for CI runners
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient
from datetime import date
from ai_pm_app.backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

def test_generate_and_endpoints():
    r = client.post('/projects/generate', json={'vision':'Test vision'})
    assert r.status_code == 200
    pid = r.json()['project_id']

    assert client.get(f'/projects/{pid}/kpis').status_code == 200
    assert client.get(f'/projects/{pid}/budget/summary').status_code == 200
    assert client.get(f'/projects/{pid}/risk/summary').status_code == 200
    assert client.get(f'/projects/{pid}/timeline').status_code == 200

    back = client.get(f'/projects/{pid}/backlog').json()
    todo = back['columns']['todo']
    if todo:
        tid = todo[0]['task_id']
        assert client.patch(f'/projects/tasks/{tid}', json={'status':'inprogress'}).status_code == 200
        assert client.patch(f'/projects/tasks/{tid}', json={'est_days': 3}).status_code == 200
        assert client.patch(f'/projects/tasks/{tid}', json={'status':'done','done':True}).status_code == 200

    start = date.today().isoformat()
    assert client.get(f'/projects/{pid}/burn?sprint_days=14&start={start}').status_code == 200
    assert client.get(f'/projects/{pid}/velocity?sprint_days=14&start={start}').status_code == 200

def test_openapi_has_tasks_route():
    spec = client.get('/openapi.json').json()
    assert '/projects/tasks/{task_id}' in spec['paths']

def test_dashboard_route():
    r = client.get('/dashboard')
    assert r.status_code == 200
    assert 'AI PM Dashboard' in r.text
