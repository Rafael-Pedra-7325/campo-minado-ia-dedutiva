# Campo Minado com IA Dedutiva

Implementação moderna do clássico **Campo Minado** acompanhada de um motor de **Inteligência Artificial Dedutiva e Probabilística** em Python, com interface web interativa em Flask e modo terminal.

## Como a IA Funciona (Sem Trapaças)

A IA recebe exclusivamente o estado público do tabuleiro (nunca acessa as posições ocultas das minas) e toma decisões em 3 camadas:

1. **Dedução de Ponto Único (Lógica Proposicional):** Identifica casas 100% seguras quando todas as minas adjacentes já foram marcadas e casas 100% minadas quando o número de vizinhos ocultos coincide com as minas restantes.
2. **Dedução de Conjuntos (Set-Difference CSP):** Compara restrições sobrepostas de células vizinhas (como padrões `1-2-1` e `1-2-2-1`) para isolar minas ou células seguras que a análise isolada não detectaria.
3. **Backtracking Exato por Componentes Conectados (Probabilidade):** Quando o tabuleiro exige um palpite, particiona a fronteira em componentes independentes e calcula a probabilidade exata de cada célula conter uma mina, sugerindo o lance de menor risco.

## Funcionalidades

- **3 Níveis de Dificuldade:** Iniciante (9×9), Intermediário (16×16) e Especialista (16×30).
- **Copiloto de IA:** Destaque visual de casas seguras e minas garantidas, execução passo a passo e modo **Auto-Resolver** com controle de velocidade.
- **Modo Raio-X Probabilístico:** Sobreposição em tempo real com o percentual de risco de cada célula da fronteira.
- **Console de Dedução:** Explicação em linguagem natural do raciocínio lógico utilizado em cada jogada.

## Executando Localmente

```bash
pip install -r requirements.txt
python app.py
