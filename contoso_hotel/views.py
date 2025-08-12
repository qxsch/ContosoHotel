from datetime import datetime, timedelta
import json
import requests
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from . import app, dblayer, config


#region -------- BACKEND API ENDPOINTS --------

@app.route("/api/setup", methods=["POST"])
def api_setup():
    try:
        record = json.loads(request.data)
        for k in ["drop_schema", "create_schema", "populate_data"]:
            if k not in record:
                record[k] = False
            record[k] = bool(record[k])
        for k, v in { "number_of_visitors" : 100, "min_bookings_per_visitor" : 1, "max_bookings_per_visitor" : 5 }.items():
            if k not in record:
                record[k] = v
            record[k] = int(record[k])
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 400
    try:
        return jsonify(dblayer.setupDb(record["drop_schema"], record["create_schema"], record["populate_data"], record["number_of_visitors"], record["min_bookings_per_visitor"], record["max_bookings_per_visitor"])), 201
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/longsqlrequest", methods=["GET"])
def api_longsqlrequest():
    try:
        return jsonify(dblayer.longsqlrequest()), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    conf = config.get_layout_configuration()
    try:
        record = json.loads(request.data)
        # validate data
        if "question" not in record:
            return jsonify({ "success" : False, "error" : "question is required" }), 400
        record["question"] = str(record["question"])
        if "chat_history" not in record:
            record["chat_history"] = []
        # do we have a demo chatbot?
        if conf.chatbot_baseurl == '/':
            return jsonify({ "answer" : "you said: " + record["question"] }), 200

        headers = {
            'Content-Type': 'application/json'
        }
        if conf.getChatbotApiKey() != '':
            headers['Authorization'] = f'Bearer {conf.getChatbotApiKey()}'
        response = requests.post(conf.getChatbotBaseurl()+'/score', json=record, headers=headers)
        if response.status_code >= 400:
            return jsonify({ "success" : False, "error" : "Chatbot returned the following http error code: " + str(response.status_code) + "\n\n" + response.text }), 502
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500


@app.route("/api/booking", methods=["DELETE", "PUT", "POST"])
def api_manage_booking():
    try:
        if request.method == "DELETE":
            bookingId = request.args.get("bookingId", None)
            if bookingId is None:
                return jsonify({ "success" : False, "error" : "bookingId is required" }), 400
            bookingId = int(bookingId)
            deleted = dblayer.delete_booking(bookingId)
            return jsonify({"success" : True, "deleted": deleted, "bookingId" : bookingId}), 200
        elif request.method == "PUT":
            record = json.loads(request.data)
            if "bookingId" in record:
                record["bookingId"] = int(record["bookingId"])
            else:
                record["bookingId"] = None
            # required values
            for k in ["visitorId", "hotelId", "adults"]:
                if k not in record:
                    return jsonify({ "success" : False, "error" : f"{k} is required" }), 400
                record[k] = int(record[k])
            for k in ["checkin", "checkout"]:
                if k not in record:
                    return jsonify({ "success" : False, "error" : f"{k} is required" }), 400
                try:
                    record[k] = datetime.fromisoformat(record[k])
                except ValueError:
                    # regex string starts with month/day/year
                    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", str(record[k]).strip())
                    if m:
                        record[k] = datetime.fromisoformat(f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}")
                    else:
                        return jsonify({ "success" : False, "error" : f"{k} has an invalid date time specification" }), 400
            # optional values
            for k in ["kids", "babies"]:
                if k not in record:
                    record[k] = 0
                record[k] = int(record[k])
            if "rooms" not in record:
                record["rooms"] = None
            else:
                record["rooms"] = int(record["rooms"])
            if "price" not in record:
                record["price"] = None
            else:
                record["price"] = float(record["price"])
            return jsonify(dblayer.create_booking(
                record["hotelId"],
                record["visitorId"],
                record["checkin"],
                record["checkout"],
                record["adults"],
                record["kids"],
                record["babies"],
                record["rooms"],
                record["price"],
                record["bookingId"]
            )), 200
        elif request.method == "POST":
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405
        else:
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405 
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/booking", methods=["GET"])
def api_get_booking():
    try:
        bookingId = request.args.get("bookingId", None)
        if bookingId is not None:
            bookingId = int(bookingId)
        else:
            return jsonify({ "success" : False, "error" : "bookingId is required" }), 400
        booking = dblayer.get_booking(bookingId)
        return jsonify(booking), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/bookings", methods=["GET"])
