function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function generateKeys() {
  const { publicKey, privateKey } = await window.crypto.subtle.generateKey(
    {
      name: "RSA-OAEP",
      modulusLength: 2048, // can be 1024, 2048, or 4096
      publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
      hash: { name: "SHA-256" }, // can be "SHA-1", "SHA-256", "SHA-384", or "SHA-512"
    },
    true, // whether the key is extractable (i.e. can be used in exportKey)
    ["encrypt", "decrypt"] // can be any combination of "encrypt" and "decrypt"
  );
  return { publicKey, privateKey };
}

async function main() {
  const { publicKey, privateKey } = await generateKeys();
  //save private key in local storage
  const privateKeyExported = await window.crypto.subtle.exportKey(
    "jwk",
    privateKey
  );

  localStorage.setItem("privateKey", JSON.stringify(privateKeyExported));
  //make a post request of the public key to the server
  const publicKeyExported = await window.crypto.subtle.exportKey(
    "jwk",
    publicKey
  );

  //combine the public key in one string
  const publicKeyString = JSON.stringify(publicKeyExported);

  //ajax post request
  $.ajax({
    type: "POST",
    url: "",
    data: {
      csrfmiddlewaretoken: getCookie("csrftoken"),
      public_key: publicKeyString,
      success: true,
    },
    success: function (data) {
      window.location = data.redirect;
    },
  });
}

main();

if (typeof parent !== 'undefined' && parent.document) {
  parent.document.title = "PrivatePing - Securing Session";
}