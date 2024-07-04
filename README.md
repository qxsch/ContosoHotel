# Contoso Hotel Demo in Python

## General setup guidance

 1. Configure Environment Variable ``MSSQL_CONNECTION_STRING`` or supply a file named ``./secrets-store/MSSQL_CONNECTION_STRING``
 1. Run the app: ``gunicorn --bind=0.0.0.0 --workers=4 startup:app``
 1. Populate Data:
    1.  **Either** go to: http://localhost:8000/setup
    1.  **Or** invoke the Rest API: ``Invoke-RestMethod -Uri 'http://localhost:8000/api/setup' -Method Post -Body '{ "drop_schema" : true, "create_schema": true, "populate_data" : true }' -ContentType 'application/json'``


## Docker based setup

 1. Build the Docker Image: ``docker build -t pycontosohotel:latest .``
 1. Run the Docker Container:
    1. Using environment variable  ``docker run -p 8000:8000 -e MSSQL_CONNECTION_STRING='DRIVER={ODBC Driver 18 for SQL Server};SERVER=MSSQLINSTANCENAME.database.windows.net;DATABASE=MSSQLDBNAME;UID=MSSQLUSERNAME;PWD=*******' pycontosohotel:latest``
    1. Using volume mount
       1. Create a file ``MSSQL_CONNECTION_STRING`` with the connection string in the ``/path/to/secrets-store`` directory
       1. ``docker run -p 8000:8000 -v '/path/to/secrets-store:/app/secrets-store' pycontosohotel:latest``
 1. Populate Data:
    1.  **Either** go to: http://localhost:8000/setup
    1.  **Or** invoke the Rest API: ``Invoke-RestMethod -Uri 'http://localhost:8000/api/setup' -Method Post -Body '{ "drop_schema" : true, "create_schema": true, "populate_data" : true }' -ContentType 'application/json'``



# API documentation

## Get Hotels

**Endpoint:** ``GET /api/hotels``

| Get Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``hotelname``  | string | *empty* | Optional Hotel Name to filter |
| ``exactMatch`` | bool | false | Optional exactMatch (``false`` uses ``like '%search%'`` ) |

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
[
  {
    "hotelId": 6,
    "hotelname": "Contoso Hotel Los Angeles",
    "pricePerNight": 350.0
  }
]
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Get Visitors

**Endpoint:** ``GET /api/visitors``

| Get Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``name``  | string | *empty* | Optional Name to filter (first or last name) |
| ``exactMatch`` | bool | false | Optional exactMatch (``false`` uses ``like '%search%'`` ) |

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
[
  {
    "firstname": "Frank",
    "lastname": "Green",
    "visitorId": 6
  }
]
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```



## Get Bookings

**Endpoint:** ``GET /api/bookings``

| Get Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``visitorId``  | int | *empty* | Optional visitorId to filter |
| ``hotelId``    | int | *empty* | Optional hotelId to filter   |
| ``fromdate``   | datetime (YYYY-MM-DD) | *empty* | Optionally filter for bookings that are after this date   |
| ``untildate``  | datetime (YYYY-MM-DD) | *empty* | Optionally filter for bookings that are before this date  |

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
[
  {
    "adults": 2,
    "babies": 0,
    "bookingId": 2,
    "checkin": "2024-07-05",
    "checkout": "2024-07-10",
    "firstname": "Bob",
    "hotelId": 2,
    "hotelname": "Contoso Hotel Paris",
    "kids": 0,
    "lastname": "Jones",
    "price": 1000.0,
    "rooms": 1,
    "visitorId": 2
  }
]
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```



## Get a single Hotel

**Endpoint:** ``GET /api/hotel?hotelId=<int>``

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "hotelId": 6,
   "hotelname": "Contoso Hotel Los Angeles",
   "pricePerNight": 350.0
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Get a single Visitor

**Endpoint:** ``GET /api/visitor?visitorId=<int>``