def api_get_bookings():
    try:
        visitorId = request.args.get("visitorId", None)
        if visitorId is not None:
            visitorId = int(visitorId)
        hotelId = request.args.get("hotelId", None)
        if hotelId is not None:
            hotelId = int(hotelId)
        fromdate = request.args.get("fromdate", None)
        if fromdate is not None:
            fromdate = datetime.fromisoformat(fromdate)
        untildate = request.args.get("untildate", None)
        if untildate is not None:
            untildate = datetime.fromisoformat(untildate)
        bookings = dblayer.get_bookings(visitorId, hotelId, fromdate, untildate)
        return jsonify(bookings), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500


@app.route("/api/hotel", methods=["DELETE", "PUT", "POST"])
def api_manage_hotel():
    try:
        if request.method == "DELETE":
            hotelId = request.args.get("hotelId", None)
            if hotelId is None:
                return jsonify({ "success" : False, "error" : "hotelId is required" }), 400
            hotelId = int(hotelId)
            deleted = dblayer.delete_hotel(hotelId)
            return jsonify({"success" : True, "deleted": deleted, "hotelId" : hotelId}), 200
        elif request.method == "PUT" or request.method == "POST":
            record = json.loads(request.data)
            if "hotelId" in record:
                if record["hotelId"] is not None:
                    record["hotelId"] = int(record["hotelId"])
            else:
                record["hotelId"] = None
            if record["hotelId"] is None and request.method == "POST":
                return jsonify({ "success" : False, "error" : "hotelId is required" }), 400
            if "pricePerNight" in record:
                record["pricePerNight"] = float(record["pricePerNight"])
            else:
                return jsonify({ "success" : False, "error" : "pricePerNight is required" }), 400
            if "totalRooms" in record:
                record["totalRooms"] = int(record["totalRooms"])
            else:
                return jsonify({ "success" : False, "error" : "totalRooms is required" }), 400
            if "hotelname" in record:
                record["hotelname"] = str(record["hotelname"])
            else:
                return jsonify({ "success" : False, "error" : "hotelname is required" }), 400
            if "country" in record:
                record["country"] = str(record["country"])
            else:
                record["country"] = None
            for k in [
                "skiing", "suites", "inRoomEntertainment", "conciergeServices", "housekeeping", "petFriendlyOptions", "laundryServices",
                "roomService", "indoorPool", "outdoorPool", "fitnessCenter", "complimentaryBreakfast", "businessCenter", "freeGuestParking",
                "complimentaryCoffeaAndTea", "climateControl", "bathroomEssentials"
            ]:
                if k not in record:
                    record[k] = None
                elif not (record[k] is None):
                    record[k] = str(record[k]).strip().lower() in ['true', '1', 'yes', 'y', 't']
            
            if request.method == "PUT":
                return jsonify(dblayer.create_hotel(
                    record["hotelname"], record["pricePerNight"], record["totalRooms"], record["hotelId"], record["country"],
                    record["skiing"], record["suites"], record["inRoomEntertainment"], record["conciergeServices"], record["housekeeping"],
                    record["petFriendlyOptions"], record["laundryServices"], record["roomService"], record["indoorPool"], record["outdoorPool"],
                    record["fitnessCenter"], record["complimentaryBreakfast"], record["businessCenter"], record["freeGuestParking"],
                    record["complimentaryCoffeaAndTea"], record["climateControl"], record["bathroomEssentials"]
                )), 200
            else:
                return jsonify(dblayer.update_hotel(
                    record["hotelname"], record["pricePerNight"], record["totalRooms"], record["hotelId"], record["country"],
                    record["skiing"], record["suites"], record["inRoomEntertainment"], record["conciergeServices"], record["housekeeping"],
                    record["petFriendlyOptions"], record["laundryServices"], record["roomService"], record["indoorPool"], record["outdoorPool"],
                    record["fitnessCenter"], record["complimentaryBreakfast"], record["businessCenter"], record["freeGuestParking"],
                    record["complimentaryCoffeaAndTea"], record["climateControl"], record["bathroomEssentials"]
                )), 200
        else:
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405 
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/hotel", methods=["GET"])
def api_get_hotel():
    try:
        hotelId = request.args.get("hotelId", None)
        if hotelId is not None:
            hotelId = int(hotelId)
        else:
            return jsonify({ "success" : False, "error" : "hotelId is required" }), 400
        hotel = dblayer.get_hotel(hotelId)
        return jsonify(hotel), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/hotels", methods=["GET"])
