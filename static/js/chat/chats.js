const socketProtocol_3 = (window.location.protocol === 'https:') ? 'wss' : 'ws';

const socket_3 = new WebSocket(socketProtocol_3 + "://" + window.location.host + '/ws/chat/status/');
socket_3.onopen = function (e) {
    socket_3.send(JSON.stringify({
        'check': 'livestatus',
        'for': getUserName(),
    }));
};

//keep checking if user is online
setInterval(function () {
    socket_3.send(JSON.stringify({
        'check': 'livestatus',
        'for': getUserName(),
    }));
}, 3000);

var count = 0;
socket_3.addEventListener('message', function (e) {
    const data = JSON.parse(e.data);
    if (data.status == 'offline') {
        if (count >= 3) {
            Swal.fire({
                icon: "error",
                title: "Oops...",
                confirmButtonColor: "#003d89",
                text: "User disconnected, Navigating you to home page!",
              }).then(function(){
                parent.location.href = "/";

              });
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

Swal.fire({
    title: "Creating a secure room!",
    text: "Please wait while we connect you.",
    confirmButtonColor: "#003d89",
    icon: "info"
  });
document.getElementById("msg_field").disabled = true;
document.getElementById("send_btn").disabled = true;

function trashmessages(){
    //play sound
    var audio = new Audio('/static/media/delete.mp3');
    audio.play();

    //Remove all messages whose id is ChatMessage
    var chatMessages = document.querySelectorAll('#ChatMessage');

    // Iterate through each element and remove it
    chatMessages.forEach(function(element) {
        element.remove();
    });

}