from flask import Blueprint, request, jsonify
from datetime import datetime
from database import users_collection, temp_users_collection, history_collection
from helpers import update_station, get_german_time
import pytz

update_bp = Blueprint("update", __name__)

@update_bp.route("/update", methods=["POST"])
def update_status():
    data = request.get_json()
    uid = data.get('uid')
    action = data.get('action')
    station = data.get('station')
    user = users_collection.find_one({'uid': uid})

    current_time = get_german_time()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    if user:
        update_station(station, action)
        if action == "Betreten":
            history_collection.insert_one({
                "uid": uid,
                "user_id": user["_id"],
                "station": station,
                "start_time": formatted_time,
                "end_time": None,
                "duration": None
            })
        elif action == "Verlassen":
            last_entry = history_collection.find_one({"uid": uid, "station": station, "end_time": None}, sort=[('_id', -1)])
            if last_entry:
                start_dt = datetime.strptime(last_entry["start_time"], "%Y-%m-%d %H:%M:%S")
                start_dt = pytz.timezone("Europe/Berlin").localize(start_dt)
                duration = get_german_time() - start_dt
                duration_str = f"{duration.seconds // 3600}h {duration.seconds % 3600 // 60}min"
                history_collection.update_one({"_id": last_entry["_id"]}, {"$set": {"end_time": formatted_time, "duration": duration_str}})

        return jsonify({"status": "success", "name": user['name'], "surname": user['surname']})

    else:
        temp_users_collection.insert_one({"uid": uid, "action": action, "station": station})
        return jsonify({"status": "user_not_found", "temp_user_created": True})