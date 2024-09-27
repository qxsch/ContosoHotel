window.chatbotHistory = [
];

function getChatbotHistory(text) {
    return {
        chat_history: window.chatbotHistory,
        question: text
    };
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
        document.getElementById("chatbotInput").value = '';

        var ask = document.createElement("div");
        ask.className ="chat-message humanbubble";
        ask.innerText = text;
        document.getElementById("chatbotContent").appendChild(ask);
        window.chatbotHistory.push({
            inputs: {content: text},
            outputs: {}
        });

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
            body: JSON.stringify(getChatbotHistory(text)),
        })
        .then(data => data.json())
        .then(function(data) {
            if("answer" in data) {
                var resp = document.createElement("div");
                resp.className ="chat-message robotbubble";
                // resp.innerText = data.answer; // without markdown
                
                // adding markdown
                var zmd = document.createElement("zero-md");
                zmd.innerHTML ='<template data-append><style> .markdown-body { background-color:transparent; } </style></template>';
                var md = document.createElement("script");
                md.type = "text/markdown";
                md.innerHTML = data.answer;
                zmd.appendChild(md);
                resp.appendChild(zmd);
                
                document.getElementById("chatbotContent").appendChild(resp);
                window.chatbotHistory[window.chatbotHistory.length-1].outputs.answer = data.answer;
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