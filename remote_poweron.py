"""
Módulo para ligar computadores remotamente utilizando Wake-on-LAN (WoL).
"""

import argparse
import json
import os
import socket

# Constantes
MAC_LENGTH = 12
CONFIG_FILE = "computers.json"


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
            print("Erro ao ler {}. Formato JSON inválido.".format(CONFIG_FILE))
            return []
    else:
        # Cria um arquivo de configuração vazio
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
        return []


def wake_on_lan(mac_address):
    """
    Envia um pacote Wake-on-LAN para o endereço MAC especificado.

    Args:
        mac_address (str): Endereço MAC no formato "XX:XX:XX:XX:XX:XX"
        ou "XX-XX-XX-XX-XX-XX".
    """
    # Remove os dois pontos ou hífens do endereço MAC
    mac_address = mac_address.replace(':', '').replace('-', '')
    print('Número MAC: {}'.format(mac_address))
    mac_address = mac_address.upper()
    print('Número MAC Upper: {}'.format(mac_address))

    # Verifica se o endereço MAC tem o formato correto
    if len(mac_address) != MAC_LENGTH:
        print('Formato inválido: {} caracteres'.format(len(mac_address)))
        raise ValueError(
            'Formato de endereço MAC inválido. Use XX:XX:XX:XX:XX:XX ou XX-XX-XX-XX-XX-XX'
        )

    # Converte o endereço MAC para bytes
    mac_bytes = bytes.fromhex(mac_address)

    # Cria o "magic packet"
    # FF:FF:FF:FF:FF:FF seguido pelo endereço MAC repetido 16 vezes
    magic_packet = b'\xff' * 6 + mac_bytes * 16

    # Configura o socket para broadcast UDP
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Envia o pacote para o endereço de broadcast na porta padrão WoL (9)
        sock.sendto(magic_packet, ('255.255.255.255', 9))

    print('Pacote Wake-on-LAN enviado com sucesso para {}'.format(mac_address))


def wake_on_lan_by_name(computer_name):
    """
    Envia um pacote Wake-on-LAN para um computador pelo nome.

    Args:
        computer_name (str): Nome do computador cadastrado.

    Returns:
        bool: True se o comando foi executado com sucesso e
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
        print("Computador '{}' não encontrado.".format(computer_name))
        return False

    try:
        print(
            "Enviando Wake-on-LAN para {} ({})...".format(
                target_computer['name'], target_computer['hostname']
            )
        )
        wake_on_lan(target_computer["mac"])
        return True
    except Exception as e:  # pylint-disable=broad-except
        print("Erro ao enviar Wake-on-LAN: {}".format(e))
        return False


def wake_on_lan_all_auto():
    """
    Envia Wake-on-LAN para todos os computadores marcados como auto_power_on.

    Returns:
        int: Número de computadores ligados com sucesso.
    """
    computers = load_computers()
    success_count = 0

    for comp in computers:
        if comp.get("auto_power_on", False):
            try:
                print("Enviando Wake-on-LAN para {} ({})...".format(comp['name'], comp['hostname']))
                wake_on_lan(comp["mac"])
                success_count += 1
            except Exception as e:  # pylint-disable=broad-except
                print("Erro ao enviar Wake-on-LAN para {}: {}".format(comp['name'], e))

    return success_count


def wake_on_lan_menu():
    """
    Exibe um menu para ligar computadores remotamente.
    """
    computers = load_computers()

    if not computers:
        print("Nenhum computador cadastrado.")
        return

    while True:
        print("\n=== Wake-on-LAN ===")
        print("1. Ligar um computador")
        print("2. Ligar todos os computadores")
        print("3. Ligar todos os computadores auto_power_on")
        print("0. Voltar ao menu principal")

        choice = input("\nEscolha uma opção: ")

        if choice == "1":
            print("\nSelecione o computador para ligar:")
            for i, comp in enumerate(computers, 1):
                print("{}. {} ({})".format(i, comp['name'], comp['hostname']))

            try:
                idx = int(input("\nNúmero do computador: ")) - 1
                if 0 <= idx < len(computers):
                    try:
                        wake_on_lan(computers[idx]["mac"])
                        print("Comando Wake-on-LAN enviado para {}.".format(computers[idx]['name']))
                    except Exception as e:  # pylint-disable=broad-except
                        print("Erro ao enviar Wake-on-LAN: {}".format(e))
                else:
                    print("Número inválido.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

        elif choice == "2":
            success_count = 0
            for comp in computers:
                try:
                    wake_on_lan(comp["mac"])
                    success_count += 1
                except Exception as e:  # pylint-disable=broad-except
                    print("Erro ao enviar Wake-on-LAN para {}: {}".format(comp['name'], e))

            print("\n{} de {} computadores foram ligados com sucesso.".format(
                success_count, len(computers)
            ))

        elif choice == "3":
            auto_computers = [comp for comp in computers if comp.get("auto_power_on", False)]

            if not auto_computers:
                print("Nenhum computador está configurado com auto_power_on.")
                continue

            success_count = wake_on_lan_all_auto()
            print(
                "\n{} de {} computadores foram ligados com sucesso.".format(
                    success_count, len(auto_computers)
                )
            )

        elif choice == "0":
            break

        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Enviar comando Wake-on-LAN para um computador remoto.'
    )
    parser.add_argument(
        'target',
        nargs='?',
        help='Endereço MAC do computador alvo ou nome do computador cadastrado',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Ligar todos os computadores cadastrados',
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Ligar apenas os computadores marcados como auto_power_on',
    )

    args = parser.parse_args()

    if args.all:
        # Ligar todos os computadores
        computers = load_computers()
        SUCCESS_COUNT = 0
        for comp in computers:
            try:
                wake_on_lan(comp["mac"])
                SUCCESS_COUNT += 1
            except Exception as e:  # pylint-disable=broad-except
                print("Erro ao enviar Wake-on-LAN para {}: {}".format(comp['name'], e))

        print(
            "\n{} de {} computadores foram ligados com sucesso.".format(
                SUCCESS_COUNT, len(computers)
            )
        )

    elif args.auto:
        # Ligar apenas os computadores auto_power_on
        SUCCESS_COUNT = wake_on_lan_all_auto()
        computers = load_computers()
        auto_computers = [comp for comp in computers if comp.get("auto_power_on", False)]
        print(
            "\n{} de {} computadores foram ligados com sucesso.".format(
                SUCCESS_COUNT, len(auto_computers)
            )
        )

    elif args.target:
        # Verifica se o alvo é um MAC ou nome de computador
        if ':' in args.target or '-' in args.target:
            try:
                wake_on_lan(args.target)
            except ValueError as e:
                print("Erro: {}".format(e))
        else:
            wake_on_lan_by_name(args.target)

    else:
        # Se nenhum argumento foi fornecido, mostrar o menu interativo
        wake_on_lan_menu()