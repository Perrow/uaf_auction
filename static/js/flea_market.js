

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

    // Fetch json data for the selected post when user presses tab in the post_id input.
    var func = function(post_id, price_id){

        $('#' + post_id).blur(function() {

            var id = $('#' + post_id).val();

            $.ajax({
                url: 'json/' + id,
                dataType: 'json',
                success: function(data){
                    if(data.hasOwnProperty('error')){
                        console.log("Not found");
                        $("#" + price_id).val("");
                        $('#scientific_name').html("").fadeIn();
                        $('#plain_name').html("").fadeIn();
                        $('#description').html("").fadeIn();
                        $('#seller_name').html("").fadeIn();
                        $('#type').html("").fadeIn();
                        $('#sold').html("").fadeIn();
                        $('#error').html("POSTEN FINNS INTE I DATABASEN").fadeIn();
                    } else {
                        console.log("Found");
                        $("#" + price_id).val(data.fixed_price);
                        $('#scientific_name').html(data.scientific_name).fadeIn();
                        $('#plain_name').html(data.plain_name).fadeIn();
                        $('#description').html(data.description).fadeIn();
                        $('#seller_name').html(data.name).fadeIn()
                //          Warning for posts not registrated for auction
                        if (data.type != "fixed_price") {
                            $('#type').html("Ej registrerad för fasta bordet").fadeIn();
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
                    $("#" + price_id).val("");
                    $('#scientific_name').html("").fadeIn();
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
    };


    // Add a new row of input boxes
    var rowNum = 1;
    $("#addbutton").click(function(){
        console.log("addbutton clicked");
        rowNum ++;
        var post_id = "post" + rowNum;
        var price_id = "price" + rowNum;

        $("#form_elements").append('<label for="' + post_id + '">Post nr:</label> <input class="loppis" id="' + post_id + '" name="post_id" type="text" value=""> <label for="' + price_id + '">Pris:</label>  <input class="loppis price" id="' + price_id + '" name="price" type="text" value=""><br>');
        func(post_id, price_id);
    });


    // Caclulate the sum the customer should pay
    $("#sumbutton").click(function(){
        var tot_sum = 0;
        $('.price').each(function(i, obj) {
            console.log(this.value);
            tot_sum += Number(this.value);
            console.log(tot_sum);
            $('#sum').html("Att betala: " + tot_sum).fadeIn();
        });
    })


    // Set handler for first post
    func("post1", "price1");

    console.log('Everything is ready.');
});


