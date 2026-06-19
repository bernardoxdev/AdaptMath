let chart = null;

document.addEventListener("DOMContentLoaded", () => {
    carregarGrafico();
    carregarMaterias();
    carregarAtividades();
});

async function carregarMaterias() {
    try {
        const response = await fetch("/api/relatorio/materias");

        const data = await response.json();

        console.log("Matérias:", data);

        if (!data.success) {
            return;
        }

        const container = document.getElementById("subjectsContainer");

        container.innerHTML = "";

        data.materias.forEach(materia => {
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
        });

    } catch (e) {

        console.error("Erro ao carregar matérias:", e);
    }
}

async function carregarGrafico() {
    try {

        const response = await fetch("/api/relatorio/evolucao");

        const data = await response.json();

        console.log(data);

        if (!data.success)
            return;

        const labels = data.meses.map(
            item => item.nome
        );

        const valores = data.meses.map(
            item => item.valor
        );

        const canvas =
            document.getElementById("weeklyChart");

        if (!canvas) {
            console.error("Canvas weeklyChart não encontrado.");
            return;
        }

        const ctx = canvas.getContext("2d");

        if (chart)
            chart.destroy();

        chart = new Chart(ctx, {

            type: "bar",

            data: {

                labels,

                datasets: [

                    {
                        label: "Desempenho (%)",
                        data: valores,
                        backgroundColor: "#38bdf8",
                        borderRadius: 10
                    }

                ]

            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                scales: {

                    y: {

                        beginAtZero: true,

                        max: 100

                    }

                }

            }

        });

    }

    catch (e) {

        console.error(e);

    }

}

async function carregarAtividades() {
    try {
        const response = await fetch("/api/dashboard/atividades");

        const data = await response.json();

        console.log("Atividades:", data);

        if (!data.success) {
            return;
        }

        const container = document.getElementById("activitiesContainer");

        container.innerHTML = "";

        data.atividades.forEach(
            atividade => {
                container.innerHTML += `
                    <div class="activity">

                        <div class="activity-info">

                            <strong>
                                ${atividade.titulo}
                            </strong>

                            <span>
                                ${atividade.descricao}
                            </span>

                        </div>

                        <div class="activity-status">
                            ${atividade.status}
                        </div>

                    </div>
                `;
            }
        );

    } catch (e) {
        console.error(
            "Erro ao carregar atividades:",
            e
        );
    }
}