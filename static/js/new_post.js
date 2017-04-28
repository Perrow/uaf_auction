

$(document).ready(function(){
  'use strict';


    var type_id = $('#type').val();
    console.log(type_id);
    var min_price_div = $('#min_price_div');
    var fixed_price_div = $('#fixed_price_div');

    $.ajax({
      url: 'json_get_type/' + type_id,
      dataType: 'json',
      success: function(data){
        if(data.hasOwnProperty('error')){
          console.log("Not found");
        } else {
          console.log("Found");
          console.log(data.sale_type);
          if (data.sale_type == "auction") {
            fixed_price_div.hide();
            min_price_div.show();
            console.log("hide fixed, show min");
          } else {
            fixed_price_div.show();
            min_price_div.hide();
            console.log("hide min, show fixed");
          }
        };

        console.log('.ajax() request returned successfully.');
      },
      error: function(jqXHR, textStatus, errorThrown){
        console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
      },
    });



  $('#type').change(function(){
    var type_id = $('#type').val();
    console.log(type_id);
    var min_price_div = $('#min_price_div');
    var fixed_price_div = $('#fixed_price_div');

    $.ajax({
      url: 'json_get_type/' + type_id,
      dataType: 'json',
      success: function(data){
        if(data.hasOwnProperty('error')){
          console.log("Not found");
        } else {
          console.log("Found");
          console.log(data.sale_type);
          if (data.sale_type == "auction") {
            fixed_price_div.hide();
            min_price_div.show();
            console.log("hide fixed, show min");
          } else {
            fixed_price_div.show();
            min_price_div.hide();
            console.log("hide min, show fixed");
          }
        };

        console.log('.ajax() request returned successfully.');
      },
      error: function(jqXHR, textStatus, errorThrown){
        console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
      },
    });
  });

  // Check that a flea market post has a numeric price
  $( "#register_form" ).submit(function( event ) {
     if ($( "#fixed_price_div:visible" ).length == 1 ) {
        var inp = $("#fixed_price");
//        alert(inp.val());
        if ($.isNumeric( inp.val() )) {
//            $( "#msg" ).text("OK");
            $( "#fixed_price_error" ).text( "" );
            return true;
        } else {
            $( "#fixed_price_error" ).text( "Måste fyllas i med ett pris" );
            return false;
        } 
     }
  });



  console.log('Everything is ready.');
});


