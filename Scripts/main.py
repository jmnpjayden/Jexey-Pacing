from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os

# Flask Application

app = Flask(__name__)
CORS(app)

# Project Folders

# Location of this file:
# Jexey Pacing/Scripts/main.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Main project folder:
# Jexey Pacing/
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# HTML and CSS folders
HTML_FOLDER = os.path.join(PROJECT_ROOT, "HTML")
CSS_FOLDER = os.path.join(PROJECT_ROOT, "CSS")

# CSV file
CSV_FILE = os.path.join(PROJECT_ROOT, "timeTrials.csv")


print("=" * 60)
print("JEXEY PACING")
print("=" * 60)
print(f"Project folder: {PROJECT_ROOT}")
print(f"HTML folder:    {HTML_FOLDER}")
print(f"CSS folder:     {CSS_FOLDER}")
print(f"CSV file:       {CSV_FILE}")
print("=" * 60)


# Create CSV if it doesn't exist

if not os.path.exists(CSV_FILE):
    empty_df = pd.DataFrame(
        columns=["Athlete", "Event", "Time"]
    )

    empty_df.to_csv(CSV_FILE, index=False)

    print("Created new timeTrials.csv file.")

else:
    print("timeTrials.csv already exists.")

# Load Existing Data

try:
    df = pd.read_csv(CSV_FILE)

    # Make sure the expected columns exist
    expected_columns = ["Athlete", "Event", "Time"]

    for column in expected_columns:
        if column not in df.columns:
            df[column] = None

    df = df[expected_columns]

except Exception as e:
    print(f"Error loading CSV: {e}")

    df = pd.DataFrame(
        columns=["Athlete", "Event", "Time"]
    )


print(f"Current results in CSV: {len(df)}")

# Website Pages

@app.route("/")
def serve_front_page():
    """
    Serve the Jexey Pacing front page.
    """

    return send_from_directory(
        HTML_FOLDER,
        "frontPage.html"
    )


@app.route("/frontPage.html")
def serve_front_page_file():
    """
    Also allow /frontPage.html directly.
    """

    return send_from_directory(
        HTML_FOLDER,
        "frontPage.html"
    )


@app.route("/main")
def serve_main_page():
    """
    Serve the main results page.
    """

    return send_from_directory(
        HTML_FOLDER,
        "mainPage.html"
    )


@app.route("/mainPage.html")
def serve_main_page_file():
    """
    Also allow /mainPage.html directly.
    """

    return send_from_directory(
        HTML_FOLDER,
        "mainPage.html"
    )


# HTML Files

@app.route("/HTML/<path:filename>")
def serve_html_files(filename):
    """
    Serve HTML files from the HTML folder.
    """

    return send_from_directory(
        HTML_FOLDER,
        filename
    )

# CSS Files

@app.route("/CSS/<path:filename>")
def serve_css_files(filename):
    """
    Serve CSS files from the CSS folder.
    """

    return send_from_directory(
        CSS_FOLDER,
        filename
    )


# Prediction Function

def predict_time(event_from, event_to, time_from):
    """
    Estimate another race distance using simple
    track-performance ratios.
    """

    ratios = {
        ("100m", "200m"): 2.03,
        ("100m", "400m"): 4.70,

        ("200m", "100m"): 0.49,
        ("200m", "400m"): 2.31,

        ("400m", "100m"): 0.21,
        ("400m", "200m"): 0.43,
    }

    ratio = ratios.get(
        (event_from, event_to),
        1
    )

    return time_from * ratio


# API: Test Server

@app.route("/api/test", methods=["GET"])
def test():
    """
    Check whether the Flask server is running.
    """

    return jsonify({
        "status": "Server is running!"
    })

# API: Add Athlete Time

