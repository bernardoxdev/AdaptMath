import { mostrarToast } from './toast_func.js';

const selectMateria = document.getElementById("selectMateria");
const selectDificuldade = document.getElementById("selectDificuldade");
const selectModelo = document.getElementById("selectModelo");

const qTitulo = document.getElementById("qTitulo");
const qContexto = document.getElementById("qContexto");
const qImagem = document.getElementById("qImagem");
const qAlternativas = document.getElementById("qAlternativas");
const qModelo = document.getElementById("qModelo");
const qDificuldade = document.getElementById("qDificuldade");

const btnResponder = document.getElementById("btnResponder");
const btnSalvar = document.getElementById("btnSalvar");
const btnHint = document.getElementById("btnHint");
const btnPular = document.getElementById("btnPular");
const btnReportar = document.getElementById("btnReportar");
const btnEnviarReporte = document.getElementById("btnEnviarReporte");

let questaoAtual = null;
let alternativaSelecionada = null;

document.addEventListener("DOMContentLoaded", carregarQuestao);

async function carregarQuestao() {
    try {
        const materia = selectMateria.value;
        const dificuldade = selectDificuldade.value;
        const modelo = selectModelo.value;

        const response = await fetch("/api/questoes/proxima", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                materia: materia,
                dificuldade: dificuldade,
                modelo: modelo
            })
        });

        const data = await response.json();

        if (!data.success) {
            mostrarToast(data.message, "error");

            qTitulo.innerHTML = data.message;
            qContexto.innerHTML = "Tente outras combinações de filtros.";
            qModelo.innerHTML = "-";
            qDificuldade.innerHTML = "-";
            qImagem.style.display = "none";
            qImagem.src = "";
            qAlternativas.innerHTML = "";

            return;
        }

        questaoAtual = data.questao;

        renderizarQuestao(questaoAtual);

    } catch (e) {
        console.error(e);
        mostrarToast(e.message || "Erro ao carregar questão", "error");
    }
}

function renderizarQuestao(questao) {
    qTitulo.innerHTML = questao.titulo || "";
    qContexto.innerHTML = questao.contexto || "";
    qModelo.innerHTML = questao.origem || "Questão";
    qDificuldade.innerHTML = questao.dificuldade || "-";

    if (questao.imagem_url) {
        qImagem.src = questao.imagem_url;
        qImagem.style.display = "block";
    } else {
        qImagem.style.display = "none";
        qImagem.src = "";
    }

    qAlternativas.innerHTML = "";

    questao.alternativas.forEach(
        alternativa => {
            qAlternativas.innerHTML += `
                <div class="alternative" data-letter="${alternativa.letra}">
                    <div class="letter">
                        ${alternativa.letra}
                    </div>

                    <div class="alternative-content">
                        ${alternativa.texto ? `<p>${alternativa.texto}</p>` : ""}

                        ${alternativa.imagem ? ` <img src="${alternativa.imagem}" class="alternative-image">` : ""}
                    </div>
                </div>
            `;
        }
    );

    configurarAlternativas();
}

function configurarAlternativas() {
    document.querySelectorAll(".alternative").forEach(alternativa => {
        alternativa.addEventListener("click", () => {
            document.querySelectorAll(".alternative").forEach(a => a.classList.remove("active"));

            alternativa.classList.add("active");

            alternativaSelecionada = alternativa.dataset.letter;
        });
    });
}

async function responderQuestao() {
    if (!alternativaSelecionada) {
        mostrarToast("Selecione uma alternativa", "error");
        return;
    }

    try {
        const response = await fetch("/api/questoes/responder", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                questao_id: questaoAtual.id,
                alternativa: alternativaSelecionada
            })
        });

        const data = await response.json();

        mostrarToast(data.message, data.acertou ? "success" : "error");

        carregarQuestao();

        alternativaSelecionada = null;

    } catch (e) {
        mostrarToast("Erro ao responder", "error");
    }
}

async function salvarQuestao() {
    try {
        const response = await fetch("/api/questoes/salvar", {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                questao_id: questaoAtual.id
            })
        });

        const data = await response.json();

        mostrarToast(data.message, data.success ? "success" : "error");

    } catch (e) {
        mostrarToast("Erro ao salvar", "error");
    }
}

async function pedirDica() {
    try {
        const response = await fetch(`/api/questoes/dica/${questaoAtual.id}`);

        const data = await response.json();

        document.getElementById("ai-text").innerHTML = data.dica;

    } catch (e) {
        mostrarToast("Erro ao gerar dica", "error");
    }
}

function selectAlternative(element) {
    document.querySelectorAll(".alternative").forEach(item => {
        item.classList.remove("active");
    });

    element.classList.add("active");
}

function abrirModalReporte() {
    const modal = new bootstrap.Modal(document.getElementById("reportModal"));
    modal.show();
}

async function reportarQuestao() {
    try {
        const tipo = document.getElementById("reportTipo").value;
        const descricao = document.getElementById("reportDescricao").value;

        const response = await fetch("/api/questoes/reportar", {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                questao_id: questaoAtual.id,
                tipo: tipo,
                descricao: descricao
            })
        });

        const data = await response.json();

        mostrarToast(data.message, data.success ? "success" : "error");

        bootstrap.Modal.getInstance(document.getElementById("reportModal")).hide();

        carregarQuestao();

    } catch (e) {

        mostrarToast("Erro ao reportar", "error");
    }
}

btnResponder.addEventListener("click", responderQuestao);
btnSalvar.addEventListener("click", salvarQuestao);
btnHint.addEventListener("click", pedirDica);
btnPular.addEventListener("click", carregarQuestao);
btnReportar.addEventListener("click", abrirModalReporte);
btnEnviarReporte.addEventListener("click", reportarQuestao);

selectDificuldade.addEventListener("change", carregarQuestao);
selectMateria.addEventListener("change", carregarQuestao);
selectModelo.addEventListener("change", carregarQuestao);