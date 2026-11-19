
async function verificarBanco() {
    try {
        const resposta = await fetch("/api/status-banco");
        const dados = await resposta.json();

        console.log("Status do banco:", dados);

    } catch (erro) {
        console.error("Erro ao verificar banco:", erro);
    }
}

verificarBanco();
