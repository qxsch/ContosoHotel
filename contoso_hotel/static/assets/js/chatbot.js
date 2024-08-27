
function getChatbotHistory(text) {
    const chatbotContent = document.getElementById("chatbotContent");
    var result = [];
    chatbotContent.childNodes.forEach(function(el) {
        // is it an element node?
        if(el.nodeType === 1 && el.nodeName === 'DIV') {
            console.log("FOUND DIV", el);
            if(el.classList.contains('humanbubble')) {
                result.push({content: el.innerText, role: 'user'});
            }
            else if(el.classList.contains('robotbubble')) {
                result.push({content: el.innerText, role: 'assistant'});
            }
        }
    });
    text = String(text).trim();
    if(text.length > 0) {
        result.push({content: text, role: 'user'});
    }
    return result;
};

if(document.getElementById("chatbotLogo")) {
    console.log('Enabling chatbot integration');
    // closing and opening chatbot sidebar
    document.getElementById("chatbotLogo").addEventListener("click", function() {
        document.querySelector('#chatbotLogo i').classList.add('fa-beat');
        document.getElementById("chatbotBar").classList.toggle('closed');
        document.getElementById("chatbotLogo").classList.toggle('closed');
        
    });
    document.getElementById("chatbotClose").addEventListener("click", function() {
        document.getElementById("chatbotBar").classList.toggle('closed');
        document.getElementById("chatbotLogo").classList.toggle('closed');
    });
    // beat animation
    document.querySelector('#chatbotLogo i').classList.add('fa-beat');
    document.getElementById("chatbotLogo").addEventListener("mouseover", function() {
        document.querySelector('#chatbotLogo i').classList.remove('fa-beat');
    });
    setTimeout(function() {
        console.log('removing fa-beat');
        document.querySelector('#chatbotLogo i').classList.remove('fa-beat');
    }, 5000);



    // submit
    document.getElementById("chatbotSubmit").addEventListener("click", function() {
        var text = document.getElementById("chatbotInput").value;
        var data = getChatbotHistory(text);
        document.getElementById("chatbotInput").value = '';

        var ask = document.createElement("div");
        ask.className ="chat-message humanbubble";
        ask.innerText = text;
        document.getElementById("chatbotContent").appendChild(ask);

        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(data => data.json())
        .then(function(data) {
            if("content" in data) {
                var resp = document.createElement("div");
                resp.className ="chat-message robotbubble";
                resp.innerText = data.content;
                document.getElementById("chatbotContent").appendChild(resp);
            }
        });
    });

    document.getElementById("chatbotInput").addEventListener("keyup", function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            document.getElementById("chatbotSubmit").click();
        }
    });
}