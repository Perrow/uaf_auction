document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const formElements = document.getElementById('form_elements');
    const addButton = document.getElementById('addbutton');
    const sumButton = document.getElementById('sumbutton');
    const changeButton = document.getElementById('changebutton');
    const form = document.getElementById('flea_market_form');

    let totalSum = 0;
    let rowNum = 1;

    function setText(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value || '';
        }
    }

    function setValue(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.value = value ?? '';
        }
    }

    function isNumeric(value) {
        return value !== '' && Number.isFinite(Number(value));
    }

    function clearPostDetails() {
        setText('scientific_name', '');
        setText('plain_name', '');
        setText('description', '');
        setText('seller_name', '');
        setText('type', '');
        setText('sold', '');
        setText('checked_in', '');
        setText('closed', '');
    }

    function hasEmptyNewRow() {
        return Array.from(document.querySelectorAll('.post_id')).some(function (input) {
            return input.value.trim() === '';
        });
    }

    function calculateSum() {
        totalSum = Array.from(document.querySelectorAll('.price')).reduce(function (sum, input) {
            return sum + (isNumeric(input.value) ? Number(input.value) : 0);
        }, 0);

        setText('sum', 'Att betala: ' + totalSum);
        setText('sum2', String(totalSum));
    }

    async function loadPost(id) {
        const postInput = document.getElementById('post' + id);
        const priceInput = document.getElementById('price' + id);
        const info = document.getElementById('info' + id);
        const postId = postInput.value.trim();

        if (postId === '') {
            priceInput.value = '';
            info.textContent = '\u00a0';
            clearPostDetails();
            setText('error', 'INGET POST ID GAVS');
            calculateSum();
            return;
        }

        if (!hasEmptyNewRow()) {
            addRow();
        }

        try {
            const response = await fetch('json/' + encodeURIComponent(postId), {
                headers: { 'Accept': 'application/json' }
            });

            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }

            const data = await response.json();

            if (Object.prototype.hasOwnProperty.call(data, 'error')) {
                priceInput.value = '';
                info.textContent = '\u00a0';
                clearPostDetails();
                setText('error', 'POSTEN FINNS INTE I DATABASEN');
                calculateSum();
                return;
            }

            info.textContent = [data.scientific_name, data.plain_name].filter(Boolean).join(' ');
            priceInput.value = data.fixed_price ?? '';
            setText('scientific_name', data.scientific_name);
            setText('plain_name', data.plain_name);
            setText('description', data.description);
            setText('seller_name', data.name);
            setText('type', data.type !== 'fixed_price' ? 'Ej registrerad för fasta bordet' : '');
            setText('checked_in', data.is_checked_in !== 'yes' ? 'Ej incheckad post' : '');
            setText('closed', data.is_closed === 'yes' ? 'Säljaren är stängd' : '');

            if (data.sold_on !== null) {
                setText('sold', 'Redan sålt');
                priceInput.value = data.sold_price ?? '';
            } else {
                setText('sold', '');
            }

            setText('error', '');
            calculateSum();
        } catch (error) {
            priceInput.value = '';
            info.textContent = '\u00a0';
            clearPostDetails();
            setText('error', 'INGET POST ID GAVS');
            calculateSum();
            console.error('Postuppslag misslyckades:', error);
        }
    }

    function bindRow(id) {
        const postInput = document.getElementById('post' + id);
        const priceInput = document.getElementById('price' + id);
        const removeButton = document.getElementById('remove' + id);

        priceInput.addEventListener('blur', function () {
            setText('error', priceInput.value === '' || isNumeric(priceInput.value) ? '' : 'Pris måste ges');
            calculateSum();
        });
        priceInput.addEventListener('input', calculateSum);
        priceInput.addEventListener('change', calculateSum);

        removeButton.addEventListener('click', function () {
            const row = document.getElementById('row' + id);
            if (row) {
                row.remove();
                calculateSum();
            }
        });

        postInput.addEventListener('blur', function () {
            loadPost(id);
        });
    }

    function addRow() {
        rowNum += 1;
        const id = rowNum;
        const wrapper = document.createElement('div');
        wrapper.id = 'row' + id;
        wrapper.className = 'sale-row mb-3';
        wrapper.innerHTML = `
            <div class="row g-2 align-items-end">
                <div class="col-md-2">
                    <label class="form-label d-md-none" for="post${id}">Post nr</label>
                    <input class="loppis post_id form-control" id="post${id}" name="post_id" type="text" autocomplete="off">
                </div>
                <div class="col-md-2">
                    <label class="form-label d-md-none" for="price${id}">Pris</label>
                    <input class="loppis price form-control" id="price${id}" name="price" type="text" inputmode="decimal" autocomplete="off">
                </div>
                <div class="col-md-6">
                    <label class="form-label d-md-none" for="info${id}">Namn</label>
                    <div class="form-control bg-body-tertiary" id="info${id}" aria-live="polite">&nbsp;</div>
                </div>
                <div class="col-md-2 d-grid">
                    <button type="button" id="remove${id}" class="btn btn-outline-danger" tabindex="-1">
                        <i class="fa fa-trash" aria-hidden="true"></i> Ta bort
                    </button>
                </div>
            </div>`;

        formElements.appendChild(wrapper);
        bindRow(id);
    }

    addButton.addEventListener('click', addRow);
    sumButton.addEventListener('click', calculateSum);

    changeButton.addEventListener('click', function () {
        const received = Number(document.getElementById('from_seller').value);
        setValue('to_seller', received - totalSum);
    });

    form.addEventListener('submit', function (event) {
        let allOk = true;

        document.querySelectorAll('.price').forEach(function (priceInput) {
            const rowId = priceInput.id.substring(5);
            const postInput = document.getElementById('post' + rowId);

            if (postInput && postInput.value.trim() !== '' && !isNumeric(priceInput.value)) {
                allOk = false;
            }
        });

        if (!allOk) {
            setText('error', 'Pris måste ges');
            event.preventDefault();
        } else {
            setText('error', '');
        }
    });

    bindRow(1);
    calculateSum();
});
