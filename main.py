from flask import Flask, request, jsonify
from dateutil import parser as date_parser  # for parsing ISO 8601 datetimes

from db.repository import create_tables, add_traffic_record

app = Flask(__name__)


@app.route('/new_register', methods=['PUT'])
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


if __name__ == '__main__':
    # Create or update tables on startup
    create_tables()

    # Run the Flask app
    app.run(host="localhost", port=6000, debug=True)
