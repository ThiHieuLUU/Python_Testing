#!/usr/bin/venv python3
import pytest
from datetime import timedelta, datetime

from server import (
    app,
    load_clubs,
    load_competitions,
    update_clubs_json,
    update_competitions_json,
    MAX_PLACES,
    NUMBER_OF_POINTS_PER_PLACE
)

# The original data
CLUBS = load_clubs()
COMPETITIONS = load_competitions()

# The data to test
clubs = load_clubs()  # Not doing: clubs = CLUBS because copy of list will make changing CLUBS if clubs change
competitions = load_competitions()  # the same reason for competitions


@pytest.fixture
def client():
    app.config["TESTING"] = True
    yield app.test_client()  # tests run here

    # teardown: return original data to jsons files
    update_clubs_json({"clubs": CLUBS})
    update_competitions_json({"competitions": COMPETITIONS})


@pytest.fixture
def club():
    """For the tests using the first club."""
    return clubs[0]


@pytest.fixture
def future_time():
    """Define one date in the future."""
    ten_days_after = datetime.now() + timedelta(days=10)
    time_format = '%Y-%m-%d %H:%M:%S'
    return ten_days_after.strftime(time_format)


@pytest.fixture
def past_time():
    """Define one date in the past."""
    ten_days_before = datetime.now() - timedelta(days=10)
    time_format = '%Y-%m-%d %H:%M:%S'
    return ten_days_before.strftime(time_format)


@pytest.fixture
def future_competition(future_time):
    """For all tests using the first competition which take places in future."""
    global competitions
    competitions[0]["date"] = future_time
    update_competitions_json({"competitions": competitions})
    competitions = load_competitions()
    return competitions[0]


@pytest.fixture
def past_competition(past_time):
    """For all tests using the first competition which happened."""
    global competitions
    competitions[0]["date"] = past_time
    update_competitions_json({"competitions": competitions})
    competitions = load_competitions()
    return competitions[0]


@pytest.fixture
def valid_places_required(club, future_competition):
    """Make sure the places required is valid.
    It means that the request is not exceeded: club's points/3, MAX_PLACES and competition's available places.
    """
    places_required = min(int(int(club['points'])/NUMBER_OF_POINTS_PER_PLACE), MAX_PLACES, int(future_competition["number_of_places"]))
    return places_required


def update_club():
    """Get updated club for the tests using the first club."""
    update_clubs_json({"clubs": clubs})
    return load_clubs()[0]


def update_competition():
    """Get updated club for the tests using the first competition."""
    update_competitions_json({"competitions": competitions})
    return load_competitions()[0]


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
    # Check the feature of clubs' points board.
    assert b"Clubs - Points:" in response.data

    for club_member in clubs:
        assert str.encode(f'{club_member["name"]}: {club_member["points"]} points') in response.data


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


def test_purchase_places__success(client, club, future_competition, valid_places_required):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book places
    THEN they receive a confirmation message
    """
    competition = future_competition

    club_name = club["name"]
    competition_name = competition['name']

    response = client.post("/purchasePlaces", data=dict(
        places=valid_places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 200
    # Make sure the redirection is effected if the purchase is success.
    assert b"<title>Summary | GUDLFT Registration</title>" in response.data  # welcome page
    # Make sure the confirmation message is displayed
    assert b"Great - booking complete!" in response.data


def test_purchase_places_using_more_than_club_points__failure(client, club, future_competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book places which is greater than a third of the club's points
    THEN they receive an error message
    """
    # Make sure that club's points/NUMBER_OF_POINTS_PER_PLACE is smaller than MAX_PLACES and competition's available
    # places in order to receive the corresponding error message

    club["points"] = MAX_PLACES - 1
    club = update_club()
    club_name = club["name"]

    competition = future_competition
    competition["number_of_places"] = MAX_PLACES
    competition = update_competition()
    competition_name = competition['name']

    # Case not allowed: places required is greater than a third of the available points of the club
    places_required = int(club["points"]/3) + 1
    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 403
    assert b"You can't book more than a third of your available points!" in response.data


