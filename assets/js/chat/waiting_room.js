$(document).ready(function(){
    function getUrlParameter(name) {
        name = name.replace(/\[/g, '\\[').replace(/\]/g, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));

    };

    function checkUserStatus(userID){
        $.ajax({
            url: 'api/room',
            method: 'GET',
            data: { user: userID }, // Pass the user ID along with the request
            success: function(response){
                if(response.status == true){
                    window.location.href = 'chat/' + userID;
                    // You can perform any action here, such as enabling chat UI
                }
            },
            error: function(){
                // You can handle errors here
            }
        });
    }

    // Extract user ID from URL parameter
    var userID = getUrlParameter('user');

    // Call the function initially when the page loads
    if(userID){
        checkUserStatus(userID);
    }

    // Set interval to periodically check user status
    setInterval(function(){
        if(userID){
            checkUserStatus(userID);
        }
    }, 1000); // Check every 1 seconds, adjust as needed
});