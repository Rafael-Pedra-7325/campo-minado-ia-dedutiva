```python
import random
from typing import Dict, List, Optional, Set, Tuple

Coord = Tuple[int, int]

DIFICULDADES: Dict[str, Dict[str, int]] = {
    "iniciante": {"linhas": 9, "colunas": 9, "minas": 10},
    "intermediario": {"linhas": 16, "colunas": 16, "minas": 40},
    "especialista": {"linhas": 16, "colunas": 30, "minas": 99},
}


class CampoMinado:
    """Gerencia o estado, regras e transições de uma partida de Campo Minado."""

    def __init__(self, dificuldade: str = "iniciante", seed: Optional[int] = None):
        config = DIFICULDADES.get(dificuldade, DIFICULDADES["iniciante"])
        self.dificuldade: str = dificuldade if dificuldade in DIFICULDADES else "iniciante"
        self.linhas: int = config["linhas"]
        self.colunas: int = config["colunas"]
        self.total_minas: int = config["minas"]
        self._rng = random.Random(seed)

        self.minas: Set[Coord] = set()
        self.reveladas: Set[Coord] = set()
        self.bandeiras: Set[Coord] = set()
        self.numeros: List[List[int]] = [
            [0 for _ in range(self.colunas)] for _ in range(self.linhas)
        ]

        self.primeiro_clique: bool = True
        self.status: str = "jogando"  # "jogando", "vitoria", "derrota"
        self.mina_explodida: Optional[Coord] = None

    def dentro_dos_limites(self, r: int, c: int) -> bool:
        return 0 <= r < self.linhas and 0 <= c < self.colunas

    def vizinhos(self, r: int, c: int) -> List[Coord]:
        resultado: List[Coord] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self.dentro_dos_limites(nr, nc):
                    resultado.append((nr, nc))
        return resultado

    def _gerar_minas(self, seguro_r: int, seguro_c: int) -> None:
        """Posiciona as minas garantindo que o primeiro clique e seus vizinhos sejam seguros."""
        zona_segura = {(seguro_r, seguro_c)} | set(self.vizinhos(seguro_r, seguro_c))
        candidatas = [
            (r, c)
            for r in range(self.linhas)
            for c in range(self.colunas)
            if (r, c) not in zona_segura
        ]

        if len(candidatas) < self.total_minas:
            candidatas = [
                (r, c)
                for r in range(self.linhas)
                for c in range(self.colunas)
                if (r, c) != (seguro_r, seguro_c)
            ]

        self.minas = set(self._rng.sample(candidatas, self.total_minas))
        self._calcular_numeros()

    def _calcular_numeros(self) -> None:
        for r in range(self.linhas):
            for c in range(self.colunas):
                if (r, c) in self.minas:
                    self.numeros[r][c] = -1
                else:
                    self.numeros[r][c] = sum(
                        1 for viz in self.vizinhos(r, c) if viz in self.minas
                    )

    def revelar(self, r: int, c: int) -> Dict:
        """Revela uma célula (ou executa chord-click em número já revelado)."""
        if self.status != "jogando" or not self.dentro_dos_limites(r, c):
            return self.estado_publico()

        coord = (r, c)
        if coord in self.bandeiras:
            return self.estado_publico()

        if self.primeiro_clique:
            self._gerar_minas(r, c)
            self.primeiro_clique = False

        # Chord-click: clicar em número revelado cujas bandeiras vizinhas batem com o valor
        if coord in self.reveladas:
            valor = self.numeros[r][c]
            if valor > 0:
                viz = self.vizinhos(r, c)
                qtd_bandeiras = sum(1 for v in viz if v in self.bandeiras)
                if qtd_bandeiras == valor:
                    for vr, vc in viz:
                        if (vr, vc) not in self.bandeiras and (vr, vc) not in self.reveladas:
                            self._revelar_celula_unica(vr, vc)
                            if self.status == "derrota":
                                break
            self._verificar_vitoria()
            return self.estado_publico()

        self._revelar_celula_unica(r, c)
        self._verificar_vitoria()
        return self.estado_publico()

    def _revelar_celula_unica(self, r: int, c: int) -> None:
        coord = (r, c)
        if coord in self.reveladas or coord in self.bandeiras:
            return

        if coord in self.minas:
            self.status = "derrota"
            self.mina_explodida = coord
            self.reveladas.add(coord)
            return

        # Flood-fill iterativo para abrir áreas vazias (valor 0)
        pilha = [coord]
        while pilha:
            atual_r, atual_c = pilha.pop()
            atual = (atual_r, atual_c)
            if atual in self.reveladas or atual in self.bandeiras:
                continue
            self.reveladas.add(atual)
            if self.numeros[atual_r][atual_c] == 0:
                for vr, vc in self.vizinhos(atual_r, atual_c):
                    viz = (vr, vc)
                    if viz not in self.reveladas and viz not in self.bandeiras:
                        pilha.append(viz)

    def alternar_bandeira(self, r: int, c: int) -> Dict:
        """Marca ou desmarca uma bandeira em uma célula não revelada."""
        if self.status != "jogando" or not self.dentro_dos_limites(r, c):
            return self.estado_publico()

        coord = (r, c)
        if coord in self.reveladas:
            return self.estado_publico()

        if coord in self.bandeiras:
            self.bandeiras.remove(coord)
        else:
            self.bandeiras.add(coord)

        return self.estado_publico()

    def _verificar_vitoria(self) -> None:
        if self.status != "jogando":
            return
        total_seguras = (self.linhas * self.colunas) - self.total_minas
        if len(self.reveladas) == total_seguras:
            self.status = "vitoria"
            # Marca automaticamente as minas restantes ao vencer
            self.bandeiras = set(self.minas)

    def estado_publico(self) -> Dict:
        """
        Retorna apenas as informações visíveis ao jogador e à IA.
        Nunca expõe minas ocultas enquanto o jogo está em andamento.
        """
        grade: List[List[Optional[object]]] = []
        for r in range(self.linhas):
            linha: List[Optional[object]] = []
            for c in range(self.colunas):
                coord = (r, c)
                if coord in self.reveladas:
                    if coord in self.minas:
                        linha.append("M")
                    else:
                        linha.append(self.numeros[r][c])
                elif coord in self.bandeiras:
                    if self.status == "derrota" and coord not in self.minas:
                        linha.append("X")  # Bandeira incorreta revelada na derrota
                    else:
                        linha.append("F")
                else:
                    if self.status == "derrota" and coord in self.minas:
                        linha.append("M")
                    else:
                        linha.append(None)
            grade.append(linha)

        return {
            "dificuldade": self.dificuldade,
            "linhas": self.linhas,
            "colunas": self.colunas,
            "total_minas": self.total_minas,
            "minas_restantes": self.total_minas - len(self.bandeiras),
            "status": self.status,
            "primeiro_clique": self.primeiro_clique,
            "mina_explodida": list(self.mina_explodida) if self.mina_explodida else None,
            "reveladas_count": len(self.reveladas),
            "total_seguras": (self.linhas * self.colunas) - self.total_minas,
            "grade": grade,
        }
