import { mostrarToast } from './toast_func.js';

function redirect_page(page) {
    var loc = "/dashboard";

    if (page == 1) {
        loc = "/dashboard/aptidao";
    } else if (page == 2) {
        loc = "/dashboard/questoes";
    } else if (page == 3) {
        loc = "/dashboard/questoes/salvas";
    } else if (page == 4) {
        loc = "/dashboard/dados";
    } else if (page == 5) {
        loc = "/dashboard/relatorio";
    } else if (page == 6) {
        loc = "/dashboard/ia";
    }

    setTimeout(() => {window.location.href = loc;}, 800);
}

document.querySelectorAll(".card-btn").forEach(button => {
    button.addEventListener("click", () => {
        const page = button.dataset.page;

        redirect_page(page);

        mostrarToast("Redirecionando...");
    });
});

document.querySelectorAll(".logout").forEach(button => {
    button.addEventListener("click", () => {
        window.location.href = "/logout";
    });
});

const sidebar = document.getElementById('sidebarMobile');
const btn = document.getElementById('menuBtn');

sidebar.addEventListener('show.bs.offcanvas', () => {
    btn.style.display = 'none';
});

sidebar.addEventListener('hidden.bs.offcanvas', () => {
    btn.style.display = 'flex';
});