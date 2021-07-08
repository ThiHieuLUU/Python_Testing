from datetime import timedelta, datetime

from flask_testing import TestCase

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


def future_time():
    """Define one date in the future."""
    ten_days_after = datetime.now() + timedelta(days=10)
    time_format = '%Y-%m-%d %H:%M:%S'
    return ten_days_after.strftime(time_format)


class IntegrationTest(TestCase):

    def create_app(self):
        app.config["TESTING"] = True
        return app

    def setUp(self):
        # Build a club and a competition such that all test conditions pass
        clubs = load_clubs()
        club = clubs[0]
        club["points"] = str(MAX_PLACES)
        update_clubs_json({"clubs": clubs})

        self.clubs = load_clubs()
        self.club = self.clubs[0]

        competitions = load_competitions()
        competition = competitions[0]
        # Build a future competition
        competition["date"] = future_time()
        competition["number_of_places"] = str(MAX_PLACES*2)
        update_competitions_json({"competitions": competitions})

        self.competitions = load_competitions()
        self.competition = self.competitions[0]

    def tearDown(self):
        # Turn back to original json data
        update_clubs_json({"clubs": CLUBS})
        update_competitions_json({"competitions": COMPETITIONS})

    def test_integration(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('index.html')
        self.assertContext("clubs", self.clubs)

        response = self.client.post("/showSummary", data={"email": self.club["email"]})
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('welcome.html')
        self.assertContext("club", self.club)
        self.assertContext("competitions", self.competitions)
        self.assertContext("clubs", self.clubs)

        response = self.client.get(f'/book/{self.competition["name"]}/{self.club["name"]}')
        assert response.status_code == 200
        self.assert_template_used('booking.html')
        self.assertContext("club", self.club)
        self.assertContext("competition", self.competition)

        data = {
            "competition": self.competition["name"],
            "club": self.club["name"],
            "places": int((MAX_PLACES/NUMBER_OF_POINTS_PER_PLACE) - 1),  # here, 12/3 - 1 = 3
        }
        response = self.client.post("/purchasePlaces", data=data)

        # Club's points and competition's number_of_places must be reduced correctly
        self.club["points"] = str(int(self.club["points"]) - data["places"] * NUMBER_OF_POINTS_PER_PLACE)
        self.competition["number_of_places"] = str(int(self.competition["number_of_places"]) - data["places"])

        assert response.status_code == 200
        self.assert_template_used('welcome.html')

        self.assertContext("club", self.club)
        self.assertContext("competitions", self.competitions)
        self.assertContext("clubs", self.clubs)

        response = self.client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        self.assert_template_used('index.html')
        self.assertContext("clubs", self.clubs)

