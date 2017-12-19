

$(document).ready(function(){
    'use strict';

    // TEst function for development
    var func_test = function(post_id, price_id) {
//        $("#form_elements").append('<label for="' + post_id + '">Post nr:</label> <input class="loppis" id="' + post_id + '" name="post_id" type="text" value=""> <label for="' + price_id + '">Pris:</label>  <input class="loppis price" id="' + price_id + '" name="price" type="text" value="">');
        var jq_post_id = "#" + post_id;
        var jq_price_id = "#" + price_id;
        console.log("func_test");

        $(jq_post_id).blur(function() {
            $(jq_price_id).val($(jq_post_id).val());
        });
    };

    // Stop sending form with enter
    $("form").bind("keypress", function (e) {
        if (e.keyCode == 13) {
            return false;
        }
    });

    // Toggles the fixed price and minimum price boxes according to the select status
    var add_toggler_func = function() {
        var type_id = "#master_type";
        var fixed_price_div_id = "#fixed_price_div_id";
        $(fixed_price_div_id).hide();

        $(type_id).change(function(){
            toggle();
        });

        var toggle = function() {
            var type_id = "#master_type";
            var min_price_div_id = "#min_price_div_id";
            var fixed_price_div_id = "#fixed_price_div_id";
            var min_price_id = "#min_price_id";
            var fixed_price_id = "#fixed_price_id";
            var type_id_val = $(type_id).val();
            console.log(type_id_val);
            var min_price_div = $(min_price_div_id);
            var fixed_price_div = $(fixed_price_div_id);

            $.ajax({
                url: '/json_get_type/' + type_id_val,
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
                            $(fixed_price_id).val("");
                            console.log("hide fixed, show min");
                        } else {
                            fixed_price_div.show();
                            min_price_div.hide();
                            $(min_price_id).val("");
                            console.log("hide min, show fixed");
                        }
                    };

                    console.log('.ajax() request returned successfully.');
                },
                error: function(jqXHR, textStatus, errorThrown){
                    console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
                },
            });
        };

        toggle();

    ;}


  
  // Check if all flea_market objects has got a price, else show error text and cancel submit
  // Check that if auction objects have price it is numeric
//  $( "#register_form" ).submit(function( event ) {
  $( "#submit" ).click(function() {
     var all_ok = true;
     console.log("checking prices");
     $( ".fixed_price_input:visible" ).each(function( index ) {  // if visible its a flea market object
        if ($.isNumeric( $(this).val() )) {
            $(this).removeClass("error_border");
            $(this).siblings('div').text("");
            $( "#msg" ).text("OK");
        } else {
            $(this).siblings('div').text(" Du måste fylla i ett pris");
            $(this).addClass("error_border");
            all_ok = false;
        }         
     });
     $( ".min_price_input:visible" ).each(function( index ) {  // if visible its a auction object
        if ($.isNumeric( $(this).val() )) {
            $(this).removeClass("error_border");
            $(this).siblings('div').text("");
            $( "#msg" ).text("OK");
            console.log("price ok");
        } else {
            if ($(this).val() == "") {
                // Empty min price which is ok
                $(this).removeClass("error_border");
                $(this).siblings('div').text("");                
                console.log("Empty price");
            } else {
                $(this).siblings('div').text(" Du måste fylla i en siffra");
                $(this).addClass("error_border");
                all_ok = false;
                console.log("Non numeric price");
            }
        }
     });
     if (all_ok) {
        return true;
     } else {
        return false;
     }
  });

    var option_values = "";
    var sale_type = "error";
    add_toggler_func();


    console.log('Everything is ready.');
});


