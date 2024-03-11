const socketProtocol3 = (window.location.protocol === 'https:') ? 'wss' : 'ws';

const socket3 = new WebSocket(socketProtocol3 + "://" + window.location.host + '/ws/chat');
socket3.onopen = function (e) {
    socket3.send(JSON.stringify({
        'check': 'livestatus',
        'for': getUserName(),
    }));
};

//keep checking if user is online
setInterval(function () {
    socket3.send(JSON.stringify({
        'check': 'livestatus',
        'for': getUserName(),
    }));
}, 3000);

var count = 0;
socket3.addEventListener('message', function (e) {
    const data = JSON.parse(e.data);
    if (data.status == 'offline') {
        if (count >= 3) {
            alert("User disconnected. Navigating you to the home page.");
            window.location.href = '/';
        }
        else {
            count++;
        }
    }
    else {
        count = 0;
    }
});

//Do not send empty messages
if(document.getElementById("msg_field").value == ""){
    document.getElementById("send_btn").disabled = true;
}
else{
    document.getElementById("send_btn").disabled = false;
}

document.getElementById("msg_field").addEventListener("input", function(){
    if(document.getElementById("msg_field").value == ""){
        document.getElementById("send_btn").disabled = true;
    }
    else{
        document.getElementById("send_btn").disabled = false;
    }
});

alert("Please wait, User is connecting...");
document.getElementById("msg_field").disabled = true;
document.getElementById("send_btn").disabled = true;