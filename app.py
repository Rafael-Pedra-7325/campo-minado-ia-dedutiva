import os
import uuid
from typing import Dict
from flask import Flask, jsonify, render_template, request, session
from ia import IADedutivaCampoMinado
from jogo import CampoMinado

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "campo-minado-ia-dedutiva-secret-key")

PARTIDAS: Dict[str, CampoMinado] = {}
MOTOR_IA = IADedutivaCampoMinado()


def _obter_jogo() -> CampoMinado:
    jogo_id = session.get("jogo_id")
    if not jogo_id or jogo_id not in PARTIDAS:
        jogo_id = str(uuid.uuid4())
        session["jogo_id"] = jogo_id
        PARTIDAS[jogo_id] = CampoMinado("iniciante")
    return PARTIDAS[jogo_id]


@app.route("/")
def index():
    _obter_jogo()
    return render_template("index.html")


@app.route("/api/estado", methods=["GET"])
def api_estado():
    jogo = _obter_jogo()
    return jsonify(jogo.estado_publico())


@app.route("/api/novo-jogo", methods=["POST"])
def api_novo_jogo():
    dados = request.get_json(silent=True) or {}
    dificuldade = dados.get("dificuldade", "iniciante")
    jogo_id = str(uuid.uuid4())
    session["jogo_id"] = jogo_id

    # Mantém limite simples de sessões em memória
    if len(PARTIDAS) > 500:
        PARTIDAS.clear()

    jogo = CampoMinado(dificuldade=dificuldade)
    PARTIDAS[jogo_id] = jogo
    return jsonify(jogo.estado_publico())


@app.route("/api/revelar", methods=["POST"])
def api_revelar():
    dados = request.get_json(silent=True) or {}
    r = int(dados.get("linha", -1))
    c = int(dados.get("coluna", -1))
    jogo = _obter_jogo()
    estado = jogo.revelar(r, c)
    return jsonify(estado)


@app.route("/api/bandeira", methods=["POST"])
def api_bandeira():
    dados = request.get_json(silent=True) or {}
    r = int(dados.get("linha", -1))
    c = int(dados.get("coluna", -1))
    jogo = _obter_jogo()
    estado = jogo.alternar_bandeira(r, c)
    return jsonify(estado)


@app.route("/api/analisar-ia", methods=["GET"])
def api_analisar_ia():
    jogo = _obter_jogo()
    estado = jogo.estado_publico()
    analise = MOTOR_IA.analisar_tabuleiro(estado)
    return jsonify({"estado": estado, "analise": analise})


@app.route("/api/passo-ia", methods=["POST"])
def api_passo_ia():
    jogo = _obter_jogo()
    estado_atual = jogo.estado_publico()
    if estado_atual["status"] != "jogando":
        return jsonify({"estado": estado_atual, "jogada_executada": None, "analise": None})

    analise = MOTOR_IA.analisar_tabuleiro(estado_atual)
    jogada = analise.get("melhor_jogada")

    if jogada:
        r, c = jogada["coord"]
        if jogada["acao"] == "bandeira":
            novo_estado = jogo.alternar_bandeira(r, c)
        else:
            novo_estado = jogo.revelar(r, c)
    else:
        novo_estado = estado_atual

    nova_analise = MOTOR_IA.analisar_tabuleiro(novo_estado)
    return jsonify(
        {
            "estado": novo_estado,
            "jogada_executada": jogada,
            "analise": nova_analise,
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
