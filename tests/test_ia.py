import unittest
from ia import IADedutivaCampoMinado
from jogo import CampoMinado


class TestIADedutivaCampoMinado(unittest.TestCase):
    def setUp(self):
        self.ia = IADedutivaCampoMinado()

    def test_primeiro_clique_sempre_seguro(self):
        for seed in range(15):
            jogo = CampoMinado(dificuldade="iniciante", seed=seed)
            estado = jogo.revelar(4, 4)
            self.assertEqual(estado["status"], "jogando")
            self.assertEqual(estado["grade"][4][4], 0)

    def test_deducao_simples_minas_e_seguras(self):
        # Tabuleiro 3x3 customizado onde (1,1) = 1 e apenas (0,0) está oculta
        estado = {
            "linhas": 3,
            "colunas": 3,
            "minas_restantes": 1,
            "status": "jogando",
            "grade": [
                [None, 1, 0],
                [1, 1, 0],
                [0, 0, 0],
            ],
        }
        analise = self.ia.analisar_tabuleiro(estado)
        minas = [tuple(item["coord"]) for item in analise["minas"]]
        self.assertIn((0, 0), minas)
        self.assertEqual(analise["melhor_jogada"]["acao"], "bandeira")
        self.assertEqual(analise["melhor_jogada"]["coord"], [0, 0])

        # Agora com a bandeira marcada em (0,0), (1,0) que tem valor 1 libera (2,0)
        estado_com_bandeira = {
            "linhas": 3,
            "colunas": 3,
            "minas_restantes": 0,
            "status": "jogando",
            "grade": [
                ["F", 1, 0],
                [1, 1, 0],
                [None, 0, 0],
            ],
        }
        analise2 = self.ia.analisar_tabuleiro(estado_com_bandeira)
        seguras = [tuple(item["coord"]) for item in analise2["seguras"]]
        self.assertIn((2, 0), seguras)
        self.assertEqual(analise2["melhor_jogada"]["acao"], "revelar")
        self.assertEqual(analise2["melhor_jogada"]["coord"], [2, 0])

    def test_deducao_conjuntos_padrao_1_2_1(self):
        # Padrão clássico 1-2-1 na linha 1; linha 0 oculta.
        # Nenhuma célula isolada resolve o padrão, mas a dedução de conjuntos
        # prova que (0,0) e (0,2) são minas e (0,1) é 100% segura.
        estado = {
            "linhas": 3,
            "colunas": 3,
            "minas_restantes": 2,
            "status": "jogando",
            "grade": [
                [None, None, None],
                [1, 2, 1],
                [0, 0, 0],
            ],
        }
        analise = self.ia.analisar_tabuleiro(estado)
        minas = {tuple(item["coord"]) for item in analise["minas"]}
        seguras = {tuple(item["coord"]) for item in analise["seguras"]}

        self.assertEqual(minas, {(0, 0), (0, 2)})
        self.assertIn((0, 1), seguras)

    def test_calculo_probabilidade_exata_em_ambiguidade(self):
        # Situação 50/50 simétrica: (1,0) = 1 com duas casas ocultas (0,0) e (0,1)
        estado = {
            "linhas": 2,
            "colunas": 2,
            "minas_restantes": 1,
            "status": "jogando",
            "grade": [
                [None, None],
                [1, 1],
            ],
        }
        analise = self.ia.analisar_tabuleiro(estado)
        self.assertEqual(analise["seguras"], [])
        self.assertEqual(analise["minas"], [])
        self.assertAlmostEqual(analise["probabilidades"]["0,0"], 0.5)
        self.assertAlmostEqual(analise["probabilidades"]["0,1"], 0.5)
        self.assertEqual(analise["melhor_jogada"]["metodo"], "probabilidade")

    def test_auto_resolucao_partida_iniciante(self):
        jogo = CampoMinado(dificuldade="iniciante", seed=42)
        passos = 0
        while jogo.status == "jogando" and passos < 200:
            analise = self.ia.analisar_tabuleiro(jogo.estado_publico())
            jogada = analise["melhor_jogada"]
            self.assertIsNotNone(jogada)
            r, c = jogada["coord"]
            if jogada["acao"] == "bandeira":
                jogo.alternar_bandeira(r, c)
            else:
                jogo.revelar(r, c)
            passos += 1

        self.assertEqual(jogo.status, "vitoria")


if __name__ == "__main__":
    unittest.main()
