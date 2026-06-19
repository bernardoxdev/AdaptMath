import { mostrarToast } from './toast_func.js';

const exerciseList = document.getElementById("exerciseList");

let questaoSelecionada = null;

document.addEventListener(
    "DOMContentLoaded",
    carregarQuestoesSalvas
);

async function carregarQuestoesSalvas() {
    try {
        const response = await fetch(
            "/api/questoes/salvas"
        );

        const data = await response.json();

        if (!data.success) {
            mostrarToast(
                data.message || "Erro ao carregar exercícios",
                "error"
            );
            return;
        }

        renderizarLista(
            data.questoes
        );

    } catch (e) {
        console.error(e);

        mostrarToast(
            "Erro ao carregar exercícios",
            "error"
        );
    }
}

function renderizarLista(questoes) {

    exerciseList.innerHTML = "";

    document.querySelector(
        ".saved-count"
    ).textContent =
        `${questoes.length} Exercícios Salvos`;

    if (questoes.length === 0) {

        exerciseList.innerHTML = `
            <div class="exercise-item">
                <div class="exercise-info">
                    <h2>
                        Nenhum exercício salvo
                    </h2>

                    <p>
                        Você ainda não salvou nenhum exercício.
                    </p>
                </div>
            </div>
        `;

        return;
    }

    questoes.forEach(questao => {

        exerciseList.innerHTML += `
            <div class="exercise-item">

                <div class="exercise-info">

                    <h2>
                        ${questao.titulo}
                    </h2>

                    <p>
                        ${(questao.contexto || "").substring(0, 150)}
                    </p>

                    <div class="tags">

                        <div class="tag">
                            ${questao.assunto}
                        </div>

                        <div class="tag">
                            ${questao.origem}
                        </div>

                        <div class="tag">
                            Dificuldade ${questao.dificuldade}
                        </div>

                    </div>

                </div>

                <div class="actions">

                    <button
                        class="view-btn"
                        data-id="${questao.id}">
                        👁 Visualizar
                    </button>

                    <button
                        class="remove-btn"
                        data-id="${questao.id}">
                        🗑 Remover
                    </button>

                </div>

            </div>
        `;
    });

    document
        .querySelectorAll(".view-btn")
        .forEach(btn => {

            btn.addEventListener(
                "click",
                () => visualizarQuestao(
                    btn.dataset.id
                )
            );

        });

    document
        .querySelectorAll(".remove-btn")
        .forEach(btn => {

            btn.addEventListener(
                "click",
                () => abrirRemocao(
                    btn.dataset.id
                )
            );

        });
}

async function visualizarQuestao(id) {

    try {

        const response =
            await fetch(
                `/api/questoes/salvas/${id}`
            );

        const data =
            await response.json();

        if (!data.success) {
            mostrarToast(
                data.message,
                "error"
            );

            return;
        }

        const questao =
            data.questao;

        document.getElementById(
            "modalTitulo"
        ).innerHTML =
            questao.titulo || "";

        document.getElementById(
            "modalContexto"
        ).innerHTML =
            questao.contexto || "";

        const modalImagem =
            document.getElementById(
                "modalImagem"
            );

        if (questao.imagem_url) {

            modalImagem.src =
                questao.imagem_url;

            modalImagem.style.display =
                "block";

        } else {

            modalImagem.style.display =
                "none";

            modalImagem.src = "";
        }

        const alternativas =
            document.getElementById(
                "modalAlternativas"
            );

        alternativas.innerHTML = "";

        questao.alternativas.forEach(alt => {
            alternativas.innerHTML += `
                    <div class="alternative">

                        <div class="letter">
                            ${alt.letra}
                        </div>

                        <div class="alternative-content">

                            ${alt.texto
                    ? `<p>${alt.texto}</p>`
                    : ""
                }

                            ${alt.imagem
                    ? `
                                    <img
                                        src="${alt.imagem}"
                                        class="alternative-image"
                                        style="max-width:100%;margin-top:10px;"
                                    >
                                `
                    : ""
                }

                        </div>

                    </div>
                `;
        });

        openViewModal();

    } catch (e) {
        console.error(e);

        mostrarToast("Erro ao carregar exercício", "error");
    }
}

function abrirRemocao(id) {
    questaoSelecionada = id;

    openRemoveModal();
}

async function removerQuestao() {
    if (!questaoSelecionada)
        return;

    try {
        const response = await fetch(`/api/questoes/salvas/${questaoSelecionada}`, {
            method: "DELETE"
        });

        const data = await response.json();

        if (!data.success) {
            mostrarToast(data.message, "error");

            return;
        }

        mostrarToast(data.message, "success");

        closeRemoveModal();

        questaoSelecionada = null;

        carregarQuestoesSalvas();

    } catch (e) {
        console.error(e);

        mostrarToast("Erro ao remover exercício", "error");
    }
}

document.querySelector(".confirm-btn").addEventListener("click", removerQuestao);

function openViewModal() {
    document.getElementById("viewModal").style.display = "flex";
}

function closeViewModal() {
    document.getElementById("viewModal").style.display = "none";
}

function openRemoveModal() {
    document.getElementById("removeModal").style.display = "flex";
}

function closeRemoveModal() {
    document.getElementById("removeModal").style.display = "none";
}

window.addEventListener("click", (event) => {
    const viewModal = document.getElementById("viewModal");

    const removeModal = document.getElementById("removeModal");

    if (event.target === viewModal) {
        closeViewModal();
    }

    if (event.target === removeModal) {
        closeRemoveModal();
    }
});

window.closeViewModal = closeViewModal;
window.closeRemoveModal = closeRemoveModal;