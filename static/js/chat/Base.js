function escapeHtml(text) {
    return text.replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function getUserName(){
    //check if current page is waiting room without function
    if (window.location.href.indexOf("waiting-room") > -1) {
        name = 'user';
        name = escapeHtml(name);
        name = name.replace(/\[/g, '\\[').replace(/\]/g, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
        
    }
    else if (window.location.href.indexOf("chat") > -1) {
            // Remove trailing slashes if any
            url = window.location.href;
            url = url.replace(/\/+$/, '');
            // Split the URL by slashes
            var parts = url.split('/');
            // Get the last part of the array
            var lastPart = parts[parts.length - 1];
            // Return the last directory
            return lastPart;
    }
    else{
        return "NULL";
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i].trim();
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(
            cookie.substring(name.length + 1)
            );
            break;
        }
        }
    }
    return cookieValue;
}

async function encryptData(data, publicKey) {
    //convert the public key to an object
    publicKey = JSON.parse(publicKey);
    //convert the public key to a CryptoKey object
    publicKey = await window.crypto.subtle.importKey(
        "jwk",
        publicKey,
        {
            name: "RSA-OAEP",
            hash: {name: "SHA-256"},
        },
        true,
        ["encrypt"]
    );
  const encryptedData = await window.crypto.subtle.encrypt(
    {
      name: "RSA-OAEP",
    },
    publicKey, // from generateKey or importKey above
    data // ArrayBuffer of data you want to encrypt
  );
    return encryptedData;
}

async function decryptData(encryptedData, privateKey) {
    // convert the private key to a CryptoKey object
    privateKey = await window.crypto.subtle.importKey(
        "jwk",
        privateKey,
        {
            name: "RSA-OAEP",
            hash: {name: "SHA-256"},
        },
        true,
        ["decrypt"]
    );

  const decryptedData = await window.crypto.subtle.decrypt(
    {
      name: "RSA-OAEP",
    },
    privateKey, // from generateKey or importKey above
    encryptedData // ArrayBuffer of the data
  );
  return decryptedData;
}

//driver code

async function main(){
    //get the private key from local storage
    
    //do encrypt
    const privateKey = await window.crypto.subtle.importKey(
        "jwk",
        JSON.parse(localStorage.getItem("privateKey")),
        {
            name: "RSA-OAEP",
            hash: {name: "SHA-256"},
        },
        true,
        ["decrypt"]
    );

}

$(document).ready(function() {
    $('#adduserbutton').prop('disabled', true)
    $('#finduser').on('keyup', function(){
        var username = $('#finduser').val();
        $.ajax({
            url: '../api/check_username/',
            dataType: 'json',
            data: { 
                'username': username 
            },
            success: function(response){
                if(response.status == "ok"){
                    if(!response.available){
                        if(!response.self){
                        $('#finduser').css('border', '2px solid green');
                        $('#adduserbutton').prop('disabled', false);
                        }
                        else{
                            $('#finduser').css('border', '2px solid red');
                            $('#adduserbutton').prop('disabled', true);
                        }
                    }
                    else{
                        $('#finduser').css('border', '2px solid red');
                        $('#adduserbutton').prop('disabled', true);

                    }
                }
            }
        });
    })
});

//limit note length
$(document).ready(function() {
    $('#note').on('keyup', function(){
        var note = $('#note').val();
        if(note.length > 100){
            $('#note').val(note.substring(0, 100));
        }
    })
});

function destroyer(delay, element){
setTimeout(() => {
    //element is class name
    var Message = document.getElementsByClassName(element);
    Message = Message[0];
    Message.remove();
    
}, delay * 1000);
}

function delete_friend(friend){
    Swal.fire({
        title: 'Are you sure?',
        text: "You want to remove this user from your friend list. This action cannot be undone!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, delete it!'
      }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: '../delete_friend',
                dataType: 'json',
                data: { 
                    'friend': friend 
                },
                success: function(response){
                    if(response.status == true){
                        Swal.fire({
                            title: 'Deleted!',
                            text: 'User has been deleted.',
                            confirmButtonColor: '#3085d6',
                            icon: 'success',
                          }).then(function(){
                            parent.location.href = '/';
                          });
                    }
                    else{
                        Swal.fire({
                            title: 'Error!',
                            text: 'An error occured. Please try again later.',
                            confirmButtonColor: '#3085d6',
                            icon: 'error',
                    });
                    }
                },
                error: function(response){
                    Swal.fire(
                        'Error!',
                        'An error occured. Please try again later.',
                        'error'
                      );
                }
            });
        
        }
      });
    }

