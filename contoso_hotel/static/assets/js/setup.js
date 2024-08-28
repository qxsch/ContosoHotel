document.getElementById('setupdb').addEventListener('click', function() {
    document.getElementById('log').innerHTML = 'Running...';
    var drop_schema = document.getElementById('drop_schema').checked;
    var create_schema = document.getElementById('create_schema').checked;
    var populate_data = document.getElementById('populate_data').checked;
    if (!drop_schema && !create_schema && !populate_data) {
        document.getElementById('log').innerHTML = '';
        var el = document.createElement('h2');
        el.innerHTML = 'No action selected';
        document.getElementById('log').appendChild(el);
        return;
    }
    fetch(window.getContosoUrl(window.contoso_configuration.api_baseurl, '/api/setup'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'drop_schema' : drop_schema,
            'create_schema': create_schema,
            'populate_data': populate_data
        })
    })
    .then(response => response.json())
    .then(data => {
        if("error" in data) {
            throw new Error(data['error']);
        }
        console.log(data);
        if(data['success']) {
            document.getElementById('log').innerHTML = '';
            var el = document.createElement('h2');
            el.innerHTML = 'Sucessfully setup database';
            document.getElementById('log').appendChild(el);
            var p = document.createElement('p');
            p.innerHTML = "";
            if(data['drop_schema']) {
                p.innerHTML += "Dropped schema<br>";
            }
            if(data['create_schema']) {
                var s = "";
                for (let [key, value] of Object.entries(data['create_schema'])) {
                    if(value) {
                        s += "Created table: " + key.replace(/[\x26\x0A\<>'"]/g,function(r){return"&#"+r.charCodeAt(0)+";"}) + "<br>";
                    }                    
                }
                if(s != "") {
                    p.innerHTML += "Creating schema<br>" + s;
                }
                else if(create_schema) {
                    p.innerHTML += "No schema creation required<br>";
                }
            }
            if(data['populate_data']) {
                var s = "";
                for (let [key, value] of Object.entries(data['populate_data'])) {
                    if(value) {
                        s += "Populated data into table: " + key.replace(/[\x26\x0A\<>'"]/g,function(r){return"&#"+r.charCodeAt(0)+";"}) + "<br>";
                    }                    
                }
                if(s != "") {
                    p.innerHTML += "Populating data<br>" + s;
                }
                else if(populate_data) {
                    p.innerHTML += "No data population required<br>";
                }
            }
            document.getElementById('log').appendChild(p);    
        } else {
            document.getElementById('log').innerHTML = '';
            var el = document.createElement('h2');
            el.innerHTML = 'Failed to setup database';
            document.getElementById('log').appendChild(el);
        }
    })
    .catch((error) => {
        document.getElementById('log').innerHTML = '';
        var el = document.createElement('h2');
        el.innerHTML = 'Failed to setup database';
        document.getElementById('log').appendChild(el);
        var p = document.createElement('p');
        p.textContent = error;
        document.getElementById('log').appendChild(p);
        console.log('Error:', error);
    });
});