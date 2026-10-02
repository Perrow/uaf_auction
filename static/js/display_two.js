'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const postInput = document.getElementById('post_id');
    const form = document.getElementById('display_form');
    const latestSaleElement = document.getElementById('latest-sale');
    const nextPostStorageKey = 'uaf.displayTwo.nextPost';
    const nextPostChannel = 'BroadcastChannel' in window
        ? new BroadcastChannel('uaf.displayTwo')
        : null;

    let currentData = null;
    let nextData = null;
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
        const value = data || emptyData;
        setText('next_post_id', value.obj_id ? `#${value.obj_id}` : '');
        setText('next_scientific_name', value.scientific_name);
        setText('next_plain_name', value.plain_name);

        if (data) {
            const serialized = JSON.stringify(data);
            window.localStorage.setItem(nextPostStorageKey, serialized);
            if (nextPostChannel) {
                nextPostChannel.postMessage({ type: 'next-post', data: data });
            }
        } else {
            window.localStorage.removeItem(nextPostStorageKey);
            if (nextPostChannel) {
                nextPostChannel.postMessage({ type: 'next-post', data: null });
            }
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

        const numericPrice = Number(sale.sold_price);
        const price = Number.isFinite(numericPrice)
            ? numericPrice.toLocaleString('sv-SE', { maximumFractionDigits: 2 })
            : sale.sold_price;
        latestSaleElement.textContent = `${sale.obj_id} · ${sale.name || ''} · ${price} kr`;
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
        latestSalePollTimer = window.setInterval(pollLatestSaleOnce, 3000);
        pollLatestSaleOnce();
    }

    async function loadPost(postId) {
        const response = await fetch(`json/${encodeURIComponent(postId)}`, {
            headers: { Accept: 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (Object.prototype.hasOwnProperty.call(data, 'error')) {
            return null;
        }
        return data;
    }

    async function promoteNextPost() {
        if (!nextData) {
            return;
        }

        currentData = nextData;
        nextData = null;
        displayCurrent(currentData);
        displayNext(null);
        await setDisplayState(currentData.obj_id);
        startLatestSalePolling();
    }

    async function applyPost(data) {
        if (nextData) {
            await promoteNextPost();
        }

        nextData = data;
        displayNext(nextData);
    }

    async function fetchData() {
        const postId = postInput.value.trim();
        if (!postId) {
            return;
        }

        postInput.value = '';
        postInput.focus();
        setAlert('error', '');

        try {
            if (nextData && String(nextData.obj_id) === postId) {
                await promoteNextPost();
                return;
            }

            const data = await loadPost(postId);
            if (!data) {
                setAlert('error', `Post ${postId} finns inte`);
                return;
            }

            await applyPost(data);
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
    fetchLatestSale()
        .then(renderLatestSale)
        .catch(function (error) {
            console.error('Kunde inte hämta senaste försäljning:', error);
        });
});