// This socket is to notify a user, if another user is waiting.
const socketProtocol_4 = (window.location.protocol === "https:") ? "wss" : "ws";
const socket_4 = new WebSocket(socketProtocol_4 + "://" + window.location.host + '/ws/notify/');

socket_4.onopen = function (e) {
    socket_4.send(JSON.stringify({
        'available': 'ping'
    }));
};

IgnoreList = new Array(); // List of users to ignore
Notified = new Array(); // List of users who are already notified
LoaderNotifying = new Array(); // List of users who are already showing loader

socket_4.addEventListener('message', function (e) {
    const data = JSON.parse(e.data);
    if (data.status == 'notify') { //if status is notify, it means, someone is waiting
        users = JSON.parse(data.from);
        
        //if current page is chat page, then remove the current user from the list
        if(window.location.href.indexOf("chat") > -1){
            users = users.filter(function(value, index, arr){
                return value != getUserName();
            });
        }

        // if there is a loader, but user is no longer online, then remove the loader
        for (var i = 0; i < LoaderNotifying.length; i++) {
            user = LoaderNotifying[i];
            if(!users.includes(user)){
                $('#live_notification_'+user).empty();
                LoaderNotifying.splice(i, 1);
            }
        }

        // Show loader and toast notification
        for(var i=0; i < users.length; i++){    
            CurrentUser = users[i]
            if(IgnoreList.includes(CurrentUser)){ // If user is in ignore list, then do not show toast notification
                 if(!LoaderNotifying.includes(CurrentUser)){
                    // show loader
                     $('#live_notification_'+CurrentUser).append("<img src='/static/images/wait.gif' style='width: 30px; height: 30px' /><small style='font-size:50%;' >Waiting!</small>");
                     LoaderNotifying.push(CurrentUser);
                 }
                continue;
            }

            // if user is not yet notified, then show loader
            if(!Notified.includes(CurrentUser)){
                $('#live_notification_'+CurrentUser).append("<img src='/static/images/wait.gif' style='width: 30px; height: 30px' /><small style='font-size:50%;' ><b>Waiting!</b></small>");
                LoaderNotifying.push(CurrentUser);
            }

            // Notify a user (toast notification)
            Notified.push(CurrentUser);
            //play sound
            var audio = new Audio('/static/media/notification.mp3');
            audio.play();
            Swal.fire({
                title: "A Secure Chat Room",
                text: CurrentUser + " is waiting for you in the waiting room!",
                icon: "warning",
                position: "top-end",
                confirmButtonText: 'Join Now',
                denyButtonText: 'Ignore!',
                toast: true,
                showDenyButton: true,
                confirmButtonColor: "#003d89",
                timer: 3000,
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = "/waiting-room?user=" + CurrentUser;
                    //remove the user from the list
                    users.splice(users.indexOf(CurrentUser), 1);

                }
                else if (result.isDenied) {
                    IgnoreList.push(CurrentUser); //add user to ignore list
                    //show toast message that user is ignored
                    Swal.fire({
                        title: "User Ignored",
                        text: "You will not be notified again for this user for a while!",
                        icon: "info",
                        position: "top-end",
                        toast: true,
                        showConfirmButton: false,
                        timer: 4000,
                    });
                    
                }
            }
            );
            
        };
    }
    else{
        //No users are waiting
       //if any loader active and no user is waiting, then remove the loader
         for (var i = 0; i < LoaderNotifying.length; i++) {
                user = LoaderNotifying[i];
                $('#live_notification_'+user).empty();
                LoaderNotifying.splice(i, 1);
          }
    }
});

setInterval(function () {
    socket_4.send(JSON.stringify({
        'available': 'ping',
    }));
}, 3000);

parent.document.title = "PrivatePing - A Secure Chat Room";