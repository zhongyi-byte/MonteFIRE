from flask import Flask, request, jsonify, send_from_directory
from simulation_logic import FIRESimulator
import os

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json
    
    # Parse Config
    config = {
        'current_age': int(data.get('current_age', 25)),
        'life_expectancy': int(data.get('life_expectancy', 90)),
        'current_assets': float(data.get('current_assets', 100)),
        'annual_income': float(data.get('annual_income', 56)),
        'annual_expense': float(data.get('annual_expense', 12)),
        'simulations': int(data.get('simulations', 1000)),
        'inflation_mean': float(data.get('inflation_mean', 0.035)),
        'return_mean': float(data.get('return_mean', 0.05)), # Simplified mapping if needed, but logic uses min/max
        'return_min': float(data.get('return_min', -0.10)),
        'return_max': float(data.get('return_max', 0.15)),
        'post_retirement_income': float(data.get('post_retirement_income', 0)),
    }
    
    simulator = FIRESimulator(config)
    
    # Range
    start_age = int(data.get('retire_age_start', 35))
    end_age = int(data.get('retire_age_end', 60))
    
    results = simulator.run_simulation(start_age, end_age)
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
