import { mostrarToast } from './toast_func.js';

const numeroQuestao = document.getElementById('nQuestao');
const totalQuestoes = document.getElementById('qQuestao');

const estiloQuestao = document.getElementById('qStyle');
const dificuldadeQuestao = document.getElementById('qDificuldade');

const tituloQuestao = document.getElementById('qTitulo');
const contextoQuestao = document.getElementById('qContexto');
const imagemQuestao = document.getElementById('qImagem');

const alternativasQuestao = document.getElementById('qAlternativas');
const proximaQuestao = document.getElementById('proximaQuestao');
const salvarQ = document.getElementById('qSalvar');

const barraProgresso = document.querySelector(".progress");

let alternativaSelecionada = null;
let questaoAtual = 1;
let questaoAtualId = null;

async function carregarQuestao() {
    try {
        console.log("Carregando questão:", questaoAtual);

        const response = await fetch(`/api/teste/questao/${questaoAtual}`);

        const data = await response.json();

        console.log("Resposta API:", data);

        if (!data.success) {
            mostrarToast(data.message);
            return;
        }

        preencherQuestao(data.questao);

    } catch (error) {
        console.error(error);
        mostrarToast(error.message, 'error');
    }
}

function preencherQuestao(questao) {
    questaoAtualId = questao.id;

    alternativasQuestao.innerHTML = "";

    tituloQuestao.innerHTML = "";
    contextoQuestao.innerHTML = "";

    imagemQuestao.style.display = "none";
    imagemQuestao.src = "";

    numeroQuestao.textContent = questao.numero;
    totalQuestoes.textContent = questao.total;

    tituloQuestao.innerHTML = questao.titulo || "";
    contextoQuestao.innerHTML = questao.contexto || "";

    estiloQuestao.textContent = questao.assunto || "";
    dificuldadeQuestao.textContent = questao.dificuldade || "";

    if (questao.imagem_url) {
        imagemQuestao.src = questao.imagem_url;
        imagemQuestao.style.display = "block";
    }

    atualizarBarra(questao.numero, questao.total);

    renderQuestion(questao.alternativas);
}

function atualizarBarra(atual, total) {
    const percentual = (atual / total) * 100;

    barraProgresso.style.width = `${percentual}%`;
}

function renderQuestion(alternativas) {
    console.log("Alternativas recebidas:", alternativas);

    alternativasQuestao.innerHTML = '';

    alternativas.forEach(alternativa => {
        console.log("Renderizando:", alternativa);

        let imagemHTML = "";

        if (alternativa.imagem) {
            imagemHTML = `
                <img
                    src="${alternativa.imagem}"
                    class="alternative-image"
                >
            `;
        }

        alternativasQuestao.innerHTML += `
            <div class="alternative" data-letter="${alternativa.letra}">
                <div class="letter">
                    ${alternativa.letra}
                </div>

                <div class="alternative-content">
                    <p>${alternativa.texto || ''}</p>
                    ${imagemHTML}
                </div>
            </div>
        `;
    });

    console.log("HTML final:", alternativasQuestao.innerHTML);

    setupAlternativas();
}

function setupAlternativas() {
    const alternativas = document.querySelectorAll(".alternative");

    alternativas.forEach(alternativa => {
        alternativa.addEventListener("click", () => {
            alternativas.forEach(a => a.classList.remove("selected"));

            alternativa.classList.add("selected");

            alternativaSelecionada = alternativa.dataset.letter;
        });
    });
}

async function enviarResposta() {
    if (!alternativaSelecionada) {
        mostrarToast("Selecione uma alternativa.", "error");
        return;
    }

    try {
        const response = await fetch(
            '/api/teste/responder',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    numero: questaoAtual,
                    alternativa: alternativaSelecionada
                })
            }
        );

        const data = await response.json();

        if (data.acertou) {
            mostrarToast(data.message, "success");
        } else {
            mostrarToast(data.message, "error");
        }

        if (data.finalizado) {
            window.location.href = "/dashboard";

            return;
        }

        questaoAtual++;

        alternativaSelecionada = null;

        carregarQuestao();

    } catch (error) {
        mostrarToast(error.message, 'error');
    }
}

async function showHint() {
    try {
        const response = await fetch(`/api/questoes/dica/${questaoAtual}`);

        const data = await response.json();

        document.getElementById(
            "ai-text"
        ).innerHTML = data.dica;

    } catch (error) {
        mostrarToast(error.message, 'error');
    }
}

async function salvarQuestao() {
    if (!questaoAtualId) {
        mostrarToast("Nenhuma questão carregada.", "error");
        return;
    }

    try {
        const response = await fetch("/api/questoes/salvar", {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                questao_id: questaoAtualId
            })
        });

        const data = await response.json();

        if (data.success) {
            mostrarToast(data.message, "success");
        } else {
            mostrarToast(data.message, "error");
        }

    } catch (error) {
        mostrarToast(error.message, "error");
    }
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
                questao_id:
                    questaoAtual.id,
                tipo,
                descricao
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

salvarQ.addEventListener('click', salvarQuestao)

window.showHint = showHint;

proximaQuestao.addEventListener('click', enviarResposta);

document.addEventListener("DOMContentLoaded", carregarQuestao);

btnReportar.addEventListener("click", abrirModalReporte);
btnEnviarReporte.addEventListener("click", reportarQuestao);