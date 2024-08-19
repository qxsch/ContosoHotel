DROP TABLE IF EXISTS bookings, hotels, visitors;



CREATE TABLE hotels (
    hotelId SERIAL PRIMARY KEY,
    hotelname VARCHAR(200) NOT NULL,
    pricePerNight FLOAT NOT NULL CHECK (pricePerNight > 0),
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



-- select TABLE_NAME, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT from INFORMATION_SCHEMA.COLUMNS where TABLE_NAME = 'hotels' or TABLE_NAME = 'visitors' or TABLE_NAME = 'bookings';

