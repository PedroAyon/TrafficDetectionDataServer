from flask import Flask, request, jsonify
from dateutil import parser as date_parser  # for parsing ISO 8601 datetimes
from data.repository import *
from db.database import create_tables

app = Flask(__name__)


@app.route('/new_register', methods=['POST'])
def new_register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    required_fields = [
        "traffic_cam_id",
        "start_datetime",
        "end_datetime",
        "vehicle_count",
        "average_speed"
    ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    print(f"Received new register: {data}")

    try:
        start_time = date_parser.isoparse(data['start_datetime'])
        end_time = date_parser.isoparse(data['end_datetime'])

        # Use the repository method to insert the record
        add_traffic_record(
            device_id=data['traffic_cam_id'],
            start_time=start_time,
            end_time=end_time,
            vehicle_count=data['vehicle_count'],
            average_speed=data['average_speed']
        )

        return jsonify({"message": "Register received successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/cities', methods=['GET'])
def list_cities():
    try:
        cities = get_available_cities()
        return jsonify({"cities": cities}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/cams/<string:city>', methods=['GET'])
def cams_by_city(city):
    try:
        cams = get_cams_by_city(city)
        # Serialize each TrafficCam object to dict
        cams_list = [
            {
                "id": cam.id,
                "alias": cam.alias,
                "city": cam.city,
                "latitude": float(cam.location_lat),
                "longitude": float(cam.location_lng)
            }
            for cam in cams
        ]
        return jsonify({"cams": cams_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/traffic/<int:traffic_cam_id>', methods=['GET'])
def traffic_state(traffic_cam_id):
    try:
        state = get_traffic_state(traffic_cam_id)
        # Assuming state is an Enum, return its name
        return jsonify({"traffic_state": state.name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    create_tables()

    app.run(host="localhost", port=6000, debug=True)
