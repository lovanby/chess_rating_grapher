"""
Chess Rating Tracker
=====================
Pulls rating history for two users (for now) from Lichess and/or
Chess.com and plots it either by games played or by date.
Chart can be downloaded as a .png file.

Install deps:
    pip install requests matplotlib flask

Usage:
    Run main.py and go to http://127.0.0.1:5000 to access input form.
"""

import json
import time
import datetime as dt
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
from flask import Flask, send_file, request, render_template

HEADERS = {"User-Agent": "chess-rating-tracker/1.0 (personal use)"}

app = Flask(__name__)

# ---------------------------------------------------------------------------
# LICHESS
# ---------------------------------------------------------------------------
def get_lichess_history(username: str, game_type="rapid"):
    """
    Returns a list of (date, rating) tuples, ONE PER GAME PLAYED, for the
    chosen variant. Uses Lichess's games export API (NDJSON stream) rather
    than the rating-history endpoint, since the latter only gives one
    point per day the rating changed -- not per game.
    """
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "rated": "true",
        "perfType": game_type,
        "sort": "dateAsc",
        "moves": "false",
        "opening": "false",
        "clocks": "false",
        "evals": "false",
        "pgnInJson": "false",
    }
    headers = {**HEADERS, "Accept": "application/x-ndjson"}

    r = requests.get(url, params=params, headers=headers, stream=True, timeout=60)
    r.raise_for_status()

    uname_lower = username.lower()
    points = []
    for line in r.iter_lines():
        if not line:
            continue
        game = json.loads(line)

        players = game.get("players", {})
        white = players.get("white", {}).get("user", {})
        black = players.get("black", {}).get("user", {})

        if white.get("id", "").lower() == uname_lower:
            rating = players["white"].get("rating")
        elif black.get("id", "").lower() == uname_lower:
            rating = players["black"].get("rating")
        else:
            continue  # e.g. game vs. an anonymous/AI account missing user id

        if rating is None:
            continue

        created_ms = game.get("createdAt")
        date = dt.date.fromtimestamp(created_ms / 1000) if created_ms else None
        points.append((date, rating))

    return points  # already chronological due to sort=dateAsc


# ---------------------------------------------------------------------------
# CHESS.COM
# ---------------------------------------------------------------------------
def get_chesscom_history(username: str, game_type="rapid"):
    """
    Returns a list of (date, rating) tuples, one per game played,
    by walking through the player's monthly game archives.
    """
    username = username.lower()
    archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    r = requests.get(archives_url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    archive_urls = r.json()["archives"]

    points = []
    for url in archive_urls:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            continue
        games = resp.json().get("games", [])
        for game in games:
            if game.get("time_class") != game_type:
                continue
            white = game.get("white", {})
            black = game.get("black", {})
            if white.get("username", "").lower() == username:
                rating = white.get("rating")
            elif black.get("username", "").lower() == username:
                rating = black.get("rating")
            else:
                continue
            date = dt.date.fromtimestamp(game["end_time"])
            points.append((date, rating))
        time.sleep(0.2)  # be polite to the API

    return sorted(points)


# ---------------------------------------------------------------------------
# PLOTTING
# ---------------------------------------------------------------------------
def rolling_average(values, window=10):
    """
    Simple trailing rolling average with no extra dependencies.
    For index i, averages over the trailing `window` points (or fewer
    at the start, so the line still starts at point 1 instead of being
    cut off).
    """
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start:i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def plot_ratings(players: dict, chart_type, window: int = 10):
    """
    players: dict like {"key": ([(date, rating), ...], label)}
    chart_type: "date" or "games"
    window: rolling average window size (in data points)
    """
    plt.figure(figsize=(10, 6))
    try:

        # Give each player a consistent colour for raw + smoothed lines
        color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        for i, (key, (points, label)) in enumerate(players.items()):
            if not points:
                print(f"No data for {key}, skipping.")
                continue

            color = color_cycle[i % len(color_cycle)]

            if chart_type == "games":
                x = list(range(1, len(points) + 1))
            else:
                x = [p[0] for p in points]
            y = [p[1] for p in points]

            # Raw data, faded
            plt.plot(x, y, linewidth=1, alpha=0.25, color=color)

            # Rolling average, full opacity, on top
            smoothed = rolling_average(y, window=window)
            plt.plot(x, smoothed, linewidth=2, alpha=1.0, color=color, label=label)

        plt.xlabel("Games played" if chart_type == "games" else "Date")
        plt.ylabel("Rating")
        plt.title(f"Rating Progress ({'games played' if chart_type == 'games' else 'date'}, "
                  f"{window}-point rolling avg)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, dpi=150, format='png')
        buf.seek(0)

    finally:
        plt.close()

    return buf

@app.route("/")
def home():
    return render_template("form.html")

@app.route("/generate-chart", methods=['POST'])
def generate_chart():
    user_data = {}
    i = 1

    # Run indefinitely until hitting an empty row
    while True:
        if f"user{i}_username" not in request.form:
            break

        username = request.form.get(f"user{i}_username").strip()
        label = request.form.get(f"user{i}_name", "").strip()
        platform = request.form.get(f"user{i}_platform").strip()
        game_type = request.form.get(f"user{i}_gametype").strip()

        # Combine into key
        key = f"{username} {platform} {game_type}"

        user_data[key] = (platform, username, game_type, label)

        i += 1
    chart_type = request.form["chart_type"]

    results = {}
    for key, (platform, username, game_type, label) in user_data.items():
        print(f"Fetching {label} ({platform}: {username})...")
        try:
            if platform == "lichess":
                results[key] = (get_lichess_history(username, game_type), label)
            elif platform == "chesscom":
                results[key] = (get_chesscom_history(username, game_type), label)
        except requests.HTTPError as e:
            print(f"  Failed: {e}")
            results[key] = [[], label]
    return send_file(plot_ratings(results, chart_type), mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)