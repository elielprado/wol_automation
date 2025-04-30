# Sistema de Gerenciamento de Energia Remota

Este sistema permite gerenciar o desligamento e ligamento automático de computadores remotos com base no status da bateria de um notebook. Foi projetado para proteger seus servidores e computadores em caso de queda de energia, evitando desligamentos abruptos.

## Funcionalidades

- **Wake-on-LAN**: Ligar computadores remotamente via rede
- **Desligamento remoto**: Desligar computadores Windows (via PSTools) e Linux (via SSH)
- **Monitoramento automático**: Serviço que monitora o status da bateria do notebook
- **Desligamento de emergência**: Desliga computadores automaticamente quando a energia cai
- **Religamento automático**: Liga computadores automaticamente quando a energia é restaurada
- **Interface de linha de comando**: Acesso direto às funcionalidades via argumentos

## Requisitos

- Python 3.13 ou superior
- Bibliotecas Python: requests, paramiko, psutil
- Para Windows: PSTools (baixado automaticamente)
- Para Linux: Acesso SSH aos computadores
- Wake-on-LAN habilitado nas máquinas a serem ligadas
- Privilégios de administrador nas máquinas remotas

## Instalação

1. Clone ou baixe este repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Configure seus computadores no sistema

## Uso

### Menu Interativo

Para iniciar o menu interativo:

```
python main.py
```

### Comandos Diretos

Para ligar um computador:
```
python main.py wol NOME_DO_COMPUTADOR
```
ou
```
python remote_poweron.py NOME_DO_COMPUTADOR
```

Para desligar um computador:
```
python main.py shutdown NOME_DO_COMPUTADOR
```
ou
```
python remote_shutdown.py NOME_DO_COMPUTADOR
```

Para ligar todos os computadores marcados para auto power on:
```
python remote_poweron.py --auto
```

Para desligar todos os computadores marcados para auto power off:
```
python remote_shutdown.py --auto
```

Para listar todos os computadores:
```
python main.py list
```

### Serviço de Monitoramento

Para iniciar o serviço de monitoramento:
```
python monitor_service.py
```

É recomendável configurar o serviço para iniciar automaticamente com o sistema.

## Configuração

### Computadores

Os computadores são armazenados no arquivo `computers.json`. Você pode adicionar, remover e editar computadores através do menu principal.

Campos importantes:
- `name`: Nome único para identificar o computador
- `hostname`: Nome de host ou endereço IP
- `mac`: Endereço MAC no formato XX:XX:XX:XX:XX:XX
- `os_type`: Tipo de sistema operacional ("windows" ou "linux")
- `auto_power_on`: Se deve ligar automaticamente após restauração de energia
- `auto_power_off`: Se deve desligar automaticamente durante queda de energia

### Serviço de Monitoramento

A configuração do serviço é armazenada no arquivo `service_config.json`. Você pode editar essas configurações através do menu principal.

Campos importantes:
- `battery_threshold`: Limite de bateria para desligamento (%)
- `time_without_charger`: Tempo sem carregador para desligamento (minutos)
- `delay_after_power_restore`: Atraso após restauração de energia (minutos)

## Estrutura do Projeto

- `main.py`: Menu principal e ponto de entrada do sistema
- `remote_poweron.py`: Funções para ligar computadores (Wake-on-LAN)
- `remote_shutdown.py`: Funções para desligar computadores (Windows e Linux)
- `monitor_service.py`: Serviço de monitoramento de energia
- `computers.json`: Dados dos computadores cadastrados
- `service_config.json`: Configuração do serviço de monitoramento
- `power_status.json`: Status atual do sistema
- `PSTools/`: Diretório para os utilitários PSTools (criado automaticamente)

## Solução de Problemas

### Wake-on-LAN não funciona

1. Verifique se o Wake-on-LAN está habilitado na BIOS/UEFI
2. Verifique se a placa de rede suporta Wake-on-LAN
3. Certifique-se de que o endereço MAC está correto
4. Verifique as configurações de energia do sistema operacional

### Desligamento de Windows não funciona

1. Verifique se o PSTools foi baixado corretamente
2. Verifique as credenciais de administrador
3. Certifique-se de que o firewall não está bloqueando a conexão

### Desligamento de Linux não funciona

1. Verifique as credenciais SSH
2. Certifique-se de que o usuário tem permissão para executar comandos sudo
3. Verifique se o SSH está habilitado no servidor

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.