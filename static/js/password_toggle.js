'use strict';

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-password-toggle]').forEach(button => {
        const targetId = button.getAttribute('data-password-toggle');
        const input = document.getElementById(targetId);
        if (!input) {
            return;
        }

        button.addEventListener('click', () => {
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            button.textContent = show ? 'Dölj' : 'Visa';
            button.setAttribute('aria-pressed', show ? 'true' : 'false');
        });
    });
});
