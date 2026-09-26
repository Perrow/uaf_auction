document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    const postIdInput = document.getElementById('post_id');
    const priceInput = document.getElementById('price');
    const submitButton = document.getElementById('submit');
    const auctionForm = document.getElementById('auction_form');
    const displayCurrentPost = document.getElementById('display-current-post');
    let lastSubmittedPost = sessionStorage.getItem('auctionLastSubmittedPost') || '';

    function setHtml(id, value) {
        document.getElementById(id).innerHTML = value == null ? '' : value;
    }

    function clearPostDetails() {
        ['scientific_name', 'min_price', 'plain_name', 'description', 'seller_name',
            'type', 'sold', 'checked_in', 'closed'].forEach(function (id) {
            setHtml(id, '');
        });
    }

    async function loadPostDetails() {
        const postId = postIdInput.value.trim();

        if (postId === '') {
            clearPostDetails();
            setHtml('error', '');
            priceInput.value = '';
            return;
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
                clearPostDetails();
                setHtml('error', 'POSTEN FINNS INTE I DATABASEN');
                return;
            }

            setHtml('scientific_name', data.scientific_name);
            setHtml('min_price', data.minimum_price);
            setHtml('plain_name', data.plain_name);
            setHtml('description', data.description);
            setHtml('seller_name', data.name);
            setHtml('type', data.type !== 'auction' ? 'Ej registrerad som auktionsgods' : '');
            setHtml('checked_in', data.is_checked_in !== 'yes' ? 'Ej incheckad post' : '');
            setHtml('closed', data.is_closed === 'yes' ? 'Säljaren är stängd' : '');

            if (data.sold_on !== null) {
                setHtml('sold', 'Redan sålt');
                priceInput.value = data.sold_price;
            } else {
                setHtml('sold', '');
                priceInput.value = '';
            }

            setHtml('error', '');
        } catch (error) {
            clearPostDetails();
            setHtml('error', 'INGET POST ID GAVS');
            console.error('Postuppslag misslyckades:', error);
        }
    }

    async function refreshDisplayState() {
        try {
            const response = await fetch('json_display_state', {
                credentials: 'same-origin',
                cache: 'no-store',
                headers: { 'Accept': 'application/json' }
            });
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }

            const data = await response.json();
            const currentPost = data.post_id == null ? '' : String(data.post_id);
            displayCurrentPost.textContent = currentPost || 'Ingen post';

            if (!currentPost) {
                return;
            }

            if (lastSubmittedPost && currentPost === lastSubmittedPost) {
                return;
            }

            if (lastSubmittedPost && currentPost !== lastSubmittedPost) {
                lastSubmittedPost = '';
                sessionStorage.removeItem('auctionLastSubmittedPost');
            }

            if (postIdInput.value.trim() === '') {
                postIdInput.value = currentPost;
                await loadPostDetails();
                priceInput.focus();
            }
        } catch (error) {
            console.error('Kunde inte hämta aktuell displaypost:', error);
            displayCurrentPost.textContent = 'Kunde inte hämtas';
        }
    }

    postIdInput.addEventListener('blur', loadPostDetails);

    submitButton.addEventListener('click', function (event) {
        if (postIdInput.value === '') {
            return;
        }

        const price = priceInput.value.trim();
        const isNumeric = price !== '' && Number.isFinite(Number(price));

        if (isNumeric) {
            setHtml('error', '');
            return;
        }

        setHtml('error', 'Pris måste ges');
        event.preventDefault();
    });

    auctionForm.addEventListener('submit', function () {
        const postId = postIdInput.value.trim();
        if (postId) {
            sessionStorage.setItem('auctionLastSubmittedPost', postId);
        }
    });

    refreshDisplayState();
    window.setInterval(refreshDisplayState, 3000);
});