@app.route("/api/add_time", methods=["POST"])
def add_time():
    """
    Save an athlete's result to timeTrials.csv.
    """

    global df

    try:

        # Get JSON sent by the website
        data = request.get_json()

        if not data:
            return jsonify({
                "status": "error",
                "message": "No data was received."
            }), 400

        # Get submitted information

        athlete_name = str(
            data.get("aname", "")
        ).strip()

        event_name = str(
            data.get("ename", "")
        ).strip()

        time_value = data.get("time")

        # Validate athlete name

        if not athlete_name:

            return jsonify({
                "status": "error",
                "message": "Athlete name is required."
            }), 400

        # Validate event

        allowed_events = [
            "100m",
            "200m",
            "400m"
        ]

        if event_name not in allowed_events:

            return jsonify({
                "status": "error",
                "message": "Invalid event."
            }), 400

        # Validate time

        try:

            time_value = float(time_value)

        except (TypeError, ValueError):

            return jsonify({
                "status": "error",
                "message": "Time must be a number."
            }), 400


        if time_value <= 0:

            return jsonify({
                "status": "error",
                "message": "Time must be greater than zero."
            }), 400


        # Create new row

        new_row = pd.DataFrame({
            "Athlete": [athlete_name],
            "Event": [event_name],
            "Time": [time_value]
        })

        # Add row to existing data

        df = pd.concat(
            [df, new_row],
            ignore_index=True
        )

        # Save to CSV

        df.to_csv(
            CSV_FILE,
            index=False
        )


        print(
            f"Saved result: "
            f"{athlete_name} | "
            f"{event_name} | "
            f"{time_value}"
        )


        # Return success

        return jsonify({
            "status": "success",
            "message": "Result saved successfully.",
            "total_rows": len(df)
        })


    except Exception as e:

        print(f"Error saving result: {e}")

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# API: Predict Splits

@app.route("/api/predict_splits", methods=["POST"])
def predict_splits():
    """
    Calculate split predictions for the athlete.
    """

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No data received."
            }), 400


        event_name = data.get("ename")
        athlete_name = data.get("aname")

        try:

            total_time = float(
                data.get("time")
            )

        except (TypeError, ValueError):

            return jsonify({
                "error": "Time must be a number."
            }), 400


        if total_time <= 0:

            return jsonify({
                "error": "Time must be greater than zero."
            }), 400


        print(
            f"Predicting splits for "
            f"{athlete_name}, "
            f"{event_name}, "
            f"{total_time}"
        )


        predictions = {}


        # 400m

        if event_name == "400m":

            per_100m = total_time / 4

            predictions["100m"] = round(
                per_100m,
                2
            )

            predictions["200m"] = round(
                per_100m * 2,
                2
            )

            predictions["300m"] = round(
                per_100m * 3,
                2
            )


        # 200m

        elif event_name == "200m":

            predictions["100m"] = round(
                total_time / 2,
                2
            )


        # 100m

        elif event_name == "100m":

            predictions["60m"] = round(
                total_time * 0.60,
                2
            )

            predictions["50m"] = round(
                total_time / 2,
                2
            )

            predictions["predicted_200m"] = round(
                predict_time(
                    "100m",
                    "200m",
                    total_time
                ),
                2
            )

            predictions["predicted_400m"] = round(
                predict_time(
                    "100m",
                    "400m",
                    total_time
                ),
                2
            )


        else:

            return jsonify({
                "error": "Invalid event."
            }), 400


        print(
            f"Predictions: {predictions}"
        )


        return jsonify(predictions)


    except Exception as e:

        print(
            f"Error in predict_splits: {e}"
        )

        return jsonify({
            "error": str(e)
        }), 500


# API: Get All Data

@app.route("/api/all_data", methods=["GET"])
def get_all_data():
    """
    Return all saved athlete results.
    Useful for testing/debugging.
    """

    try:

        data = df.to_dict(
            orient="records"
        )

        return jsonify({
            "data": data,
            "total_rows": len(data)
        })


    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# Start Flask
# ============================================================
if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("Starting Jexey Pacing Flask Server")
    print("=" * 60)
    print("Website:")
    print("http://127.0.0.1:5000")
    print()
    print("Test API:")
    print("http://127.0.0.1:5000/api/test")
    print("=" * 60 + "\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )