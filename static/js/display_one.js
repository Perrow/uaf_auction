$(document).ready(function () {
    'use strict';
    var current_data = "";
    var next_data = "";
    var empty_data = { description: "", fixed_price: "", minimum_price: "", name: "", obj_id: "", plain_name: "", scientific_name: "", sold_on: "", sold_price: "", type: "" };

    // leave the input box, with tab for example
    $('#post_id').blur(function () {
        fetch_data();
        get_sold_stat();
    });

    // Press enter
    // $(document).keypress(function (e) {
    //     if (e.which == 13) {
    //         console.log('You pressed enter!');
    //         fetch_data();
    //     }
    // });

    var display_current = function () {
        console.log("Display current");
        var cur_id = "";
        if (current_data.obj_id == null || current_data.obj_id == ""){
            cur_id = "";
            console.log("id = null");
        } else {
            cur_id = "Post : " + current_data.obj_id;
        }
        
        $('#current_post_id').html(cur_id).fadeIn();
        $('#current_scientific_name').html(current_data.scientific_name).fadeIn();
        if (current_data.minimum_price == null || current_data.minimum_price == "") {
            $('#current_min_price').html("").fadeIn();
        } else {
            $('#current_min_price').html("Reservationspris: " + current_data.minimum_price + "kr").fadeIn();
        }
        $('#current_plain_name').html(current_data.plain_name).fadeIn();
        $('#current_description').html(current_data.description).fadeIn();
        if (current_data.name == null || current_data.name == "") {
            $('#current_seller_name').html("").fadeIn();
        } else {
            $('#current_seller_name').html("Säljare: " + current_data.name).fadeIn();
        }

    };


    var clear_current = function () {
        console.log("Clearing");
        $('#current_post_id').html("").fadeIn();
        $('#current_scientific_name').html("").fadeIn();
        $('#current_min_price').html("").fadeIn();
        $('#current_plain_name').html("").fadeIn();
        $('#current_description').html("").fadeIn();
        $('#current_seller_name').html("").fadeIn();
        $('#current_type').html("").fadeIn();
        $('#current_sold').html("").fadeIn();
        $('#current_error').html("POSTEN FINNS INTE I DATABASEN").fadeIn();
    };


    var set_focus = function () {
        var input = $("#post_id");
        input.focus();
    };

    // Fetches post data via ajax from server
    var fetch_data = function () {
        console.log("fetch data");
        var post_id = $('#post_id').val();
        $('#post_id').val("");
        $("#post_id").focus();
        console.log(post_id);
        if (post_id == "") {
            console.log("empty data, advance one row");
            current_data = empty_data;
            display_current();
        } else {
            $.ajax({
                url: 'json/' + post_id,
                dataType: 'json',
                success: function (data) {
                    if (data.hasOwnProperty('error')) {
                        console.log("Not found");
                        // clear_current();
                    } else {
                        console.log("Found");
                        current_data = data;
                        console.log(data);
                        display_current();

                        // Warning for posts not registrated for auction
                        if (data.type != "auction") {
                            $('#current_type').html("Ej registrerad som auktionsgods").fadeIn();
                        } else {
                            $('#current_type').html("").fadeIn();
                        }
                        if (data.sold_on !== null) {
                            $('#current_sold').html("Redan sålt").fadeIn();
                            document.getElementById("price").value = data.sold_price;
                        } else {
                            $('#current_sold').html("").fadeIn();
                            document.getElementById("price").value = "";
                        }
                        $('#error').html("").fadeIn();
                    }


                    console.log('.ajax() request returned successfully.');
                },
                error: function (jqXHR, textStatus, errorThrown) {
                    // clear_current();
                    $('#error').html("INGET POST ID GAVS").fadeIn();
                    console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
                }
            });
        }
    };


    // Check that all posts has a price before submitting
    $("#submit").click(function () {
        var all_ok = false;
        console.log("submit clicked");
        fetch_data();
        get_sold_stat();

        return false;
    });

    // Get sold statistic via json and updates progressbars
    var get_sold_stat = function () {
        // result = {"total": total, "total_auction": total_auction, "sold_auction": sold_auction, "sold_auction_percent": sold_auction_percent, "total_fleamarket": total_fleamarket, "sold_fleamarket": sold_fleamarket, "sold_fleamarket_percent": sold_fleamarket_percent}
        $.ajax({
            url: 'json_sold',
            dataType: 'json',
            success: function (data) {
                if (data.hasOwnProperty('error')) {
                    console.log("Not found");
                } else {
                    console.log("Found");
                    $('#sold_auction').css('width', data.sold_auction_percent + '%');
                    $('#sold_fleamarket').css('width', data.sold_fleamarket_percent + '%');
                    $('#sold_auction_text').html(data.sold_auction + ' av ' + data.total_auction);
                    $('#sold_fleamarket_text').html(data.sold_fleamarket + ' av ' + data.total_fleamarket);
                }
                console.log('.ajax() request returned successfully.');
            },
            error: function (jqXHR, textStatus, errorThrown) {
                console.log('.ajax() request failed: ' + textStatus + ', ' + errorThrown);
            }
        });
    };


    $('#submit').hide();
    get_sold_stat();
    console.log('Everything is ready.');
});


