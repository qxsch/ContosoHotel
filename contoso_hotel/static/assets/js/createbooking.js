document.getElementById("createbooking").addEventListener("click", function() {
    document.getElementById('log').innerHTML = 'Running...';

    errorMsgs = [];
    if(!document.getElementById("hotel").dataset.value   || document.getElementById("hotel").dataset.value == "") {
        errorMsgs.push("Please select a hotel");
    }
    if(!document.getElementById("visitor").dataset.value || document.getElementById("visitor").dataset.value == "") {
        errorMsgs.push("Please select a visitor");
    }
    if(errorMsgs.length > 0) {
        document.getElementById('log').innerHTML = '';
        var el = document.createElement('h2');
        el.innerHTML = 'Please provide all required data';
        document.getElementById('log').appendChild(el);
        errorMsgs.forEach(msg => {
            var p = document.createElement('p');
            p.textContent = msg;
            document.getElementById('log').appendChild(p);
        });
        return;
    }

    fetch(window.getContosoUrl(window.contoso_configuration.api_baseurl, '/api/booking'), {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "hotelId": parseInt(document.getElementById("hotel").dataset.value),
            "visitorId": parseInt(document.getElementById("visitor").dataset.value),
            "checkin": document.getElementById("checkin").value,
            "checkout": document.getElementById("checkout").value,
            "adults": parseInt(document.getElementById("adults").value),
            "kids": parseInt(document.getElementById("kids").value),
            "babies": parseInt(document.getElementById("babies").value),
            "rooms": parseInt(document.getElementById("rooms").value)
        })
    })
    .then(response => response.json())
    .then(data => {
        if("error" in data) {
            throw new Error(data['error']);
        }
        console.log(data);

        document.getElementById('log').innerHTML = '';
        var el = document.createElement('h2');
        el.innerHTML = 'Sucessfully created the booking';
        document.getElementById('log').appendChild(el);
    })
    .catch((error) => {
        document.getElementById('log').innerHTML = '';
        var el = document.createElement('h2');
        el.innerHTML = 'Failed to create booking';
        document.getElementById('log').appendChild(el);
        var p = document.createElement('p');
        p.textContent = error;
        document.getElementById('log').appendChild(p);
        console.log('Error:', error);
    });

});


function recalculateRooms() {
    var rooms = Math.ceil( Math.max(1, parseInt(document.getElementById("adults").value)) / 2 + Math.max(0, parseInt(document.getElementById("kids").value)) / 4 + Math.max(0, parseInt(document.getElementById("babies").value)) / 8 );
    if(rooms > 10) {
        rooms = 10;
    }
    document.getElementById("rooms").value = String(rooms);
}

document.getElementById("checkin").addEventListener("change", function() {
    var checkindate = new Date(Date.parse(document.getElementById("checkin").value));
    checkindate.setDate(checkindate.getDate() + 1);
    checkindate = checkindate.toISOString().split('T')[0];
    if(checkindate >= document.getElementById("checkout").value) {
        document.getElementById("checkout").value = checkindate;
    }
});

document.getElementById("adults").addEventListener("change", function() {
    recalculateRooms();
});

document.getElementById("kids").addEventListener("change", function() {
    recalculateRooms();
});

document.getElementById("babies").addEventListener("change", function() {
    recalculateRooms();
});