#!/usr/bin/venv python3

import pytest
from server import (
    app,
    load_clubs,
    load_competitions,
    update_clubs_json,
    update_competitions_json,
    MAX_PLACES
)

clubs = load_clubs()
competitions = load_competitions()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    yield app.test_client()  # tests run here


@pytest.fixture
def club():
    """For the tests using the first club."""
    return clubs[0]


@pytest.fixture
def competition():
    """For the tests using the first competition."""
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


def test_purchase_places__success(client, club, competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book places
    THEN they receive a confirmation message
    """

    # Make sure that places_required isn't exceeded: club's points, MAX_PLACES and competition's available places
    places_required = min(int(club['points']), MAX_PLACES, int(competition["number_of_places"]))

    club_name = club["name"]
    competition_name = competition['name']

    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 200
    # Make sure the redirection is effected if the purchase is success.
    assert b"<title>Summary | GUDLFT Registration</title>" in response.data  # welcome page
    # Make sure the confirmation message is displayed
    assert b"Great - booking complete!" in response.data


def test_purchase_places_using_more_than_club_points__failure(client, club, competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book places which is greater than the club's points
    THEN they receive an error message
    """

    # Make sure that club's points is smaller than MAX_PLACES and competition's available places
    # in order to receive the corresponding error message

    club["points"] = MAX_PLACES - 1
    competition["number_of_places"] = MAX_PLACES

    update_clubs_json({"clubs": clubs})
    update_competitions_json({"competitions": competitions})

    clubs_updated = load_clubs()
    competitions_updated = load_competitions()

    club = clubs_updated[0]
    competition = competitions_updated[0]

    club_name = club["name"]
    competition_name = competition['name']

    # Case not allowed: places required is greater than the available points of the club
    places_required = club["points"] + 1
    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 403
    assert b"You can't book more than your available points!" in response.data


def test_purchase_more_than_12_places_per_competition__failure(client, club, competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book more than 12 places per competition
    THEN they receive an error message
    """
    # Make sure that MAX_PLACES is smaller than club's points and competition's available places
    # in order to receive the corresponding error message

    club["points"] = MAX_PLACES + 1
    competition["number_of_places"] = MAX_PLACES + 2

    update_clubs_json({"clubs": clubs})
    update_competitions_json({"competitions": competitions})

    clubs_updated = load_clubs()
    competitions_updated = load_competitions()

    club = clubs_updated[0]
    competition = competitions_updated[0]

    club_name = club["name"]
    competition_name = competition['name']

    # Case not allowed: places required is greater than MAX_PLACES = 12
    places_required = MAX_PLACES + 1
    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 403
    assert b"You can't book more than 12 places!" in response.data


def test_purchase_more_than_available_places_of_competition__failure(client, club, competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book more than available places of a competition
    THEN they receive an error message
    """
    # Make sure that competition's available places is smaller than club's points and MAX_PLACES
    # in order to receive the corresponding error message

    club["points"] = MAX_PLACES
    competition["number_of_places"] = MAX_PLACES - 1

    update_clubs_json({"clubs": clubs})
    update_competitions_json({"competitions": competitions})

    clubs_updated = load_clubs()
    competitions_updated = load_competitions()

    club = clubs_updated[0]
    competition = competitions_updated[0]

    club_name = club["name"]
    competition_name = competition['name']

    # Case not allowed: places required is greater than available places of the competition
    places_required = int(competition["number_of_places"]) + 1
    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 403
    assert b"You can't book more than available places of this competition!" in response.data


def test_purchase_reflect_points_remained(client, club, competition):
    """
    GIVEN a club logged in
    WHEN the secretary books some places with success
    THEN they see club's total points reduced
    """

    club_name = club["name"]
    available_point = int(club['points'])

    competition_name = competition['name']

    # Make sure the booking is success
    places_required = min(int(club['points']), MAX_PLACES, int(competition["number_of_places"]))
    new_available_point = available_point - places_required

    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 200
    assert str.encode(f'Points available: {new_available_point}\n') in response.data
