'use strict';

document.addEventListener('DOMContentLoaded', function () {
    const storageKey = 'uaf.displayTwo.nextPost';
    const channel = 'BroadcastChannel' in window
        ? new BroadcastChannel('uaf.displayTwo')
        : null;

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

    function render(data) {
        const empty = document.getElementById('next_empty');

        if (!data) {
            setText('next_post_id', '');
            setText('next_min_price', '');
            setText('next_plain_name', '');
            setText('next_scientific_name', '');
            setText('next_description', '');
            setText('next_seller_name', '');
            setAlert('next_type', '');
            setAlert('next_sold', '');
            empty.classList.remove('d-none');
            return;
        }

        empty.classList.add('d-none');

        setText('next_post_id', data.obj_id ? `Post: ${data.obj_id}` : '');
        setText(
            'next_min_price',
            data.minimum_price !== null && data.minimum_price !== ''
                ? `Minpris: ${data.minimum_price} kr`
                : ''
        );
        setText('next_plain_name', data.plain_name);
        setText('next_scientific_name', data.scientific_name);
        setText('next_description', data.description);
        setText('next_seller_name', data.name ? `Säljare: ${data.name}` : '');
        setAlert('next_type', data.type && data.type !== 'auction' ? 'Ej registrerad som auktionsgods' : '');
        setAlert('next_sold', data.sold_on !== null && data.sold_on !== undefined ? 'Redan sålt' : '');
    }

    function readStoredPost() {
        const value = window.localStorage.getItem(storageKey);
        if (!value) {
            return null;
        }

        try {
            return JSON.parse(value);
        } catch (error) {
            console.error('Kunde inte läsa nästa post från webbläsarlagringen:', error);
            return null;
        }
    }


    if (channel) {
        channel.addEventListener('message', function (event) {
            if (!event.data || event.data.type !== 'next-post') {
                return;
            }
            render(event.data.data || null);
        });
    }

    window.addEventListener('storage', function (event) {
        if (event.key !== storageKey) {
            return;
        }

        if (!event.newValue) {
            render(null);
            return;
        }

        try {
            render(JSON.parse(event.newValue));
        } catch (error) {
            console.error('Kunde inte läsa uppdaterad nästa post:', error);
        }
    });

    render(readStoredPost());
});
