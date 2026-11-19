
let graficoTemperatura = null;
let graficoUmidade = null;

async function atualizarDashboard() {
    try {
        const resposta = await fetch("/api/dashboard");

        if (!resposta.ok) {
            throw new Error("Erro ao buscar dados do dashboard");
        }

        const dados = await resposta.json();

        document.getElementById("temperatura-valor").textContent =
            dados.temperatura ?? "--";

        document.getElementById("umidade-valor").textContent =
            dados.umidade ?? "--";

        document.getElementById("sensores-ativos").textContent =
            dados.sensores_ativos ?? 0;

        const historico = dados.historico || [];

        const temperaturas = historico.filter(item =>
            item.tipo.toLowerCase().includes("temperatura")
        );

        const umidades = historico.filter(item =>
            item.tipo.toLowerCase().includes("umidade")
        );

        atualizarGrafico(
            "graficoTemperatura",
            temperaturas,
            "Temperatura (°C)",
            graficoTemperatura,
            "temperatura"
        );

        atualizarGrafico(
            "graficoUmidade",
            umidades,
            "Umidade (%)",
            graficoUmidade,
            "umidade"
        );

        atualizarTabela(historico);

    } catch (erro) {
        console.error("Erro no dashboard:", erro);
    }
}

function atualizarGrafico(id, dados, titulo, graficoAtual, tipo) {
    const canvas = document.getElementById(id);

    if (!canvas) return;

    const labels = dados.map(item => item.data_hora);
    const valores = dados.map(item => item.valor);

    if (graficoAtual) {
        graficoAtual.data.labels = labels;
        graficoAtual.data.datasets[0].data = valores;
        graficoAtual.update();
        return;
    }

    const novoGrafico = new Chart(canvas, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: titulo,
                data: valores,
                borderColor: tipo === "temperatura" ? "#e67e22" : "#2980b9",
                backgroundColor: tipo === "temperatura"
                    ? "rgba(230,126,34,0.12)"
                    : "rgba(41,128,185,0.12)",
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });

    if (tipo === "temperatura") {
        graficoTemperatura = novoGrafico;
    } else {
        graficoUmidade = novoGrafico;
    }
}

function atualizarTabela(historico) {
    const tabela = document.getElementById("tabela-historico");

    if (!tabela) return;

    tabela.innerHTML = "";

    if (historico.length === 0) {
        tabela.innerHTML = `
            <tr>
                <td colspan="4">Nenhuma medição registrada.</td>
            </tr>
        `;
        return;
    }

    historico.slice().reverse().forEach(item => {
        const linha = document.createElement("tr");

        const tipo = document.createElement("td");
        tipo.textContent = item.tipo;

        const valor = document.createElement("td");
        valor.textContent = item.valor;

        const unidade = document.createElement("td");
        unidade.textContent = item.unidade;

        const data = document.createElement("td");
        data.textContent = item.data_hora;

        linha.append(tipo, valor, unidade, data);
        tabela.appendChild(linha);
    });
}

atualizarDashboard();
setInterval(atualizarDashboard, 10000);
