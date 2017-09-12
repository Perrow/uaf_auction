

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
    var add_toggler_func = function(rownr) {
        console.log("row " + rownr);
        var type_id = "#type" + rownr;
        var fixed_price_div = "#fixed_price_div" + rownr;
        $(fixed_price_div).hide();

        $(type_id).change(function(){
            var type_id = "#type" + rownr;
            var min_price_div_id = "#min_price_div" + rownr;
            var fixed_price_div_id = "#fixed_price_div" + rownr;
            var type_id_val = $(type_id).val();
            console.log(type_id_val);
            var min_price_div = $(min_price_div_id);
            var fixed_price_div = $(fixed_price_div_id);

            $.ajax({
                url: 'json_get_type/' + type_id_val,
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

    ;}


    //  Copies all values from the post above to current post
    var copy_func = function(rownr) {
        var prev_row = rownr - 1;
        var copybutton_id = "#" + "copybutton" + rownr;
        var source_type_id = "#" + "type" + prev_row;
        var dest_type_id = "#" + "type" + rownr;
        var source_sciname_id = "#" + "sciname" + prev_row;
        var dest_sciname_id = "#" + "sciname" + rownr;
        var source_popname_id = "#" + "popname" + prev_row;
        var dest_popname_id = "#" + "popname" + rownr;
        var source_min_price_id = "#" + "min_price" + prev_row;
        var dest_min_price_id = "#" + "min_price" + rownr;
        var source_fixed_price_id = "#" + "fixed_price" + prev_row;
        var dest_fixed_price_id = "#" + "fixed_price" + rownr;
        var source_description_id = "#" + "description" + prev_row;
        var dest_description_id = "#" + "description" + rownr;
        $(copybutton_id).click(function() {
            $(dest_type_id).val($(source_type_id).val());
            $(dest_sciname_id).val($(source_sciname_id).val());
            $(dest_popname_id).val($(source_popname_id).val());
            $(dest_min_price_id).val($(source_min_price_id).val());
            $(dest_fixed_price_id).val($(source_fixed_price_id).val());
            $(dest_description_id).val($(source_description_id).val());
            $(dest_type_id).trigger("change");
        });

    };

    // Makes a json call to server and fetches the sell types from the database in order to generate the drop down
    var make_option_value = function(){
        console.log("make_dropdown");
        var e = document.getElementById("master_type");
        var selected_id = e.options[e.selectedIndex].value;
        console.log("selected: " + selected_id);
        option_values = "";
        jQuery.ajax({
            async: false,
            url: 'json_get_sell_types',
            dataType: 'json',
            success: function(data){
                if(data.hasOwnProperty('error')){
                    console.log("Not found");
                } else {
                    console.log("Found");
                    $(jQuery.parseJSON(JSON.stringify(data))).each(function() {
                    if (this.type_id == selected_id) {
                        option_values += '<option value="' + this.type_id + '" selected="selected" >' + this.description + '</option>'; 
                        sale_type = this.sale_type;
                    } else {
                        option_values += '<option value="' + this.type_id + '">' + this.description + '</option>';                    
                    }

                    });
                    console.log(option_values);
                };
                console.log('.ajax() request returned successfully.');
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
            },
        });
    };


    // Add a a number of new post forms
    var rowNum = 0;
    $("#addbutton").click(function(){
        console.log("addbutton clicked");
        make_option_value();

        console.log("+++" + option_values);
        rowNum = Number($("#numberofposts").val());
        for (var i=0; i < rowNum; i++) {
            var type_id = "type" + i;
            var sciname_id = "sciname" + i;
            var popname_id = "popname" + i;

            var min_price_id = "min_price" + i;
            var fixed_price_id = "fixed_price" + i;
            var min_price_div_id = "min_price_div" + i;
            var fixed_price_div_id = "fixed_price_div" + i;
            var min_price_error_id = "min_price_error" + i;
            var fixed_price_error_id = "fixed_price_error" + i;
            var description_id = "description" + i;
            var copybutton_id = "copybutton" + i;

            var new_post_html = '<br>' +
            '<div class="blackborder">' +
            '<label for="' + type_id + '">Godstyp</label>' +
            '<select id="' + type_id + '" name="type">' + option_values +
            '</select>' +
            '<br>' +

            '<div class="left forty" >' +
                '<label for="' + sciname_id + '">Vetenskapligt namn:</label><br>' +
                '<input class="ninety" id="' + sciname_id + '" name="sciname" type="text" value=""> <br>' +
            '</div>' +
            '<div  class="left forty">' +
                '<label for="' + popname_id + '">Populärnamn:</label><br>' +
                '<input class="ninety" id="' + popname_id + '" name="popname" type="text" value=""> <br>' +
            '</div>' +
            '<div  id="' + min_price_div_id + '" class="left ten">' +
                '<label for="' + min_price_id + '">Reservationspris:</label><span id="' + min_price_error_id + ' " class="error"></span><br>' +
            '   <input class="ninety min_price_input" id="' + min_price_id + '" name="min_price" type="text" value=""> <br>' +
            '</div>' +
            '<div  id="' + fixed_price_div_id + '" class="left ten ">' +
                '<label for="' + fixed_price_id + '">Fast pris:</label><span id="' + fixed_price_error_id + ' " class="error"></span><br>' +
               '<input class="ninety fixed_price_input" id="' + fixed_price_id + '" name="fixed_price" type="text" value=""> <br>' +
           '</div>' +

            '<div  class="left ninetyfour">' +
                '<label for="' + description_id + '">Beskrivning:</label><br>' +
                '<input class="ninety" id="' + description_id + '" name="description" type="text" value=""> <br>' +
            '</div>'
            if (i > 0) {  // Do not put copy button on the first subform
                new_post_html += '<button id="' + copybutton_id + '" type="button">Kopiera post</button>'
            }
            new_post_html += '</div>' ;

            $("#form_elements").append(new_post_html);
            copy_func(i);
            add_toggler_func(i);
            console.log(sale_type);
            if (sale_type == "auction") {
                $("#" + fixed_price_div_id).hide();
                $("#" + min_price_div_id).show();
            } 
            if (sale_type == "fixed_price") {
                          $("#" + fixed_price_div_id).show();
                $("#" + min_price_div_id).hide();
            } 
            $("#create_posts").hide();
            $("#submit").show();
        }
    });


  // Check if all flea_market objects has got a price, else show error text and cancel submit
  // Check that if auction objects have price it is numeric
  $( "#register_form" ).submit(function( event ) {
     var all_ok = true;
     console.log("checking prices");
     $( ".fixed_price_input:visible" ).each(function( index ) {  // if visible its a flea market object
        if ($.isNumeric( $(this).val() )) {
            $(this).removeClass("error_border");
            $(this).siblings('span').text("");
            $( "#msg" ).text("OK");
        } else {
            $(this).siblings('span').text(" Du måste fylla i ett pris");
            $(this).addClass("error_border");
            all_ok = false;
        }         
     });
     $( ".min_price_input:visible" ).each(function( index ) {  // if visible its a auction object
        if ($.isNumeric( $(this).val() )) {
            $(this).removeClass("error_border");
            $(this).siblings('span').text("");
            $( "#msg" ).text("OK");
            console.log("price ok");
        } else {
            if ($(this).val() == "") {
                // Empty min price which is ok
                console.log("Empty price");
            } else {
                $(this).siblings('span').text(" Du måste fylla i en siffra");
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
    $("#submit").hide();

    console.log('Everything is ready.');
});


