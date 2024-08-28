import random, math
from typing import List
from datetime import datetime, timedelta

def generateBookings(visitorId : int, hotelIds : List[int], min_bookings : int = 2, max_bookings : int = 5, startDate: datetime = datetime.now()):
    if min_bookings > max_bookings:
        raise ValueError("min_bookings must be less than or equal to max_bookings")
    if min_bookings < 0:
        raise ValueError("min_bookings must be greater than or equal to 0")
    if min_bookings > 10:
        raise ValueError("min_bookings must be less than or equal to 10")
    if max_bookings < 1:
        raise ValueError("max_bookings must be greater than 0")
    if max_bookings > 20:
        raise ValueError("max_bookings must be less than or equal to 20")
    if min_bookings == max_bookings:
        number = min_bookings
    else:
        number = random.randint(min_bookings, max_bookings)
    if number == 0:
        return []
    
    results = []
    checkout = startDate
    for i in range(number):
        checkin = checkout + timedelta(days=random.randint(0, 14))
        nights = random.randint(1, 21)
        checkout = checkin + timedelta(days=nights)
        adults = random.randint(1, 2)
        kids = random.randint(0, 4)
        rooms = int(math.ceil((adults / 2) + (kids / 4)))
        price = (random.randint(1000, 80000) / 100) * nights * rooms
        results.append({
            "visitorid" : visitorId,
            "hotelid": random.choice(hotelIds),
            "checkin": checkin.strftime('%Y-%m-%d'),
            "checkout": checkout.strftime('%Y-%m-%d'),
            "adults": adults,
            "kids": kids,
            "babies": 0,
            "rooms": rooms,
            "price": (math.ceil(price * 100) / 100)
        })
    return results




