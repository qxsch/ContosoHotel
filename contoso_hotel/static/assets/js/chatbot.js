
function getChatbotHistory(text) {
    const chatbotContent = document.getElementById("chatbotContent");
    var result = {};
    result.chat_history = [];
    var last_history = null;
    chatbotContent.childNodes.forEach(function(el) {
        // is it an element node?
        if(el.nodeType === 1 && el.nodeName === 'DIV') {
            history = {};
            console.log("FOUND DIV", el);
            if(el.classList.contains('humanbubble')) {
                if(last_history) {
                    result.chat_history.push(last_history);
                }
                last_history = {inputs: {content: el.innerText}, outputs: {}};
            }
            else if(el.classList.contains('robotbubble')) {
                last_history.outputs.answer = el.innerText;
            }
        }
    });
    if(last_history) {
        result.chat_history.push(last_history);
    }
    text = String(text).trim();
    if(text.length > 0) {
        result.question = text;
    }
    return result;
};

if(document.getElementById("chatbotLogo") && document.getElementById("chatbotBar")) {
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

        var chatUrl = "";
        if(window.contoso_configuration.chatbot_frontend_use_chatbot_baseurl) {
            chatUrl = window.contoso_configuration.chatbot_baseurl;
            if(chatUrl == "" || chatUrl == "/") {
                console.error("chatbot_baseurl is not properly set in configuration");
                return;
            }
        }
        else {
            chatUrl = window.getContosoUrl(window.contoso_configuration.api_baseurl, '/api/chat');
        }

        fetch(window.getContosoUrl(window.contoso_configuration.api_baseurl, '/api/chat'), {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        })
        .then(data => data.json())
        .then(function(data) {
            if("answer" in data) {
                var resp = document.createElement("div");
                resp.className ="chat-message robotbubble";
                resp.innerText = data.answer;
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