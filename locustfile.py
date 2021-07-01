from datetime import timedelta, datetime
from locust import HttpUser, task, between
from server import (
    load_clubs,
    load_competitions,
    update_clubs_json,
    update_competitions_json,
)

# The original data
CLUBS = load_clubs()

COMPETITIONS = load_competitions()

# The data to test
clubs = load_clubs()  # Not doing: clubs = CLUBS because copy of list will make changing CLUBS if clubs change
competitions = load_competitions()  # the same reason for competitions


def future_time():
    """Define one date in the future."""
    ten_days_after = datetime.now() + timedelta(days=10)
    time_format = '%Y-%m-%d %H:%M:%S'
    return ten_days_after.strftime(time_format)


def get_new_club(club_index):
    """Test only with new club created by this method."""
    new_club = {
        "name": 'club' + str(club_index),
        "email": 'club' + str(club_index) + "@gmail.com",
        "points": "10"
    }
    return new_club


def get_new_competition(competition_index):
    """Test only with new competition created by this method."""
    competition_date = future_time()
    new_competition = {
        "name": 'competition' + str(competition_index),
        "date": competition_date,
        "number_of_places": "100"
    }
    return new_competition


# To create different clubs and competitions for tests.
index = 0


class WebUser(HttpUser):
    wait_time = between(1, 10)
    competition = {}
    club = {}

    def on_start(self):
        """Setup: each test, create and use one couple of club and competition"""
        global index
        self.competition = get_new_competition(index)  # competition used for tests
        self.club = get_new_club(index)  # club used for tests
        clubs.append(self.club)
        competitions.append(self.competition)
        update_clubs_json({"clubs": clubs})
        update_competitions_json({"competitions": competitions})
        index = index + 1

    @task
    def index_page(self):
        self.client.get("/")

    @task
    def login(self):
        self.client.post(
            "/showSummary", data=dict(
                email=self.club["email"],
            ), allow_redirects=True)

    @task
    def logout(self):
        self.client.get("/logout")

    @task
    def purchase_places(self):
        club_name = self.club["name"]
        competition_name = self.competition["name"]
        places_required = 1

        self.client.post("/purchasePlaces", data=dict(
            places=places_required,
            club=club_name,
            competition=competition_name),
                         allow_redirects=True)

    def on_stop(self):
        """Teardown: after all tests, come back to the original data."""
        clubs.pop()
        competitions.pop()
        update_competitions_json({"competitions": COMPETITIONS})
        update_clubs_json({"clubs": CLUBS})
