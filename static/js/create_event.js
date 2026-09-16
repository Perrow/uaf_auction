$(document).ready(function () {
    'use strict';

    $('#create_event_form').submit(function () {
        var checkboxStatus = $('#cookies').is(':checked') && $('#database').is(':checked');
        $('#checkbox_message').text(checkboxStatus
            ? ''
            : 'Du måste godkänna både att cookies används och att personlig data lagras.');

        var status = true;
        $('#create_event_form input').each(function () {
            var type = ($(this).attr('type') || 'text').toLowerCase();
            var name = $(this).attr('name');

            if (!name || type === 'checkbox' || type === 'button' || type === 'submit' || type === 'hidden') {
                return;
            }

            if ($(this).val() === '') {
                status = false;
            }
        });

        $('#message').text(status ? '' : 'Du måste fylla i alla fält.');
        return checkboxStatus && status;
    });

    console.log('Everything is ready.');
});