def generateVisitorData(numberOfVisitors: int):
    if numberOfVisitors > 10000:
        raise ValueError("numberOfVisitors must be less than or equal to 10000")
    if numberOfVisitors < 2:
        raise ValueError("numberOfVisitors must be greater than 1")


    firstNamesMales = [
        'Albert', 'Andrew', 'Anthony', 'Ben', 'Bernd', 'Bob', 'Brian', 'Charles', 'Christian', 'Christopher', 'Claus', 'Constantin',
        'Daniel', 'David', 'Dennis', 'Dieter', 'Donald', 'Dylan', 'Eliah', 'Erik', 'Felix', 'Finn', 'Frank', 'Geoffrey', 'Gregory',
        'Gustav', 'Hank', 'Hans', 'Heinz', 'Henry', 'Ian', 'Ingo', 'Jack', 'Jake', 'James', 'Johannes', 'John', 'Joos', 'Joseph',
        'Judson', 'Kevin', 'Klaus', 'Lars', 'Liam', 'Ludwig', 'Lukas', 'Luke', 'Manfred', 'Marco', 'Mark', 'Martin', 'Matthew',
        'Maximilian', 'Michael', 'Nate', 'Nathan', 'Nico', 'Norbert', 'Oliver', 'Oscar', 'Otto', 'Patrick', 'Patty', 'Paul', 'Peter',
        'Quincy', 'Quinn', 'Raphael', 'Richard', 'Robert', 'Ronald', 'Rudolf', 'Sam', 'Sebastian', 'Seth', 'Simon', 'Steve', 'Steven',
        'Theodor', 'Thomas', 'Timothy', 'Tobias', 'Tom', 'Ulrich', 'Ulysses', 'Uwe', 'Valentin', 'Viktor', 'Vince', 'Walter',
        'Werner', 'William', 'Wolfgang', 'Xander', 'Xaver', 'Xavier', 'Yannick', 'Yara', 'Yves', 'Zach', 'Zacharias', 'Zane', 'Zeno', 'Zoltan',
    ]
    firstNamesFemales = [
        'Alice', 'Amanda', 'Amelie', 'Anastasia', 'Anna', 'Ashley', 'Ava', 'Barbara', 'Cathy', 'Charlotte', 'Chiara', 'Christina',
        'Clara', 'Diana', 'Elena', 'Elianne', 'Elisabeth', 'Elizabeth', 'Emilia', 'Emily', 'Emma', 'Eva', 'Eve', 'Fiona', 'Frederike',
        'Frieda', 'Gabrielle', 'Gina', 'Giselle', 'Grace', 'Greta', 'Hanna', 'Helena', 'Helene', 'Irene', 'Iris', 'Isablle', 'Ivy',
        'Jasmin', 'Jennifer', 'Jenny', 'Jessica', 'Johanna', 'Julia', 'Juliette', 'Kara', 'Katharina', 'Katie', 'Kimberly', 'Klara',
        'Lara', 'Larissa', 'Laura', 'Lena', 'Lisa', 'Maila', 'Mandy', 'Maren', 'Maria', 'Marie', 'Mathilda', 'Melissa', 'Mia', 'Michelle',
        'Molly', 'Nadine', 'Natalie', 'Nicole', 'Nina', 'Nora', 'Olive', 'Olivia', 'Pamela', 'Paula', 'Pauline', 'Rachel', 'Rebecca',
        'Rike', 'Rita', 'Rosa', 'Rosalie', 'Rose', 'Sabrina', 'Sara', 'Saskia', 'Sophia', 'Sophie', 'Stephanie', 'Susan', 'Tabea', 'Tara',
        'Theresa', 'Tiffany', 'Tina', 'Uma', 'Valerie', 'Vanessa', 'Victoria', 'Vivian', 'Wendy', 'Yara', 'Yvonne', 'Zara', 'Zoe'
    ]

    lastNames = [
        'Bach', 'Bachmann', 'Bachmeier', 'Baker', 'Bauer', 'Baumann', 'Beck', 'Becker', 'Bennett', 'Beyer', 'Black', 'Brooks',
        'Brown', 'Carter', 'Clark', 'Cook', 'Cooper', 'Davis', 'Evans', 'Fisher', 'Fisher', 'Fuchs', 'Gray', 'Grayson', 'Green',
        'Hall', 'Harrison', 'Henderson', 'Hill', 'Hoffmann', 'Hudson', 'James', 'Johnson', 'Jones', 'Kaiser', 'Kelly', 'King',
        'Koch', 'Krause', 'Lang', 'Lee', 'Lehmann', 'Meier', 'Meyer', 'Miller', 'Mitchell', 'Morgan', 'Muller', 'Murphy',
        'Neumann', 'Owens', 'Parker', 'Reed', 'Reiter', 'Richter', 'Ross', 'Ruescher', 'Schmidt', 'Schmitz', 'Schneider',
        'Schreiber', 'Schulz', 'Schumacher', 'Schuster', 'Smith', 'Spencer', 'Staub', 'Steiner', 'Taylor', 'Thomas', 'Wagner',
        'Watson', 'Weber', 'Wentlandt', 'White', 'Williams', 'Wilson', 'Wood', 'Wyler', 'Zeder', 'Zeder', 'Zederbauer',
        'Zederbauer', 'Zehnder', 'Zeller', 'Zellweger', 'Ziegler', 'Zimmer', 'Zimmerman'
    ]

    # create a list of unique visitor names
    visitorNames = {}
    duplicates = 0
    while len(visitorNames) < numberOfVisitors:
        if len(visitorNames) % 2 == 0:
            firstName = random.choice(firstNamesMales)
            gender = "male"
        else:
            firstName = random.choice(firstNamesFemales)
            gender = "female"
        lastName = random.choice(lastNames)
        k =  firstName + '|' + lastName
        if k not in visitorNames:
            duplicates = 0
            visitorNames[k] = {
                'firstname' : firstName,
                'lastname'  : lastName,
                'gender'    : gender
            }
        else:
            duplicates += 1
            if duplicates > 1000:
                raise ValueError("Failed to generate names, too many duplicates generated")
    return list(visitorNames.values())

