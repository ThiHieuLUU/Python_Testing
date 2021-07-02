from datetime import datetime

from collections import OrderedDict
import json
from flask import Flask, render_template, request, redirect, flash, url_for, abort

MAX_PLACES = 12
NUMBER_OF_POINTS_PER_PLACE = 3


def load_clubs():
    with open('clubs.json') as c:
        list_of_clubs = json.load(c)['clubs']
        return list_of_clubs


def load_competitions():
    with open('competitions.json') as comps:
        list_of_competitions = json.load(comps)['competitions']
        return list_of_competitions


def update_clubs_json(updated_clubs):
    with open("clubs.json", "w") as c:
        json.dump(updated_clubs, c)


def update_competitions_json(updated_competitions):
    with open("competitions.json", "w") as comps:
        json.dump(updated_competitions, comps)


app = Flask(__name__)
app.secret_key = 'something_special'

competitions = load_competitions()
clubs = load_clubs()


@app.route('/')
def index():
    clubs_updated = load_clubs()
    return render_template('index.html', clubs=clubs_updated)


@app.route('/showSummary', methods=['POST'])
def show_summary():
    competitions = load_competitions()
    clubs = load_clubs()
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
    except IndexError:
        abort(404, "Sorry, that email wasn't found.")
    return render_template('welcome.html', club=club, competitions=competitions, clubs=clubs)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    found_club = [c for c in clubs if c['name'] == club][0]
    found_competition = [c for c in competitions if c['name'] == competition][0]
    if found_club and found_competition:
        return render_template('booking.html', club=found_club, competition=found_competition)
    else:
        flash("Something went wrong - please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


def build_dict(seq, key):
    return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))


@app.route('/purchasePlaces', methods=['POST'])
def purchase_places():
    # Reload clubs and competitions in order to have updated information.
    competitions_updated = load_competitions()
    clubs_updated = load_clubs()

    competitions_dict = build_dict(competitions_updated, key="name")
    competition_name = request.form['competition']
    competition = competitions_dict.get(competition_name)  # index key is added in information of competition
    competition_index = competition["index"]  # index of the competition in the list from json file

    clubs_dict = build_dict(clubs_updated, key="name")
    club_name = request.form['club']
    club = clubs_dict.get(club_name)  # index key is added in information of club
    club_index = club["index"]  # index of the competition in the list from json file

    places_required = int(request.form['places'])
    available_point = int(club['points'])
    available_places = int(competition['number_of_places'])

    booking_conditions = {
        "available_club_ability": int(available_point/NUMBER_OF_POINTS_PER_PLACE),
        "max_places": MAX_PLACES,
        "available_places": available_places
    }

    error_messages = {
        # "available_point": "You can't book more than your available points!",
        "available_club_ability": "You can't book more than a third of your available points!",
        "max_places": "You can't book more than 12 places!",
        "available_places": "You can't book more than available places of this competition!"
    }

    # sorted the dictionary by value using OrderedDict
    booking_conditions_sorted = OrderedDict(sorted(booking_conditions.items(), key=lambda item: item[1]))
    sorted_keys = list(booking_conditions_sorted.keys())
    key_condition = sorted_keys[0]

    value_condition = booking_conditions[key_condition]
    error_message = error_messages[key_condition]

    # Checking if the competition is in the past.
    if datetime.fromisoformat(competition["date"]) <= datetime.now():
        abort(400, description="You can't book this past competition!")

    # Display only the error message associated with the smallest value for different conditions
    # Here, there are 3 conditions to check: available_point, available_places and MAX_PLACES
    # Sorting conditions allows to avoid the depend on the order of if conditions and display correctly error.
    if places_required > value_condition:
        abort(403, description=error_message)
    elif places_required < 0:
        abort(403, description="You can't book a negative number of places")
    else:
        # competition['number_of_places'] = available_places - places_required
        flash('Great - booking complete!')

        new_available_point = available_point - places_required*NUMBER_OF_POINTS_PER_PLACE
        new_number_of_places = available_places - places_required

        # Update club's point after purchase
        club['points'] = str(new_available_point)

        clubs_updated[club_index]['points'] = str(new_available_point)
        competitions_updated[competition_index]['number_of_places'] = str(new_number_of_places)

        # Save the change into json files
        update_clubs_json({"clubs": clubs_updated})
        update_competitions_json({"competitions": competitions_updated})

        return render_template('welcome.html', club=club, competitions=competitions_updated, clubs=clubs_updated)


# TODO: Add route for points display
@app.route('/clubsPoints')
def display_clubs_points():
    clubs_updated = load_clubs()
    return render_template('index.html', clubs=clubs_updated)


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
