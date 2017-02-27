

$(document).ready(function(){
  'use strict';

  $('#post_id').blur(function(){
    var post_id = $('#post_id').val();

    $.ajax({
      url: 'json/' + post_id,
      dataType: 'json',
      success: function(data){
        if(data.hasOwnProperty('error')){
          console.log("Not found");
          $('#scientific_name').html("").fadeIn();
          $('#min_price').html("").fadeIn();
          $('#plain_name').html("").fadeIn();
          $('#description').html("").fadeIn();
          $('#seller_name').html("").fadeIn();
          $('#type').html("").fadeIn();
          $('#sold').html("").fadeIn();
          $('#error').html("POSTEN FINNS INTE I DATABASEN").fadeIn();
        } else {
          console.log("Found");
          $('#scientific_name').html(data.scientific_name).fadeIn();
          $('#min_price').html(data.minimum_price).fadeIn();
          $('#plain_name').html(data.plain_name).fadeIn();
          $('#description').html(data.description).fadeIn();
          $('#seller_name').html(data.name).fadeIn()
//          Warning for posts not registrated for auction
          if (data.type != "auction") {
              $('#type').html("Ej registrerad som auktionsgods").fadeIn();
          } else {
              $('#type').html("").fadeIn();
          }
          if (data.sold_on !== null) {
              $('#sold').html("Redan sålt").fadeIn();
              document.getElementById("price").value = data.sold_price;
          } else {
              $('#sold').html("").fadeIn();
              document.getElementById("price").value = "";
          }
          $('#error').html("").fadeIn();
        };

        console.log('.ajax() request returned successfully.');
      },
      error: function(jqXHR, textStatus, errorThrown){
        $('#scientific_name').html("").fadeIn();
        $('#min_price').html("").fadeIn();
        $('#plain_name').html("").fadeIn();
        $('#description').html("").fadeIn();
        $('#seller_name').html("").fadeIn();
        $('#type').html("").fadeIn();
        $('#sold').html("").fadeIn();
        $('#error').html("INGET POST ID GAVS").fadeIn();
        console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
      },
    });
  });


  console.log('Everything is ready.');
});


