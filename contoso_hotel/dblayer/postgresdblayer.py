import psycopg2
from psycopg2.extras import RealDictCursor
import os, time, math
from datetime import datetime, timedelta
from typing import Dict, Union, Iterable
from enum import Enum


from . import SQLMode, get_defined_database, parse_connection_string_to_dict


def get_postgres_connection() -> psycopg2.extensions.connection:
    connectionstring, connectionname = get_defined_database()
    if connectionname != "POSTGRES_CONNECTION_STRING":
        raise ValueError("Connection string is not for Postgres")
    if not connectionstring:
        raise ValueError("Connection string is empty")

    info = parse_connection_string_to_dict(connectionstring, {"host" : "", "port" : "\\d+", "user" : "", "password" : "", "database" : ""})
    if "host" not in info or "port" not in info or "user" not in info or "password" not in info or "database" not in info:
        raise ValueError("Connection string is missing required parameters (host, port, user, password, database)")
    info["port"] = int(info["port"])

    return psycopg2.connect(host=info["host"], port=info["port"], user=info["user"], password=info["password"], database=info["database"])


def longsqlrequest() -> int:
    connection = get_postgres_connection()
    cursor = connection.cursor()
    cursor.execute("select 'hi' as hello")
    cursor.fetchall()
    time.sleep(10)
    cursor.execute("select 'hi' as hello")
    cursor.fetchall()
    time.sleep(10)
    cursor.close()
    connection.close()
    return 10 + 10

