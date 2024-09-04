class Booking {
    #elementId = null;
    #search = "";
    #searchTimeoutId = null;
    #intervalSeconds = null;
    #data = null;
    constructor(elementId) {
        this.#elementId = String(elementId);
    }

    #renderData() {
        const tableCols = new Map([
            ['hotelname', 'Hotel Name'],
            ['visitorId', 'Visitor ID'],
            ['firstname', 'First Name'],
            ['lastname', 'Last Name'],
            ['checkin', 'Checkin'],
            ['checkout', 'Checkout'],
            ['rooms', 'Rooms'],
            ['adults', 'Adults'],
            ['kids', 'Kids'],
            ['babies', 'Babies'],
            ['price', 'Price']
        ]);

        if (!this.#data) {
            document.getElementById(this.#elementId).innerHTML = "";
            return;
        }
        // create a new table
        var tbl = document.createElement('table');
        tbl.classList.add('nicetable');
        var thead = document.createElement('thead');
        var html = '<tr>';
        for(const val of tableCols.values()) {
            html += '<th>' + val + '</th>';
        }
        html += '<th>Actions</th></tr>';
        thead.innerHTML = html;
        tbl.appendChild(thead);
        var tbody = document.createElement('tbody');
        tbl.appendChild(tbody);
        // add the new data
        this.#data.forEach(entry => {
            if(this.#search.length > 0) {
                for(var part of this.#search.toLowerCase().split(' ')) {
                    part = part.trim();
                    if(part.length === 0) {
                        continue;
                    }
                    var found = false;
                    for(const k of tableCols.keys()) {
                        if(String(entry[k]).toLowerCase().indexOf(part) !== -1) {
                            found = true;
                            break;
                        }
                    }
                    if(!found) {
                        return;
                    }
                }
            }
            /* bookingId,checkin, checkout, adults, kids, babies, rooms, price, hotelId, hotelname, visitorId, firstname, lastname */
            var row = document.createElement('tr');
            for(const k of tableCols.keys()) {
                var cell = document.createElement('td');
                cell.innerHTML = entry[k];
                row.appendChild(cell);
            }
            var actionsCell = document.createElement('td');
            var deleteButton = document.createElement('i');
            //  fa-beat
            deleteButton.classList = "fa-regular fa-calendar-xmark";
            deleteButton.title = "Delete";
            deleteButton.style.cursor = "pointer";
            deleteButton.addEventListener('mouseover', () => {
                deleteButton.classList.add('fa-beat');
            });
            deleteButton.addEventListener('mouseout', () => {
                deleteButton.classList.remove('fa-beat');
            });
            deleteButton.addEventListener('click', async () => {
                try {
                    var response = await fetch(window.getContosoUrl(window.contoso_configuration.api_baseurl, '/api/booking') + '?bookingId=' + String(entry.bookingId), {method: 'DELETE'}).then(response => response.json());
                    if(typeof(response) == "object" && "success" in response && response.success) {
                        this.refresh();
                    }
                    else {
                        console.log(response);
                    }
                }
                catch(error) {
                    console.log(error);
                }
            });
            actionsCell.appendChild(deleteButton);
            row.appendChild(actionsCell);

            tbody.appendChild(row);
        });
        // add the new table
        var bookingList = document.getElementById(this.#elementId);
        bookingList.innerHTML = "";
        bookingList.appendChild(tbl);
    }

    search(searchString, delaySeconds = 0) {
        if(this.#searchTimeoutId !== null) {
            clearTimeout(this.#searchTimeoutId);
            this.#searchTimeoutId = null;
        }
        delaySeconds = parseFloat(delaySeconds);
        if (delaySeconds > 0) {
            this.#searchTimeoutId = setTimeout(() => this.search(searchString), delaySeconds * 1000);
            return;
        }
        console.log("Searching for: " + searchString);
        this.#search = String(searchString).toLowerCase();
        this.#renderData();
    }

    async refresh() {
        try {
            var data = await fetch(window.getContosoUrl(window.contoso_configuration.api_baseurl, '/api/bookings')).then(response => response.json())
            if (Array.isArray(data)) {
                this.#data = data;
            }
            else {
                if(typeof(d) == "object" && "error" in data) {
                    console.log("Received error from Rest API: " + data["error"]);
                }
                else {
                    console.log(data);
                }
            }
        }
        catch(error) {
            console.log(error);
        }
        this.#renderData();
    }

    async #periodicRefresh() {
        if(this.#intervalSeconds === null) {
            return;
        }
        console.log("Periodic refresh started");
        while(this.#intervalSeconds !== null) {
            console.log("Refreshing data");
            await this.refresh();
            await new Promise(resolve => setTimeout(resolve, this.#intervalSeconds * 1000));
        }
        console.log("Periodic refresh stopped");
    }

    cancelPeriodicRefresh() {
        this.#intervalSeconds = null;
    }
    setPeriodicRefresh(seconds) {
        this.#intervalSeconds = parseFloat(seconds);
        this.#periodicRefresh();
    }
}

var bookingObj = new Booking("bookinglist");
document.addEventListener('DOMContentLoaded', function() {
    bookingObj.setPeriodicRefresh(1);
});

document.getElementById('search').addEventListener('keyup', function(event) {
    bookingObj.search(event.target.value, 0.1);
});