| Get Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``name``  | string | *empty* | Optional Name to filter (first or last name) |
| ``exactMatch`` | bool | false | Optional exactMatch (``false`` uses ``like '%search%'`` ) |

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
[
  {
    "firstname": "Frank",
    "lastname": "Green",
    "visitorId": 6
  }
]
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Get a single Booking

**Endpoint:** ``GET /api/booking?bookingId=<int>``

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "adults": 2,
   "babies": 0,
   "bookingId": 2,
   "checkin": "2024-07-05",
   "checkout": "2024-07-10",
   "firstname": "Bob",
   "hotelId": 2,
   "hotelname": "Contoso Hotel Paris",
   "kids": 0,
   "lastname": "Jones",
   "price": 1000.0,
   "rooms": 1,
   "visitorId": 2
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Create Hotel

**Endpoint:** ``PUT /api/hotel``

**Request Body:**
```json
{
   "hotelname": "Contoso Hotel Los Angeles",
   "pricePerNight": 350.0
}
```

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "hotelId": 6,
   "hotelname": "Contoso Hotel Los Angeles",
   "pricePerNight": 350.0
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Create Visitor

**Endpoint:** ``PUT /api/visitor``

**Request Body:**
```json
{
   "firstname": "Frank",
   "lastname": "Green"
}
```

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "visitorId": 6,
   "firstname": "Frank",
   "lastname": "Green"
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```

## Create Booking

**Endpoint:** ``PUT /api/booking``

**Request Body:**
```json
{
   "visitorId": 6,
   "hotelId": 2,
   "checkin": "2024-07-05",
   "checkout": "2024-07-10",
   "adults": 2,
   "kids": 0,       // optional
   "babies": 0,     // optional
   "rooms": 1,      // optional
   "price": 1000.0  // optional
}
```

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "bookingId": 2,
   "visitorId": 6,
   "hotelId": 2,
   "checkin": "2024-07-05",
   "checkout": "2024-07-10",
   "rooms": 1,
   "adults": 2,
   "kids": 0,
   "babies": 0,
   "price": 1000.0
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```

## Update Hotel

**Endpoint:** ``POST /api/hotel``

**Request Body:**
```json
{
   "hotelId": 6,
   "hotelname": "Contoso Hotel Los Angeles",
   "pricePerNight": 350.0
}
```

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "hotelId": 6,
   "hotelname": "Contoso Hotel Los Angeles",
   "pricePerNight": 350.0
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Update Visitor

**Endpoint:** ``POST /api/visitor``

**Request Body:**
```json
{
   "visitorId": 6,
   "firstname": "Frank",
   "lastname": "Green"
}
```

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "visitorId": 6,
   "firstname": "Frank",
   "lastname": "Green"
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```


## Delete Hotel

**Endpoint:** ``DELETE /api/hotel?hotelId=<int>``

| Url Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``hotelId``  | int | *empty* | Required id of the hotel |

**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "success": true,
   "deleted": true,  // indicates if deletion was necessary
   "hotelId": 6
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```

## Delete Visitor

**Endpoint:** ``DELETE /api/visitor?visitorId=<int>``

| Url Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``visitorId``  | int | *empty* | Required id of the visitor |


**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "success": true,
   "deleted": true,  // indicates if deletion was necessary
   "visitorId": 6
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```

## Delete Booking

**Endpoint:** ``DELETE /api/booking?bookingId=<int>``

| Url Parameter | Type | Default Value | Description |
| --- | --- | --- | --- |
| ``bookingId``  | int | *empty* | Required id of the booking |


**Response Codes:**
| Code | Description |
| --- | --- |
| 200 | Success |
| 400 | Bad Request (Invalid input data) |
| 500 | Internal Server Error (Server side processing error) |

**Example Body (Success - 200):**
```json
{
   "success": true,
   "deleted": true,  // indicates if deletion was necessary
   "bookingId": 2
}
```

**Example Body (Failure - 400 or 500):**
```json
{ 
   "success" : false,
   "error" : "Some error message here"
}
```
