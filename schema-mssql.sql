DROP TABLE IF EXISTS bookings, hotels, visitors;



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
);

CREATE TABLE visitors (
    visitorId INT NOT NULL PRIMARY KEY,
    firstname VARCHAR(200) NOT NULL,
    lastname VARCHAR(200) NOT NULL,
    CONSTRAINT visitornameUq UNIQUE(firstname, lastname)
);

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
    CONSTRAINT ck_checkdates CHECK (
        checkin < checkout and
        checkin >= cast(GETDATE() as date) and
        checkout >= cast(GETDATE() as date)
    ),
    CONSTRAINT ck_rooms CHECK (
        rooms >= cast(CEILING((adults / 2) + (kids / 4) + (babies / 8)) as int) 
    ),
    FOREIGN KEY (hotelId) REFERENCES hotels(hotelId) ON DELETE CASCADE,
    FOREIGN KEY (visitorId) REFERENCES visitors(visitorId) ON DELETE CASCADE
);





DROP FUNCTION IF EXISTS GetRoomsUsageWithinTimeSpan

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


-- select TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME = 'hotels' or TABLE_NAME = 'visitors' or TABLE_NAME = 'bookings';

