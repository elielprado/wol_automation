"""
Menu principal para gerenciamento de energia de computadores remotos.
Permite ligar e desligar computadores remotamente,
além de configurar o serviço de monitoramento.
"""

import argparse
import json
import os
import platform
import subprocess
import sys

# Importando os módulos necessários
from remote_poweron import wake_on_lan, wake_on_lan_by_name, wake_on_lan_menu, load_computers
from remote_shutdown import shutdown_by_name, shutdown_menu
import email_service

# Constantes
CONFIG_FILE = "computers.json"
SERVICE_CONFIG_FILE = "service_config.json"
MAX_BATTERY_THRESHOLD = 100
INVALID_ENTRY = "Entrada inválida. Digite um número."
MONITOR_SERVICE_SCRIPT = "monitor_service.py"
SERVICE_NOT_RUNNING = "Serviço não está em execução."


def load_computers():
    """Carrega a lista de computadores do arquivo JSON."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Erro ao ler {}. Formato JSON inválido.".format(CONFIG_FILE))
            return []
    else:
        # Cria um arquivo de configuração vazio
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
        return []


def save_computers(computers):
    """Salva a lista de computadores no arquivo JSON."""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(computers, f, indent=4)


def load_service_config():
    """Carrega a configuração do serviço do arquivo JSON."""
    default_config = {
        "battery_threshold": 25,
        "time_without_charger": 10,  # minutos
        "delay_after_power_restore": 2,  # minutos
        "last_execution": None,
        "power_failure_detected": False,
    }

    if os.path.exists(SERVICE_CONFIG_FILE):
        try:
            with open(SERVICE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Garante que todas as chaves padrão existam
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except json.JSONDecodeError:
            print("Erro ao ler {}. Usando configuração padrão.".format(SERVICE_CONFIG_FILE))
            return default_config
    else:
        # Cria um arquivo de configuração padrão
        with open(SERVICE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config


def save_service_config(config):
    """Salva a configuração do serviço no arquivo JSON."""
    with open(SERVICE_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def add_computer():
    """Adiciona um novo computador à lista."""
    print("\n=== Adicionar Novo Computador ===")

    name = input("Nome do computador (identificador único): ")
    hostname = input("Hostname ou IP: ")
    mac = input("Endereço MAC (formato XX:XX:XX:XX:XX:XX): ")

    # Determina o tipo de sistema operacional
    os_type = input("Sistema Operacional (windows/linux): ").lower()

    if os_type == "windows":
        username = input("Nome de usuário Windows: ")
        save_password = input("Salvar senha? (s/n): ").lower() == 's'
        password = input("Senha (deixe em branco para não salvar): ") if save_password else ""

        computer = {
            "name": name,
            "hostname": hostname,
            "mac": mac,
            "os_type": "windows",
            "username": username,
            "password": password,
            "save_password": save_password,
            "auto_power_on": input("Ligar automaticamente após queda de energia? (s/n): ").lower()
            == 's',
            "auto_power_off": input(
                "Desligar automaticamente durante queda de energia? (s/n): "
            ).lower()
            == 's',
        }

    elif os_type == "linux":
        username = input("Nome de usuário SSH: ")
        ssh_key = input("Caminho para a chave SSH (deixe em branco para usar senha): ")
        password = ""
        save_password = False

        if not ssh_key:
            save_password = input("Salvar senha? (s/n): ").lower() == 's'
            password = input("Senha (deixe em branco para não salvar): ") if save_password else ""

        computer = {
            "name": name,
            "hostname": hostname,
            "mac": mac,
            "os_type": "linux",
            "username": username,
            "ssh_key": ssh_key,
            "password": password,
            "save_password": save_password,
            "auto_power_on": input("Ligar automaticamente após queda de energia? (s/n): ").lower()
            == 's',
            "auto_power_off": input(
                "Desligar automaticamente durante queda de energia? (s/n): "
            ).lower()
            == 's',
        }

    else:
        print("Sistema operacional não suportado. Use 'windows' ou 'linux'.")
        return None

    return computer


def list_computers():
    """Lista todos os computadores cadastrados."""
    computers = load_computers()

    if not computers:
        print("Nenhum computador cadastrado.")
        return

    print("\n=== Computadores Cadastrados ===")
    for i, comp in enumerate(computers, 1):
        os_type = comp["os_type"]
        auto_on = "Sim" if comp.get("auto_power_on", False) else "Não"
        auto_off = "Sim" if comp.get("auto_power_off", False) else "Não"

        print("{}. {} ({}) - {}".format(
            i, comp['name'], comp['hostname'], os_type.capitalize()
        ))
        print("   Sistema Operacional: {}".format(os_type.capitalize()))
        print("   MAC: {}".format(comp['mac']))
        print("   Auto Power On: {}, Auto Power Off: {}".format(auto_on, auto_off))
        print()


def configure_service():
    """Configura o serviço de monitoramento."""
    config = load_service_config()

    print("\n=== Configuração do Serviço de Monitoramento ===")
    print("1. Limite de bateria para desligamento: {}%".format(
        config['battery_threshold']
    ))
    print("2. Tempo sem carregador para desligamento: {} minutos".format(
        config['time_without_charger']
    ))
    print("3. Atraso após restauração de energia: {} minutos".format(
        config['delay_after_power_restore']
    ))
    print("4. Voltar ao menu principal")

    choice = input("\nEscolha uma opção para alterar: ")

    if choice == "1":
        try:
            value = int(input("Novo limite de bateria (%): "))
            if 0 <= value <= MAX_BATTERY_THRESHOLD:
                config["battery_threshold"] = value
                save_service_config(config)
                print("Limite de bateria alterado para {}%".format(value))
            else:
                print("Valor inválido. Use um número entre 0 e 100.")
        except ValueError:
            print(INVALID_ENTRY)

    elif choice == "2":
        try:
            value = int(input("Novo tempo sem carregador (minutos): "))
            if value > 0:
                config["time_without_charger"] = value
                save_service_config(config)
                print("Tempo sem carregador alterado para {} minutos".format(value))
            else:
                print("Valor inválido. Use um número positivo.")
        except ValueError:
            print(INVALID_ENTRY)

    elif choice == "3":
        try:
            value = int(input("Novo atraso após restauração de energia (minutos): "))
            if value >= 0:
                config["delay_after_power_restore"] = value
                save_service_config(config)
                print("Atraso alterado para {} minutos".format(value))
            else:
                print("Valor inválido. Use um número não negativo.")
        except ValueError:
            print(INVALID_ENTRY)

    elif choice == "4":
        return

    else:
        print("Opção inválida.")


def start_stop_service():
    """Inicia ou para o serviço de monitoramento."""

    system = platform.system()

    print("\n=== Controle do Serviço de Monitoramento ===")
    print("1. Iniciar serviço")
    print("2. Parar serviço")
    print("3. Status do serviço")
    print("4. Voltar ao menu principal")

    choice = input("\nEscolha uma opção: ")

    script_path = os.path.abspath(MONITOR_SERVICE_SCRIPT)

    if choice == "1":
        if system == "Windows":
            print("Para iniciar o serviço no Windows, você precisa:")
            print("1. Abra o Agendador de Tarefas")
            print("2. Crie uma nova tarefa que execute: python {}".format(script_path))
            print(
                "3. Configure-a para executar ao iniciar o sistema e repetir a cada 1 minuto"
            )
        else:  # Linux
            print("Para iniciar o serviço no Linux, você pode usar:")
            print("python {} &".format(script_path))
            print("Ou configure um serviço systemd para inicialização automática.")

            start = input("Deseja iniciar o serviço agora? (s/n): ")
            if start.lower() == 's':
                try:
                    subprocess.Popen(["python", script_path])
                    print("Serviço iniciado em segundo plano.")
                except Exception as e:  # pylint disable=too-broad-except
                    print("Erro ao iniciar o serviço: {}".format(e))

    elif choice == "2":
        if system == "Windows":
            print("Para parar o serviço no Windows:")
            print("1. Abra o Gerenciador de Tarefas")
            print("2. Encontre o processo python.exe que está executando monitor_service.py")
            print("3. Finalize o processo")
        else:  # Linux
            print("Para parar o serviço no Linux:")
            try:
                output = subprocess.check_output(["pgrep", "-f", MONITOR_SERVICE_SCRIPT])
                pids = output.decode().strip().split("\n")
                for pid in pids:
                    subprocess.call(["kill", pid])
                print("Serviço parado (PID: {})".format(", ".join(pids)))
            except subprocess.CalledProcessError:
                print(SERVICE_NOT_RUNNING)
            except Exception as e:  # pylint disable=too-broad-except
                print("Erro ao parar o serviço: {}".format(e))

    elif choice == "3":
        if system == "Windows":
            print("Para verificar o status no Windows, confira o Gerenciador de Tarefas.")
        else:  # Linux
            try:
                output = subprocess.check_output(["pgrep", "-f", MONITOR_SERVICE_SCRIPT])
                pids = output.decode().strip().split("\n")
                print("Serviço está em execução (PID: {})".format(", ".join(pids)))
            except subprocess.CalledProcessError:
                print(SERVICE_NOT_RUNNING)
            except Exception as e:  # pylint disable=too-broad-except
                print("Erro ao verificar o status: {}".format(e))

    elif choice == "4":
        return

    else:
        print("Opção inválida.")


def configure_email():
    """Configura as opcoes de email para notificacoes."""
    config = email_service.load_email_config()

    while True:
        print("\n=== Configuração de Email ===")
        enabled_status = "Habilitado" if config["enabled"] else "Desabilitado"
        print("1. Status: {}".format(enabled_status))
        print("2. Servidor SMTP: {}".format(config["smtp_server"]))
        print("3. Porta SMTP: {}".format(config["smtp_port"]))
        print("4. Usuário: {}".format(config["username"]))
        print("5. Senha: {}".format("*****" if config["password"] else "Não configurada"))
        print("6. Endereço de origem: {}".format(config["from_address"]))
        print("7. Gerenciar destinatários ({} configurados)".format(len(config["recipients"])))
        print("8. Configurar eventos de notificação")
        print("9. Testar configuração")
        print("0. Voltar ao menu principal")

        choice = input("\nEscolha uma opção: ")

        if choice == "1":
            toggle = input("Habilitar envio de emails? (s/n): ").lower()
            config["enabled"] = toggle == 's'
            email_service.save_email_config(config)
            print("Status de envio de emails {}!".format(
                "habilitado" if config["enabled"] else "desabilitado"))

        elif choice == "2":
            server = input("Servidor SMTP (ex: smtp.gmail.com): ")
            if server:
                config["smtp_server"] = server
                email_service.save_email_config(config)
                print("Servidor SMTP atualizado.")

        elif choice == "3":
            try:
                port = int(input("Porta SMTP (ex: 587 para TLS): "))
                config["smtp_port"] = port
                email_service.save_email_config(config)
                print("Porta SMTP atualizada.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

        elif choice == "4":
            username = input("Usuário (endereço de email completo): ")
            if username:
                config["username"] = username
                email_service.save_email_config(config)
                print("Usuário atualizado.")

        elif choice == "5":
            password = input("Senha (ficará salva em texto simples): ")
            if password:
                config["password"] = password
                email_service.save_email_config(config)
                print("Senha atualizada.")
            else:
                print("Senha não alterada.")

        elif choice == "6":
            from_address = input("Endereço de email de origem: ")
            if from_address:
                config["from_address"] = from_address
                email_service.save_email_config(config)
                print("Endereço de origem atualizado.")

        elif choice == "7":
            manage_recipients(config)

        elif choice == "8":
            configure_notification_events(config)

        elif choice == "9":
            if email_service.test_email_config():
                print("Teste de email concluído com sucesso!")
            else:
                print("Falha no teste de email. Verifique suas configurações.")

        elif choice == "0":
            break

        else:
            print("Opção inválida.")


def manage_recipients(config):
    """Gerencia a lista de destinatários para notificações."""
    while True:
        print("\n=== Gerenciar Destinatários ===")
        if not config["recipients"]:
            print("Nenhum destinatário configurado.")
        else:
            print("Destinatários configurados:")
            for i, recipient in enumerate(config["recipients"], 1):
                print("{}. {}".format(i, recipient))
        
        print("\n1. Adicionar destinatário")
        print("2. Remover destinatário")
        print("0. Voltar")

        choice = input("\nEscolha uma opção: ")

        if choice == "1":
            recipient = input("Digite o endereço de email: ")
            if recipient and "@" in recipient:
                if recipient not in config["recipients"]:
                    config["recipients"].append(recipient)
                    email_service.save_email_config(config)
                    print("Destinatário adicionado.")
                else:
                    print("Este email já está na lista.")
            else:
                print("Endereço de email inválido.")

        elif choice == "2":
            if not config["recipients"]:
                print("Não há destinatários para remover.")
                continue
                
            try:
                idx = int(input("Digite o número do destinatário a remover: ")) - 1
                if 0 <= idx < len(config["recipients"]):
                    removed = config["recipients"].pop(idx)
                    email_service.save_email_config(config)
                    print("Destinatário {} removido.".format(removed))
                else:
                    print("Número inválido.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

        elif choice == "0":
            break

        else:
            print("Opção inválida.")


def configure_notification_events(config):
    """Configura quais eventos devem gerar notificações por email."""
    event_names = {
        "power_disconnected": "Energia desconectada",
        "power_restored": "Energia restaurada",
        "shutdown_initiated": "Desligamento iniciado",
        "poweron_initiated": "Inicialização remota",
        "low_battery": "Bateria fraca"
    }

    while True:
        print("\n=== Configurar Eventos de Notificação ===")
        for i, (event_key, event_name) in enumerate(event_names.items(), 1):
            status = "Habilitado" if config["notification_events"].get(event_key, False) else "Desabilitado"
            print("{}. {}: {}".format(i, event_name, status))
        
        print("0. Voltar")

        choice = input("\nEscolha um evento para alterar (0 para voltar): ")
        
        if choice == "0":
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(event_names):
                event_key = list(event_names.keys())[idx]
                toggle = input("Habilitar notificações para este evento? (s/n): ").lower()
                config["notification_events"][event_key] = toggle == 's'
                email_service.save_email_config(config)
                print("Configuração atualizada.")
            else:
                print("Número inválido.")
        except ValueError:
            print("Entrada inválida. Digite um número.")


def main_menu():
    """Exibe o menu principal e processa as opções do usuário."""
    while True:
        print("\n====== Sistema de Gerenciamento de Energia Remota ======")
        print("1. Ligar computador(es)")
        print("2. Desligar computador(es)")
        print("3. Listar computadores cadastrados")
        print("4. Adicionar computador")
        print("5. Remover computador")
        print("6. Configurar serviço de monitoramento")
        print("7. Iniciar/parar serviço de monitoramento")
        print("8. Configurar notificações por email")  # Nova opção
        print("0. Sair")

        choice = input("\nEscolha uma opção: ")

        if choice == "1":
            wake_on_lan_menu()

        elif choice == "2":
            shutdown_menu()

        elif choice == "3":
            list_computers()

        elif choice == "4":
            computers = load_computers()
            new_computer = add_computer()
            if new_computer:
                computers.append(new_computer)
                save_computers(computers)
                print("Computador {} adicionado com sucesso!".format(new_computer['name']))

        elif choice == "5":
            computers = load_computers()
            if not computers:
                print("Nenhum computador cadastrado.")
                continue

            print("\nSelecione o computador para remover:")
            for i, comp in enumerate(computers, 1):
                print("{}. {} ({})".format(i, comp['name'], comp['hostname']))

            try:
                idx = int(input("\nNúmero do computador: ")) - 1
                if 0 <= idx < len(computers):
                    removed = computers.pop(idx)
                    save_computers(computers)
                    print("Computador {} removido com sucesso!".format(removed['name']))
                else:
                    print("Número inválido.")
            except ValueError:
                print(INVALID_ENTRY)

        elif choice == "6":
            configure_service()

        elif choice == "7":
            start_stop_service()
            
        elif choice == "8":  # Nova opção para configuração de email
            configure_email()

        elif choice == "0":
            print("Saindo...")
            sys.exit(0)

        else:
            print("Opção inválida. Tente novamente.")


def handle_command_line():
    """Processa argumentos de linha de comando
    para acesso direto às funções."""
    parser = argparse.ArgumentParser(description='Gerenciamento de energia remota')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando wake-on-lan
    wol_parser = subparsers.add_parser('wol', help='Enviar comando Wake-on-LAN')
    wol_parser.add_argument('target', help='Nome do computador cadastrado ou endereço MAC')

    # Comando shutdown
    shutdown_parser = subparsers.add_parser('shutdown', help='Desligar computador remoto')
    shutdown_parser.add_argument('target', help='Nome do computador cadastrado ou hostname')

    # Comando list
    subparsers.add_parser('list', help='Listar computadores cadastrados')

    # Comando start/stop
    service_parser = subparsers.add_parser('service', help='Controlar serviço de monitoramento')
    service_parser.add_argument(
        'action',
        choices=['start', 'stop', 'status'],
        help='Ação para o serviço (start, stop, status)',
    )
    
    # Comando email
    email_parser = subparsers.add_parser('email', help='Configurar notificações por email')
    email_parser.add_argument(
        'action',
        choices=['configure', 'test'],
        help='Ação para o serviço de email (configure, test)',
    )

    args = parser.parse_args()

    if args.command == 'wol':
        # Verifica se o alvo é um MAC ou nome de computador
        if ':' in args.target or '-' in args.target:
            wake_on_lan(args.target)
        else:
            wake_on_lan_by_name(args.target)

    elif args.command == 'shutdown':
        # Verifica se o alvo é um hostname ou nome de computador
        shutdown_by_name(args.target)

    elif args.command == 'list':
        list_computers()

    elif args.command == 'service':

        script_path = os.path.abspath(MONITOR_SERVICE_SCRIPT)

        if args.action == 'start':
            try:
                subprocess.Popen(["python", script_path])
                print("Serviço iniciado em segundo plano.")
            except Exception as e:  # pylint disable=too-broad-except
                print("Erro ao iniciar o serviço: {}".format(e))

        elif args.action == 'stop':
            try:

                if platform.system() == "Windows":
                    os.system(
                        'taskkill /F /FI "IMAGENAME eq python.exe"'
                        + ' /FI "WINDOWTITLE eq *monitor_service.py*"'
                    )
                else:  # Linux
                    output = subprocess.check_output(["pgrep", "-f", MONITOR_SERVICE_SCRIPT])
                    pids = output.decode().strip().split("\n")
                    for pid in pids:
                        subprocess.call(["kill", pid])
                    print("Serviço parado (PID: {})".format(", ".join(pids)))
            except Exception as e:  # pylint disable=too-broad-except
                print("Erro ao parar o serviço: {}".format(e))

        elif args.action == 'status':
            try:

                if platform.system() == "Windows":
                    print(
                        "Funcionalidade não disponível no Windows através da linha de comando."
                    )
                else:  # Linux
                    output = subprocess.check_output(["pgrep", "-f", MONITOR_SERVICE_SCRIPT])
                    pids = output.decode().strip().split("\n")
                    print("Serviço está em execução (PID: {})".format(", ".join(pids)))
            except subprocess.CalledProcessError:
                print(SERVICE_NOT_RUNNING)
            except Exception as e:  # pylint disable=too-broad-except
                print("Erro ao verificar o status: {}".format(e))
                
    elif args.command == 'email':
        if args.action == 'configure':
            configure_email()
        elif args.action == 'test':
            if email_service.test_email_config():
                print("Teste de email concluído com sucesso!")
            else:
                print("Falha no teste de email. Verifique suas configurações.")

    else:
        # Se nenhum comando foi fornecido, mostrar o menu interativo
        main_menu()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        handle_command_line()
    else:
        main_menu()
