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
                    console.log("ok1");
                    if(!response.available){
                        console.log("ok2")
                        if(!response.self){
                            console.log("ok3")
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


parent.document.title = "PrivatePing - A Secure Chat Room";