def create_booking(hotelId : int, visitorId : int, checkin : datetime, checkout : datetime, adults : int, kids : int, babies : int, rooms : int = None, price : float = None, bookingId : int = None) -> Dict[str, Union[int, str, float, bool]]:
    if adults <= 0:
        raise ValueError("At least one adult is required")
    if checkin >= checkout:
        raise ValueError("Checkin date must be before checkout date")
    if rooms is None:
        rooms = int(math.ceil((adults / 2) + (kids / 4) + (babies / 8)))
    elif rooms < int(math.ceil((adults / 2) + (kids / 4) + (babies / 8))):
        raise ValueError("Not enough rooms for the number of guests")

    connection = get_postgres_connection()
    # checking hotel exists
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT hotelId, pricePerNight FROM hotels WHERE hotelId = %s", (hotelId,))
    row = cursor.fetchone()
    if row is not None:
        hotelExists = True
        if price is None or price <= 0:
            price = row['pricepernight'] * (checkout - checkin).days * rooms
    else:
        hotelExists = False
    cursor.close()
    if not hotelExists:
        raise ValueError("Hotel does not exist")
    # checking visitor exists
    cursor = connection.cursor()
    cursor.execute("SELECT count(*) as num FROM visitors WHERE visitorId = %s", (visitorId,))
    row = cursor.fetchone()
    visitorExists = row[0] > 0
    cursor.close()
    if not visitorExists:
        raise ValueError("Visitor does not exist")
    # checking if booking already exists and getting next bookingId
    cursor = connection.cursor()
    if bookingId is None:
        cursor.execute("SELECT count(*) as num, (select max(b.bookingId) from bookings as b) as currentMaxId FROM bookings WHERE hotelId = %s and visitorId = %s and checkin = %s and checkout = %s", (hotelId, visitorId, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d')))
    else:
        cursor.execute("SELECT count(*) as num, (select max(b.bookingId) from bookings as b) as currentMaxId FROM bookings WHERE bookingId = %s or (hotelId = %s and visitorId = %s and checkin = %s and checkout = %s)", (bookingId, hotelId, visitorId, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d')))
    row = cursor.fetchone()
    alreadyExists = row[0] > 0
    nextId = row[1] + 1
    cursor.close()
    
    if alreadyExists:
        raise RuntimeError("Booking already exists")

    if nextId <= 0:
        nextId = 1
    
    cursor = connection.cursor()
    cursor.execute("INSERT INTO bookings (bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (nextId, hotelId, visitorId, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d'), adults, kids, babies, rooms, price))
    cursor.close()
    connection.commit()
    connection.close()
    return { "bookingId" : nextId, "hotelId" : hotelId, "visitorId" : visitorId, "checkin" : checkin, "checkout" : checkout, "adults" : adults, "kids" : kids, "babies" : babies, "rooms" : rooms, "price" : price }

def delete_booking(bookingId : int) -> bool:
    connection = get_postgres_connection()
    requiresDeletion = tablePrimaryKeyExists(connection, "bookings", bookingId)
    if requiresDeletion:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bookings WHERE bookingId = %s", (bookingId,))
        cursor.close()
        connection.commit()
    connection.close()
    return requiresDeletion

def get_booking(bookingId : int) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_postgres_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("select bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price from bookings where bookingId = %s", (bookingId,))
    row = cursor.fetchone()
    if row is None:
        return {}
    booking = {
        "bookingId" : row['bookingid'],
        "hotelId" : row['hotelid'],
        "visitorId" : row['visitorid'],
        "checkin" :  row['checkin'].strftime('%Y-%m-%d'),
        "checkout" : row['checkout'].strftime('%Y-%m-%d'),
        "adults" : row['adults'],
        "kids" :   row['kids'],
        "babies" : row['babies'],
        "rooms" : row['rooms'],
        "price" : row['price']
    }
    cursor.close()
    connection.close()
    return booking

def get_bookings(visitorId : int = None, hotelId : int = None, fromdate : datetime = None, untildate : datetime = None) -> Iterable[Dict[str, Union[int, str, float, bool]]]:
    params = []
    query = """
    select
        bookings.bookingId,
        bookings.checkin,
        bookings.checkout,
        bookings.adults,
        bookings.kids,
        bookings.babies,
        bookings.rooms,
        bookings.price,
        bookings.hotelId,
        (select hotelname from hotels where hotels.hotelId = bookings.hotelId) as hotelname,
        bookings.visitorId,
        visitors.firstname,
        visitors.lastname
    from bookings
    left join visitors on visitors.visitorId = bookings.visitorId
    """
    if visitorId is not None:
        if len(params) <= 0:
            query += "where "
        query += "bookings.visitorId = %s"
        params.append(visitorId)
    if hotelId is not None:
        if len(params) <= 0:
            query += "where "
        else:
            query += " and "
        query += "bookings.hotelId = %s"
        params.append(hotelId)
    if fromdate is not None and untildate is not None and fromdate > untildate:
        raise Exception("fromdate cannot be greater than untildate")
    if fromdate is not None:
        if len(params) <= 0:
            query += "where "
        else:
            query += " and "
        query += "bookings.checkout >= %s"
        params.append(fromdate.strftime('%Y-%m-%d'))
    if untildate is not None:
        if len(params) <= 0:
            query += "where "
        else:
            query += " and "
        query += "bookings.checkin <= %s"
        params.append(untildate.strftime('%Y-%m-%d'))
    query += " order by bookings.bookingId desc"
    connection = get_postgres_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, params)
    bookings = []
    for row in cursor.fetchall():
        bookings.append({
            "bookingId" : row['bookingid'],
            "checkin" : row['checkin'].strftime('%Y-%m-%d'),
            "checkout" : row['checkout'].strftime('%Y-%m-%d'),
            "adults" : row['adults'],
            "kids" : row['kids'],
            "babies" : row['babies'],
            "rooms" : row['rooms'],
            "price" : row['price'],
            "hotelId" : row['hotelid'],
            "hotelname" : row['hotelname'],
            "visitorId" : row['visitorid'],
            "firstname" : row['firstname'],
            "lastname" : row['lastname']
        })
    cursor.close()
    connection.close()
    return bookings


def create_visitor(firstname : str, lastname : str, visitorId : int = None) -> Dict[str, Union[int, str, float, bool]]:
    return manage_visitor(firstname, lastname, visitorId, SQLMode.INSERT)
def update_visitor(firstname : str, lastname : str, visitorId : int) -> Dict[str, Union[int, str, float, bool]]:
    return manage_visitor(firstname, lastname, visitorId, SQLMode.UPDATE)
def manage_visitor(firstname : str, lastname : str, visitorId : int = None, sqlmode : SQLMode = 1) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_postgres_connection()
    cursor = connection.cursor()
    if visitorId is None:
        if sqlmode == SQLMode.UPDATE:
            raise ValueError("visitorId is required for update")
        cursor.execute("SELECT count(*) as num, (select max(v.visitorId) from visitors as v) as currentMaxId FROM visitors WHERE firstname = %s and lastname = %s", (firstname, lastname))
    else:
        cursor.execute("SELECT count(*) as num, (select max(v.visitorId) from visitors as v) as currentMaxId FROM visitors WHERE visitorId = %s or (firstname = %s and lastname = %s)", (visitorId, firstname, lastname))
    row = cursor.fetchone()
    alreadyExists = row[0] > 0
    nextId = row[1] + 1
    cursor.close()
    
    if alreadyExists:
        if sqlmode == SQLMode.INSERT:
            raise RuntimeError("Visitor already exists")
        if sqlmode == SQLMode.UPDATE:
            if not tablePrimaryKeyExists(connection, "visitors", visitorId):
                raise RuntimeError("Visitor does not exist")
    else:
        if sqlmode == SQLMode.UPDATE:
            raise RuntimeError("Visitor does not exist")

    if nextId <= 0:
        nextId = 1
    
    cursor = connection.cursor()
    if sqlmode == SQLMode.UPDATE:
        nextId = visitorId
        cursor.execute("UPDATE visitors SET firstname = %s, lastname = %s WHERE visitorId = %s", (firstname, lastname, visitorId))
    elif sqlmode == SQLMode.INSERT:
        cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (%s, %s, %s)", (nextId, firstname, lastname))
    else:
        raise ValueError("Invalid SQL mode")
    cursor.close()
    connection.commit()
    connection.close()
    return { "visitorId" : nextId, "firstname" : firstname, "lastname" : lastname }


def delete_visitor(visitorId : int) -> bool:
    connection = get_postgres_connection()
    requiresDeletion = tablePrimaryKeyExists(connection, "visitors", visitorId)
    if requiresDeletion:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM visitors WHERE visitorId = %s", (visitorId,))
        cursor.close()
        connection.commit()
    connection.close()
    return requiresDeletion

def get_visitor(visitorId : int) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_postgres_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT visitorId, firstname, lastname FROM visitors WHERE visitorId = %s", (visitorId,))
    row = cursor.fetchone()
    if row is None:
        return {}
    visitor = {
        "visitorId" : row['visitorid'],
        "firstname" : row['firstname'],
        "lastname" : row['lastname']
    }
    cursor.close()
    connection.close()
    return visitor

def get_visitors(name : str = "", exactMatch : bool = False) -> Iterable[Dict[str, Union[int, str, float, bool]]]:
    connection = get_postgres_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    name = str(name).strip()
    if name != "":
        if exactMatch:
            cursor.execute("SELECT visitorId, firstname, lastname FROM visitors WHERE firstname = %s or lastname = %s order by visitorId desc", (name, name))
        else:
            name = "%" + name + "%"
            cursor.execute("SELECT visitorId, firstname, lastname FROM visitors WHERE firstname like %s or lastname like %s order by visitorId desc", (name, name))
    else:
        cursor.execute("SELECT visitorId, firstname, lastname FROM visitors order by visitorId desc")
    visitors = []
    for row in cursor.fetchall():
        visitors.append({
            "visitorId" : row['visitorid'],
            "firstname" : row['firstname'],
            "lastname" : row['lastname']
        })
    cursor.close()
    connection.close()
    return visitors


def create_hotel(hotelname : str, pricePerNight : float, hotelId : int = None) -> Dict[str, Union[int, str, float, bool]]:
    return manage_hotel(hotelname, pricePerNight, hotelId, SQLMode.INSERT)
def update_hotel(hotelname : str, pricePerNight : float, hotelId : int) -> Dict[str, Union[int, str, float, bool]]:
    return manage_hotel(hotelname, pricePerNight, hotelId, SQLMode.UPDATE)
def manage_hotel(hotelname : str, pricePerNight : float, hotelId : int = None, sqlmode : SQLMode = 1) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_postgres_connection()
    cursor = connection.cursor()
    if hotelId is None:
        if sqlmode == SQLMode.UPDATE:
            raise ValueError("hotelId is required for update")
        cursor.execute("SELECT count(*) as num, (select max(h.hotelId) from hotels as h) as currentMaxId FROM hotels WHERE hotelname = %s", (hotelname,))
    else:
        cursor.execute("SELECT count(*) as num, (select max(h.hotelId) from hotels as h) as currentMaxId FROM hotels WHERE hotelId = %s or hotelname = %s", (hotelId, hotelname))    
    row = cursor.fetchone()
    alreadyExists = row[0] > 0
    nextId = row[1] + 1
    cursor.close()
    
    if alreadyExists:
        if sqlmode == SQLMode.INSERT:
            raise RuntimeError("Hotel already exists")
        if sqlmode == SQLMode.UPDATE:
            if not tablePrimaryKeyExists(connection, "hotels", hotelId):
                raise RuntimeError("Hotel does not exist")
    else:
        if sqlmode == SQLMode.UPDATE:
            raise RuntimeError("Hotel does not exist")

    if nextId <= 0:
        nextId = 1
    
    cursor = connection.cursor()
    if sqlmode == SQLMode.UPDATE:
        nextId = hotelId
        cursor.execute("UPDATE hotels SET hotelname = %s, pricePerNight = %s WHERE hotelId = %s", (hotelname, pricePerNight, hotelId))
    elif sqlmode == SQLMode.INSERT:
        cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (%s, %s, %s)", (nextId, hotelname, pricePerNight))
    else:
        raise ValueError("Invalid SQL mode")
    cursor.close()
    connection.commit()
    connection.close()
    return { "hotelId" : nextId, "hotelname" : hotelname, "pricePerNight" : pricePerNight }


def delete_hotel(hotelId : int) -> bool:
    connection = get_postgres_connection()
    requiresDeletion = tablePrimaryKeyExists(connection, "hotels", hotelId)
    if requiresDeletion:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hotels WHERE hotelId = %s", (hotelId,))
        cursor.close()
        connection.commit()
    connection.close()
    return requiresDeletion

def get_hotel(hotelId : int) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_postgres_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT hotelId, hotelname, pricePerNight FROM hotels WHERE hotelId = %s", (hotelId,))
    row = cursor.fetchone()
    if row is None:
        return {}
    hotel = {
        "hotelId" : row['hotelid'],
        "hotelname" : row['hotelname'],
        "pricePerNight" : row['pricepernight']
    }
    cursor.close()
    connection.close()
    return hotel

def get_hotels(name : str = "", exactMatch : bool = False) -> Iterable[Dict[str, Union[int, str, float, bool]]]:
    connection = get_postgres_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    name = str(name).strip()
    if name != "":
        if exactMatch:
            cursor.execute("SELECT hotelId, hotelname, pricePerNight FROM hotels WHERE hotelname = %s order by hotelId desc", (name,))
        else:
            name = "%" + name + "%"
            cursor.execute("SELECT hotelId, hotelname, pricePerNight FROM hotels WHERE hotelname like %s order by hotelId desc", (name,))
    else:
        cursor.execute("SELECT hotelId, hotelname, pricePerNight FROM hotels order by hotelId desc")
    hotels = []
    for row in cursor.fetchall():
        hotels.append({
            "hotelId" : row['hotelid'],
            "hotelname" : row['hotelname'],
            "pricePerNight" : row['pricepernight']
        })
    cursor.close()
    connection.close()
    return hotels


def tablePrimaryKeyExists(connection, tableName : str, primaryKey : str) -> bool:
    if tableName == "hotels":
        query = "SELECT count(*) as num from hotels where hotelId = %s"
    elif tableName == "visitors":
        query = "SELECT count(*) as num from visitors where visitorId = %s"
    elif tableName == "bookings":
        query = "SELECT count(*) as num from bookings where bookingId = %s"
    else:
        raise ValueError("Invalid table name")
    cursor = connection.cursor()
    cursor.execute(query, (primaryKey,))
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    return exists

def doesTableHaveRows(connection, tableName : str) -> bool:
    tableName = str(tableName).strip()
    cursor = connection.cursor()
    cursor.execute("SELECT count(*) as num FROM " + tableName)
    hasRows = cursor.fetchone()[0] > 0
    cursor.close()
    return hasRows

def doesTableExist(connection, tableName : str) -> bool:
    tableName = str(tableName).strip()
    cursor = connection.cursor()
    cursor.execute("SELECT count(TABLE_NAME) as num FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' and TABLE_NAME = %s", (tableName,))
    exists = cursor.fetchone()[0] > 0
    cursor.close()
    return exists

def allTablesExists() -> bool:
    try:
        connection = get_postgres_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT count(TABLE_NAME) as num FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' and TABLE_NAME  in ('hotels', 'visitors', 'bookings')")
        exists = cursor.fetchone()[0] >= 3
        cursor.close()
        connection.close()
        return exists
    except Exception as e:
        return False

def setupDb(drop_schema : bool, create_schema : bool, populate_data : bool):
    if drop_schema and not create_schema:
        raise Exception("Cannot drop schema without creating schema")
    responseDict = {
        "success" : True,
        "drop_schema" : False,
        "create_schema" : { "hotels" : False, "visitors" : False, "bookings" : False },
        "populate_data" : { "hotels" : False, "visitors" : False, "bookings" : False }
    }
    connection = get_postgres_connection()
    if drop_schema:
        responseDict["drop_schema"] = True
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS bookings, hotels, visitors")
        cursor.close()
        connection.commit()
    if create_schema:     
        if not doesTableExist(connection, "hotels"):
            responseDict["create_schema"]["hotels"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE hotels (
                    hotelId SERIAL PRIMARY KEY,
                    hotelname VARCHAR(200) NOT NULL,
                    pricePerNight FLOAT NOT NULL CHECK (pricePerNight > 0),
                    CONSTRAINT hotelnameUq UNIQUE(hotelname)
                )
            """)
            cursor.close()
        if not doesTableExist(connection, "visitors"):
            responseDict["create_schema"]["visitors"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE visitors (
                    visitorId SERIAL PRIMARY KEY,
                    firstname VARCHAR(200) NOT NULL,
                    lastname VARCHAR(200) NOT NULL,
                    CONSTRAINT visitornameUq UNIQUE (firstname, lastname)
                )
            """)
            cursor.close()
        if not doesTableExist(connection, "bookings"):
            responseDict["create_schema"]["bookings"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE bookings (
                    bookingId SERIAL PRIMARY KEY,
                    hotelId INT NOT NULL,
                    visitorId INT NOT NULL,
                    checkin DATE NOT NULL,
                    checkout DATE NOT NULL,
                    adults INT NOT NULL CHECK (adults > 0 AND adults <= 10),
                    kids INT NOT NULL CHECK (kids >= 0 AND kids <= 10),
                    babies INT NOT NULL CHECK (babies >= 0 AND babies <= 10),
                    rooms INT NOT NULL CHECK (rooms > 0 AND rooms <= 10),
                    price FLOAT NOT NULL,
                    CONSTRAINT ck_checkdates CHECK (
                        checkin < checkout AND
                        checkin >= CURRENT_DATE AND
                        checkout >= CURRENT_DATE
                    ),
                    CONSTRAINT ck_rooms CHECK (
                        rooms >= ROUND((adults / 2.0) + (kids / 4.0) + (babies / 8.0))
                    ),
                    FOREIGN KEY (hotelId) REFERENCES hotels(hotelId) ON DELETE CASCADE,
                    FOREIGN KEY (visitorId) REFERENCES visitors(visitorId) ON DELETE CASCADE
                )
            """)
            cursor.close()
        connection.commit()
    if populate_data:
        if not doesTableHaveRows(connection, "hotels"):
            responseDict["populate_data"]["hotels"] = True
            cursor = connection.cursor()
            cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (1, 'Contoso Hotel Zurich', 400.0)")
            cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (2, 'Contoso Hotel Paris', 200.0)")
            cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (3, 'Contoso Hotel London', 250.0)")
            cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (4, 'Contoso Hotel Berlin', 150.0)")
            cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (5, 'Contoso Hotel Chicago', 300.0)")
            cursor.execute("INSERT INTO hotels (hotelId, hotelname, pricePerNight) VALUES (6, 'Contoso Hotel Los Angeles', 350.0)")
            cursor.close()
        if not doesTableHaveRows(connection, "visitors"):
            responseDict["populate_data"]["visitors"] = True
            cursor = connection.cursor()
            cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (1, 'Alice', 'Smith')")
            cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (2, 'Bob', 'Jones')")
            cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (3, 'Charlotte', 'Brown')")
            cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (4, 'David', 'White')")
            cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (5, 'Eve', 'Black')")
            cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (6, 'Frank', 'Green')")
            cursor.close()
        if not doesTableHaveRows(connection, "bookings"):
            responseDict["populate_data"]["bookings"] = True
            cursor = connection.cursor()
            n = datetime.now()
            cursor.execute("INSERT INTO bookings (bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price) VALUES (1, 1, 1, '" + (n + timedelta(days=10)).strftime('%Y-%m-%d') + "', '" + (n + timedelta(days=14)).strftime('%Y-%m-%d') + "', 2, 1, 0, 2, 3900.0)")
            cursor.execute("INSERT INTO bookings (bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price) VALUES (2, 2, 2, '" + (n + timedelta(days=2)).strftime('%Y-%m-%d') + "', '" + (n + timedelta(days=7)).strftime('%Y-%m-%d') + "', 2, 0, 0, 1, 1000.0)")
            cursor.close()
        connection.commit()
    connection.close()
    return responseDict