def test_purchase_more_than_12_places_per_competition__failure(client, club, future_competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book more than 12 places per competition
    THEN they receive an error message
    """
    # Make sure that MAX_PLACES is smaller than (club's points/NUMBER_OF_POINTS_PER_PLACE) and competition's
    # available places in order to receive the corresponding error message

    club["points"] = (MAX_PLACES + 1)*NUMBER_OF_POINTS_PER_PLACE
    club = update_club()
    club_name = club["name"]

    competition = future_competition
    competition["number_of_places"] = MAX_PLACES + 2
    competition = update_competition()
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


def test_purchase_more_than_available_places_of_competition__failure(client, club, future_competition):
    """
    GIVEN a club logged in
    WHEN the secretary wants to book more than available places of a competition
    THEN they receive an error message
    """
    # Make sure that competition's available places is smaller than (club's points)/NUMBER_OF_POINTS_PER_PLACE and
    # MAX_PLACES in order to receive the corresponding error message
    club["points"] = MAX_PLACES*NUMBER_OF_POINTS_PER_PLACE
    club = update_club()
    club_name = club["name"]

    competition = future_competition
    competition["number_of_places"] = MAX_PLACES - 1
    competition = update_competition()
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


def test_purchase_reflect_points_remained(client, club, future_competition):
    """
    GIVEN a club logged in
    WHEN the secretary books some places with success
    THEN they see club's total points reduced
    """
    club["points"] = MAX_PLACES - 1
    club = update_club()
    club_name = club["name"]

    competition = future_competition
    competition["number_of_places"] = MAX_PLACES + 1
    competition = update_competition()
    competition_name = competition['name']

    places_required = int(int(club["points"])/NUMBER_OF_POINTS_PER_PLACE)  # It's is a valid request.
    available_point = int(club['points'])
    new_available_point = available_point - places_required*NUMBER_OF_POINTS_PER_PLACE

    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 200
    assert str.encode(f'Points available: {new_available_point}\n') in response.data


def test_purchase_negative_places__failure(client, club, future_competition):
    """
    GIVEN a club logged in
    WHEN the secretary books some negative places
    THEN they receive an error message
    """
    club_name = club["name"]
    competition = future_competition
    competition_name = competition['name']

    places_required = -10

    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 403
    assert b"You can't book a negative number of places" in response.data


def test_purchase_future_places__success(client, club, future_competition, valid_places_required):
    """
    GIVEN a club logged in
    WHEN the secretary books some places in a future competition
    THEN they receive a confirmation message
    """
    club["points"] = MAX_PLACES - 1
    club = update_club()

    competition = future_competition
    competition["number_of_places"] = MAX_PLACES + 1
    competition = update_competition()

    club_name = club["name"]
    competition_name = competition['name']

    response = client.post("/purchasePlaces", data=dict(
        places=valid_places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 200
    # Make sure the redirection is effected if the purchase is success.
    assert b"<title>Summary | GUDLFT Registration</title>" in response.data  # welcome page
    # Make sure the confirmation message is displayed
    assert b"Great - booking complete!" in response.data


def test_purchase_past_places__failure(client, club, past_competition):
    """
    GIVEN a club logged in
    WHEN the secretary books some places in a past competition
    THEN they receive an error message
    """
    club["points"] = MAX_PLACES - 1
    club = update_club()

    competition = past_competition
    competition["number_of_places"] = MAX_PLACES + 1
    competition = update_competition()

    club_name = club["name"]
    competition_name = competition['name']

    # Attention: do not calling "valid_places_required" here because it involves the future_competition
    places_required = min(int(club['points']), MAX_PLACES, int(competition["number_of_places"]))

    response = client.post("/purchasePlaces", data=dict(
        places=places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 400
    assert b"You can't book this past competition!" in response.data


def test_clubs_points_board_updated_after_success_purchase(client, club, future_competition, valid_places_required):
    """
    GIVEN a club logged in
    WHEN the secretary books places with success
    THEN they receive a confirmation message and see the change of the clubs' points board
    """
    competition = future_competition

    club_name = club["name"]
    competition_name = competition['name']

    response = client.post("/purchasePlaces", data=dict(
        places=valid_places_required,
        club=club_name,
        competition=competition_name,
    ), follow_redirects=True)

    assert response.status_code == 200
    # Make sure the redirection is effected if the purchase is success.
    assert b"<title>Summary | GUDLFT Registration</title>" in response.data  # welcome page
    # Make sure the confirmation message is displayed
    assert b"Great - booking complete!" in response.data

    # Check the feature of clubs' points board.
    assert b"Clubs - Points:" in response.data

    clubs_updated = load_clubs()
    for club_member in clubs_updated:
        assert str.encode(f'{club_member["name"]}: {club_member["points"]} points') in response.data


def test_clubs_points_board_displayed_without_logged_in(client):
    """
    GIVEN a club not logged in
    WHEN the secretary goes to the index page
    THEN they see the clubs' points board
    """
    response = client.get("/")
    assert response.status_code == 200
    assert b"Clubs - Points:" in response.data
    clubs_updated = load_clubs()
    for club_member in clubs_updated:
        assert str.encode(f'{club_member["name"]}: {club_member["points"]} points') in response.data


def test_clubs_points_board_updated_when_log_out(client):
    """
    GIVEN a club logged in
    WHEN the secretary clicks on the logout
    THEN they see the updated clubs' points board
    """
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Clubs - Points:" in response.data
    clubs_updated = load_clubs()
    for club_member in clubs_updated:
        assert str.encode(f'{club_member["name"]}: {club_member["points"]} points') in response.data


def test_competitions_places_displayed_correctly_while_booking(client, club, future_competition):
    """
    GIVEN a club logged in
    WHEN the secretary clicks on the "Book Places" from welcome page
    THEN they see the updated competitions' places
    """
    competition = future_competition
    competition["number_of_places"] = 100
    competition = update_competition()
    parameters = '/'.join([competition["name"], club["name"]])
    response = client.get("/book/" + parameters)
    assert response.status_code == 200
    assert str.encode(f'Places available: {competition["number_of_places"]}') in response.data
