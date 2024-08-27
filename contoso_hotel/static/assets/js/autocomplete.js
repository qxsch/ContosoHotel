class AutoCompleteInput {
    #inputElement = null;
    #dropdownList = null;
    #insertAfterInput = false;
    #dropdownListLimit = 100;
    #resolver = null;
    #searchTimeoutId = null;
    #search = "";
    #defaultSearchDelay = 0.05;
    #listItems = [];

    constructor(inputElement, resolvingPromise, insertAfterInput = false) {
        this.#inputElement = inputElement;
        this.#insertAfterInput = insertAfterInput;

        // is resolving promise an array or a function?
        if(resolvingPromise instanceof Array) {
            // create a promise that resolves the array
            this.#resolver = function(search) {
                return new Promise(function(resolve, reject) {
                    var results = [];
                    for(var i = 0; i < resolvingPromise.length; i++) {
                        if(search == "" || resolvingPromise[i]['text'].toLowerCase().indexOf(search.toLowerCase()) !== -1) {
                            results.push({
                                'html' : resolvingPromise[i]['html'],
                                'text' : resolvingPromise[i]['text'],
                                'value' : resolvingPromise[i]['value']
                            });
                        }
                    }
                    resolve(results);
                });
            }
        }
        else if(typeof(resolvingPromise) === "function") {
            this.#resolver = resolvingPromise;
        }
        else {
            throw "Invalid resolving promise";
        }

        // add dropdown list to the DOM
        this.#dropdownList = document.createElement("div");
        this.#dropdownList.className = "autocompletelist";
        this.#dropdownList.style.display = "none";

        if(this.#insertAfterInput) {
            this.#inputElement.insertAdjacentElement("afterend", this.#dropdownList);
        }
        else {
            document.body.appendChild(this.#dropdownList);
        }

        var that = this;
        this.#inputElement.addEventListener("focus", function() {
            console.log("focus");
            that.showDropdownList();
        });

        this.#inputElement.addEventListener("blur", function() {
            console.log("blur");
            if(that.isDropdownListVisible()) {
                // wait for the click event to be processed
                setTimeout(function() {
                    if(document.activeElement !== that.#dropdownList) {
                        that.hideDropdownList();
                    }
                }, 200);
            }
        });

        this.#inputElement.addEventListener("keyup", function() {
            that.onKeyUp();
        });

        // add event listener to hide dropdown list when resizing the window
        window.addEventListener("resize", function() {
            that.hideDropdownList();
        });
    }

    setDropdownListLimit(limit) {
        this.#dropdownListLimit = limit;
    }
    getDropdownListLimit() {
        return this.#dropdownListLimit;
    }

    setDefaultSearchDelay(delaySeconds) {
        this.#defaultSearchDelay = delaySeconds;
    }
    getDefaultSearchDelay() {
        return this.#defaultSearchDelay
    }

    onKeyUp() {
        this.search(this.#inputElement.value, this.#defaultSearchDelay);
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
        searchString = String(searchString).toLowerCase().trim();
        if(this.#search === searchString) {
            return;
        }
        console.log("Searching for: " + searchString);
        this.#search = searchString;

        this.#renderData();
    }

    async #renderData() {
        this.#inputElement.dataset.value = "";
        var data = await this.#resolver(this.#search);
        if (Array.isArray(data)) {
            // limit the number of items
            if(data.length > this.#dropdownListLimit) {
                this.#listItems = data.slice(0, this.#dropdownListLimit);
            }
            else {
                this.#listItems = data;
            }
        }
        else {
            if(typeof(d) == "object" && "error" in data) {
                console.log("Received error from Rest API: " + data["error"]);
            }
            else {
                console.log(data);
            }
        }

        this.#dropdownList.innerHTML = "";
        var that = this;
        var inputElement = this.#inputElement;

        if(this.#listItems.length === 0) {
            this.hideDropdownList();
            return;
        }
        else if(this.#listItems.length === 1) {
            if(!("text" in this.#listItems[0]) || !("value" in this.#listItems[0])) {
                console.log("Invalid item in list (expecting text and value keys)", item);
            }
            else {
                that.setValue(this.#listItems[0]);
            }
            this.hideDropdownList();
            return;
        }

        this.#listItems.forEach(item => {
            // does it have text and value?
            if(!("text" in item) || !("value" in item)) {
                console.log("Invalid item in list (expecting text and value keys)", item);
                return;
            }
            var el = document.createElement("div");
            el.className = "autocompleteitem";
            el.textContent = item.text;
            if(("html" in item) && item.html) {
                el.innerHTML = item.html;
            }
            else {
                el.textContent = item.text;
            }
            el.dataset.value = item.value;
            el.addEventListener("click", function() {
                that.setValue(item);
                that.hideDropdownList();
            });
            that.#dropdownList.appendChild(el);
        });

        if(!this.isDropdownListVisible()) {
            this.showDropdownList();
        }
    }

    setValue(value) {
        // does it have text and value?
        if(!("text" in value) || !("value" in value)) {
            console.log("Invalid item in list (expecting text and value keys)", value);
            return;
        }
        this.#inputElement.value = String(value.text);
        this.#inputElement.dataset.value = String(value.value);
    }
    getValue() {
        return {
            'text' : this.#inputElement.value,
            'value' : this.#inputElement.dataset.value
        };
    }

    isDropdownListVisible() {
        return this.#dropdownList.style.display === "block";
    }

    hideDropdownList() {
        this.#dropdownList.style.display = "none";
    }

    showDropdownList() {
        this.#dropdownList.style.display = "block";
        this.#dropdownList.style.position = "absolute";
        if(this.#insertAfterInput) {
            this.#dropdownList.style.width = this.#inputElement.offsetWidth + "px";
            this.#dropdownList.style.left = this.#inputElement.offsetLeft + "px";
            this.#dropdownList.style.top = this.#inputElement.offsetTop + this.#inputElement.offsetHeight + "px";
            this.#dropdownList.style.maxHeight = "250px";
        }
        else {
            var rect = this.#inputElement.getBoundingClientRect();
            this.#dropdownList.style.width = rect.width + "px";
            this.#dropdownList.style.left = rect.x + "px";
            this.#dropdownList.style.top = rect.y + rect.height + "px";
    
            // calculate the max-height of the dropdown list (until end of the window)
            var maxHeight = window.innerHeight - rect.y - rect.height - 50;
            if(maxHeight < 100) {
                maxHeight = 100;
            }
            this.#dropdownList.style.maxHeight = maxHeight + "px";
        }
    }
 
    getInputElement() {
        return this.#inputElement;
    }
}

