document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const formElements = document.getElementById('form_elements');
    const addButton = document.getElementById('addbutton');
    const sumButton = document.getElementById('sumbutton');
    const changeButton = document.getElementById('changebutton');
    const swishButton = document.getElementById('swishbutton');
    const swishQrContainer = document.getElementById('swish_qr_container');
    const swishQrImage = document.getElementById('swish_qr_image');
    const swishQrDetails = document.getElementById('swish_qr_details');
    const form = document.getElementById('flea_market_form');

    const loadingPostInputs = new WeakSet();

    let totalSum = 0;
    let rowNum = 1;
    let swishQrObjectUrl = null;

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

    function normalizePostId(value) {
        const trimmed = value.trim();
        if (/^\d+$/.test(trimmed)) {
            return String(Number(trimmed));
        }
        return trimmed;
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

    function clearSwishQr() {
        if (swishQrObjectUrl) {
            URL.revokeObjectURL(swishQrObjectUrl);
            swishQrObjectUrl = null;
        }
        if (swishQrImage) {
            swishQrImage.removeAttribute('src');
        }
        if (swishQrDetails) {
            swishQrDetails.textContent = '';
        }
        if (swishQrContainer) {
            swishQrContainer.classList.add('d-none');
        }
    }

    function hasEmptyNewRow() {
        return Array.from(document.querySelectorAll('.post_id')).some(function (input) {
            return input.value.trim() === '';
        });
    }

    function findDuplicatePostInput(currentInput) {
        const normalizedPostId = normalizePostId(currentInput.value);
        if (normalizedPostId === '') {
            return null;
        }

        return Array.from(document.querySelectorAll('.post_id')).find(function (input) {
            return input !== currentInput
                && input.value.trim() !== ''
                && normalizePostId(input.value) === normalizedPostId;
        }) || null;
    }

    function findFirstDuplicatePostInput() {
        const seenPostIds = new Set();

        for (const input of document.querySelectorAll('.post_id')) {
            const normalizedPostId = normalizePostId(input.value);
            if (normalizedPostId === '') {
                continue;
            }
            if (seenPostIds.has(normalizedPostId)) {
                return input;
            }
            seenPostIds.add(normalizedPostId);
        }

        return null;
    }

    function calculateSum() {
        totalSum = Array.from(document.querySelectorAll('.price')).reduce(function (sum, input) {
            return sum + (isNumeric(input.value) ? Number(input.value) : 0);
        }, 0);

        setText('sum', 'Att betala: ' + totalSum);
        setText('sum2', String(totalSum));
        clearSwishQr();
    }

    function collectSwishItems() {
        const items = [];

        for (const postInput of document.querySelectorAll('.post_id')) {
            const postId = postInput.value.trim();
            if (postId === '') {
                continue;
            }

            const rowId = postInput.id.substring(4);
            const priceInput = document.getElementById('price' + rowId);
            if (!priceInput || !isNumeric(priceInput.value)) {
                return null;
            }

            items.push({
                post_id: normalizePostId(postId),
                price: priceInput.value.trim()
            });
        }

        return items;
    }

    async function createSwishQr(triggerButton) {
        calculateSum();

        const duplicateInput = findFirstDuplicatePostInput();
        if (duplicateInput) {
            setText('error', 'SAMMA POSTNUMMER KAN INTE FINNAS MER ÄN EN GÅNG I LISTAN');
            duplicateInput.focus();
            return;
        }

        const items = collectSwishItems();
        if (!items || items.length === 0) {
            setText('error', 'LÄGG TILL MINST EN POST MED ETT GILTIGT PRIS FÖRST');
            return;
        }

        const itemTotal = items.reduce(function (sum, item) {
            return sum + Number(item.price);
        }, 0);
        if (itemTotal !== totalSum || totalSum <= 0) {
            setText('error', 'KONTROLLERA ATT ALLA PRISER HÖR TILL EN POST OCH ÄR STÖRRE ÄN NOLL');
            return;
        }

        const activeButton = triggerButton || sumButton;
        const originalButtonText = activeButton ? activeButton.textContent : '';
        if (activeButton) {
            activeButton.disabled = true;
            activeButton.textContent = 'Skapar Swish-QR...';
        }

        try {
            const response = await fetch('/swish_qr', {
                method: 'POST',
                headers: {
                    'Accept': 'image/png',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ items: items })
            });

            if (!response.ok) {
                let message = 'KUNDE INTE SKAPA SWISH-QR';
                try {
                    const errorData = await response.json();
                    if (errorData.error) {
                        message = errorData.error;
                    }
                } catch (error) {
                    // Keep the generic message if the response was not JSON.
                }
                throw new Error(message);
            }

            const qrBlob = await response.blob();
            swishQrObjectUrl = URL.createObjectURL(qrBlob);
            if (swishQrImage) {
                swishQrImage.src = swishQrObjectUrl;
            }

            const amount = response.headers.get('X-Swish-Amount') || String(totalSum);
            const message = response.headers.get('X-Swish-Message') || '';
            if (swishQrDetails) {
                swishQrDetails.textContent = amount + ' kr' + (message ? ' · ' + message : '');
            }
            if (swishQrContainer) {
                swishQrContainer.classList.remove('d-none');
            }
            setText('error', '');
        } catch (error) {
            clearSwishQr();
            setText('error', error.message || 'KUNDE INTE SKAPA SWISH-QR');
            console.error('Swish QR kunde inte skapas:', error);
        } finally {
            if (activeButton) {
                activeButton.disabled = false;
                activeButton.textContent = originalButtonText;
            }
        }
    }

    function focusNextEmptyPostInput(currentInput) {
        const postInputs = Array.from(document.querySelectorAll('.post_id'));
        const currentIndex = postInputs.indexOf(currentInput);
        const nextEmptyInput = postInputs.slice(currentIndex + 1).find(function (input) {
            return input.value.trim() === '';
        });

        if (nextEmptyInput) {
            nextEmptyInput.focus();
            return;
        }

        const newPostInput = addRow();
        newPostInput.focus();
    }

    async function loadPost(id, focusNextAfterLoad) {
        const postInput = document.getElementById('post' + id);
        const priceInput = document.getElementById('price' + id);
        const info = document.getElementById('info' + id);

        if (loadingPostInputs.has(postInput)) {
            return;
        }

        const postId = postInput.value.trim();

        if (postId === '') {
            priceInput.value = '';
            info.textContent = '\u00a0';
            clearPostDetails();
            setText('error', 'INGET POST ID GAVS');
            calculateSum();
            return;
        }

        const duplicateInput = findDuplicatePostInput(postInput);
        if (duplicateInput) {
            priceInput.value = '';
            info.textContent = '\u00a0';
            postInput.value = '';
            clearPostDetails();
            setText('error', 'POSTNUMMER ' + postId + ' FINNS REDAN I LISTAN');
            calculateSum();
            postInput.focus();
            return;
        }

        if (!hasEmptyNewRow()) {
            addRow();
        }

        loadingPostInputs.add(postInput);

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

            if (focusNextAfterLoad) {
                focusNextEmptyPostInput(postInput);
            }
        } catch (error) {
            priceInput.value = '';
            info.textContent = '\u00a0';
            clearPostDetails();
            setText('error', 'INGET POST ID GAVS');
            calculateSum();
            console.error('Postuppslag misslyckades:', error);
        } finally {
            loadingPostInputs.delete(postInput);
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

        postInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                event.stopPropagation();
                loadPost(id, true);
            }
        });

        postInput.addEventListener('blur', function () {
            loadPost(id, false);
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
        return document.getElementById('post' + id);
    }

    addButton.addEventListener('click', addRow);
    sumButton.addEventListener('click', function () {
        createSwishQr(sumButton);
    });

    changeButton.addEventListener('click', function () {
        const received = Number(document.getElementById('from_seller').value);
        setValue('to_seller', received - totalSum);
    });

    if (swishButton) {
        swishButton.addEventListener('click', function () {
            createSwishQr(swishButton);
        });
    }

    form.addEventListener('submit', function (event) {
        let allOk = true;
        const duplicateInput = findFirstDuplicatePostInput();

        if (duplicateInput) {
            setText('error', 'SAMMA POSTNUMMER KAN INTE FINNAS MER ÄN EN GÅNG I LISTAN');
            event.preventDefault();
            duplicateInput.focus();
            return;
        }

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
