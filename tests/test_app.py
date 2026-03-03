import copy

test_activities_snapshot = None

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Keep the global activities dictionary from leaking between tests.

    A deep copy is created before each test and then restored afterwards.  The
    fixture is marked ``autouse`` so that tests don't need to explicitly
    request it; every function runs with a clean state.
    """
    global test_activities_snapshot
    test_activities_snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(test_activities_snapshot)


client = TestClient(app)


def test_root_redirect():
    # TestClient follows redirects by default, so disable that behaviour
    # when we want to assert on the initial status code.
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"
    # confirming that following the redirect returns a 200 page
    final = client.get(response.headers["location"])
    assert final.status_code == 200


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    assert response.json() == activities


# signup tests

def test_signup_success():
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 200
    assert email in activities[activity]["participants"]
    assert "Signed up" in response.json()["message"]


def test_signup_missing_activity():
    response = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    assert response.status_code == 404


def test_signup_already_registered():
    activity = "Chess Club"
    existing = activities[activity]["participants"][0]
    response = client.post(f"/activities/{activity}/signup", params={"email": existing})
    assert response.status_code == 400


# unregister tests

def test_unregister_success():
    activity = "Chess Club"
    email = activities[activity]["participants"][0]
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})
    assert response.status_code == 200
    assert email not in activities[activity]["participants"]
    assert "Unregistered" in response.json()["message"]


def test_unregister_missing_activity():
    response = client.delete("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    assert response.status_code == 404


def test_unregister_not_signed_up():
    response = client.delete("/activities/Chess Club/signup", params={"email": "not@here.com"})
    assert response.status_code == 400
