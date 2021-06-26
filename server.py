from collections import OrderedDict
import json
from flask import Flask, render_template, request, redirect, flash, url_for, abort

MAX_PLACES = 12


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
    return render_template('index.html')


@app.route('/showSummary', methods=['POST'])
def show_summary():
    try:
        club = [club for club in clubs if club['email'] == request.form['email']][0]
    except IndexError:
        abort(404, "Sorry, that email wasn't found.")
    return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/book/<competition>/<club>')
def book(competition, club):
    found_club = [c for c in clubs if c['name'] == club][0]
    found_competition = [c for c in competitions if c['name'] == competition][0]
    if found_club and found_competition:
        return render_template('booking.html', club=found_club, competition=found_competition)
    else:
        flash("Something went wrong - please try again")
        return render_template('welcome.html', club=club, competitions=competitions)


@app.route('/purchasePlaces', methods=['POST'])
def purchase_places():
    competitions_updated = load_competitions()
    clubs_updated = load_clubs()

    competition = [c for c in competitions_updated if c['name'] == request.form['competition']][0]
    club = [c for c in clubs_updated if c['name'] == request.form['club']][0]

    places_required = int(request.form['places'])
    available_point = int(club['points'])
    available_places = int(competition['number_of_places'])

    booking_conditions = {
        "available_point": available_point,
        "max_places": MAX_PLACES,
        "available_places": available_places
    }

    error_messages = {
        "available_point": "You can't book more than your available points!",
        "max_places": "You can't book more than 12 places!",
        "available_places": "You can't book more than available places of this competition!"
    }

    # sorted the dictionary by value using OrderedDict
    booking_conditions_sorted = OrderedDict(sorted(booking_conditions.items(), key=lambda item: item[1]))
    sorted_keys = list(booking_conditions_sorted.keys())
    key_condition = sorted_keys[0]

    value_condition = booking_conditions[key_condition]
    error_message = error_messages[key_condition]

    # Display only the error message associated with the smallest value for different conditions
    # Here, there are 3 conditions to check: available_point, available_places and MAX_PLACES
    # This avoids to depend on the order of if conditions
    if places_required > value_condition:
        abort(403, description=error_message)
    else:
        competition['number_of_places'] = available_places - places_required
        flash('Great - booking complete!')
        return render_template('welcome.html', club=club, competitions=competitions)


# TODO: Add route for points display


@app.route('/logout')
def logout():
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
