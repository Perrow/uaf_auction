'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('register_form');
    const addButton = document.getElementById('addbutton');
    const numberInput = document.getElementById('numberofposts');
    const masterType = document.getElementById('master_type');
    const createPosts = document.getElementById('create_posts');
    const createError = document.getElementById('create_error');
    const formElements = document.getElementById('form_elements');
    const formActions = document.getElementById('form_actions');
    const message = document.getElementById('msg');
    const isAdminRegistration = window.location.pathname.endsWith('/admin_register_many_posts');

    let auctionLimitStatus = null;

    if (!form || !addButton || !numberInput || !masterType) {
        return;
    }

    masterType.classList.remove('form-control');
    masterType.classList.add('form-select');

    if (isAdminRegistration) {
        addButton.disabled = true;
        masterType.disabled = true;
    }

    form.addEventListener('keypress', function (event) {
        if (event.key === 'Enter' && event.target.tagName !== 'TEXTAREA') {
            event.preventDefault();
        }
    });

    const isNumeric = value => value.trim() !== '' && Number.isFinite(Number(value));

    async function getJson(url) {
        const response = await fetch(url, { headers: { Accept: 'application/json' } });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }

    function auctionTypeIdSet() {
        if (!auctionLimitStatus || !Array.isArray(auctionLimitStatus.auction_type_ids)) {
            return new Set();
        }
        return new Set(auctionLimitStatus.auction_type_ids.map(id => String(id)));
    }

    function removeAuctionOptions(select) {
        if (!isAdminRegistration || !auctionLimitStatus || !auctionLimitStatus.is_full) {
            return;
        }

        const auctionTypeIds = auctionTypeIdSet();
        Array.from(select.options).forEach(option => {
            if (auctionTypeIds.has(String(option.value))) {
                option.remove();
            }
        });
    }

    function filterTypesForLimit(types) {
        if (!isAdminRegistration || !auctionLimitStatus || !auctionLimitStatus.is_full) {
            return types;
        }

        const auctionTypeIds = auctionTypeIdSet();
        return types.filter(type => !auctionTypeIds.has(String(type.type_id)));
    }

    async function initializeAuctionLimitFiltering() {
        if (!isAdminRegistration) {
            return;
        }

        try {
            auctionLimitStatus = await getJson('/json_auction_post_limit_status');
            removeAuctionOptions(masterType);

            if (auctionLimitStatus.is_full) {
                createError.textContent = 'Maxantalet auktionsposter är nått. Endast andra godstyper kan registreras.';
            }

            if (masterType.options.length === 0) {
                createError.textContent = 'Maxantalet auktionsposter är nått och det finns inga andra godstyper att registrera.';
                return;
            }
        } catch (error) {
            console.error('Kunde inte läsa maxgränsen för auktionsposter:', error);
        } finally {
            masterType.disabled = false;
            addButton.disabled = masterType.options.length === 0;
        }
    }

    async function getSellTypes() {
        const data = await getJson('/json_get_sell_types');
        if (Object.prototype.hasOwnProperty.call(data, 'error')) {
            throw new Error('Kunde inte läsa godstyper');
        }
        const types = Array.isArray(data) ? data : Object.values(data);
        return filterTypesForLimit(types);
    }

    function createTypeOptions(select, types, selectedId) {
        types.forEach(type => {
            const option = document.createElement('option');
            option.value = type.type_id;
            option.textContent = type.description;
            option.selected = String(type.type_id) === String(selectedId);
            select.appendChild(option);
        });
    }

    function createRow(index, types, selectedId) {
        const article = document.createElement('article');
        article.className = 'card shadow-sm';
        article.id = `post_row${index}`;
        article.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h2 class="h5 mb-0">Post ${index + 1}</h2>
                    ${index > 0 ? `<button id="copybutton${index}" type="button" class="btn btn-sm btn-outline-secondary">Kopiera posten ovanför</button>` : ''}
                </div>
                <div class="row g-3">
                    <div class="col-md-4">
                        <label class="form-label" for="type${index}">Godstyp</label>
                        <select id="type${index}" name="type" class="form-select"></select>
                    </div>
                    <div class="col-md-4" id="sciname_div_id${index}">
                        <label class="form-label" for="sciname${index}">Vetenskapligt namn</label>
                        <input class="form-control sciname" id="sciname${index}" name="sciname" type="text">
                        <div id="sciname_error${index}" class="invalid-feedback d-block"></div>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label" id="popname_label${index}" for="popname${index}">Populärnamn</label>
                        <input class="form-control" id="popname${index}" name="popname" type="text">
                    </div>
                    <div class="col-md-4" id="min_price_div${index}">
                        <label class="form-label" for="min_price${index}">Frivilligt minipris</label>
                        <input class="form-control min_price_input" id="min_price${index}" name="min_price" type="number" min="0" step="1">
                        <div id="min_price_error${index}" class="invalid-feedback d-block"></div>
                    </div>
                    <div class="col-md-4 d-none" id="fixed_price_div${index}">
                        <label class="form-label" for="fixed_price${index}">Fast pris</label>
                        <input class="form-control fixed_price_input" id="fixed_price${index}" name="fixed_price" type="number" min="0" step="1">
                        <div id="fixed_price_error${index}" class="invalid-feedback d-block"></div>
                    </div>
                    <div class="col-12">
                        <label class="form-label" for="description${index}">Beskrivning</label>
                        <input class="form-control" id="description${index}" name="description" type="text" maxlength="100">
                        <div class="form-text">Färg, antal eller annat intressant. Max cirka 100 tecken.</div>
                    </div>
                </div>
            </div>`;

        const typeSelect = article.querySelector(`#type${index}`);
        createTypeOptions(typeSelect, types, selectedId);
        formElements.appendChild(article);

        typeSelect.addEventListener('change', () => updateRowType(index));
        if (index > 0) {
            article.querySelector(`#copybutton${index}`).addEventListener('click', () => copyPreviousRow(index));
        }
    }

    async function updateRowType(index) {
        const typeSelect = document.getElementById(`type${index}`);
        const minPriceDiv = document.getElementById(`min_price_div${index}`);
        const fixedPriceDiv = document.getElementById(`fixed_price_div${index}`);
        const minPrice = document.getElementById(`min_price${index}`);
        const fixedPrice = document.getElementById(`fixed_price${index}`);
        const sciDiv = document.getElementById(`sciname_div_id${index}`);
        const sciInput = document.getElementById(`sciname${index}`);
        const popLabel = document.getElementById(`popname_label${index}`);

        try {
            const data = await getJson(`/json_get_type/${encodeURIComponent(typeSelect.value)}`);
            if (Object.prototype.hasOwnProperty.call(data, 'error')) {
                return;
            }

            const isAuction = data.sale_type === 'auction';
            minPriceDiv.classList.toggle('d-none', !isAuction);
            fixedPriceDiv.classList.toggle('d-none', isAuction);
            if (isAuction) {
                fixedPrice.value = '';
            } else {
                minPrice.value = '';
            }

            const showScientific = data.display_scientific_name_input === 'yes';
            sciDiv.classList.toggle('d-none', !showScientific);
            popLabel.textContent = showScientific ? 'Populärnamn' : 'Vad';
            if (!showScientific) {
                sciInput.value = '';
            }

            sciInput.classList.toggle('check_sciname', data.scientific_name_obligatory === 'yes');
        } catch (error) {
            console.error('Kunde inte hämta godstyp:', error);
        }
    }

    async function copyPreviousRow(index) {
        const previous = index - 1;
        const fields = ['sciname', 'popname', 'min_price', 'fixed_price', 'description'];
        const sourceType = document.getElementById(`type${previous}`);
        const destinationType = document.getElementById(`type${index}`);

        destinationType.value = sourceType.value;
        await updateRowType(index);

        fields.forEach(prefix => {
            const source = document.getElementById(`${prefix}${previous}`);
            const destination = document.getElementById(`${prefix}${index}`);
            if (source && destination) {
                destination.value = source.value;
            }
        });
    }

    function setInvalid(input, errorElement, text) {
        input.classList.toggle('is-invalid', Boolean(text));
        errorElement.textContent = text || '';
    }

    function validateRow(index) {
        let valid = true;
        const sci = document.getElementById(`sciname${index}`);
        const pop = document.getElementById(`popname${index}`);
        const minPrice = document.getElementById(`min_price${index}`);
        const fixedPrice = document.getElementById(`fixed_price${index}`);
        const minDiv = document.getElementById(`min_price_div${index}`);
        const fixedDiv = document.getElementById(`fixed_price_div${index}`);
        const sciError = document.getElementById(`sciname_error${index}`);
        const minError = document.getElementById(`min_price_error${index}`);
        const fixedError = document.getElementById(`fixed_price_error${index}`);
        const rowHasContent = sci.value.trim() !== '' || pop.value.trim() !== '';

        const scientificRequired = rowHasContent && sci.classList.contains('check_sciname');
        const scientificValid = !scientificRequired || sci.value.trim() !== '';
        setInvalid(sci, sciError, scientificValid ? '' : 'Du måste fylla i vetenskapligt namn');
        valid = valid && scientificValid;

        if (!fixedDiv.classList.contains('d-none') && rowHasContent) {
            const fixedValid = isNumeric(fixedPrice.value);
            setInvalid(fixedPrice, fixedError, fixedValid ? '' : 'Du måste fylla i ett pris');
            valid = valid && fixedValid;
        } else {
            setInvalid(fixedPrice, fixedError, '');
        }

        if (!minDiv.classList.contains('d-none') && rowHasContent) {
            const value = minPrice.value.trim();
            const minValid = value === '' || isNumeric(value);
            setInvalid(minPrice, minError, minValid ? '' : 'Du måste fylla i en siffra');
            valid = valid && minValid;
        } else {
            setInvalid(minPrice, minError, '');
        }

        return valid;
    }

    function validateForm() {
        const rows = formElements.querySelectorAll('[id^="post_row"]');
        let valid = true;
        rows.forEach((row, index) => {
            valid = validateRow(index) && valid;
        });

        message.textContent = valid ? '' : 'Kontrollera de markerade fälten.';
        message.className = valid ? 'mb-3' : 'alert alert-danger mb-3';
        return valid;
    }

    addButton.addEventListener('click', async function () {
        const count = Number(numberInput.value);
        if (!Number.isInteger(count) || count < 1) {
            createError.textContent = 'Ange hur många poster som ska skapas.';
            numberInput.classList.add('is-invalid');
            return;
        }

        createError.textContent = '';
        numberInput.classList.remove('is-invalid');
        addButton.disabled = true;

        try {
            const types = await getSellTypes();
            if (types.length === 0) {
                createError.textContent = 'Det finns inga godstyper som kan registreras.';
                addButton.disabled = false;
                return;
            }

            formElements.replaceChildren();
            for (let index = 0; index < count; index += 1) {
                createRow(index, types, masterType.value);
            }
            await Promise.all(Array.from({ length: count }, (_, index) => updateRowType(index)));
            createPosts.classList.add('d-none');
            formActions.classList.remove('d-none');
            formElements.querySelector('input, select')?.focus();
        } catch (error) {
            console.error('Kunde inte skapa poster:', error);
            createError.textContent = 'Kunde inte läsa godstyper. Försök igen.';
            addButton.disabled = false;
        }
    });

    form.addEventListener('submit', function (event) {
        if (!validateForm()) {
            event.preventDefault();
        }
    });

    initializeAuctionLimitFiltering();
});
