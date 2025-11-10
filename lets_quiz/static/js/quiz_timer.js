document.addEventListener("DOMContentLoaded", () => {
    const display = document.getElementById("timer-display");
    if (!display) return;

    let timeLeft = parseInt(display.dataset.timeleft);

    // ha nincs időkorlát vagy hiba van az adatban, ne csináljon semmit
    if (isNaN(timeLeft) || timeLeft <= 0) {
        display.innerHTML = "Nincs időkorlát";
        return;
    }

    function formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs < 10 ? "0" + secs : secs}`;
    }

    function tick() {
        if (isNaN(timeLeft)) {
            display.innerHTML = "Hiba az időmérésben";
            return;
        }

        if (timeLeft <= 0) {
            display.innerHTML = "Lejárt az idő!";
            window.location.href = display.dataset.endurl;
            return;
        }

        display.innerHTML = formatTime(timeLeft);
        timeLeft -= 1;
    }

    tick();
    setInterval(tick, 1000);
});
