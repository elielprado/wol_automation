"""
Módulo para desligar computadores remotamente, tanto Windows quanto Linux.
"""

import argparse
import getpass
import json
import logging
import os
import subprocess
import zipfile

import paramiko
import requests

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Constantes
PSTOOLS_URL = "https://download.sysinternals.com/files/PSTools.zip"
PSTOOLS_DIR = "PSTools"
CONFIG_FILE = "computers.json"


def ensure_pstools_exists():
    """
    Verifica se o PSTools está disponível, baixa e extrai se necessário.

    Returns:
        bool: True se PSTools está disponível, False caso contrário.
    """
    psshutdown_path = os.path.join(PSTOOLS_DIR, "psshutdown.exe")

    # Verifica se o PSTools já existe
    if os.path.exists(psshutdown_path):
        logger.info("PSTools já está instalado.")
        return True

    # Cria o diretório PSTools se não existir
    if not os.path.exists(PSTOOLS_DIR):
        os.makedirs(PSTOOLS_DIR)
        logger.info("Diretório %s criado.", PSTOOLS_DIR)

    # Baixa o arquivo PSTools.zip
    try:
        logger.info("Baixando PSTools de %s...", PSTOOLS_URL)
        response = requests.get(PSTOOLS_URL, stream=True, timeout=10)
        response.raise_for_status()

        # Salva o arquivo zip
        zip_path = os.path.join(PSTOOLS_DIR, "PSTools.zip")
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Extrai o arquivo zip
        logger.info("Extraindo PSTools.zip...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(PSTOOLS_DIR)

        # Remove o arquivo zip após a extração
        os.remove(zip_path)
        logger.info("PSTools instalado com sucesso.")

        return os.path.exists(psshutdown_path)

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Erro ao baixar ou extrair PSTools: %s", e)
        return False


def load_computers():
    """
    Carrega as configurações de computadores do arquivo JSON.

    Returns:
        list: Lista de dicionários com as configurações dos computadores.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Erro ao ler %s. Formato JSON inválido.", CONFIG_FILE)
            return []
    else:
        # Cria um arquivo de configuração vazio
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
        return []


def save_computers(computers):
    """
    Salva as configurações de computadores no arquivo JSON.

    Args:
        computers (list): Lista de dicionários com as
        configurações dos computadores.
    """
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(computers, f, indent=4)


def shutdown_windows(computer):
    """
    Desliga um computador Windows remoto usando PSShutdown.

    Args:
        computer (dict): Dicionário com as configurações do computador.

    Returns:
        bool: True se o comando foi executado com sucesso e
        False caso contrário.
    """
    hostname = computer["hostname"]
    username = computer["username"]
    password = computer["password"]

    # Se a senha não estiver salva, solicita ao usuário
    if not computer["save_password"]:
        password = getpass.getpass(f"Senha para {username}@{hostname}: ")

    psshutdown_path = os.path.join(PSTOOLS_DIR, "psshutdown.exe")

    # Constrói o comando
    cmd = [
        psshutdown_path,
        f"\\\\{hostname}",
        "-u",
        username,
        "-p",
        password,
        "-f",  # Força o fechamento de aplicativos
        "-t",
        "0",  # Tempo de espera (0 = imediato)
        "-accepteula",  # Aceita o EULA
    ]

    try:
        logger.info("Desligando %s...", hostname)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        print(f'Resposta do comando: {result.stdout}')

        if result.returncode == 0:
            logger.info("Comando de desligamento enviado com sucesso para %s", hostname)
            return True
        else:
            logger.error("Erro ao desligar %s: %s", hostname, result.stderr)
            return False

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Erro ao executar psshutdown: %s", e)
        return False


def shutdown_linux(computer):
    """
    Desliga um computador Linux remoto usando SSH com shell interativo.

    Args:
        computer (dict): Dicionário com as configurações do computador.

    Returns:
        bool: True se o comando foi executado com sucesso,
        False caso contrário.
    """
    hostname = computer["hostname"]
    username = computer["username"]
    ssh_key = computer.get("ssh_key", "")
    password = computer["password"]

    # Se a senha não estiver salva, solicita ao usuário
    if not computer["save_password"] and not ssh_key:
        password = getpass.getpass(f"Senha para {username}@{hostname}: ")

    try:
        logger.info("Conectando via SSH a %s...", hostname)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Conecta usando chave SSH ou senha
        if ssh_key and os.path.exists(ssh_key):
            ssh.connect(hostname, username=username, key_filename=ssh_key)
        else:
            ssh.connect(hostname, username=username, password=password)

        # Inicia um shell interativo
        logger.info("Iniciando shell interativo...")
        shell = ssh.invoke_shell()
        shell.settimeout(15)  # Define um timeout adequado

        # Limpa qualquer saída inicial
        if shell.recv_ready():
            shell.recv(1024)

        # Envia o comando de desligamento
        logger.info("Enviando comando de desligamento para %s...", hostname)
        shell.send("sudo shutdown -h now\n")

        # Aguarda por um prompt de senha ou por um timeout
        import time

        time.sleep(1)  # Breve pausa para dar tempo de processar o comando

        # Verifica se precisa fornecer senha
        password_requested = False
        start_time = time.time()
        timeout_seconds = 10

        while (time.time() - start_time) < timeout_seconds:
            if shell.recv_ready():
                output = shell.recv(1024).decode('utf-8', errors='ignore')
                logger.info("Saída recebida: %s", output.strip())

                if "password" in output.lower():
                    password_requested = True
                    logger.info("Prompt de senha detectado, enviando senha...")
                    shell.send(password + "\n")
                    time.sleep(1)  # Aguarda um momento após enviar a senha
                    break

            time.sleep(0.5)  # Pequena pausa para não sobrecarregar o CPU

        # Verificação adicional se o comando foi bem-sucedido
        success = True

        # Se deu timeout sem solicitar senha, pode ser um bom sinal
        # (o usuário tem permissão para sudo sem senha)
        if not password_requested and (time.time() - start_time) >= timeout_seconds:
            logger.info("Nenhum prompt de senha detectado, assumindo comando executado")

        # Aguarda um pouco mais para dar tempo de iniciar o desligamento
        time.sleep(2)

        # Tenta fechar a conexão
        try:
            shell.close()
            ssh.close()
        except Exception:  # pylint: disable=broad-except
            # Se a conexão falhou ao fechar, pode ser um sinal de que o desligamento começou
            logger.info("Conexão fechada abruptamente, possível sinal de desligamento iniciado")

        logger.info("Comando de desligamento enviado com sucesso para %s", hostname)
        return success

    except Exception as e:  # pylint: disable=broad-except
        logger.error("Erro ao desligar via SSH: %s", e)
        return False


def shutdown_computer(computer):
    """
    Desliga um computador remoto, independente do sistema operacional.

    Args:
        computer (dict): Dicionário com as configurações do computador.

    Returns:
        bool: True se o comando foi executado com sucesso,
        False caso contrário.
    """
    if computer["os_type"].lower() == "windows":
        if ensure_pstools_exists():
            return shutdown_windows(computer)
        else:
            logger.error("PSTools não está disponível para desligar " + "computadores Windows.")
            return False
    elif computer["os_type"].lower() == "linux":
        return shutdown_linux(computer)
    else:
        logger.error("Sistema operacional não suportado: %s", computer['os_type'])
        return False


def shutdown_by_name(computer_name):
    """
    Desliga um computador pelo nome.

    Args:
        computer_name (str): Nome do computador cadastrado.

    Returns:
        bool: True se o comando foi executado com sucesso,
        False caso contrário.
    """
    computers = load_computers()

    # Procura o computador pelo nome
    target_computer = None
    for comp in computers:
        if comp["name"].lower() == computer_name.lower():
            target_computer = comp
            break

    if not target_computer:
        print(f"Computador '{computer_name}' não encontrado.")
        return False

    return shutdown_computer(target_computer)


def shutdown_all_auto():
    """
    Desliga todos os computadores marcados como auto_power_off.

    Returns:
        int: Número de computadores desligados com sucesso.
    """
    computers = load_computers()
    success_count = 0

    for comp in computers:
        if comp.get("auto_power_off", False) and shutdown_computer(comp):
            success_count += 1

    return success_count


def shutdown_menu():
    """
    Exibe um menu para desligar computadores remotamente.
    """
    computers = load_computers()

    if not computers:
        print("Nenhum computador cadastrado.")
        return

    while True:
        print("\n=== Desligamento Remoto ===")
        print("1. Desligar um computador")
        print("2. Desligar todos os computadores")
        print("3. Desligar todos os computadores auto_power_off")
        print("0. Voltar ao menu principal")

        choice = input("\nEscolha uma opção: ")

        if choice == "1":
            print("\nSelecione o computador para desligar:")
            for i, comp in enumerate(computers, 1):
                print(
                    f"{i}. {comp['name']} ({comp['hostname']}) - {
                        comp['os_type'].capitalize()}"
                )

            try:
                idx = int(input("\nNúmero do computador: ")) - 1
                if 0 <= idx < len(computers):
                    success = shutdown_computer(computers[idx])
                    if success:
                        print(
                            f"Comando de desligamento enviado para {
                                computers[idx]['name']
                                }."
                        )
                    else:
                        print(f"Falha ao desligar {computers[idx]['name']}.")
                else:
                    print("Número inválido.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

        elif choice == "2":
            success_count = 0
            for comp in computers:
                if shutdown_computer(comp):
                    success_count += 1

            print(
                f"\n{success_count} de {len(computers)} computadores foram "
                + "desligados com sucesso."
            )

        elif choice == "3":
            auto_computers = [comp for comp in computers if comp.get("auto_power_off", False)]

            if not auto_computers:
                print("Nenhum computador está configurado com auto_power_off.")
                continue

            success_count = shutdown_all_auto()
            print(
                f"\n{success_count} de {len(auto_computers)} computadores"
                + " foram desligados com sucesso."
            )

        elif choice == "0":
            break

        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Desligar computadores remotamente.')
    parser.add_argument('target', nargs='?', help='Nome do computador cadastrado')
    parser.add_argument(
        '--all',
        action='store_true',
        help='Desligar todos os computadores cadastrados',
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Desligar apenas os computadores marcados como auto_power_off',
    )

    args = parser.parse_args()

    if args.all:
        # Desligar todos os computadores
        computers = load_computers()
        SUCCESS_COUNT = 0
        for comp in computers:
            if shutdown_computer(comp):
                SUCCESS_COUNT += 1

        print(
            f"\n{SUCCESS_COUNT} de {len(computers)} computadores foram "
            + "desligados com sucesso."
        )

    elif args.auto:
        # Desligar apenas os computadores auto_power_off
        SUCCESS_COUNT = shutdown_all_auto()
        computers = load_computers()
        auto_computers = [comp for comp in computers if comp.get("auto_power_off", False)]
        print(
            f"\n{SUCCESS_COUNT} de {len(auto_computers)} computadores "
            + "foram desligados com sucesso."
        )

    elif args.target:
        shutdown_by_name(args.target)

    else:
        # Se nenhum argumento foi fornecido, mostrar o menu interativo
        shutdown_menu()
