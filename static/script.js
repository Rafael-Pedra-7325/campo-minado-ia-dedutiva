let estadoAtual = null;
let analiseAtual = null;
let dificuldadeAtual = "iniciante";
let segundos = 0;
let timerInterval = null;
let autoResolverAtivo = false;
let autoTimeout = null;

const elTabuleiro = document.getElementById("tabuleiro");
const elHudMinas = document.getElementById("hud-minas");
const elHudTempo = document.getElementById("hud-tempo");
const elStatusIcon = document.getElementById("status-icon");
const elStatusText = document.getElementById("status-text");
const elBtnNovoJogo = document.getElementById("btn-novo-jogo");
const elProgressBar = document.getElementById("progress-bar");
const elToggleRaioX = document.getElementById("toggle-raiox");
const elCountSeguras = document.getElementById("count-seguras");
const elCountMinas = document.getElementById("count-minas");
const elLogDeducao = document.getElementById("log-deducao");
const elBtnAuto = document.getElementById("btn-auto-ia");
const elAiDot = document.getElementById("ai-dot");

function formatarNumero(num) {
    const sinal = num < 0 ? "-" : "";
    const abs = Math.min(999, Math.abs(num));
    return sinal + String(abs).padStart(3, "0");
}

function iniciarTimer() {
    if (timerInterval) return;
    timerInterval = setInterval(() => {
        if (estadoAtual && estadoAtual.status === "jogando" && !estadoAtual.primeiro_clique) {
            segundos++;
            elHudTempo.textContent = formatarNumero(segundos);
        }
    }, 1000);
}

function resetarTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    segundos = 0;
    elHudTempo.textContent = "000";
}

function adicionarLog(metodo, texto) {
    const nomesMetodos = {
        abertura: "ABERTURA",
        deducao_simples: "DEDUÇÃO SIMPLES",
        deducao_conjuntos: "CONJUNTOS CSP",
        csp_exato: "CSP COMBINATÓRIO",
        probabilidade: "PROBABILIDADE",
        erro: "ALERTA",
        info: "SISTEMA"
    };

    const div = document.createElement("div");
    div.className = `log-entry ${metodo}`;
    div.innerHTML = `
        <span class="tag">${nomesMetodos[metodo] || metodo.toUpperCase()}</span>
        <p>${texto}</p>
    `;
    elLogDeducao.prepend(div);

    // Mantém no máximo 25 entradas no console
    while (elLogDeducao.children.length > 25) {
        elLogDeducao.removeChild(elLogDeducao.lastChild);
    }
}

function pararAutoResolver() {
    autoResolverAtivo = false;
    clearTimeout(autoTimeout);
    elBtnAuto.classList.remove("active-auto");
    elBtnAuto.innerHTML = "<span>🤖</span> Auto-Resolver";
    elAiDot.textContent = "Pronto";
    elAiDot.classList.remove("running");
}

function atualizarHUD() {
    if (!estadoAtual) return;

    elHudMinas.textContent = formatarNumero(estadoAtual.minas_restantes);

    const pct = estadoAtual.total_seguras > 0
        ? Math.round((estadoAtual.reveladas_count / estadoAtual.total_seguras) * 100)
        : 0;
    elProgressBar.style.width = `${pct}%`;

    elBtnNovoJogo.classList.remove("vitoria", "derrota");
    if (estadoAtual.status === "vitoria") {
        elStatusIcon.textContent = "🏆";
        elStatusText.textContent = "Vitória!";
        elBtnNovoJogo.classList.add("vitoria");
        pararAutoResolver();
    } else if (estadoAtual.status === "derrota") {
        elStatusIcon.textContent = "💥";
        elStatusText.textContent = "Detonado";
        elBtnNovoJogo.classList.add("derrota");
        pararAutoResolver();
    } else {
        elStatusIcon.textContent = "🛡️";
        elStatusText.textContent = "Em Operação";
    }

    if (analiseAtual) {
        elCountSeguras.textContent = analiseAtual.seguras.length;
        elCountMinas.textContent = analiseAtual.minas.length;
    } else {
        elCountSeguras.textContent = "0";
        elCountMinas.textContent = "0";
    }
}

function renderizarTabuleiro() {
    if (!estadoAtual) return;

    const { linhas, colunas, grade, mina_explodida } = estadoAtual;
    elTabuleiro.style.gridTemplateColumns = `repeat(${colunas}, 1fr)`;
    elTabuleiro.classList.toggle("compact", colunas >= 24);
    elTabuleiro.innerHTML = "";

    const segurasSet = new Set();
    const minasSet = new Set();
    let melhorCoord = null;
    const probs = analiseAtual ? analiseAtual.probabilidades : {};

    if (analiseAtual) {
        analiseAtual.seguras.forEach(item => segurasSet.add(`${item.coord[0]},${item.coord[1]}`));
        analiseAtual.minas.forEach(item => minasSet.add(`${item.coord[0]},${item.coord[1]}`));
        if (analiseAtual.melhor_jogada) {
            melhorCoord = `${analiseAtual.melhor_jogada.coord[0]},${analiseAtual.melhor_jogada.coord[1]}`;
        }
    }

    const mostrarRaioX = elToggleRaioX.checked;

    for (let r = 0; r < linhas; r++) {
        for (let c = 0; c < colunas; c++) {
            const val = grade[r][c];
            const key = `${r},${c}`;
            const cell = document.createElement("div");
            cell.className = "cell";

            if (val === null) {
                cell.classList.add("hidden");

                if (segurasSet.has(key)) {
                    cell.classList.add("ai-safe");
                } else if (minasSet.has(key)) {
                    cell.classList.add("ai-mine");
                }

                if (melhorCoord === key) {
                    cell.classList.add("ai-best");
                }

                if (mostrarRaioX && key in probs) {
                    const p = Math.round(probs[key] * 100);
                    const badge = document.createElement("span");
                    badge.className = "prob-badge";
                    badge.textContent = `${p}%`;
                    if (p === 0) {
                        badge.style.color = "#6ee7b7";
                    } else if (p === 100) {
                        badge.style.color = "#fca5a5";
                    } else if (p <= 35) {
                        badge.style.color = "#fde68a";
                    } else {
                        badge.style.color = "#fdba74";
                    }
                    cell.appendChild(badge);
                }
            } else if (val === "F") {
                cell.classList.add("hidden", "flagged");
                cell.textContent = "🚩";
            } else if (val === "X") {
                cell.classList.add("revealed", "mine");
                cell.textContent = "❌";
            } else if (val === "M") {
                cell.classList.add("revealed", "mine");
                if (mina_explodida && mina_explodida[0] === r && mina_explodida[1] === c) {
                    cell.classList.add("mine-exploded");
                }
                cell.textContent = "💣";
            } else {
                cell.classList.add("revealed");
                if (val > 0) {
                    cell.classList.add("has-number", `num-${val}`);
                    cell.textContent = val;
                }
            }

            cell.addEventListener("click", () => clicarRevelar(r, c));
            cell.addEventListener("contextmenu", (e) => {
                e.preventDefault();
                clicarBandeira(r, c);
            });

            elTabuleiro.appendChild(cell);
        }
    }

    atualizarHUD();
}

