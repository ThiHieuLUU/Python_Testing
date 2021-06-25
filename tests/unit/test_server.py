#!/usr/bin/venv python3

import pytest
from server import app, load_clubs, load_competitions

clubs = load_clubs()
competitions = load_competitions()


@pytest.fixture
def client():
    app.config["TESTING"] = True

    yield app.test_client()  # tests run here


@pytest.fixture
def club():
    """Tests will be realized with the first club."""

    return clubs[0]


@pytest.fixture
def competition():
    """Tests will be realized with the first competition."""

    return competitions[0]


def login(client, email):
    """Define the login function for app."""

    return client.post("/showSummary", data=dict(
        email=email,
    ), follow_redirects=True)


def test_login_for_known_email__success(client, club):
    """
    GIVEN an email of a known club
    WHEN a user enters this email to login
    THEN user is redirected to the welcome page
    """

    email = club["email"]
    response = login(client, email)
    assert response.status_code == 200
    assert b"<title>Summary | GUDLFT Registration</title>" in response.data
    assert b"Logout" in response.data
    string = f'<h2>Welcome, {email} </h2>'
    assert str.encode(string) in response.data


def test_login_for_unknown_email__failure(client, club):
    """
    GIVEN an email of an unknown club
    WHEN a user enters this email to login
    THEN user see an error message
    """

    email = club["email"] + "xyz"  # an unknown email
    response = login(client, email)
    assert response.status_code == 404
    assert b"Sorry, that email wasn't found." in response.data



