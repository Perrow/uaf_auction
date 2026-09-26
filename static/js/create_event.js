document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const form = document.getElementById('create_event_form');
    if (!form) {
        return;
    }

    form.addEventListener('submit', function (event) {
        const cookies = document.getElementById('cookies');
        const database = document.getElementById('database');
        const checkboxMessage = document.getElementById('checkbox_message');
        const message = document.getElementById('message');

        const checkboxStatus = cookies.checked && database.checked;
        checkboxMessage.textContent = checkboxStatus
            ? ''
            : 'Du måste godkänna både att cookies används och att personlig data lagras.';

        const requiredInputs = form.querySelectorAll('input[name]');
        let status = true;

        requiredInputs.forEach(function (input) {
            const type = (input.type || 'text').toLowerCase();

            if (type === 'checkbox' || type === 'button' || type === 'submit' || type === 'hidden') {
                return;
            }

            if (input.value.trim() === '') {
                status = false;
            }
        });

        message.textContent = status ? '' : 'Du måste fylla i alla fält.';

        if (!checkboxStatus || !status) {
            event.preventDefault();
        }
    });
});
