from collections import defaultdict, deque
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

Coord = Tuple[int, int]
Restricao = Tuple[Coord, FrozenSet[Coord], int]  # (origem, celulas_ocultas, minas_faltando)


class IADedutivaCampoMinado:
    """
    Motor de IA em 3 níveis para Campo Minado (100% livre de trapaças):
      1. Dedução de Ponto Único (Lógica Proposicional básica)
      2. Dedução de Conjuntos (Diferença entre restrições sobrepostas / CSP)
      3. Backtracking Exato em Componentes Conectados (Análise Probabilística)
    """

    LIMITE_EXATO_COMPONENTE = 18

    def _vizinhos(self, r: int, c: int, linhas: int, colunas: int) -> List[Coord]:
        res: List[Coord] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < linhas and 0 <= nc < colunas:
                    res.append((nr, nc))
        return res

    def analisar_tabuleiro(self, estado: Dict) -> Dict:
        linhas: int = estado["linhas"]
        colunas: int = estado["colunas"]
        grade = estado["grade"]
        minas_restantes: int = max(0, estado["minas_restantes"])
        status: str = estado["status"]

        if status != "jogando":
            return {
                "seguras": [],
                "minas": [],
                "probabilidades": {},
                "melhor_jogada": None,
                "aviso": None,
            }

        # Caso 0: Tabuleiro totalmente fechado (abertura estratégica no centro)
        celulas_reveladas = [
            (r, c)
            for r in range(linhas)
            for c in range(colunas)
            if isinstance(grade[r][c], int)
        ]
        if not celulas_reveladas:
            centro = (linhas // 2, colunas // 2)
            return {
                "seguras": [
                    {
                        "coord": list(centro),
                        "metodo": "abertura",
                        "explicacao": f"Abertura estratégica no centro ({centro[0]+1},{centro[1]+1}) para maximizar expansão.",
                    }
                ],
                "minas": [],
                "probabilidades": {f"{centro[0]},{centro[1]}": 0.0},
                "melhor_jogada": {
                    "acao": "revelar",
                    "coord": list(centro),
                    "probabilidade_mina": 0.0,
                    "metodo": "abertura",
                    "explicacao": f"Abertura estratégica no centro ({centro[0]+1},{centro[1]+1}) para maximizar área segura.",
                },
                "aviso": None,
            }

        seguras_map: Dict[Coord, Tuple[str, str]] = {}
        minas_map: Dict[Coord, Tuple[str, str]] = {}
        restricoes: List[Restricao] = []
        aviso: Optional[str] = None

        # =====================================================================
        # CAMADA 1: Dedução de Ponto Único & Coleta de Restrições
        # =====================================================================
        for r, c in celulas_reveladas:
            valor = grade[r][c]
            if valor <= 0:
                continue

            viz = self._vizinhos(r, c, linhas, colunas)
            ocultos = [v for v in viz if grade[v[0]][v[1]] is None]
            bandeiras = [v for v in viz if grade[v[0]][v[1]] == "F"]
            faltando = valor - len(bandeiras)

            if faltando < 0 or faltando > len(ocultos):
                aviso = (
                    f"Inconsistência detectada ao redor de ({r+1},{c+1}). "
                    "Verifique se há alguma bandeira marcada incorretamente."
                )
                continue

            if not ocultos:
                continue

            if faltando == 0:
                for cel in ocultos:
                    if cel not in seguras_map:
                        seguras_map[cel] = (
                            "deducao_simples",
                            f"Célula ({r+1},{c+1}) já possui todas as {valor} mina(s) marcada(s); ({cel[0]+1},{cel[1]+1}) é 100% segura.",
                        )
            elif faltando == len(ocultos):
                for cel in ocultos:
                    if cel not in minas_map:
                        minas_map[cel] = (
                            "deducao_simples",
                            f"Célula ({r+1},{c+1}) precisa de {faltando} mina(s) e só restam {len(ocultos)} casa(s) oculta(s); ({cel[0]+1},{cel[1]+1}) é 100% mina.",
                        )
            else:
                restricoes.append(((r, c), frozenset(ocultos), faltando))

        # =====================================================================
        # CAMADA 2: Dedução de Conjuntos (Set-Difference / Subconjuntos CSP)
        # =====================================================================
        # Refina restrições removendo células já deduzidas na Camada 1
        restricoes_refinadas: List[Restricao] = []
        for origem, conj, faltando in restricoes:
            novo_conj = frozenset(
                cel for cel in conj if cel not in seguras_map and cel not in minas_map
            )
            novo_faltando = faltando - sum(1 for cel in conj if cel in minas_map)
            if novo_conj and 0 < novo_faltando < len(novo_conj):
                restricoes_refinadas.append((origem, novo_conj, novo_faltando))
            elif novo_conj and novo_faltando == 0:
                for cel in novo_conj:
                    seguras_map.setdefault(
                        cel,
                        (
                            "deducao_conjuntos",
                            f"Dedução encadeada a partir de ({origem[0]+1},{origem[1]+1}) libera ({cel[0]+1},{cel[1]+1}) como segura.",
                        ),
                    )
            elif novo_conj and novo_faltando == len(novo_conj):
                for cel in novo_conj:
                    minas_map.setdefault(
                        cel,
                        (
                            "deducao_conjuntos",
                            f"Dedução encadeada a partir de ({origem[0]+1},{origem[1]+1}) confirma ({cel[0]+1},{cel[1]+1}) como mina.",
                        ),
                    )

        # Compara pares de restrições próximas (distância de Chebyshev <= 2)
        n_rest = len(restricoes_refinadas)
        for i in range(n_rest):
            orig1, conj1, k1 = restricoes_refinadas[i]
            for j in range(n_rest):
                if i == j:
                    continue
                orig2, conj2, k2 = restricoes_refinadas[j]
                if abs(orig1[0] - orig2[0]) > 2 or abs(orig1[1] - orig2[1]) > 2:
                    continue

                if conj1.issubset(conj2) and len(conj1) < len(conj2):
                    diff = conj2 - conj1
                    dk = k2 - k1
                    if dk == 0:
                        for cel in diff:
                            seguras_map.setdefault(
                                cel,
                                (
                                    "deducao_conjuntos",
                                    f"Dedução de Conjuntos entre ({orig1[0]+1},{orig1[1]+1}) e ({orig2[0]+1},{orig2[1]+1}) isola ({cel[0]+1},{cel[1]+1}) como 100% segura.",
                                ),
                            )
                    elif dk == len(diff):
                        for cel in diff:
                            minas_map.setdefault(
                                cel,
                                (
                                    "deducao_conjuntos",
                                    f"Dedução de Conjuntos entre ({orig1[0]+1},{orig1[1]+1}) e ({orig2[0]+1},{orig2[1]+1}) exige mina em ({cel[0]+1},{cel[1]+1}).",
                                ),
                            )

        # =====================================================================
        # CAMADA 3: Backtracking Exato & Mapa Probabilístico da Fronteira
        # =====================================================================
        probabilidades: Dict[Coord, float] = {}
        for cel in seguras_map:
            probabilidades[cel] = 0.0
        for cel in minas_map:
            probabilidades[cel] = 1.0

        # Prepara restrições residuais para células da fronteira ainda incertas
        rest_residuais: List[Tuple[List[Coord], int]] = []
        celulas_fronteira_incertas: Set[Coord] = set()

        for _, conj, faltando in restricoes_refinadas:
            incertas = [
                cel for cel in conj if cel not in seguras_map and cel not in minas_map
            ]
            k_res = faltando - sum(1 for cel in conj if cel in minas_map)
            if incertas and 0 <= k_res <= len(incertas):
                if k_res == 0:
                    for cel in incertas:
                        seguras_map.setdefault(
                            cel,
                            (
                                "deducao_conjuntos",
                                f"Propagação de restrições confirma ({cel[0]+1},{cel[1]+1}) como 100% segura.",
                            ),
                        )
                        probabilidades[cel] = 0.0
                elif k_res == len(incertas):
                    for cel in incertas:
                        minas_map.setdefault(
                            cel,
                            (
                                "deducao_conjuntos",
                                f"Propagação de restrições confirma ({cel[0]+1},{cel[1]+1}) como 100% mina.",
                            ),
                        )
                        probabilidades[cel] = 1.0
                else:
                    rest_residuais.append((incertas, k_res))
                    celulas_fronteira_incertas.update(incertas)

        minas_nao_marcadas_max = max(0, minas_restantes - len(minas_map))
        componentes = self._agrupar_componentes(celulas_fronteira_incertas, rest_residuais)

        for comp_vars, comp_rest in componentes:
            if len(comp_vars) <= self.LIMITE_EXATO_COMPONENTE:
                probs_comp = self._resolver_componente_exato(
                    comp_vars, comp_rest, minas_nao_marcadas_max
                )
            else:
                probs_comp = self._estimar_componente_heuristico(comp_vars, comp_rest)

            for cel, prob in probs_comp.items():
                probabilidades[cel] = round(prob, 4)
                if prob == 0.0 and cel not in seguras_map:
                    seguras_map[cel] = (
                        "csp_exato",
                        f"Análise combinatória (CSP) provou 0% de chance de mina em ({cel[0]+1},{cel[1]+1}).",
                    )
                elif prob == 1.0 and cel not in minas_map:
                    minas_map[cel] = (
                        "csp_exato",
                        f"Análise combinatória (CSP) provou 100% de chance de mina em ({cel[0]+1},{cel[1]+1}).",
                    )

        # Calcula probabilidade de fundo para células ocultas longe da fronteira
        todas_ocultas = [
            (r, c)
            for r in range(linhas)
            for c in range(colunas)
            if grade[r][c] is None
        ]
        interior = [cel for cel in todas_ocultas if cel not in probabilidades]
        minas_esperadas_fronteira = sum(probabilidades.values())
        minas_interior = max(0.0, minas_restantes - minas_esperadas_fronteira)
        prob_interior = (
            round(min(1.0, minas_interior / len(interior)), 4) if interior else 0.0
        )

        # =====================================================================
        # Escolha da Melhor Jogada
        # =====================================================================
        melhor_jogada = self._selecionar_melhor_jogada(
            seguras_map=seguras_map,
            minas_map=minas_map,
            probabilidades=probabilidades,
            interior=interior,
            prob_interior=prob_interior,
            linhas=linhas,
            colunas=colunas,
        )

        seguras_lista = [
            {"coord": [r, c], "metodo": metodo, "explicacao": exp}
            for (r, c), (metodo, exp) in sorted(seguras_map.items())
        ]
        minas_lista = [
            {"coord": [r, c], "metodo": metodo, "explicacao": exp}
            for (r, c), (metodo, exp) in sorted(minas_map.items())
        ]
        probs_serializadas = {
            f"{r},{c}": prob for (r, c), prob in sorted(probabilidades.items())
        }

        return {
            "seguras": seguras_lista,
            "minas": minas_lista,
            "probabilidades": probs_serializadas,
            "probabilidade_interior": prob_interior,
            "melhor_jogada": melhor_jogada,
            "aviso": aviso,
        }

    def _agrupar_componentes(
        self,
        variaveis: Set[Coord],
        restricoes: List[Tuple[List[Coord], int]],
    ) -> List[Tuple[List[Coord], List[Tuple[List[Coord], int]]]]:
        """Divide variáveis da fronteira em subproblemas independentes."""
        if not variaveis:
            return []

        adj: Dict[Coord, Set[Coord]] = defaultdict(set)
        for escopo, _ in restricoes:
            for u in escopo:
                for v in escopo:
                    if u != v:
                        adj[u].add(v)

        visitados: Set[Coord] = set()
        componentes: List[Tuple[List[Coord], List[Tuple[List[Coord], int]]]] = []

        for var in sorted(variaveis):
            if var in visitados:
                continue
            comp_vars: List[Coord] = []
            fila = deque([var])
            visitados.add(var)
            while fila:
                atual = fila.popleft()
                comp_vars.append(atual)
                for viz in adj[atual]:
                    if viz not in visitados:
                        visitados.add(viz)
                        fila.append(viz)

            comp_set = set(comp_vars)
            comp_rest = [
                (escopo, k)
                for escopo, k in restricoes
                if any(v in comp_set for v in escopo)
            ]
            componentes.append((comp_vars, comp_rest))

        return componentes

    def _resolver_componente_exato(
        self,
        variaveis: List[Coord],
        restricoes: List[Tuple[List[Coord], int]],
        max_minas: int,
    ) -> Dict[Coord, float]:
        """Enumera todas as atribuições válidas (0 ou 1) via backtracking com poda."""
        # Ordena variáveis por grau de participação para podar ramos inválidos cedo
        freq: Dict[Coord, int] = defaultdict(int)
        for escopo, _ in restricoes:
            for v in escopo:
                freq[v] += 1
        vars_ordenadas = sorted(variaveis, key=lambda v: -freq[v])
        idx_map = {v: i for i, v in enumerate(vars_ordenadas)}
        n = len(vars_ordenadas)

        rest_idx: List[Tuple[List[int], int]] = [
            ([idx_map[v] for v in escopo], k) for escopo, k in restricoes
        ]

        # Pré-calcula em qual índice cada restrição fica totalmente atribuída
        gatilhos: Dict[int, List[Tuple[List[int], int]]] = defaultdict(list)
        for escopo_i, k in rest_idx:
            gatilhos[max(escopo_i)].append((escopo_i, k))

        atribuicao = [0] * n
        contagem_minas = [0] * n
        total_solucoes = 0

        def backtrack(pos: int, minas_usadas: int) -> None:
            nonlocal total_solucoes
            if minas_usadas > max_minas:
                return
            if pos == n:
                total_solucoes += 1
                for i in range(n):
                    if atribuicao[i] == 1:
                        contagem_minas[i] += 1
                return

            for val in (0, 1):
                if minas_usadas + val > max_minas:
                    continue
                atribuicao[pos] = val

                valido = True
                for escopo_i, k in gatilhos[pos]:
                    soma = sum(atribuicao[idx] for idx in escopo_i)
                    if soma != k:
                        valido = False
                        break

                if valido:
                    backtrack(pos + 1, minas_usadas + val)

        backtrack(0, 0)

        if total_solucoes == 0:
            return self._estimar_componente_heuristico(variaveis, restricoes)

        return {
            vars_ordenadas[i]: contagem_minas[i] / total_solucoes for i in range(n)
        }

    def _estimar_componente_heuristico(
        self,
        variaveis: List[Coord],
        restricoes: List[Tuple[List[Coord], int]],
    ) -> Dict[Coord, float]:
        """Fallback rápido para fronteiras muito grandes (>18 células conectadas)."""
        somas: Dict[Coord, float] = defaultdict(float)
        pesos: Dict[Coord, int] = defaultdict(int)
        for escopo, k in restricoes:
            p = k / len(escopo)
            for v in escopo:
                somas[v] += p
                pesos[v] += 1
        return {v: somas[v] / pesos[v] for v in variaveis}

    def _selecionar_melhor_jogada(
        self,
        seguras_map: Dict[Coord, Tuple[str, str]],
        minas_map: Dict[Coord, Tuple[str, str]],
        probabilidades: Dict[Coord, float],
        interior: List[Coord],
        prob_interior: float,
        linhas: int,
        colunas: int,
    ) -> Optional[Dict]:
        # 1. Prioridade máxima: abrir uma célula 100% segura deduzida
        if seguras_map:
            cel = sorted(seguras_map.keys())[0]
            metodo, exp = seguras_map[cel]
            return {
                "acao": "revelar",
                "coord": list(cel),
                "probabilidade_mina": 0.0,
                "metodo": metodo,
                "explicacao": exp,
            }

        # 2. Segunda prioridade: marcar uma mina 100% garantida com bandeira
        if minas_map:
            cel = sorted(minas_map.keys())[0]
            metodo, exp = minas_map[cel]
            return {
                "acao": "bandeira",
                "coord": list(cel),
                "probabilidade_mina": 1.0,
                "metodo": metodo,
                "explicacao": exp,
            }

        # 3. Terceira prioridade: palpite calculado de menor risco
        candidatos: List[Tuple[float, int, Coord]] = []

        def bonus_canto(c: Coord) -> int:
            # Prefere cantos e bordas em empates probabilísticos
            eh_borda_r = c[0] in (0, linhas - 1)
            eh_borda_c = c[1] in (0, colunas - 1)
            if eh_borda_r and eh_borda_c:
                return 0
            if eh_borda_r or eh_borda_c:
                return 1
            return 2

        for cel, prob in probabilidades.items():
            candidatos.append((prob, bonus_canto(cel), cel))

        if interior:
            melhor_int = min(interior, key=lambda c: (bonus_canto(c), c))
            candidatos.append((prob_interior, bonus_canto(melhor_int), melhor_int))

        if not candidatos:
            return None

        candidatos.sort(key=lambda item: (item[0], item[1], item[2]))
        menor_prob, _, escolhida = candidatos[0]
        pct = round(menor_prob * 100, 1)

        return {
            "acao": "revelar",
            "coord": list(escolhida),
            "probabilidade_mina": menor_prob,
            "metodo": "probabilidade",
            "explicacao": (
                f"Sem dedução 100% determinística disponível. Melhor lance probabilístico em "
                f"({escolhida[0]+1},{escolhida[1]+1}) com apenas {pct}% de risco de mina."
            ),
        }