def api_get_hotels():
    try:
        exactMatch = request.args.get("exactMatch", "false", str).lower() == "true"
        hotelname = request.args.get("hotelname", "", str)
        hotels = dblayer.get_hotels(hotelname, exactMatch)
        return jsonify(hotels), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500


@app.route("/api/visitor", methods=["DELETE", "PUT", "POST"])
def api_manage_visitor():
    try:
        if request.method == "DELETE":
            visitorId = request.args.get("visitorId", None)
            if visitorId is None:
                return jsonify({ "success" : False, "error" : "visitorId is required" }), 400
            visitorId = int(visitorId)
            deleted = dblayer.delete_visitor(visitorId)
            return jsonify({"success" : True, "deleted": deleted, "visitorId" : visitorId}), 200
        elif request.method == "PUT" or request.method == "POST":
            record = json.loads(request.data)
            if "visitorId" in record:
                if record["visitorId"] is not None:
                    record["visitorId"] = int(record["visitorId"])
            else:
                record["visitorId"] = None
            if record["visitorId"] is None and request.method == "POST":
                return jsonify({ "success" : False, "error" : "visitorId is required" }), 400
            for k in ["firstname", "lastname"]:
                if k not in record:
                    return jsonify({ "success" : False, "error" : f"{k} is required" }), 400
                record[k] = str(record[k])
            if request.method == "PUT":
                return jsonify(dblayer.create_visitor(record["firstname"], record["lastname"], record["visitorId"])), 200
            else:
                return jsonify(dblayer.update_visitor(record["firstname"], record["lastname"], record["visitorId"])), 200
        else:
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405 
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/visitor", methods=["GET"])
def api_get_visitor():
    try:
        visitorId = request.args.get("visitorId", None)
        if visitorId is not None:
            visitorId = int(visitorId)
        else:
            return jsonify({ "success" : False, "error" : "visitorId is required" }), 400
        visitor = dblayer.get_visitor(visitorId)
        return jsonify(visitor), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/visitors", methods=["GET"])
def api_get_visitors(name : str = ""):
    try:
        exactMatch = request.args.get("exactMatch", "false", str).lower() == "true"
        name = request.args.get("name", "", str)
        visitors = dblayer.get_visitors(name, exactMatch)
        return jsonify(visitors), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

@app.route("/api/amenities", methods=["GET"])
def api_get_amenities():
    try:
        amenities = dblayer.get_amenities()
        return jsonify(amenities), 200
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 500

#endregion -------- BACKEND API ENDPOINTS --------


#region -------- FRONTEND API ENDPOINTS --------

@app.route("/setup")
def setup():
    return render_template("setup.html", config=config.get_layout_configuration())


@app.route("/")
def home():
    # ------- START: CHECK IF THE DATABASE IS SETUP -------
    #TODO: remove this check when splitting frontend and backend as dblayer doesn't exist in frontend
    if not dblayer.allTablesExists():
        return redirect(url_for("setup"))
    # ------- END: CHECK IF THE DATABASE IS SETUP -------
    return render_template("home.html", config=config.get_layout_configuration())


@app.route("/list")
def list():
    return render_template("list.html", config=config.get_layout_configuration())

@app.route("/create")
def create():
    return render_template("create.html", config=config.get_layout_configuration(), checkin=datetime.now().strftime('%Y-%m-%d'), checkout=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))

#endregion -------- FRONTEND API ENDPOINTS --------
