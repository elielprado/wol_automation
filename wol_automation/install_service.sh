#!/bin/bash
# Script para instalar o serviço de monitoramento como um serviço systemd no Linux

# Verifica se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script precisa ser executado como root."
  exit 1
fi

# Diretório atual
CURRENT_DIR=$(pwd)

# Nome do serviço
SERVICE_NAME="power-monitor"

# Usuário atual
CURRENT_USER=$(logname)

# Cria o arquivo de serviço systemd
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=Power Monitor Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/monitor_service.py
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Configura permissões
chmod 644 /etc/systemd/system/$SERVICE_NAME.service

# Recarrega o daemon do systemd
systemctl daemon-reload

# Habilita o serviço para iniciar na inicialização
systemctl enable $SERVICE_NAME.service

# Inicia o serviço
systemctl start $SERVICE_NAME.service

echo "Serviço $SERVICE_NAME instalado e iniciado com sucesso."
echo "Para verificar o status: systemctl status $SERVICE_NAME"
echo "Para parar o serviço: systemctl stop $SERVICE_NAME"
echo "Para iniciar o serviço: systemctl start $SERVICE_NAME"
echo "Para desabilitar na inicialização: systemctl disable $SERVICE_NAME"