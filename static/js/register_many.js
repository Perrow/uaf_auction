

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



    var add_toggler_func = function(rownr) {
        // Toggles the fixed price and minimum price boxes according to the select status
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

    var copy_func = function(rownr) {
        //  Copies all values from the post above to current post
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


    // Add a a number of new post forms
    var rowNum = 0;
    $("#addbutton").click(function(){
        console.log("addbutton clicked");
        rowNum = Number($("#numberofposts").val());
        for (var i=0; i < rowNum; i++) {
            var type_id = "type" + i;
            var sciname_id = "sciname" + i;
            var popname_id = "popname" + i;

            var min_price_id = "min_price" + i;
            var fixed_price_id = "fixed_price" + i;
            var min_price_div_id = "min_price_div" + i;
            var fixed_price_div_id = "fixed_price_div" + i;
            var description_id = "description" + i;
            var copybutton_id = "copybutton" + i;

            var new_post_html = '<br>' +
                '<div class="blackborder">' +
                '<label for="' + type_id + '">Godstyp</label>' +
                '<select id="' + type_id + '" name="type">' +
                '<option value="1">Fisk till auktionen</option>' +
                '<option value="2">Fisk till fasta bordet</option>' +
                '<option value="3">Övriga djur till fasta bordet</option>' +
                '<option value="4">Övrigt levande till auktionen</option>' +
                '<option value="5">Övrigt till fasta bordet</option>' +
                '<option value="6">Räkor till auktionen</option>' +
                '<option value="7">Tillbehör till auktionen</option>' +
                '<option value="8">Tillbehör till fasta bordet</option>' +
                '<option value="9">Växter</option>' +
                '<option value="10">Växter till fasta bordet</option>' +
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
                '<label for="' + min_price_id + '">Utropspris:</label><br>' +
            '   <input class="ninety" id="' + min_price_id + '" name="min_price" type="text" value=""> <br>' +
            '</div>' +
            '<div  id="' + fixed_price_div_id + '" class="left ten ">' +
                '<label for="' + fixed_price_id + '">Fast pris:</label><br>' +
               '<input class="ninety" id="' + fixed_price_id + '" name="fixed_price" type="text" value=""> <br>' +
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
        }
    });


    console.log('Everything is ready.');
});


