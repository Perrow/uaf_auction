$(document).ready(function () {
    'use strict';
    var tot_sum = 0;
    
    // TEst function for development
    var func_test = function (post_id, price_id) {
//        $("#form_elements").append('<label for="' + post_id + '">Post nr:</label> <input class="loppis" id="' + post_id + '" name="post_id" type="text" value=""> <label for="' + price_id + '">Pris:</label>  <input class="loppis price" id="' + price_id + '" name="price" type="text" value="">');
        var jq_post_id = "#" + post_id;
        var jq_price_id = "#" + price_id;
        console.log("func_test");

        $(jq_post_id).blur(function () {
            $(jq_price_id).val($(jq_post_id).val());
        });
    };

    // Handlers for the items in the input rows
    var func = function (id) {
        console.log(id);
//        var row_id = "row" + id;
        var post_id = "post" + id;
        var price_id = "price" + id;
        var info_id = "info" + id;
        var remove_id = "remove" + id;
        console.log("Remove: " + remove_id, id);

        // Leave price input
        $('#' + price_id).blur(function () {
            if ($.isNumeric($('#' + price_id).val())) {
                $('#error').html("").fadeIn();
            } else {
                $('#error').html("Pris måste ges").fadeIn();
            }
            calculate_sum();
        });

        // Calculates the sum when cursor leaves the price input box
        $('#' + price_id).change(function () {
            calculate_sum();
        });
        
        //This calculates the sum when the value in the price input box changes on the fly
        var e = document.getElementById(price_id);
        e.oninput = calculate_sum;
        e.onpropertychange = e.oninput; // for IE8

        // Removes a row in the form
        $('#' + remove_id).click(function () {
            var row_id = "row" + id;
            console.log("Remove: " + row_id);
//            $('#' + row_id).html("").fadeIn();
            $("#" + row_id).remove();
            calculate_sum();
        });

        // Fetches info about the post and displays
        $('#' + post_id).blur(function () {
            var cur_post_id = $('#' + post_id).val();
            var price_id = "price" + id;

            $(this).removeClass('newRow');
            if ($("input").hasClass("newRow")) {
                console.log("Found a newRow");
            } else {
                console.log("postid: " + cur_post_id);
                if (cur_post_id != "") {
                    add_row();
                }
            }

            $.ajax({
                url: 'json/' + cur_post_id,
                dataType: 'json',
                success: function (data) {
                    if (data.hasOwnProperty('error')) {
                        console.log("Not found");
                        $("#" + price_id).val("");
                        $('#scientific_name').html("").fadeIn();
                        $('#plain_name').html("").fadeIn();
                        $('#description').html("").fadeIn();
                        $('#seller_name').html("").fadeIn();
                        $('#type').html("").fadeIn();
                        $('#sold').html("").fadeIn();
                        $('#checked_in').html("").fadeIn();
                        $('#error').html("POSTEN FINNS INTE I DATABASEN").fadeIn();
                    } else {
                        console.log("Found");
                        console.log(info_id)
                        $("#" + info_id).html([data.scientific_name, data.plain_name].join(" ")).fadeIn();
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
                        if (data.is_checked_in != "yes") {
                            $('#checked_in').html("Ej incheckad post").fadeIn();
                        } else {
                            $('#checked_in').html("").fadeIn();
                        }
                        if (data.sold_on !== null) {
                            $('#sold').html("Redan sålt").fadeIn();
                            console.log("price_id: " + price_id + " id: " + id + " sold for: " + data.sold_price);
                            $("#" + price_id).val(data.sold_price);
                        } else {
                            $('#sold').html("").fadeIn();
//                         document.getElementById("#" + price_id).value = "";
                        }
                        $('#error').html("").fadeIn();
                        $("#" + price_id).trigger("change");
                    }
                    console.log('.ajax() request returned successfully.');
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    $("#" + price_id).val("");
                    $('#scientific_name').html("").fadeIn();
                    $('#plain_name').html("").fadeIn();
                    $('#description').html("").fadeIn();
                    $('#seller_name').html("").fadeIn();
                    $('#type').html("").fadeIn();
                    $('#sold').html("").fadeIn();
                    $('#checked_in').html("").fadeIn();
                    $('#error').html("INGET POST ID GAVS").fadeIn();
                    console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
                }
            });
        });
    };


    // Handler for add button
    var rowNum = 1;
    $("#addbutton").click(function () {
        console.log("addbutton clicked");
        add_row();
    });

    // Add a new row of input boxes
    function add_row() {
        rowNum++;
        var row_id = "row" + rowNum;
        var post_id = "post" + rowNum;
        var price_id = "price" + rowNum;
        var info_id = "info" + rowNum;
        var remove_id = "remove" + rowNum;
        var html_str = '<div id="' + row_id + '">' +
            '<div class="row" >' +
            '<div class="col-sm-2">' +
            '<input class="loppis form-control newRow" id="' + post_id + '" name="post_id" type="text" value="">' +
            '</div>' +
            '<div class="col-sm-2">' +
            '<input class="loppis price form-control" id="' + price_id + '" name="price" type="text" value="">' +
            '</div>' +
            '<div class="col-sm-6">' +
            '<div class="form-control" id="' + info_id + '"> </div>' +
            '</div>' +
            '<div class="col-sm-2">' +
            '<button type="button" id="' + remove_id + '" class="btn btn-danger btn-block" tabindex="-1">Ta bort <span class="glyphicon glyphicon-remove"></span></button>' +
            '</div>' +
            '</div>' +
            '<br>' +
            '</div>';

        $("#form_elements").append(html_str);
        // Add handler to items in the new row
        func(rowNum);
    }


    // Handler for sumbutton
    $("#sumbutton").click(function () {
        calculate_sum();
    });
    

    // Calculate the sum the customer should pay    
    function calculate_sum() {
        tot_sum = 0;
        $('.price').each(function (i, obj) {
            console.log(this.value);
            tot_sum += Number(this.value);
            console.log(tot_sum);
            $('#sum').html("Att betala: " + tot_sum).fadeIn();
            $('#sum2').html( tot_sum).fadeIn();
        });
    }

    // Calculate the change the custumer should receive
    $("#changebutton").click( function () {
        console.log("changebutton");
        var from_seller = Number($("#from_seller").val());
        console.log(from_seller);
        console.log(tot_sum);
        var change = from_seller - tot_sum;
        console.log(change);
        $("#to_seller").val(change);
    });
    
    // Check that all posts has a price before submitting
    $("#submit").click(function () {
        var all_ok = true;
        console.log("checking prices");
        $(".price").each(function () {
            var price_id = $(this).attr('id'); //get the id of current price input
            var post_id = "#post" + price_id.substring(5); // construct a id tag for matching post_id input
            if ($(post_id).val() != "") { // Only check prices for rows with post nr 
                if ($.isNumeric($(this).val())) {
                    $('#error').html("").fadeIn();
                } else {
                    $('#error').html("Pris måste ges").fadeIn();
                    all_ok = false;
                }
            }
        });
        if (all_ok) {
            return true;
        } else {
            return false;
        }
    });

    // Set handler for first post
    func(1);

    console.log('Everything is ready.');
});


