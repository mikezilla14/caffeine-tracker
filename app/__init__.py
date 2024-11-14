import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend to avoid tkinter issues

from flask import Flask, request, jsonify, render_template
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta  # Import timedelta here

app = Flask(__name__)

# Initialize global intake data to store caffeine intake entries
intake_data = []

# Caffeine decay function based on exponential decay
def calculate_caffeine_concentration(dose, hours_since_intake, half_life=5):
    decay_constant = np.log(2) / half_life
    return dose * np.exp(-decay_constant * hours_since_intake)

# Route for main page with intake form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle intake submissions and update concentrations

@app.route('/add_intake', methods=['POST'])
def add_intake():
    data = request.json
    dose = float(data.get('dose'))
    time_str = data.get('time')

    # Use today's date with the specified hour and minute
    intake_time = datetime.now().replace(
        hour=int(time_str[:2]),
        minute=int(time_str[3:5]),
        second=0,
        microsecond=0
    )

    intake_data.append({'dose': dose, 'time': intake_time})

    # Debug: Print the corrected intake time
    print(f"Corrected intake time: {intake_time}")

    return jsonify({"message": "Intake added successfully"}), 200


# Route to calculate and plot caffeine concentration timeline
@app.route('/plot_concentration')
def plot_concentration():
    hours_before = 12  # Hours before the current time to display
    hours_after = 12  # Hours after the current time to display
    total_hours = hours_before + hours_after  # Total 24-hour window

    # Calculate start time 12 hours before and end time 12 hours after
    current_time = datetime.now()
    start_time = current_time - timedelta(hours=hours_before)
    concentrations = np.zeros(total_hours)  # Initialize an array for concentrations

    # Debug: Print current intake data
    print("Current intake data:", intake_data)

    # Calculate cumulative concentration for each hour based on intakes
    for entry in intake_data:
        dose = entry['dose']
        hours_since_intake = (current_time - entry['time']).total_seconds() / 3600

        # Debug: Print each intake and the calculated hours since intake
        print(f"Intake: {dose} mg at {entry['time']}, hours since intake: {hours_since_intake}")

        for hour in range(-hours_before, hours_after):
            if hours_since_intake + hour >= 0:
                concentrations[hour + hours_before] += calculate_caffeine_concentration(dose, hours_since_intake + hour)

    # Generate x-axis labels relative to the current time
    time_labels = [(start_time + timedelta(hours=hour)).strftime("%H:%M") for hour in range(total_hours)]

    # Debug: Print final concentrations array
    print("Concentrations over time:", concentrations)

    # Plotting the cumulative concentration over time
    plt.figure(figsize=(12, 6))
    plt.plot(range(total_hours), concentrations, label="Cumulative Caffeine Concentration")
    plt.xticks(range(total_hours), time_labels, rotation=45, ha='right')  # Show time labels on x-axis
    plt.xlabel("Time")
    plt.ylabel("Caffeine Concentration (mg)")
    plt.title("Caffeine Concentration Timeline (12 Hours Before and After Now)")
    plt.legend()
    plt.grid(True)

    # Convert plot to image
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return jsonify({"plot": image_base64}), 200

@app.route('/get_intakes')
def get_intakes():
    # Format intake data for JSON response
    formatted_data = [
        {"dose": entry["dose"], "time": entry["time"].strftime("%Y-%m-%d %H:%M:%S")}
        for entry in intake_data
    ]
    return jsonify(formatted_data)