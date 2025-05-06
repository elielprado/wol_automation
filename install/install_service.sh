#!/bin/bash
# Script para instalar o serviço de monitoramento como um serviço systemd no Linux

# Verifica se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script precisa ser executado como root."
  exit 1
fi

# Diretório atual (instalação)
INSTALL_DIR=$(pwd)
# Diretório do projeto (um nível acima)
PROJECT_DIR=$(dirname "$INSTALL_DIR")

# Nome do serviço
SERVICE_NAME="wol-automation"

# Usuário atual
CURRENT_USER=$(logname || whoami)

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não está instalado. Por favor, instale-o antes de continuar."
    exit 1
fi

# Verifica se os pacotes necessários estão instalados
echo "Verificando dependências..."
python3 -c "import paramiko" 2>/dev/null || {
    echo "Pacote 'paramiko' não encontrado. Tentando instalar..."
    pip3 install paramiko
}

python3 -c "import psutil" 2>/dev/null || {
    echo "Pacote 'psutil' não encontrado. Tentando instalar..."
    pip3 install psutil
}

python3 -c "import jinja2" 2>/dev/null || {
    echo "Pacote 'jinja2' não encontrado. Tentando instalar..."
    pip3 install jinja2
}

# Cria diretórios necessários
mkdir -p "$PROJECT_DIR/assets"
mkdir -p "$PROJECT_DIR/templates"

# Cria o arquivo de serviço systemd
cat > /etc/systemd/system/$SERVICE_NAME.service <<EOF
[Unit]
Description=WoL Automation - Serviço de Monitoramento de Energia
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/monitor_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
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
echo "Para visualizar logs: journalctl -u $SERVICE_NAME"
echo "Para parar o serviço: systemctl stop $SERVICE_NAME"
echo "Para iniciar o serviço: systemctl start $SERVICE_NAME"
echo "Para desabilitar na inicialização: systemctl disable $SERVICE_NAME"

# Instruções adicionais sobre recursos específicos do Linux
echo ""
echo "Nota: Para o Linux, o desligamento remoto usa SSH em vez de PSTools."
echo "Certifique-se de que suas chaves SSH estejam configuradas corretamente ou"
echo "que as senhas sejam fornecidas para os computadores remotos."