from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

BASE = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE, "models", "exercises_optionA_varied_v3.csv")

try:
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip().str.lower()

    
    for c in ["day_index", "order", "sets", "reps", "duration_sec"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    print("Loaded exercises CSV:", CSV_PATH)
except Exception as e:
    print("Failed loading CSV:", e)
    df = pd.DataFrame()

VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}

def clean_row_for_output(r):
    out = {"exercise_name": r["exercise_name"]}
    if int(r.get("sets", 0)) > 0:
        out["sets"] = int(r["sets"])
    if int(r.get("reps", 0)) > 0:
        out["reps"] = int(r["reps"])
    if int(r.get("duration_sec", 0)) > 0:
        out["duration_sec"] = int(r["duration_sec"])
    return out


@app.route("/", methods=["GET"])
def home():
    return "Exercise API (CSV lookup) running!"

@app.route("/get_day_exercises", methods=["POST"])
def get_day_exercises():
    if df.empty:
        return jsonify({"error": "Dataset not loaded"}), 500

    payload = request.get_json(force=True) or {}
    workout_type = payload.get("workout_type")
    fitness_level = payload.get("fitness_level")
    day_index = payload.get("day_index")

    if not workout_type or not fitness_level or day_index is None:
        return jsonify({"error": "Provide workout_type, fitness_level, and day_index"}), 400

    try:
        day_index = int(day_index)
    except ValueError:
        return jsonify({"error": "day_index must be an integer"}), 400

    
    filtered = df[
        (df["workout_type"] == workout_type) &
        (df["fitness_level"] == fitness_level) &
        (df["day_index"] == day_index)
    ].sort_values("order")

    
    if filtered.empty and fitness_level != "Beginner":
        filtered = df[
            (df["workout_type"] == workout_type) &
            (df["fitness_level"] == "Beginner") &
            (df["day_index"] == day_index)
        ].sort_values("order")

    if filtered.empty:
        return jsonify({"message": "No exercises found for given inputs"}), 404

    plan = [clean_row_for_output(row) for _, row in filtered.iterrows()]
    return jsonify({
        "workout_type": workout_type,
        "fitness_level": fitness_level,
        "day_index": day_index,
        "plan": plan
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
