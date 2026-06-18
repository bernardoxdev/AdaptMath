let chart = null;

document.addEventListener(
    "DOMContentLoaded",
    () => {
        carregarResumo();
        carregarGrafico();
        carregarMaterias();
        carregarInsights();
        carregarAnaliseIA();
    }
);

async function carregarResumo() {

    const response =
        await fetch(
            "/api/relatorio/resumo"
        );

    const data =
        await response.json();

    if (!data.success)
        return;

    const container =
        document.getElementById(
            "summaryContainer"
        );

    container.innerHTML = `
        <div class="summary-card">
            <div class="summary-icon">📈</div>
            <h2>${data.media_geral}%</h2>
            <span>Média Geral</span>
        </div>

        <div class="summary-card">
            <div class="summary-icon">🎯</div>
            <h2>${data.questoes}</h2>
            <span>Questões Realizadas</span>
        </div>

        <div class="summary-card">
            <div class="summary-icon">🧠</div>
            <h2>${data.melhor.percentual}%</h2>
            <span>${data.melhor.nome}</span>
        </div>

        <div class="summary-card">
            <div class="summary-icon">⚠️</div>
            <h2>${data.pior.percentual}%</h2>
            <span>${data.pior.nome}</span>
        </div>
    `;
}

async function carregarGrafico() {

    const response =
        await fetch(
            "/api/relatorio/evolucao"
        );

    const data =
        await response.json();

    if (!data.success)
        return;

    const labels =
        data.meses.map(
            item => item.nome
        );

    const valores =
        data.meses.map(
            item => item.valor
        );

    const ctx =
        document
            .getElementById(
                "monthlyChart"
            )
            .getContext("2d");

    if (chart)
        chart.destroy();

    chart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Desempenho (%)",
                data: valores,
                backgroundColor: "#38bdf8",
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: "#ffffff"
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: "#cbd5e1"
                    },
                    grid: {
                        color: "rgba(255,255,255,.05)"
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: "#cbd5e1"
                    },
                    grid: {
                        color: "rgba(255,255,255,.05)"
                    }
                }
            }
        }
    });
}

async function carregarMaterias() {

    const response =
        await fetch(
            "/api/relatorio/materias"
        );

    const data =
        await response.json();

    if (!data.success)
        return;

    const container =
        document.getElementById(
            "subjectsContainer"
        );

    container.innerHTML = "";

    data.materias.forEach(
        materia => {

            container.innerHTML += `
                <div class="subject">

                    <div class="subject-top">
                        <span>${materia.nome}</span>
                        <span>${materia.percentual}%</span>
                    </div>

                    <div class="progress">
                        <div
                            class="progress-fill"
                            style="width:${materia.percentual}%">
                        </div>
                    </div>

                </div>
            `;
        }
    );
}

async function carregarInsights() {

    const response =
        await fetch(
            "/api/relatorio/insights"
        );

    const data =
        await response.json();

    if (!data.success)
        return;

    const container =
        document.getElementById(
            "insightsContainer"
        );

    container.innerHTML = "";

    data.insights.forEach(
        insight => {

            container.innerHTML += `
                <div class="insight-card">

                    <h3>
                        ${insight.titulo}
                    </h3>

                    <p>
                        ${insight.texto}
                    </p>

                </div>
            `;
        }
    );
}

async function carregarAnaliseIA() {

    const response =
        await fetch(
            "/api/relatorio/analise"
        );

    const data =
        await response.json();

    if (!data.success)
        return;

    const container =
        document.getElementById(
            "aiAnalysisContainer"
        );

    container.innerHTML = "";

    data.textos.forEach(
        texto => {

            container.innerHTML += `
                <p>
                    ${texto}
                </p>
            `;
        }
    );
}