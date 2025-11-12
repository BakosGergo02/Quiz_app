// Drag & Drop párosító logika
// - jobb oldali elemeket random sorrendbe keverjük
// - a bal oldali dobozokra húzva a jobb oldali elem ténylegesen "átköltözik"
// - minden bal doboz max 1 elemet tartalmaz
// - egy jobb oldali elem egyszerre csak egy balhoz lehet hozzárendelve
// - vissza is lehet húzni a pool-ba

document.addEventListener('DOMContentLoaded', function () {
    const pool = document.getElementById('matching-right-container');
    if (!pool) return; // nincs párosító kérdés ezen az oldalon

    // 1) Jobb oldali elemek random sorrendbe keverése
    let items = Array.prototype.slice.call(
        pool.querySelectorAll('.matching-right-item')
    );

    if (items.length > 1) {
        for (let i = items.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            const tmp = items[i];
            items[i] = items[j];
            items[j] = tmp;
        }
        pool.innerHTML = '';
        items.forEach(el => pool.appendChild(el));
    }

    let draggedEl = null;
    let draggedId = null;

    // 2) Jobb oldali elemek draggolhatóvá tétele
    function makeDraggable(el) {
        el.addEventListener('dragstart', function (ev) {
            draggedEl = el;
            draggedId = el.getAttribute('data-right-id');
            if (ev.dataTransfer) {
                ev.dataTransfer.setData('text/plain', String(draggedId));
            }
        });
    }

    items.forEach(makeDraggable);

    // 3) Bal oldali droptargetek
    const drops = document.querySelectorAll('.matching-drop');

    drops.forEach(drop => {
        drop.addEventListener('dragover', function (ev) {
            ev.preventDefault();
        });

        drop.addEventListener('drop', function (ev) {
            ev.preventDefault();

            const leftId = drop.getAttribute('data-left-id');
            let rightId = draggedId;

            if (!rightId && ev.dataTransfer) {
                rightId = ev.dataTransfer.getData('text/plain');
                draggedEl = document.querySelector(
                    '.matching-right-item[data-right-id="' + rightId + '"]'
                );
            }

            if (!draggedEl || !rightId) return;

            const slot = drop.querySelector('.matching-slot');

            // ha már van elem ebben a slotban, azt visszatesszük a pool-ba
            const existing = slot.querySelector('.matching-right-item');
            if (existing) {
                pool.appendChild(existing);
                existing.classList.remove('bg-success');
            }

            // ha ez a jobb oldali elem már hozzárendelt egy másik balhoz,
            // onnan is vegyük ki és töröljük a mappinget
            const inputs = document.querySelectorAll('input[id^="mapping_"]');
            inputs.forEach(inp => {
                if (inp.value === rightId && inp.id !== 'mapping_' + leftId) {
                    inp.value = '';
                    const prevLeftId = inp.id.replace('mapping_', '');
                    const prevDrop = document.querySelector(
                        '.matching-drop[data-left-id="' + prevLeftId + '"]'
                    );
                    if (prevDrop) {
                        const prevSlot = prevDrop.querySelector('.matching-slot');
                        const prevItem = prevSlot.querySelector('.matching-right-item');
                        if (prevItem && prevItem.getAttribute('data-right-id') === rightId) {
                            pool.appendChild(prevItem);
                            prevItem.classList.remove('bg-success');
                        }
                    }
                }
            });

            // ténylegesen átrakjuk a jobb oldali elemet a bal slotba
            slot.appendChild(draggedEl);
            draggedEl.classList.add('bg-success');

            // hidden input kitöltése
            const hidden = document.getElementById('mapping_' + leftId);
            if (hidden) hidden.value = rightId;
        });
    });

    // 4) A jobb oldali pool maga is droptarget → ide vissza lehet húzni
    pool.addEventListener('dragover', function (ev) {
        ev.preventDefault();
    });

    pool.addEventListener('drop', function (ev) {
        ev.preventDefault();

        let rightId = draggedId;
        if (!rightId && ev.dataTransfer) {
            rightId = ev.dataTransfer.getData('text/plain');
        }
        if (!rightId) return;

        const el = document.querySelector(
            '.matching-right-item[data-right-id="' + rightId + '"]'
        );
        if (!el) return;

        // tegyük vissza a pool-ba
        pool.appendChild(el);
        el.classList.remove('bg-success');

        // töröljük a mappinget annál a balnál, ahol ez be volt állítva
        const inputs = document.querySelectorAll('input[id^="mapping_"]');
        inputs.forEach(inp => {
            if (inp.value === rightId) {
                inp.value = '';
            }
        });
    });
});
