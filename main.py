from ia import IADedutivaCampoMinado
from jogo import CampoMinado


def imprimir_tabuleiro(estado: dict) -> None:
    linhas = estado["linhas"]
    colunas = estado["colunas"]
    grade = estado["grade"]

    cabecalho = "    " + " ".join(f"{c+1:2d}" for c in range(colunas))
    print("\n" + cabecalho)
    print("   +" + "---" * colunas + "+")
    for r in range(linhas):
        linha_str = []
        for c in range(colunas):
            val = grade[r][c]
            if val is None:
                linha_str.append(" .")
            elif val == "F":
                linha_str.append(" F")
            elif val == "M":
                linha_str.append(" *")
            elif val == "X":
                linha_str.append(" X")
            elif val == 0:
                linha_str.append("  ")
            else:
                linha_str.append(f" {val}")
        print(f"{r+1:2d} |{''.join(linha_str)} |")
    print("   +" + "---" * colunas + "+")
    print(f"Minas restantes: {estado['minas_restantes']} | Status: {estado['status'].upper()}")


def executar_terminal() -> None:
    print("=== CAMPO MINADO COM IA DEDUTIVA (MODO TERMINAL) ===")
    dificuldade = input("Escolha a dificuldade [iniciante/intermediario/especialista] (Enter = iniciante): ").strip().lower()
    if dificuldade not in ("iniciante", "intermediario", "especialista"):
        dificuldade = "iniciante"

    jogo = CampoMinado(dificuldade=dificuldade)
    ia = IADedutivaCampoMinado()

    while jogo.status == "jogando":
        estado = jogo.estado_publico()
        imprimir_tabuleiro(estado)
        print("\nComandos:")
        print("  r L C  -> Revelar célula (ex: r 5 5)")
        print("  f L C  -> Marcar/Desmarcar bandeira (ex: f 2 3)")
        print("  ia     -> Pedir análise e executar 1 passo da IA")
        print("  auto   -> Deixar a IA resolver o tabuleiro até o fim")
        print("  sair   -> Encerrar")

        comando = input("\n> ").strip().lower().split()
        if not comando:
            continue

        if comando[0] == "sair":
            break
        elif comando[0] == "ia":
            analise = ia.analisar_tabuleiro(estado)
            jogada = analise["melhor_jogada"]
            if jogada:
                print(f"[IA - {jogada['metodo']}] {jogada['explicacao']}")
                r, c = jogada["coord"]
                if jogada["acao"] == "bandeira":
                    jogo.alternar_bandeira(r, c)
                else:
                    jogo.revelar(r, c)
        elif comando[0] == "auto":
            passos = 0
            while jogo.status == "jogando":
                est = jogo.estado_publico()
                analise = ia.analisar_tabuleiro(est)
                jogada = analise["melhor_jogada"]
                if not jogada:
                    break
                passos += 1
                print(f"Passo {passos}: [{jogada['metodo']}] {jogada['explicacao']}")
                r, c = jogada["coord"]
                if jogada["acao"] == "bandeira":
                    jogo.alternar_bandeira(r, c)
                else:
                    jogo.revelar(r, c)
        elif comando[0] in ("r", "f") and len(comando) == 3:
            try:
                r = int(comando[1]) - 1
                c = int(comando[2]) - 1
                if comando[0] == "r":
                    jogo.revelar(r, c)
                else:
                    jogo.alternar_bandeira(r, c)
            except ValueError:
                print("Coordenadas inválidas.")
        else:
            print("Comando não reconhecido.")

    imprimir_tabuleiro(jogo.estado_publico())
    if jogo.status == "vitoria":
        print("\nVITÓRIA! Tabuleiro limpo com sucesso.")
    elif jogo.status == "derrota":
        print("\nBOOM! Uma mina foi detonada.")


if __name__ == "__main__":
    executar_terminal()
