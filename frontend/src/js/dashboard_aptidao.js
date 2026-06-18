import { mostrarToast } from "./toast_func.js";

async function startTest() {
    const response = await fetch('/start-aptidao', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();

    if (data.redirect) {
        window.location.href = data.redirect;
    } else {
        mostrarToast(data.message);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("startBtn").addEventListener("click", startTest);
});