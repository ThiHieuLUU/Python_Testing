from datetime import timedelta, datetime
from locust import HttpUser, TaskSet, task, constant, between
from server import app
from server import (
    app,
    load_clubs,
    load_competitions,
    update_clubs_json,
    update_competitions_json,
    MAX_PLACES
)

# # The original data
# CLUBS = load_clubs()
# NB_CLUBS = len(CLUBS)
#
# COMPETITIONS = load_competitions()
# NB_COMPETITIONS = len(COMPETITIONS)

# The data to test
clubs = load_clubs()  # Not doing: clubs = CLUBS because copy of list will make changing CLUBS if clubs change
competitions = load_competitions()  # the same reason for competitions

# number_clubs_to_simulate = 6
# competition = competitions[0]
#
#
# def append_to_clubs(n):
#     club_number = 0
#
#     for i in range(n):
#         new_club = {
#             "name": 'club' + str(club_number),
#             "email": 'club' + str(club_number) + "@gmail.com",
#             "points": "10"
#         }
#         club_number += 1
#         clubs.append(new_club)
#         club_number += 1
#         clubs.append(new_club)
#     return clubs
#
# clubs = append_to_clubs(number_clubs_to_simulate)
# update_clubs_json({"clubs": clubs})
#
#
# index = 0



def future_time():
    """Define one date in the future."""
    ten_days_after = datetime.now() + timedelta(days=10)
    time_format = '%Y-%m-%d %H:%M:%S'
    return ten_days_after.strftime(time_format)

club0 = clubs[0]
competition0 = competitions[0]
competition0["date"] = future_time()

update_competitions_json({"competitions": competitions})

class UserBehaviour(HttpUser):
    wait_time = between(1, 10)
    # club = clubs[NB_CLUBS + index]
    club = club0
    competition = competition0

    @task
    def login(self):
        self.client.post(
            "/showSummary", data=dict(
                email=self.club["email"],
            ), allow_redirects=True)
        # global index
        # index += 1

    # @task
    # def purchase_places(self):
    #     club_name = self.club["name"]
    #     competition_name = self.competition["name"]
    #
    #     places_required = 1
    #     response = self.client.post("/purchasePlaces", data=dict(
    #         places=places_required,
    #         club=self.club["name"],
    #         competition=self.competition),
    #         allow_redirects=True)
    #
    @task
    def perf_purchasePlaces(self):
        # competition = "Ragnarok"
        # club = "The strongs"
        places = 4
        self.client.post("/purchasePlaces", data={ "competition": self.competition["name"], "club": self.club["name"], "places": places },  allow_redirects=True)

    @task
    def logout(self):
        self.client.get("/logout")

    @task
    def index_page(self):
        self.client.get("/")








# from datetime import timedelta, datetime
# from locust import HttpUser, TaskSet, task, between
# from server import (
#     app,
#     load_clubs,
#     load_competitions,
#     update_clubs_json,
#     update_competitions_json,
#     MAX_PLACES
# )
#
# # The original data
# CLUBS = load_clubs()
#
# COMPETITIONS = load_competitions()
#
# # The data to test
# clubs = load_clubs()  # Not doing: clubs = CLUBS because copy of list will make changing CLUBS if clubs change
# competitions = load_competitions()  # the same reason for competitions
#
#
# def future_time():
#     """Define one date in the future."""
#     ten_days_after = datetime.now() + timedelta(days=10)
#     time_format = '%Y-%m-%d %H:%M:%S'
#     return ten_days_after.strftime(time_format)
#
#
# def get_new_club(club_index):
#     new_club = {
#         "name": 'club' + str(club_index),
#         "email": 'club' + str(club_index) + "@gmail.com",
#         "points": "10"
#     }
#     return new_club
#
#
# def get_new_competition(competition_index):
#     competition_date = future_time()
#     new_competition = {
#         "name": 'competition' + str(competition_index),
#         "date": competition_date,
#         "number_of_places": "100"
#     }
#     return new_competition
#
#
# index = 0
#
#
# class WebUser(HttpUser):
#     wait_time = between(1, 10)
#
#     # competition = get_new_competition(index)
#     # club = get_new_club(index)
#     # competition = {}
#     # club = {}
#     club = clubs[0]
#
#     # def on_start(self):
#     #     global index
#     #     self.competition = get_new_competition(index)
#     #     self.club = get_new_club(index)
#     #     clubs.append(self.club)
#     #     competitions.append(self.competition)
#     #     update_clubs_json({"clubs": clubs})
#     #     update_competitions_json({"competitions": competitions})
#     #     index = index + 1
#
#     @task
#     def index_page(self):
#         self.client.get("/")
#
#     @task
#     def login(self):
#         self.club = clubs[0]
#         print(self.club)
#         self.client.post(
#             "/showSummary", data=dict(
#                 email=self.club["email"],
#             ), allow_redirects=True)
#
#     # def on_stop(self):
#     #     clubs.pop()
#     #     competitions.pop()
#     #     update_competitions_json({"competitions": COMPETITIONS})
#     #     update_clubs_json({"clubs": CLUBS})
#
#     # @task
#     # def purchase_places(self):
#     #     club_name = self.club["name"]
#     #     competition_name = self.competition["name"]
#     #
#     #     places_required = 1
#     #     response = self.client.post("/purchasePlaces", data=dict(
#     #         places=places_required,
#     #         club=self.club["name"],
#     #         competition=self.competition),
#     #         allow_redirects=True)
#     #
#     # @task
#     # def perf_purchasePlaces(self):
#     #     # competition = "Ragnarok"
#     #     # club = "The strongs"
#     #     places = 4
#     #     self.client.post("/purchasePlaces",
#     #                      data={"competition": self.competition["name"], "club": self.club["name"], "places": places},
#     #                      allow_redirects=True)
#     #
#     # @task
#     # def logout(self):
#     #     self.client.get("/logout")
#     #
#     # @task
#     # def index_page(self):
#     #     self.client.get("/")
