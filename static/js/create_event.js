$(document).ready(function(){
    'use strict';
    
   
$('form').submit(function() {
    // Checks that all the fields have some sort of value except the description text area.
    // The two checkboxes must also be checked to submit the form
    var checkbox_status = true;
    if ($(cookies).is(":checked") && $(database).is(":checked")) {
        console.log("Cookies and database checked");
         $("#checkbox_message").text("");
        checkbox_status = true;
    } else {
        console.log("Cookies or database uncheked");
        $("#checkbox_message").text("Du måste godkänna både att cookies används och att personlig data lagras.");
        checkbox_status = false;
    }
    
    var status = true;
    
    $('input[type=text]').each(function(){
        var text_value=$(this).val();
        if(text_value!='') {
            console.log('Value exist', text_value);
        } else {
            status = false;
        }
    })
    
    if (status === false) {
        $("#message").text("Du måste fylla i alla fält.")
    } else {
        $("#message").text("")
    }

    return (checkbox_status && status)
});
    
    console.log('Everything is ready.');
});