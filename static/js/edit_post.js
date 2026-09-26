'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('edit_post_form');
    const typeSelect = document.getElementById('master_type');
    const minPriceDiv = document.getElementById('min_price_div_id');
    const fixedPriceDiv = document.getElementById('fixed_price_div_id');
    const minPriceInput = document.getElementById('min_price_id');
    const fixedPriceInput = document.getElementById('fixed_price_id');
    const minPriceError = document.getElementById('min_price_error_id');
    const fixedPriceError = document.getElementById('fixed_price_error_id');
    const message = document.getElementById('msg');

    if (!form || !typeSelect) {
        return;
    }

    typeSelect.classList.remove('form-control');
    typeSelect.classList.add('form-select');

    form.addEventListener('keypress', function (event) {
        if (event.key === 'Enter' && event.target.tagName !== 'TEXTAREA') {
            event.preventDefault();
        }
    });

    async function updatePriceFields() {
        const typeId = typeSelect.value;
        try {
            const response = await fetch(`/json_get_type/${encodeURIComponent(typeId)}`, {
                headers: { Accept: 'application/json' }
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (Object.prototype.hasOwnProperty.call(data, 'error')) {
                return;
            }

            const auction = data.sale_type === 'auction';
            minPriceDiv.classList.toggle('d-none', !auction);
            fixedPriceDiv.classList.toggle('d-none', auction);

            if (auction) {
                fixedPriceInput.value = '';
            } else {
                minPriceInput.value = '';
            }
        } catch (error) {
            console.error('Kunde inte hämta godstyp:', error);
        }
    }

    function isNumeric(value) {
        return value.trim() !== '' && Number.isFinite(Number(value));
    }

    function setFieldState(input, errorElement, errorText) {
        input.classList.toggle('is-invalid', Boolean(errorText));
        errorElement.textContent = errorText || '';
    }

    function validate() {
        let valid = true;

        if (!fixedPriceDiv.classList.contains('d-none')) {
            const fixedValid = isNumeric(fixedPriceInput.value);
            setFieldState(fixedPriceInput, fixedPriceError, fixedValid ? '' : 'Du måste fylla i ett pris');
            valid = valid && fixedValid;
        } else {
            setFieldState(fixedPriceInput, fixedPriceError, '');
        }

        if (!minPriceDiv.classList.contains('d-none')) {
            const value = minPriceInput.value.trim();
            const minValid = value === '' || isNumeric(value);
            setFieldState(minPriceInput, minPriceError, minValid ? '' : 'Du måste fylla i en siffra');
            valid = valid && minValid;
        } else {
            setFieldState(minPriceInput, minPriceError, '');
        }

        message.textContent = valid ? '' : 'Kontrollera de markerade fälten.';
        message.className = valid ? 'mb-3' : 'alert alert-danger mb-3';
        return valid;
    }

    typeSelect.addEventListener('change', updatePriceFields);
    form.addEventListener('submit', function (event) {
        if (!validate()) {
            event.preventDefault();
        }
    });

    updatePriceFields();
});
