#!/usr/bin/venv python3

import pytest
from server import app, load_clubs, load_competitions

clubs = load_clubs()
competitions = load_competitions()

@pytest.fixture
def client():
    app.config["TESTING"] = True

    yield app.test_client()  # tests run here

def login(client, email):
    return client.post("/showSummary", data=dict(
        email=email,
    ), follow_redirects=True)


def test_login_for_known_email__success(client):
    club = clubs[0]
    # Test case for a known email
    email = club["email"]

    response = login(client, email)
    assert response.status_code == 200
    assert b"<title>Summary | GUDLFT Registration</title>" in response.data
    assert b"Logout" in response.data
    string = f'<h2>Welcome, {email} </h2>'
    assert str.encode(string) in response.data


def test_login_for_unknown_email__failure(client):
    club = clubs[0]
    # Test case for an unknown email
    email = club["email"] + "x"
    response = login(client, email)
    assert response.status_code == 404
    assert b"Sorry, that email wasn't found." in response.data