async function novoJogo(dificuldade = dificuldadeAtual) {
    pararAutoResolver();
    dificuldadeAtual = dificuldade;
    resetarTimer();
    analiseAtual = null;

    const resp = await fetch("/api/novo-jogo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dificuldade })
    });
    estadoAtual = await resp.json();
    renderizarTabuleiro();
    adicionarLog("info", `Novo tabuleiro (${dificuldade}) inicializado.`);
}

async function clicarRevelar(r, c) {
    if (!estadoAtual || estadoAtual.status !== "jogando") return;
    if (estadoAtual.primeiro_clique) iniciarTimer();

    const resp = await fetch("/api/revelar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ linha: r, coluna: c })
    });
    estadoAtual = await resp.json();

    if (elToggleRaioX.checked && estadoAtual.status === "jogando") {
        await analisarComIA(false);
    } else {
        analiseAtual = null;
        renderizarTabuleiro();
    }
}

async function clicarBandeira(r, c) {
    if (!estadoAtual || estadoAtual.status !== "jogando") return;

    const resp = await fetch("/api/bandeira", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ linha: r, coluna: c })
    });
    estadoAtual = await resp.json();

    if (elToggleRaioX.checked && estadoAtual.status === "jogando") {
        await analisarComIA(false);
    } else {
        analiseAtual = null;
        renderizarTabuleiro();
    }
}

async function analisarComIA(registrarLog = true) {
    if (!estadoAtual || estadoAtual.status !== "jogando") return;

    const resp = await fetch("/api/analisar-ia");
    const dados = await resp.json();
    estadoAtual = dados.estado;
    analiseAtual = dados.analise;
    renderizarTabuleiro();

    if (registrarLog && analiseAtual) {
        if (analiseAtual.aviso) {
            adicionarLog("erro", analiseAtual.aviso);
        } else if (analiseAtual.melhor_jogada) {
            adicionarLog(
                analiseAtual.melhor_jogada.metodo,
                analiseAtual.melhor_jogada.explicacao
            );
        }
    }
}

async function executarPassoIA() {
    if (!estadoAtual || estadoAtual.status !== "jogando") return false;
    if (estadoAtual.primeiro_clique) iniciarTimer();

    const resp = await fetch("/api/passo-ia", { method: "POST" });
    const dados = await resp.json();
    estadoAtual = dados.estado;
    analiseAtual = dados.analise;

    if (dados.jogada_executada) {
        adicionarLog(
            dados.jogada_executada.metodo,
            dados.jogada_executada.explicacao
        );
    }

    renderizarTabuleiro();
    return estadoAtual.status === "jogando";
}

async function loopAutoResolver() {
    if (!autoResolverAtivo) return;
    const continuar = await executarPassoIA();
    if (continuar && autoResolverAtivo) {
        const delay = parseInt(document.getElementById("select-velocidade").value, 10);
        autoTimeout = setTimeout(loopAutoResolver, delay);
    } else {
        pararAutoResolver();
    }
}

// Event Listeners
document.querySelectorAll(".diff-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".diff-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        novoJogo(btn.dataset.diff);
    });
});

elBtnNovoJogo.addEventListener("click", () => novoJogo(dificuldadeAtual));
document.getElementById("btn-analisar").addEventListener("click", () => analisarComIA(true));
document.getElementById("btn-passo-ia").addEventListener("click", () => {
    pararAutoResolver();
    executarPassoIA();
});

elBtnAuto.addEventListener("click", () => {
    if (autoResolverAtivo) {
        pararAutoResolver();
        return;
    }
    if (!estadoAtual || estadoAtual.status !== "jogando") return;

    autoResolverAtivo = true;
    elBtnAuto.classList.add("active-auto");
    elBtnAuto.innerHTML = "<span>⏹️</span> Parar Auto-IA";
    elAiDot.textContent = "Resolvendo...";
    elAiDot.classList.add("running");
    loopAutoResolver();
});

elToggleRaioX.addEventListener("change", () => {
    if (elToggleRaioX.checked && estadoAtual && estadoAtual.status === "jogando") {
        analisarComIA(false);
    } else {
        renderizarTabuleiro();
    }
});

document.getElementById("btn-limpar-log").addEventListener("click", () => {
    elLogDeducao.innerHTML = "";
});

// Inicialização
novoJogo("iniciante");
