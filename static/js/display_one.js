'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const postInput = document.getElementById('post_id');
    const form = document.getElementById('display_form');

    const latestSaleElement = document.getElementById('latest-sale');
    let latestSalePollTimer = null;
    let renderedSaleKey = null;

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

    async function setDisplayState(postId) {
        try {
            await fetch('json_display_state', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ post_id: postId })
            });
        } catch (error) {
            console.error('Kunde inte uppdatera aktuell displaypost:', error);
        }
    }

    function saleKey(sale) {
        if (!sale) {
            return null;
        }
        return [sale.obj_id, sale.sold_price, sale.time_stamp_sold].join('|');
    }

    function renderLatestSale(sale) {
        if (!sale) {
            latestSaleElement.textContent = 'Ingen försäljning ännu';
            renderedSaleKey = null;
            return;
        }

        latestSaleElement.textContent = `${sale.obj_id} · ${sale.name || ''} · ${sale.sold_price} kr`;
        renderedSaleKey = saleKey(sale);
    }

    async function fetchLatestSale() {
        const response = await fetch('json_latest_auction_sale', {
            credentials: 'same-origin',
            cache: 'no-store',
            headers: { Accept: 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        return data.sale;
    }

    function stopLatestSalePolling() {
        if (latestSalePollTimer !== null) {
            window.clearInterval(latestSalePollTimer);
            latestSalePollTimer = null;
        }
    }

    async function pollLatestSaleOnce() {
        try {
            const sale = await fetchLatestSale();
            if (saleKey(sale) !== renderedSaleKey) {
                renderLatestSale(sale);
                stopLatestSalePolling();
                await getSoldStat();
            }
        } catch (error) {
            console.error('Kunde inte hämta senaste försäljning:', error);
        }
    }

    function startLatestSalePolling() {
        stopLatestSalePolling();
        pollLatestSaleOnce();
        latestSalePollTimer = window.setInterval(pollLatestSaleOnce, 1000);
    }

    function displayCurrent(data) {
        const postId = data.obj_id ? `Post: ${data.obj_id}` : '';
        const minPrice = data.minimum_price !== null && data.minimum_price !== ''
            ? `Minpris: ${data.minimum_price} kr`
            : '';

        setText('current_post_id', postId);
        setText('current_min_price', minPrice);
        setText('current_plain_name', data.plain_name);
        setText('current_scientific_name', data.scientific_name);
        setText('current_description', data.description);
        setText('current_seller_name', data.name ? `Säljare: ${data.name}` : '');
        setAlert('current_type', data.type && data.type !== 'auction' ? 'Ej registrerad som auktionsgods' : '');
        setAlert('current_sold', data.sold_on !== null && data.sold_on !== undefined ? 'Redan sålt' : '');
    }

    async function fetchData() {
        const postId = postInput.value.trim();
        postInput.value = '';
        postInput.focus();
        setAlert('error', '');

        if (!postId) {
            displayCurrent(emptyData);
            await setDisplayState(null);
            return;
        }

        try {
            const response = await fetch(`json/${encodeURIComponent(postId)}`, { headers: { Accept: 'application/json' } });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (Object.prototype.hasOwnProperty.call(data, 'error')) {
                displayCurrent({ ...emptyData, obj_id: postId, plain_name: 'Posten finns inte' });
                await setDisplayState(null);
                return;
            }
            displayCurrent(data);
            await setDisplayState(data.obj_id);
            startLatestSalePolling();
        } catch (error) {
            console.error('Kunde inte hämta post:', error);
            setAlert('error', 'Kunde inte hämta posten');
            await setDisplayState(null);
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

            const auctionBar = document.getElementById('sold_auction');
            const fleaBar = document.getElementById('sold_fleamarket');
            auctionBar.style.width = `${data.sold_auction_percent}%`;
            fleaBar.style.width = `${data.sold_fleamarket_percent}%`;
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

    getSoldStat();
    fetchLatestSale()
        .then(renderLatestSale)
        .catch(function (error) {
            console.error('Kunde inte hämta senaste försäljning:', error);
        });
});
