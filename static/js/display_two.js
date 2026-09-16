'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const postInput = document.getElementById('post_id');
    const form = document.getElementById('display_form');

    let currentData = null;
    let nextData = null;

    const emptyData = {
        description: '', minimum_price: '', name: '', obj_id: '', plain_name: '', scientific_name: ''
    };

    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value ?? '';
        }
    };

    const setAlert = (id, message) => {
        const element = document.getElementById(id);
        if (!element) {
            return;
        }
        element.textContent = message || '';
        element.classList.toggle('d-none', !message);
    };

    function displayCurrent(data) {
        const value = data || emptyData;
        const postId = value.obj_id ? `Post: ${value.obj_id}` : '';
        const minPrice = value.minimum_price !== null && value.minimum_price !== ''
            ? `Minpris: ${value.minimum_price} kr`
            : '';

        setText('current_post_id', postId);
        setText('current_min_price', minPrice);
        setText('current_plain_name', value.plain_name);
        setText('current_scientific_name', value.scientific_name);
        setText('current_description', value.description);
        setText('current_seller_name', value.name ? `Säljare: ${value.name}` : '');
        setAlert('current_type', value.type && value.type !== 'auction' ? 'Ej registrerad som auktionsgods' : '');
        setAlert('current_sold', value.sold_on !== null && value.sold_on !== undefined ? 'Redan sålt' : '');
    }

    function displayNext(data) {
        setText('next_post_id', data?.obj_id || '');
    }

    async function fetchData() {
        const postId = postInput.value.trim();
        postInput.value = '';
        postInput.focus();
        setAlert('error', '');

        if (!postId) {
            currentData = nextData;
            nextData = null;
            displayCurrent(currentData);
            displayNext(nextData);
            return;
        }

        try {
            const response = await fetch(`json/${encodeURIComponent(postId)}`, { headers: { Accept: 'application/json' } });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();

            currentData = nextData;
            if (Object.prototype.hasOwnProperty.call(data, 'error')) {
                nextData = { ...emptyData, obj_id: postId, plain_name: 'Posten finns inte' };
            } else {
                nextData = data;
            }

            displayCurrent(currentData);
            displayNext(nextData);
        } catch (error) {
            console.error('Kunde inte hämta post:', error);
            setAlert('error', 'Kunde inte hämta posten');
        }
    }

    async function getSoldStat() {
        try {
            const response = await fetch('json_sold', { headers: { Accept: 'application/json' } });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (Object.prototype.hasOwnProperty.call(data, 'error')) {
                return;
            }

            document.getElementById('sold_auction').style.width = `${data.sold_auction_percent}%`;
            document.getElementById('sold_fleamarket').style.width = `${data.sold_fleamarket_percent}%`;
            setText('sold_auction_text', `${data.sold_auction} av ${data.total_auction}`);
            setText('sold_fleamarket_text', `${data.sold_fleamarket} av ${data.total_fleamarket}`);
        } catch (error) {
            console.error('Kunde inte hämta försäljningsstatistik:', error);
        }
    }

    postInput.addEventListener('blur', async function () {
        await fetchData();
        await getSoldStat();
    });

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        await fetchData();
        await getSoldStat();
    });

    displayCurrent(null);
    displayNext(null);
    getSoldStat();
});
