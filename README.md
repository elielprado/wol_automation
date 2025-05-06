# WoL Automation

Sistema de gerenciamento remoto de energia para computadores em rede. Permite ligar e desligar computadores remotamente, além de gerenciar o desligamento automático em caso de queda de energia.

## Funcionalidades

- **Wake-on-LAN (WoL)**: Liga computadores remotamente enviando um pacote mágico WoL.
- **Desligamento Remoto**: Desliga computadores Windows e Linux remotamente.
- **Monitoramento de Energia**: Monitora o status da bateria e energia elétrica.
- **Automação**: Desliga automaticamente computadores quando a energia é interrompida.
- **Notificações por Email**: Envia emails sobre eventos relacionados à energia.

## Requisitos

### Requisitos do Sistema
- Python 3.8 ou superior
- Bibliotecas Python (instaladas automaticamente):
  - paramiko (para SSH em Linux)
  - psutil (para monitoramento de bateria)
  - jinja2 (para templates de email)
  - requests (para download do PSTools no Windows)

### Requisitos para Wake-on-LAN
- A placa de rede do computador deve suportar Wake-on-LAN
- WoL deve estar habilitado na BIOS/UEFI
- O computador precisa estar conectado à rede elétrica

### Requisitos para Desligamento Remoto
- **Windows**: Credenciais com privilégios administrativos (usa PSTools, não requer servidor SSH)
- **Linux**: Acesso SSH (chave ou senha) com permissões sudo

## Instalação

### Windows
1. Clone ou baixe este repositório
2. Navegue até a pasta do projeto e acesse a pasta `install`
3. Execute `install_service.bat` como administrador
4. O serviço será instalado como uma tarefa agendada que inicia com o Windows

### Linux
1. Clone ou baixe este repositório
2. Navegue até a pasta do projeto e acesse a pasta `install`
3. Torne o script de instalação executável: `chmod +x install_service.sh`
4. Execute o script como root: `sudo ./install_service.sh`
5. O serviço será instalado como um serviço systemd

## Configuração

### Cadastro de Computadores
Use o menu principal para cadastrar computadores:
```
python main.py
```

Ou via linha de comando:
```
# Listar computadores
python main.py list

# Ligar um computador pelo nome
python main.py wol nome_do_computador

# Desligar um computador pelo nome
python main.py shutdown nome_do_computador
```

### Configuração de Email
Configure os parâmetros de email para receber notificações:
```
python main.py email configure
```

## Estrutura do Projeto

- `main.py`: Interface principal e menu de gerenciamento
- `monitor_service.py`: Serviço de monitoramento de energia
- `remote_poweron.py`: Funções para Wake-on-LAN
- `remote_shutdown.py`: Funções para desligamento remoto
- `email_service.py`: Serviço para envio de notificações por email
- `install/`: Scripts para instalação do serviço
- `assets/`: Recursos utilizados pelo sistema (logo para emails, etc.)
- `templates/`: Templates HTML para emails

## Serviço de Monitoramento

O serviço de monitoramento verifica continuamente o status da energia e bateria, executando ações automáticas:

1. Quando a energia é desconectada:
   - Inicia monitoramento do tempo sem energia
   - Notifica via email (se configurado)

2. Quando o limite de bateria é atingido ou o tempo sem energia excede o configurado:
   - Desliga automaticamente os computadores marcados como `auto_power_off`
   - Envia notificação sobre o desligamento

3. Quando a energia é restaurada:
   - Aguarda o tempo configurado
   - Liga automaticamente os computadores marcados como `auto_power_on`
   - Envia notificação sobre a inicialização

## Solução de Problemas

### Windows
- Verifique o status da tarefa agendada: `schtasks /Query /TN "WoLAutomationService"`
- Consulte o arquivo de log `power_monitor.log` na pasta do projeto

### Linux
- Verifique o status do serviço: `systemctl status wol-automation`
- Consulte os logs do sistema: `journalctl -u wol-automation`

## Notas Importantes

1. **Sistemas Windows**: O PSTools será baixado automaticamente na primeira execução de operação de desligamento remoto. O Windows não requer servidor SSH, pois o sistema usa PSTools para executar operações remotas através do protocolo SMB.

2. **Sistemas Linux**: O desligamento remoto utiliza SSH, certifique-se de que o acesso SSH está configurado corretamente. Para usar chaves SSH, configure o caminho ao cadastrar o computador. A maioria das distribuições Linux já possui servidor SSH disponível.

3. **Wake-on-LAN**: Alguns roteadores podem bloquear pacotes WoL. Consulte a documentação do seu roteador se houver problemas.