'use strict';

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('table[data-sortable]').forEach(table => {
        const headers = table.querySelectorAll('thead th');

        headers.forEach((header, columnIndex) => {
            if (header.dataset.sort === 'none') {
                return;
            }

            header.classList.add('user-select-none');
            header.style.cursor = 'pointer';
            header.setAttribute('title', 'Klicka för att sortera');

            header.addEventListener('click', () => {
                const tbody = table.tBodies[0];
                if (!tbody) {
                    return;
                }

                const ascending = header.dataset.direction !== 'asc';
                headers.forEach(item => delete item.dataset.direction);
                header.dataset.direction = ascending ? 'asc' : 'desc';

                const rows = Array.from(tbody.rows);
                rows.sort((left, right) => {
                    const leftValue = left.cells[columnIndex]?.textContent.trim() ?? '';
                    const rightValue = right.cells[columnIndex]?.textContent.trim() ?? '';
                    const leftNumber = Number(leftValue.replace(',', '.'));
                    const rightNumber = Number(rightValue.replace(',', '.'));

                    let result;
                    if (leftValue !== '' && rightValue !== '' && Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
                        result = leftNumber - rightNumber;
                    } else {
                        result = leftValue.localeCompare(rightValue, 'sv', { numeric: true, sensitivity: 'base' });
                    }

                    return ascending ? result : -result;
                });

                rows.forEach(row => tbody.appendChild(row));
            });
        });
    });
});
