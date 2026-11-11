# Spot Bot — robô de trade spot para Binance (com painel)

Robô que procura entradas em **spot** com alvo de **+2% líquido** (já descontadas as taxas),
coloca **alvo e stop como ordem OCO na própria Binance** e mostra tudo em um painel web local
configurável.

> ⚠️ **Leia antes de usar dinheiro de verdade.** Nenhuma estratégia garante lucro. Um alvo de 2%
> com stop de 1,5% só dá lucro se acertar mais de ~45% das vezes (depois das taxas). Isso varia com
> o mercado. Rode **backtest → simulação → testnet → valor pequeno**, nessa ordem. Use só dinheiro que
> você pode perder.

## Como rodar (3 minutos)

Requisitos: Python 3.10+.

```bash
git clone https://github.com/Felicordeirofcf/spotbot.git && cd spotbot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edite e coloque sua chave (opcional para simular)
python -m bot ui            # abre http://127.0.0.1:8765
```

**Windows (PowerShell):** rode um comando por vez, numa pasta sua (não em `C:\WINDOWS\system32`):

```powershell
cd $HOME\Documents
git clone https://github.com/Felicordeirofcf/spotbot.git
cd spotbot
.\iniciar.bat
```

Ou dê dois cliques em `iniciar.bat` no Explorer. É preciso ter o Python 3.10+ instalado, com a opção
"Add python.exe to PATH" marcada.

Sem chave da API você já consegue: varrer o mercado, rodar backtest e operar em **simulação** (os
dados públicos de mercado não exigem chave).

## O painel

- **Oportunidades de entrada**: pares que passam em todos os filtros, com o motivo, ordenados pelo score. O botão "Entrar" faz a entrada manual.
- **Posições abertas**: entrada, alvo, stop e tempo, com o botão "Fechar" (vende a mercado).
- **Configuração**: alvo, stop, taxa, risco por operação, teto por operação, número de posições, perda máxima diária, pares, intervalo, entradas automáticas sim/não, simulação/real, testnet/produção. Tudo é salvo em `settings.json`.
- **Backtest**: testa a estratégia em até 365 dias de histórico real dos pares escolhidos.
- **Log** e **Histórico**, com resultado em USDT e em %.

Para ativar o modo REAL é preciso digitar `REAL` para confirmar.

## A estratégia: "comprar o recuo na tendência de alta"

Para alvos curtos (2%), o que costuma funcionar melhor é entrar **a favor da tendência maior**, logo
após uma **correção curta**, em ativos **líquidos** com volatilidade suficiente para andar 2% em
horas, mas não tão alta a ponto de o stop ser atingido por ruído.

| Filtro | Regra |
|---|---|
| Liquidez | top N pares em USDT por volume 24h (≥ 50 mi), sem stablecoins e sem tokens alavancados |
| Tendência (1h) | preço > EMA200, EMA50 > EMA200 e EMA50 subindo |
| Volatilidade (1h) | ATR14 entre 0,6% e 5% do preço |
| Recuo (15m) | RSI14 < 35 nas últimas 8 velas **ou** toque na Bollinger inferior |
| Gatilho (15m) | vela fechada de alta, RSI virando para cima e ainda < 55 |
| Espaço | a máxima das últimas 48h já está acima do alvo |
| Não esticado | no máximo 3% acima da EMA50 de 1h |

**Saída**: OCO com alvo `LIMIT_MAKER` (que paga taxa de maker) e `STOP_LOSS_LIMIT`, mais um
fechamento por tempo (padrão: 48h).

**Tamanho da posição**: `saldo × risco% ÷ stop%`, limitado pelo teto por operação. Com saldo de
1000, risco de 1% e stop de 1,5%, a perda máxima por operação fica em ~10 USDT.

**Travas**: limite de perda diária, máximo de posições simultâneas, mínimo de notional da Binance e
venda a mercado de emergência se a OCO falhar.

## Segurança da sua chave da Binance

1. Crie a chave com **Leitura + Spot Trading** e **saque DESABILITADO**.
2. Restrinja por **IP** (o IP da máquina que roda o robô).
3. A chave fica só no `.env` (ignorado pelo git) e nunca vai para o navegador.
4. O botão "Validar chave" avisa se a chave permitir saque.
5. O painel escuta só em `127.0.0.1` e exige um token por sessão para qualquer ação.

## Linha de comando

```bash
python -m bot scan                              # oportunidades agora
python -m bot backtest BTCUSDT,ETHUSDT,SOLUSDT 90
python -m bot run                               # robô sem painel
python -m bot check                             # valida a chave
python -m unittest discover tests               # testes
```

## Painel público de sinais na Vercel

O repositório também publica na Vercel uma **página só de leitura** (`public/index.html` +
`api/signals.py`, região São Paulo `gru1`): ela varre os 40 pares mais líquidos e mostra os sinais.
**Não usa chave da API e não envia ordens.** O CDN guarda o resultado por 2 minutos. Parâmetros
opcionais: `/api/signals?tp=2&sl=1.5`.

Deploy: em vercel.com → *Add New → Project* → importe `spotbot` → *Deploy* (não precisa de
variável de ambiente).

## Rodar 24h num servidor (sem deixar o PC ligado)

Use um servidor Ubuntu **no Brasil** (a Binance bloqueia IPs dos EUA). A opção gratuita é a
**Oracle Cloud Always Free**, região *Brazil East (São Paulo)*, com IP fixo. Também servem VPS pagas
em São Paulo (Vultr, AWS Lightsail, Magalu Cloud).

No servidor, rode:

```bash
curl -fsSL https://raw.githubusercontent.com/Felicordeirofcf/spotbot/main/deploy/install.sh | bash
```

O script instala tudo e registra o serviço `spotbot`, que liga junto com o servidor e reinicia
sozinho se cair. Se o robô estava rodando antes de um reinício, ele volta a rodar sozinho. No final, o script mostra o IP para
cadastrar na chave da Binance.

O painel **não fica exposto na internet**. Para acessá-lo, abra um túnel SSH a partir do seu PC:

```bash
ssh -L 8765:127.0.0.1:8765 ubuntu@IP_DO_SERVIDOR
```

e acesse http://127.0.0.1:8765. Depois de iniciar o robô no painel, você pode fechar o túnel e
desligar o PC.

| Tarefa | Comando no servidor |
|---|---|
| Editar a chave | `nano ~/spotbot/.env` e `sudo systemctl restart spotbot` |
| Ver o log ao vivo | `journalctl -u spotbot -f` |
| Atualizar o robô | `cd ~/spotbot && git pull && sudo systemctl restart spotbot` |

## Por que não na Vercel

A Vercel só roda funções curtas e não tem processo contínuo nem IP fixo, por isso ela hospeda
apenas o painel público de sinais.
