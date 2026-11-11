#!/usr/bin/env bash
# Instala o Spot Bot num servidor Ubuntu e deixa rodando 24h (systemd).
# Uso, no servidor:
#   curl -fsSL https://raw.githubusercontent.com/Felicordeirofcf/spotbot/main/deploy/install.sh | bash
set -euo pipefail

APP_DIR="$HOME/spotbot"
REPO="https://github.com/Felicordeirofcf/spotbot.git"

echo "==> Instalando dependências do sistema"
sudo apt-get update -y -qq
sudo apt-get install -y -qq git python3 python3-venv curl

echo "==> Baixando/atualizando o robô em $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

echo "==> Criando ambiente Python"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi
chmod 600 .env

echo "==> Registrando serviço (liga sozinho e reinicia se cair)"
sudo tee /etc/systemd/system/spotbot.service >/dev/null <<EOF
[Unit]
Description=Spot Bot (Binance)
After=network-online.target
Wants=network-online.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$APP_DIR/.venv/bin/python -m bot ui 8765
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable -q spotbot
sudo systemctl restart spotbot

IP=$(curl -fsS https://api.ipify.org || echo "?")
cat <<MSG

============================================================
 Spot Bot instalado e rodando como serviço.

 1) IP deste servidor (cadastre na chave da Binance):  $IP
 2) Coloque a chave:   nano $APP_DIR/.env
    e depois:          sudo systemctl restart spotbot
 3) Painel, a partir do SEU computador:
      ssh -L 8765:127.0.0.1:8765 $USER@$IP
    e abra http://127.0.0.1:8765 no navegador.

 Ver log:     journalctl -u spotbot -f
 Atualizar:   cd $APP_DIR && git pull && sudo systemctl restart spotbot
============================================================
MSG
