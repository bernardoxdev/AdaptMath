let conversaAtual = null;

const historyContainer = document.getElementById("historyContainer");
const chatArea = document.getElementById("chatArea");
const inputArea = document.getElementById("inputArea");
const messageInput = document.getElementById("messageInput");
const btnEnviar = document.getElementById("btnEnviar");
const btnNovaConversa = document.getElementById("btnNovaConversa");

const menuBtn = document.getElementById("menuBtn");
const sidebar = document.querySelector(".sidebar");

menuBtn.addEventListener("click", () => {
    sidebar.classList.toggle("active");

    menuBtn.innerHTML = sidebar.classList.contains("active") ? "✕" : "☰";
});

document.addEventListener("DOMContentLoaded", async () => {
    await carregarHistorico();

    limparChat();
});

function limparChat() {
    conversaAtual = null;

    chatArea.innerHTML = `
        <div class="message ai-message">
            <strong>🤖 AdaptMath IA</strong>

            Olá! Como posso ajudar você hoje?
        </div>
    `;
}

async function carregarHistorico() {
    try {
        const response = await fetch("/api/chat/conversas");

        const data = await response.json();

        if (!data.success) {
            return;
        }

        historyContainer.innerHTML = "";

        data.conversas.forEach(conversa => {
            historyContainer.innerHTML += `
                    <div
                        class="history-item"
                        data-id="${conversa.id}">
                        <h4>
                            ${conversa.titulo}
                        </h4>

                        <span>
                            ${conversa.data}
                        </span>
                    </div>
                `;
        });

        document.querySelectorAll(".history-item").forEach(item => {
            item.addEventListener("click", () => carregarConversa(item.dataset.id));
        });

    } catch (e) {
        console.error(e);
    }
}

function fecharSidebar() {
    sidebar.classList.remove("active");

    menuBtn.innerHTML = sidebar.classList.contains("active") ? "✕" : "☰";
}

async function criarConversa(texto) {
    fecharSidebar();

    const response = await fetch("/api/chat/conversa", {
        method: "POST",
        headers: {
            "Content-Type":
                "application/json"
        },
        body: JSON.stringify({
            mensagem: texto
        })
    });

    const data = await response.json();

    if (!data.success) return null;

    conversaAtual = data.conversa_id;

    await carregarHistorico();

    return conversaAtual;
}

async function carregarConversa(id) {
    conversaAtual = id;
    fecharSidebar();

    try {
        const response = await fetch(`/api/chat/conversa/${id}`);

        const data = await response.json();

        if (!data.success) {
            return;
        }

        chatArea.innerHTML = "";

        data.mensagens.forEach(mensagem => {
            chatArea.innerHTML += `
                    <div class="message ${mensagem.tipo === "user"
                    ? "user-message"
                    : "ai-message"
                }">

                        <strong>
                            ${mensagem.tipo === "user"
                    ? "Você"
                    : "🤖 AdaptMath IA"
                }
                        </strong>

                        ${mensagem.texto}

                    </div>
                `;
        });

        scrollFinal();

    } catch (e) {
        console.error(e);
    }
}

async function enviarMensagem() {
    const texto = messageInput.value.trim();

    if (!texto) {
        return;
    }

    if (!conversaAtual) {
        await criarConversa(texto);
    }

    adicionarMensagemUsuario(texto);

    messageInput.value = "";

    const typing = adicionarDigitando();

    try {
        const response = await fetch("/api/chat/mensagem", {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                conversa_id: conversaAtual,
                mensagem: texto
            })
        });

        const data = await response.json();

        typing.remove();

        adicionarMensagemIA(data.resposta);

    } catch (e) {
        typing.remove();

        adicionarMensagemIA("Ocorreu um erro ao processar sua mensagem.");
    }
}

function adicionarMensagemUsuario(texto) {
    chatArea.innerHTML += `
        <div class="message user-message">

            <strong>
                Você
            </strong>

            ${texto}

        </div>
    `;

    scrollFinal();
}

function adicionarMensagemIA(texto) {
    chatArea.innerHTML += `
        <div class="message ai-message">

            <strong>
                🤖 AdaptMath IA
            </strong>

            ${texto}

        </div>
    `;

    scrollFinal();
}

function adicionarDigitando() {
    const div = document.createElement("div");

    div.className = "message ai-message typing";

    div.innerHTML = `
        <strong>
            🤖 AdaptMath IA
        </strong>

        Digitando...
    `;

    chatArea.appendChild(div);

    scrollFinal();

    return div;
}

function scrollFinal() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

btnEnviar.addEventListener("click", enviarMensagem);
btnNovaConversa.addEventListener("click", () => {
    fecharSidebar();
    limparChat();
});
chatArea.addEventListener("click", fecharSidebar);
inputArea.addEventListener("click", fecharSidebar);

messageInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();

        enviarMensagem();
    }
});