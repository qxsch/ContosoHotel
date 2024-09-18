DROP TABLE IF EXISTS bookings, hotels, visitors;



CREATE TABLE hotels (
    hotelId SERIAL PRIMARY KEY,
    hotelname VARCHAR(200) NOT NULL,
    pricePerNight FLOAT NOT NULL CHECK (pricePerNight > 0),
    totalRooms INT NOT NULL CHECK (totalRooms > 0),
    country VARCHAR(200) NOT NULL DEFAULT 'Unknown',
    skiing BOOLEAN NOT NULL DEFAULT TRUE,
    suites BOOLEAN NOT NULL DEFAULT TRUE,
    inRoomEntertainment BOOLEAN NOT NULL DEFAULT TRUE,
    conciergeServices BOOLEAN NOT NULL DEFAULT TRUE,
    housekeeping BOOLEAN NOT NULL DEFAULT TRUE,
    petFriendlyOptions BOOLEAN NOT NULL DEFAULT TRUE,
    laundryServices BOOLEAN NOT NULL DEFAULT TRUE,
    roomService BOOLEAN NOT NULL DEFAULT TRUE,
    indoorPool BOOLEAN NOT NULL DEFAULT TRUE,
    outdoorPool BOOLEAN NOT NULL DEFAULT TRUE,
    fitnessCenter BOOLEAN NOT NULL DEFAULT TRUE,
    complimentaryBreakfast BOOLEAN NOT NULL DEFAULT TRUE,
    businessCenter BOOLEAN NOT NULL DEFAULT TRUE,
    freeGuestParking BOOLEAN NOT NULL DEFAULT TRUE,
    complimentaryCoffeaAndTea BOOLEAN NOT NULL DEFAULT TRUE,
    climateControl BOOLEAN NOT NULL DEFAULT TRUE,
    bathroomEssentials BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT hotelnameUq UNIQUE(hotelname)
);

CREATE TABLE visitors (
    visitorId SERIAL PRIMARY KEY,
    firstname VARCHAR(200) NOT NULL,
    lastname VARCHAR(200) NOT NULL,
    CONSTRAINT visitornameUq UNIQUE (firstname, lastname)
);

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
        rooms >= CEILING((adults / 2.0) + (kids / 4.0) + (babies / 8.0))
    ),
    FOREIGN KEY (hotelId) REFERENCES hotels(hotelId) ON DELETE CASCADE,
    FOREIGN KEY (visitorId) REFERENCES visitors(visitorId) ON DELETE CASCADE
);




DROP FUNCTION IF EXISTS GetRoomsUsageWithinTimeSpan

CREATE FUNCTION GetRoomsUsageWithinTimeSpan(StartDate DATE, EndDate DATE)
RETURNS TABLE (
    hotelId INT,
    hotelname VARCHAR(200),
    country VARCHAR(200),
    date DATE,
    usedRooms INT,
    freeRooms INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.hotelId,
        h.hotelname,
        h.country,
        d.Date::date,
        COALESCE(SUM(b.rooms), 0)::int AS usedRooms,
        (h.totalRooms - COALESCE(SUM(b.rooms), 0))::int AS freeRooms
    FROM 
        hotels h
    CROSS JOIN 
        generate_series(StartDate, EndDate, '1 day'::interval) AS d(Date)
    LEFT JOIN 
        bookings b ON h.hotelId = b.hotelId AND d.Date::date BETWEEN b.checkin AND b.checkout
    GROUP BY 
        h.hotelId, h.hotelname, h.country, d.Date::date, h.totalRooms;
END;
$$ LANGUAGE plpgsql;




-- select TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME = 'hotels' or TABLE_NAME = 'visitors' or TABLE_NAME = 'bookings';

