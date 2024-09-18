import pyodbc
import os, time, math
from datetime import datetime, timedelta
from typing import Dict, Union, Iterable
from enum import Enum

from . import SQLMode, get_defined_database, get_bool_value


def get_mssql_connection() -> pyodbc.Connection:
    connectionstring, connectionname = get_defined_database()
    if connectionname != "MSSQL_CONNECTION_STRING":
        raise ValueError("Connection string is not for MSSQL")
    if not connectionstring:
        raise ValueError("Connection string is empty")
    
    return pyodbc.connect(connectionstring)


def longsqlrequest() -> int:
    connection = get_mssql_connection()
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

    connection = get_mssql_connection()
    # checking hotel exists
    cursor = connection.cursor()
    cursor.execute("SELECT hotelId, pricePerNight FROM hotels WHERE hotelId = ?", (hotelId))
    row = cursor.fetchone()
    if row is not None:
        hotelExists = True
        if price is None or price <= 0:
            price = row.pricePerNight * (checkout - checkin).days * rooms
    else:
        hotelExists = False
    cursor.close()
    if not hotelExists:
        raise ValueError("Hotel does not exist")
    # checking visitor exists
    cursor = connection.cursor()
    cursor.execute("SELECT count(*) as num FROM visitors WHERE visitorId = ?", (visitorId))
    row = cursor.fetchone()
    visitorExists = row.num > 0
    cursor.close()
    if not visitorExists:
        raise ValueError("Visitor does not exist")
    # checking if booking already exists and getting next bookingId
    cursor = connection.cursor()
    if bookingId is None:
        cursor.execute("SELECT count(*) as num, (select max(b.bookingId) from bookings as b) as currentMaxId FROM bookings WHERE hotelId = ? and visitorId = ? and checkin = ? and checkout = ?", (hotelId, visitorId, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d')))
    else:
        cursor.execute("SELECT count(*) as num, (select max(b.bookingId) from bookings as b) as currentMaxId FROM bookings WHERE bookingId = ? or (hotelId = ? and visitorId = ? and checkin = ? and checkout = ?)", (bookingId, hotelId, visitorId, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d')))
    row = cursor.fetchone()
    alreadyExists = row.num > 0
    nextId = row.currentMaxId + 1
    cursor.close()
    
    if alreadyExists:
        raise RuntimeError("Booking already exists")

    if nextId <= 0:
        nextId = 1
    
    cursor = connection.cursor()
    cursor.execute("INSERT INTO bookings (bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (nextId, hotelId, visitorId, checkin.strftime('%Y-%m-%d'), checkout.strftime('%Y-%m-%d'), adults, kids, babies, rooms, price))
    cursor.close()
    connection.commit()
    connection.close()
    return { "bookingId" : nextId, "hotelId" : hotelId, "visitorId" : visitorId, "checkin" : checkin, "checkout" : checkout, "adults" : adults, "kids" : kids, "babies" : babies, "rooms" : rooms, "price" : price }

def delete_booking(bookingId : int) -> bool:
    connection = get_mssql_connection()
    requiresDeletion = tablePrimaryKeyExists(connection, "bookings", bookingId)
    if requiresDeletion:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bookings WHERE bookingId = ?", (bookingId))
        cursor.close()
        connection.commit()
    connection.close()
    return requiresDeletion

def get_booking(bookingId : int) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    cursor.execute("select bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price from bookings where bookingId = ?", (bookingId))
    row = cursor.fetchone()
    if row is None:
        return {}
    booking = {
        "bookingId" : row.bookingId,
        "hotelId" : row.hotelId,
        "visitorId" : row.visitorId,
        "checkin" : row.checkin.strftime('%Y-%m-%d'),
        "checkout" : row.checkout.strftime('%Y-%m-%d'),
        "adults" : row.adults,
        "kids" : row.kids,
        "babies" : row.babies,
        "rooms" : row.rooms,
        "price" : row.price
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
        query += "bookings.visitorId = ?"
        params.append(visitorId)
    if hotelId is not None:
        if len(params) <= 0:
            query += "where "
        else:
            query += " and "
        query += "bookings.hotelId = ?"
        params.append(hotelId)
    if fromdate is not None and untildate is not None and fromdate > untildate:
        raise Exception("fromdate cannot be greater than untildate")
    if fromdate is not None:
        if len(params) <= 0:
            query += "where "
        else:
            query += " and "
        query += "bookings.checkout >= ?"
        params.append(fromdate.strftime('%Y-%m-%d'))
    if untildate is not None:
        if len(params) <= 0:
            query += "where "
        else:
            query += " and "
        query += "bookings.checkin <= ?"
        params.append(untildate.strftime('%Y-%m-%d'))
    query += " order by bookings.checkin desc, bookings.checkout desc, bookings.bookingId desc"
    connection = get_mssql_connection()
    cursor = connection.cursor()
    cursor.execute(query, params)
    bookings = []
    for row in cursor.fetchall():
        bookings.append({
            "bookingId" : row.bookingId,
            "checkin" : row.checkin.strftime('%Y-%m-%d'),
            "checkout" : row.checkout.strftime('%Y-%m-%d'),
            "adults" : row.adults,
            "kids" : row.kids,
            "babies" : row.babies,
            "rooms" : row.rooms,
            "price" : row.price,
            "hotelId" : row.hotelId,
            "hotelname" : row.hotelname,
            "visitorId" : row.visitorId,
            "firstname" : row.firstname,
            "lastname" : row.lastname
        })
    cursor.close()
    connection.close()
    return bookings


def create_visitor(firstname : str, lastname : str, visitorId : int = None) -> Dict[str, Union[int, str, float, bool]]:
    return manage_visitor(firstname, lastname, visitorId, SQLMode.INSERT)
def update_visitor(firstname : str, lastname : str, visitorId : int) -> Dict[str, Union[int, str, float, bool]]:
    return manage_visitor(firstname, lastname, visitorId, SQLMode.UPDATE)
def manage_visitor(firstname : str, lastname : str, visitorId : int = None, sqlmode : SQLMode = 1) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    if visitorId is None:
        if sqlmode == SQLMode.UPDATE:
            raise ValueError("visitorId is required for update")
        cursor.execute("SELECT count(*) as num, (select max(v.visitorId) from visitors as v) as currentMaxId FROM visitors WHERE firstname = ? and lastname = ?", (firstname, lastname))
    else:
        cursor.execute("SELECT count(*) as num, (select max(v.visitorId) from visitors as v) as currentMaxId FROM visitors WHERE visitorId = ? or (firstname = ? and lastname = ?)", (visitorId, firstname, lastname))
    row = cursor.fetchone()
    alreadyExists = row.num > 0
    nextId = row.currentMaxId + 1
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
        cursor.execute("UPDATE visitors SET firstname = ?, lastname = ? WHERE visitorId = ?", (firstname, lastname, visitorId))
    elif sqlmode == SQLMode.INSERT:
        cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (?, ?, ?)", (nextId, firstname, lastname))
    else:
        raise ValueError("Invalid SQL mode")
    cursor.close()
    connection.commit()
    connection.close()
    return { "visitorId" : nextId, "firstname" : firstname, "lastname" : lastname }


def delete_visitor(visitorId : int) -> bool:
    connection = get_mssql_connection()
    requiresDeletion = tablePrimaryKeyExists(connection, "visitors", visitorId)
    if requiresDeletion:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM visitors WHERE visitorId = ?", (visitorId))
        cursor.close()
        connection.commit()
    connection.close()
    return requiresDeletion

def get_visitor(visitorId : int) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT visitorId, firstname, lastname FROM visitors WHERE visitorId = ?", (visitorId))
    row = cursor.fetchone()
    if row is None:
        return {}
    visitor = {
        "visitorId" : row.visitorId,
        "firstname" : row.firstname,
        "lastname" : row.lastname
    }
    cursor.close()
    connection.close()
    return visitor

def get_visitors(name : str = "", exactMatch : bool = False) -> Iterable[Dict[str, Union[int, str, float, bool]]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    name = str(name).strip()
    if name != "":
        if exactMatch:
            cursor.execute("SELECT visitorId, firstname, lastname FROM visitors WHERE firstname = ? or lastname = ? order by visitorId desc", (name, name))
        else:
            name = "%" + name + "%"
            cursor.execute("SELECT visitorId, firstname, lastname FROM visitors WHERE firstname like ? or lastname like ? order by visitorId desc", (name, name))
    else:
        cursor.execute("SELECT visitorId, firstname, lastname FROM visitors order by visitorId desc")
    visitors = []
    for row in cursor.fetchall():
        visitors.append({
            "visitorId" : row.visitorId,
            "firstname" : row.firstname,
            "lastname" : row.lastname
        })
    cursor.close()
    connection.close()
    return visitors


def create_hotel(
    hotelname : str,
    pricePerNight : float,
    totalRooms : int,
    hotelId : int = None,
    country : str = 'Unknown',
    skiing : bool = False,
    suites : bool = False,
    inRoomEntertainment : bool = False,
    conciergeServices : bool = False,
    housekeeping : bool = False,
    petFriendlyOptions : bool = False,
    laundryServices : bool = False,
    roomService : bool = False,
    indoorPool : bool = False,
    outdoorPool : bool = False,
    fitnessCenter : bool = False,
    complimentaryBreakfast : bool = False,
    businessCenter : bool = False,
    freeGuestParking : bool = False,
    complimentaryCoffeaAndTea : bool = False,
    climateControl : bool = False,
    bathroomEssentials : bool = False
) -> Dict[str, Union[int, str, float, bool]]:
    return manage_hotel(
        hotelname,
        pricePerNight,
        totalRooms,
        hotelId,
        country,
        skiing,
        suites,
        inRoomEntertainment,
        conciergeServices,
        housekeeping,
        petFriendlyOptions,
        laundryServices,
        roomService,
        indoorPool,
        outdoorPool,
        fitnessCenter,
        complimentaryBreakfast,
        businessCenter,
        freeGuestParking,
        complimentaryCoffeaAndTea,
        climateControl,
        bathroomEssentials,
        SQLMode.INSERT
    )
def update_hotel(
    hotelname : str,
    pricePerNight : float,
    totalRooms : int,
    hotelId : int,
    country : str = None,
    skiing : bool = None,
    suites : bool = None,
    inRoomEntertainment : bool = None,
    conciergeServices : bool = None,
    housekeeping : bool = None,
    petFriendlyOptions : bool = None,
    laundryServices : bool = None,
    roomService : bool = None,
    indoorPool : bool = None,
    outdoorPool : bool = None,
    fitnessCenter : bool = None,
    complimentaryBreakfast : bool = None,
    businessCenter : bool = None,
    freeGuestParking : bool = None,
    complimentaryCoffeaAndTea : bool = None,
    climateControl : bool = None,
    bathroomEssentials : bool = None
) -> Dict[str, Union[int, str, float, bool]]:
    return manage_hotel(
        hotelname,
        pricePerNight,
        totalRooms,
        hotelId,
        country,
        skiing,
        suites,
        inRoomEntertainment,
        conciergeServices,
        housekeeping,
        petFriendlyOptions,
        laundryServices,
        roomService,
        indoorPool,
        outdoorPool,
        fitnessCenter,
        complimentaryBreakfast,
        businessCenter,
        freeGuestParking,
        complimentaryCoffeaAndTea,
        climateControl,
        bathroomEssentials,
        SQLMode.UPDATE
    )
def manage_hotel(
    hotelname : str,
    pricePerNight : float,
    totalRooms : int,
    hotelId : int = None,
    country : str = None,
    skiing : bool = None,
    suites : bool = None,
    inRoomEntertainment : bool = None,
    conciergeServices : bool = None,
    housekeeping : bool = None,
    petFriendlyOptions : bool = None,
    laundryServices : bool = None,
    roomService : bool = None,
    indoorPool : bool = None,
    outdoorPool : bool = None,
    fitnessCenter : bool = None,
    complimentaryBreakfast : bool = None,
    businessCenter : bool = None,
    freeGuestParking : bool = None,
    complimentaryCoffeaAndTea : bool = None,
    climateControl : bool = None,
    bathroomEssentials : bool = None,
    sqlmode : SQLMode = 1
) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    if hotelId is None:
        if sqlmode == SQLMode.UPDATE:
            raise ValueError("hotelId is required for update")
        cursor.execute("SELECT count(*) as num, (select max(h.hotelId) from hotels as h) as currentMaxId FROM hotels WHERE hotelname = ?", (hotelname))
    else:
        cursor.execute("SELECT count(*) as num, (select max(h.hotelId) from hotels as h) as currentMaxId FROM hotels WHERE hotelId = ? or hotelname = ?", (hotelId, hotelname))    
    row = cursor.fetchone()
    alreadyExists = row.num > 0
    nextId = row.currentMaxId + 1
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
    
    hotelname = str(hotelname).strip()

    if sqlmode == SQLMode.UPDATE:
        cursor = connection.cursor()
        nextId = hotelId
        parts = [ hotelname, pricePerNight, totalRooms ]
        setPartStmt = ""
        if country is not None:
            setPartStmt += ", country = ?"
            parts.append(country)
        if skiing is not None:
            setPartStmt += ", skiing = ?"
            parts.append(get_bool_value(skiing))
        if suites is not None:
            setPartStmt += ", suites = ?"
            parts.append(get_bool_value(suites))
        if inRoomEntertainment is not None:
            setPartStmt += ", inRoomEntertainment = ?"
            parts.append(get_bool_value(inRoomEntertainment))
        if conciergeServices is not None:
            setPartStmt += ", conciergeServices = ?"
            parts.append(get_bool_value(conciergeServices))
        if housekeeping is not None:
            setPartStmt += ", housekeeping = ?"
            parts.append(get_bool_value(housekeeping))
        if petFriendlyOptions is not None:
            setPartStmt += ", petFriendlyOptions = ?"
            parts.append(get_bool_value(petFriendlyOptions))
        if laundryServices is not None:
            setPartStmt += ", laundryServices = ?"
            parts.append(get_bool_value(laundryServices))
        if roomService is not None:
            setPartStmt += ", roomService = ?"
            parts.append(get_bool_value(roomService))
        if indoorPool is not None:
            setPartStmt += ", indoorPool = ?"
            parts.append(get_bool_value(indoorPool))
        if outdoorPool is not None:
            setPartStmt += ", outdoorPool = ?"
            parts.append(get_bool_value(outdoorPool))
        if fitnessCenter is not None:
            setPartStmt += ", fitnessCenter = ?"
            parts.append(get_bool_value(fitnessCenter))
        if complimentaryBreakfast is not None:
            setPartStmt += ", complimentaryBreakfast = ?"
            parts.append(get_bool_value(complimentaryBreakfast))
        if businessCenter is not None:
            setPartStmt += ", businessCenter = ?"
            parts.append(get_bool_value(businessCenter))
        if freeGuestParking is not None:
            setPartStmt += ", freeGuestParking = ?"
            parts.append(get_bool_value(freeGuestParking))
        if complimentaryCoffeaAndTea is not None:
            setPartStmt += ", complimentaryCoffeaAndTea = ?"
            parts.append(get_bool_value(complimentaryCoffeaAndTea))
        if climateControl is not None:
            setPartStmt += ", climateControl = ?"
            parts.append(get_bool_value(climateControl))
        if bathroomEssentials is not None:
            setPartStmt += ", bathroomEssentials = ?"
            parts.append(get_bool_value(bathroomEssentials))
        parts.append(hotelId)
        cursor.execute("UPDATE hotels SET hotelname = ?, pricePerNight = ?, totalRooms = ? " + setPartStmt + " WHERE hotelId =?", tuple(parts))
        cursor.close()
        connection.commit()
        connection.close()
        hotelResult = get_hotel(hotelId)
    elif sqlmode == SQLMode.INSERT:
        cursor = connection.cursor()
        hotelId = nextId
        if country is None:
            country = 'Unknown'
        country = str(country).strip()
        skiing = get_bool_value(skiing)
        suites = get_bool_value(suites)
        inRoomEntertainment = get_bool_value(inRoomEntertainment)
        conciergeServices = get_bool_value(conciergeServices)
        housekeeping = get_bool_value(housekeeping)
        petFriendlyOptions = get_bool_value(petFriendlyOptions)
        laundryServices = get_bool_value(laundryServices)
        roomService = get_bool_value(roomService)
        indoorPool = get_bool_value(indoorPool)
        outdoorPool = get_bool_value(outdoorPool)
        fitnessCenter = get_bool_value(fitnessCenter)
        complimentaryBreakfast = get_bool_value(complimentaryBreakfast)
        businessCenter = get_bool_value(businessCenter)
        freeGuestParking = get_bool_value(freeGuestParking)
        complimentaryCoffeaAndTea = get_bool_value(complimentaryCoffeaAndTea)
        climateControl = get_bool_value(climateControl)
        bathroomEssentials = get_bool_value(bathroomEssentials)
        cursor.execute(
            "INSERT INTO hotels (hotelId, hotelname, pricePerNight, totalRooms, country, skiing, suites, inRoomEntertainment, conciergeServices, housekeeping, petFriendlyOptions, laundryServices, roomService, indoorPool, outdoorPool, fitnessCenter, complimentaryBreakfast, businessCenter, freeGuestParking, complimentaryCoffeaAndTea, climateControl, bathroomEssentials) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (hotelId, hotelname, pricePerNight, totalRooms, country, skiing, suites, inRoomEntertainment, conciergeServices, housekeeping, petFriendlyOptions, laundryServices, roomService, indoorPool, outdoorPool, fitnessCenter, complimentaryBreakfast, businessCenter, freeGuestParking, complimentaryCoffeaAndTea, climateControl, bathroomEssentials)
        )
        cursor.close()
        connection.commit()
        connection.close()
        hotelResult = {
            "hotelId" : hotelId,
            "hotelname" : hotelname,
            "pricePerNight" : pricePerNight,
            "totalRooms" : totalRooms,
            "country" : country,
            "skiing" : skiing,
            "suites" : suites,
            "inRoomEntertainment" : inRoomEntertainment,
            "conciergeServices" : conciergeServices,
            "housekeeping" : housekeeping,
            "petFriendlyOptions" : petFriendlyOptions,
            "laundryServices" : laundryServices,
            "roomService" : roomService,
            "indoorPool" : indoorPool,
            "outdoorPool" : outdoorPool,
            "fitnessCenter" : fitnessCenter,
            "complimentaryBreakfast" : complimentaryBreakfast,
            "businessCenter" : businessCenter,
            "freeGuestParking" : freeGuestParking,
            "complimentaryCoffeaAndTea" : complimentaryCoffeaAndTea,
            "climateControl" : climateControl,
            "bathroomEssentials" : bathroomEssentials
        }
    else:
        connection.close()
        raise ValueError("Invalid SQL mode")
    return hotelResult


def delete_hotel(hotelId : int) -> bool:
    connection = get_mssql_connection()
    requiresDeletion = tablePrimaryKeyExists(connection, "hotels", hotelId)
    if requiresDeletion:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hotels WHERE hotelId = ?", (hotelId))
        cursor.close()
        connection.commit()
    connection.close()
    return requiresDeletion

def get_hotel(hotelId : int) -> Dict[str, Union[int, str, float, bool]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM hotels WHERE hotelId = ?", (hotelId))
    row = cursor.fetchone()
    if row is None:
        return {}
    hotel = {
        "hotelId" : row.hotelId,
        "hotelname" : row.hotelname,
        "pricePerNight" : row.pricePerNight,
        "totalRooms" : row.totalRooms,
        "country" : row.country,
        "skiing" : get_bool_value(row.skiing),
        "suites" : get_bool_value(row.suites),
        "inRoomEntertainment" : get_bool_value(row.inRoomEntertainment),
        "conciergeServices" : get_bool_value(row.conciergeServices),
        "housekeeping" : get_bool_value(row.housekeeping),
        "petFriendlyOptions" : get_bool_value(row.petFriendlyOptions),
        "laundryServices" : get_bool_value(row.laundryServices),
        "roomService" : get_bool_value(row.roomService),
        "indoorPool" : get_bool_value(row.indoorPool),
        "outdoorPool" : get_bool_value(row.outdoorPool),
        "fitnessCenter" : get_bool_value(row.fitnessCenter),
        "complimentaryBreakfast" : get_bool_value(row.complimentaryBreakfast),
        "businessCenter" : get_bool_value(row.businessCenter),
        "freeGuestParking" : get_bool_value(row.freeGuestParking),
        "complimentaryCoffeaAndTea" : get_bool_value(row.complimentaryCoffeaAndTea),
        "climateControl" : get_bool_value(row.climateControl),
        "bathroomEssentials" : get_bool_value(row.bathroomEssentials)
    }
    cursor.close()
    connection.close()
    return hotel

def get_hotels(name : str = "", exactMatch : bool = False) -> Iterable[Dict[str, Union[int, str, float, bool]]]:
    connection = get_mssql_connection()
    cursor = connection.cursor()
    name = str(name).strip()
    if name != "":
        if exactMatch:
            cursor.execute("SELECT hotelId, hotelname, pricePerNight, totalRooms, country FROM hotels WHERE hotelname = ? order by hotelId desc", (name))
        else:
            name = "%" + name + "%"
            cursor.execute("SELECT hotelId, hotelname, pricePerNight, totalRooms, country FROM hotels WHERE hotelname like ? order by hotelId desc", (name))
    else:
        cursor.execute("SELECT hotelId, hotelname, pricePerNight, totalRooms, country FROM hotels order by hotelId desc")
    hotels = []
    for row in cursor.fetchall():
        hotels.append({
            "hotelId" : row.hotelId,
            "hotelname" : row.hotelname,
            "pricePerNight" : row.pricePerNight,
            "totalRooms" : row.totalRooms,
            "country" : row.country
        })
    cursor.close()
    connection.close()
    return hotels


def tablePrimaryKeyExists(connection, tableName : str, primaryKey : str) -> bool:
    if tableName == "hotels":
        query = "SELECT count(*) as num from hotels where hotelId = ?"
    elif tableName == "visitors":
        query = "SELECT count(*) as num from visitors where visitorId = ?"
    elif tableName == "bookings":
        query = "SELECT count(*) as num from bookings where bookingId = ?"
    else:
        raise ValueError("Invalid table name")
    cursor = connection.cursor()
    cursor.execute(query, (primaryKey))
    exists = cursor.fetchone().num > 0
    cursor.close()
    return exists

def doesTableHaveRows(connection, tableName : str) -> bool:
    tableName = str(tableName).strip()
    cursor = connection.cursor()
    cursor.execute("SELECT count(*) as num FROM " + tableName)
    hasRows = cursor.fetchone().num > 0
    cursor.close()
    return hasRows

def doesTableExist(connection, tableName : str) -> bool:
    tableName = str(tableName).strip()
    cursor = connection.cursor()
    cursor.execute("SELECT count(TABLE_NAME) as num FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' and TABLE_NAME = ?", (tableName))
    exists = cursor.fetchone().num > 0
    cursor.close()
    return exists

def doesFunctionExist(connection, functionName : str) -> bool:
    functionName = str(functionName).strip()
    cursor = connection.cursor()
    cursor.execute("SELECT count(*) as num FROM sys.objects WHERE type IN ('FN', 'IF', 'TF') and name = ?", (functionName))
    exists = cursor.fetchone().num > 0
    cursor.close()
    return exists

def allTablesExists() -> bool:
    try:
        connection = get_mssql_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT count(TABLE_NAME) as num FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' and TABLE_NAME in ('hotels', 'visitors', 'bookings')")
        exists = cursor.fetchone().num >= 3
        cursor.close()
        connection.close()
        return exists
    except Exception as e:
        return False

def setupDb(drop_schema : bool, create_schema : bool, populate_data : bool, number_of_visitors : int, min_bookings_per_visitor : int, max_bookings_per_visitor : int):
    number_of_visitors = int(number_of_visitors)
    min_bookings_per_visitor = int(min_bookings_per_visitor)
    max_bookings_per_visitor = int(max_bookings_per_visitor)
    if number_of_visitors < 2:
        number_of_visitors = 2
    if number_of_visitors > 10000:
        number_of_visitors = 10000
    if min_bookings_per_visitor < 0:
        min_bookings_per_visitor = 0
    if min_bookings_per_visitor > 10:
        min_bookings_per_visitor = 10
    if  max_bookings_per_visitor < min_bookings_per_visitor:
        max_bookings_per_visitor = min_bookings_per_visitor
    if max_bookings_per_visitor < 1:
        max_bookings_per_visitor = 1
    if max_bookings_per_visitor > 20:
        max_bookings_per_visitor = 20
    if drop_schema and not create_schema:
        raise Exception("Cannot drop schema without creating schema")
    responseDict = {
        "success" : True,
        "drop_schema" : False,
        "create_schema" : { "hotels" : False, "visitors" : False, "bookings" : False, "GetRoomsUsageWithinTimeSpan" : False },
        "populate_data" : { "hotels" : False, "visitors" : False, "bookings" : False },
        "number_of_visitors" : number_of_visitors,
        "min_bookings_per_visitor" : min_bookings_per_visitor,
        "max_bookings_per_visitor" : max_bookings_per_visitor
    }
    connection = get_mssql_connection()
    if drop_schema:
        responseDict["drop_schema"] = True
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS bookings, hotels, visitors")
        cursor.execute("DROP FUNCTION IF EXISTS GetRoomsUsageWithinTimeSpan")
        cursor.close()
        connection.commit()
    if create_schema:     
        if not doesTableExist(connection, "hotels"):
            responseDict["create_schema"]["hotels"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE hotels (
                    hotelId INT NOT NULL PRIMARY KEY,
                    hotelname VARCHAR(200) NOT NULL,
                    pricePerNight FLOAT NOT NULL CHECK (pricePerNight > 0),
                    totalRooms INT NOT NULL CHECK (totalRooms > 0),
                    country VARCHAR(200) NOT NULL DEFAULT 'Unknown',
                    skiing BIT NOT NULL DEFAULT 0,
                    suites BIT NOT NULL DEFAULT 0,
                    inRoomEntertainment BIT NOT NULL DEFAULT 0,
                    conciergeServices BIT NOT NULL DEFAULT 0,
                    housekeeping BIT NOT NULL DEFAULT 0,
                    petFriendlyOptions BIT NOT NULL DEFAULT 0,
                    laundryServices BIT NOT NULL DEFAULT 0,
                    roomService BIT NOT NULL DEFAULT 0,
                    indoorPool BIT NOT NULL DEFAULT 0,
                    outdoorPool BIT NOT NULL DEFAULT 0,
                    fitnessCenter BIT NOT NULL DEFAULT 0,
                    complimentaryBreakfast BIT NOT NULL DEFAULT 0,
                    businessCenter BIT NOT NULL DEFAULT 0,
                    freeGuestParking BIT NOT NULL DEFAULT 0,
                    complimentaryCoffeaAndTea BIT NOT NULL DEFAULT 0,
                    climateControl BIT NOT NULL DEFAULT 0,
                    bathroomEssentials BIT NOT NULL DEFAULT 0,
                    CONSTRAINT hotelnameUq UNIQUE(hotelname)
                )
            """)
            cursor.close()
        if not doesTableExist(connection, "visitors"):
            responseDict["create_schema"]["visitors"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE visitors (
                    visitorId INT NOT NULL PRIMARY KEY,
                    firstname VARCHAR(200) NOT NULL,
                    lastname VARCHAR(200) NOT NULL,
                    CONSTRAINT visitornameUq UNIQUE(firstname, lastname)
                )
            """)
            cursor.close()
        if not doesTableExist(connection, "bookings"):
            responseDict["create_schema"]["bookings"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE bookings (
                    bookingId INT NOT NULL PRIMARY KEY,
                    hotelId INT NOT NULL,
                    visitorId INT NOT NULL,
                    checkin date NOT NULL,
                    checkout date NOT NULL,
                    adults INT NOT NULL CHECK (adults > 0 and adults <= 10),
                    kids INT NOT NULL CHECK (kids >= 0 and kids <= 10),
                    babies INT NOT NULL CHECK (babies >= 0 and babies <= 10),
                    rooms INT NOT NULL CHECK (rooms > 0  and rooms <= 10),
                    price FLOAT NOT NULL,
                    CONSTRAINT ck_checkdates CHECK
                    (
                        checkin < checkout and
                        checkin >= cast(GETDATE() as date) and
                        checkout >= cast(GETDATE() as date)
                    ),
                    CONSTRAINT ck_rooms CHECK
                    (
                        rooms >= cast(CEILING((adults / 2) + (kids / 4) + (babies / 8)) as int) 
                    ),
                    FOREIGN KEY (hotelId) REFERENCES hotels(hotelId) ON DELETE CASCADE,
                    FOREIGN KEY (visitorId) REFERENCES visitors(visitorId) ON DELETE CASCADE
                )
            """)
            cursor.close()
        if not doesFunctionExist(connection, "GetRoomsUsage"):
            responseDict["create_schema"]["GetRoomsUsageWithinTimeSpan"] = True
            cursor = connection.cursor()
            cursor.execute("""
                CREATE FUNCTION GetRoomsUsageWithinTimeSpan (@StartDate DATE, @EndDate DATE)
                RETURNS @RoomUsageTable TABLE (
                    hotelId INT,
                    hotelname VARCHAR(200),
                    country VARCHAR(200),
                    date DATE,
                    usedRooms INT,
                    freeRooms INT
                )
                AS
                BEGIN
                    -- Generate the dates in the range using a recursive CTE
                    WITH DateSeries AS (
                        SELECT @StartDate AS Date
                        UNION ALL
                        SELECT DATEADD(DAY, 1, Date)
                        FROM DateSeries
                        WHERE Date < @EndDate
                    )
                    -- Calculate room usage for each hotel and date
                    INSERT INTO @RoomUsageTable (hotelId, hotelname, country, date, usedRooms, freeRooms)
                    SELECT 
                        h.hotelId,
                        h.hotelname,
                        h.country,
                        d.Date,
                        ISNULL(SUM(b.rooms), 0) AS usedRooms,
                        h.totalRooms - ISNULL(SUM(b.rooms), 0) AS freeRooms
                    FROM 
                        hotels h
                    CROSS JOIN 
                        DateSeries d
                    LEFT JOIN 
                        bookings b ON h.hotelId = b.hotelId AND d.Date BETWEEN b.checkin AND b.checkout
                    GROUP BY 
                        h.hotelId, h.hotelname, h.country, d.Date, h.totalRooms
                    OPTION (MAXRECURSION 0);
                    RETURN;
                END;
            """)
            cursor.close()
        connection.commit()
    if populate_data:
        if not doesTableHaveRows(connection, "hotels"):
            responseDict["populate_data"]["hotels"] = True
            cursor = connection.cursor()
            startCmd = "INSERT INTO hotels (hotelId, hotelname, country, pricePerNight, totalRooms, Skiing, Suites, inRoomEntertainment, conciergeServices, housekeeping, petFriendlyOptions, laundryServices, roomService, indoorPool, outdoorPool, fitnessCenter, complimentaryBreakfast, businessCenter, freeGuestParking, complimentaryCoffeaAndTea, climateControl, bathroomEssentials) VALUES "
            cursor.execute(startCmd + " (1, 'Contoso Hotel Zurich', 'Switzerland', 400, 100, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (2, 'Contoso Hotel Paris', 'France', 200, 55, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0)")
            cursor.execute(startCmd + " (3, 'Contoso Hotel London', 'England', 250, 39, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (4, 'Contoso Hotel Berlin', 'Germany', 150, 89, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0)")
            cursor.execute(startCmd + " (5, 'Contoso Hotel Chicago', 'United States', 300, 157, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (6, 'Contoso Hotel Las Vegas', 'United States', 350, 210, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0)")
            cursor.execute(startCmd + " (7, 'Contoso Suites Boston', 'United States', 400, 134, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (8, 'Contoso Suites New York', 'United States', 400, 168, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (9, 'Contoso Suites Tokyo', 'Japan', 350, 44, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (10, 'Contoso Suites Munich', 'Germany', 375, 76, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (11, 'Contoso Suites London', 'England', 350, 64, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (12, 'Contoso Suites Paris', 'France', 375, 81, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (13, 'Alpine Ski House Zermatt', 'Switzerland', 525, 92, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (14, 'Alpine Ski House Lake Tahoe', 'United States', 500, 67, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (15, 'Alpine Ski House Aspen', 'United States', 500, 42, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (16, 'Alpine Ski House Whistler', 'Canada', 500, 31, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (17, 'Apline Ski House Niseko', 'Japan', 600, 45, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (18, 'Contoso Hotel Toronto', 'Canada', 400, 59, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0)")
            cursor.execute(startCmd + " (19, 'Contoso Hotel Sydney', 'Australia', 350, 78, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (20, 'Contoso Hotel Auckland', 'New Zealand', 350, 94, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (21, 'Contoso Suites Gold Coast', 'Australia', 350, 111, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (22, 'Contoso Hotel Los Angeles', 'United States', 250, 131, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (23, 'Contoso Suites Orlando', 'United States', 250, 41, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (24, 'Contoso Hotel Bangkok', 'Thailand', 350, 52, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (25, 'Contoso Hotel Rome', 'Italy', 450, 54, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0)")            
            cursor.execute(startCmd + " (26, 'Contoso Hotel Brussels', 'Belgium', 450, 21, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (27, 'Contoso Suites Madrid', 'Spain', 400, 63, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1)")
            cursor.execute(startCmd + " (28, 'Contoso Suites Athens', 'Greece', 400, 87, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (29, 'Alpine Ski House Oslo', 'Norway', 500, 81, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (30, 'Contoso Suites Kathmandu', 'Nepal', 200, 43, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (31, 'Contoso Hotel Doha', 'Qatar', 500, 86, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0)")
            cursor.execute(startCmd + " (32, 'Contoso Hotel Jakarta', 'Indonesia', 400, 109, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0)")
            cursor.execute(startCmd + " (33, 'Contoso Suites Jakarta', 'Indonesia', 350, 33, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (34, 'Contoso Suites Reykjavik', 'Iceland', 300, 36, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (35, 'Contoso Hotel Seoul', 'South Korea', 200, 75, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0)")
            cursor.execute(startCmd + " (36, 'Contoso Hotel Beijing', 'China', 250, 142, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0)")
            cursor.execute(startCmd + " (37, 'Contoso Hotel New Dehli', 'India', 200, 88, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0)")
            cursor.execute(startCmd + " (38, 'Contoso Suites Abu Dhabi', 'United Arab Emirates', 600, 39, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1)")
            cursor.execute(startCmd + " (39, 'Contoso Hotel Riyadh', 'Saudi Arabia', 500, 67, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0)")
            cursor.execute(startCmd + " (40, 'Contoso Suites Kuala Lumpur', 'Malaysia', 200, 27, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1)")
            cursor.close()
        if not doesTableHaveRows(connection, "visitors"):
            responseDict["populate_data"]["visitors"] = True
            cursor = connection.cursor()
            from .datagenerators import generateVisitorData
            nextId = 1
            for visitor in generateVisitorData(number_of_visitors):
                cursor.execute("INSERT INTO visitors (visitorId, firstname, lastname) VALUES (?, ?, ?)", (nextId, visitor["firstname"], visitor["lastname"]))
                nextId += 1
            cursor.close()
        if not doesTableHaveRows(connection, "bookings"):
            responseDict["populate_data"]["bookings"] = True
            cursor = connection.cursor()
            # getting required data
            startDate = datetime.now() + timedelta(days=4)
            cursor.execute("SELECT hotelId FROM hotels where hotelId <= 1000")
            hotelIds = [row.hotelId for row in cursor.fetchall()]
            cursor.execute("SELECT visitorId FROM visitors where visitorId <= 10000")
            visitorIds = [row.visitorId for row in cursor.fetchall()]
            # generating bookings
            from .datagenerators import generateBookings
            bookingId = 1
            for visitorId in visitorIds:
                for booking in generateBookings(visitorId, hotelIds, min_bookings_per_visitor, max_bookings_per_visitor, startDate):
                    cursor.execute("INSERT INTO bookings (bookingId, hotelId, visitorId, checkin, checkout, adults, kids, babies, rooms, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (bookingId, booking["hotelid"], booking["visitorid"], booking["checkin"], booking["checkout"], booking["adults"], booking["kids"], booking["babies"], booking["rooms"], booking["price"]))
                    bookingId += 1
            cursor.close()
        connection.commit()
    connection.close()
    return responseDict

