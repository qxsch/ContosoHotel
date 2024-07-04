from datetime import datetime
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from . import app, dblayer




@app.route("/api/setup", methods=["POST"])
def api_setup():
    try:
        record = json.loads(request.data)
        for k in ["drop_schema", "create_schema", "populate_data"]:
            if k not in record:
                record[k] = False
            record[k] = bool(record[k])
    except Exception as e:
        return jsonify({ "success" : False, "error" : str(e) }), 400
    try:
        return jsonify(dblayer.setupDb(record["drop_schema"], record["create_schema"], record["populate_data"])), 201
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
                record[k] = datetime.fromisoformat(record[k])
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
            if record["hotelId"] is None and request.method == "PUT":
                return jsonify({ "success" : False, "error" : "hotelId is required" }), 400
            if "pricePerNight" in record:
                record["pricePerNight"] = float(record["pricePerNight"])
            else:
                return jsonify({ "success" : False, "error" : "pricePerNight is required" }), 400
            if "hotelname" in record:
                record["hotelname"] = str(record["hotelname"])
            else:
                return jsonify({ "success" : False, "error" : "hotelname is required" }), 400
            return jsonify(dblayer.create_hotel(record["hotelname"], record["pricePerNight"], record["hotelId"])), 200
        else:
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405 
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
        elif request.method == "PUT":
            record = json.loads(request.data)
            if "visitorId" in record:
                record["visitorId"] = int(record["visitorId"])
            else:
                record["visitorId"] = None
            for k in ["firstname", "lastname"]:
                if k not in record:
                    return jsonify({ "success" : False, "error" : f"{k} is required" }), 400
                record[k] = str(record[k])
            return jsonify(dblayer.create_visitor(record["firstname"], record["lastname"], record["visitorId"])), 200
        elif request.method == "POST":
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405
        else:
            return jsonify({ "success" : False, "error" : "Method not allowed" }), 405 
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


@app.route("/setup")
def setup():
    return render_template("setup.html")


@app.route("/")
def home():
    if not dblayer.allTablesExists():
        return redirect(url_for("setup"))
    return render_template("home.html")


@app.route("/list")
def list():
    return render_template("list.html")
