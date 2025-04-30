"""
Serviço de monitoramento do status da bateria para desligamento automático
de computadores em caso de falha de energia.
"""

import datetime
import json
import logging
import os
import platform
import time
from logging.handlers import RotatingFileHandler

import psutil
from remote_poweron import wake_on_lan_all_auto

# Importando as funções de desligamento e ligação
from remote_shutdown import shutdown_all_auto

# Configuração de logging
LOG_FILE = "power_monitor.log"
LOG_MAX_SIZE = 50 * 1024 * 1024  # 50MB em bytes
LOG_BACKUP_COUNT = 3  # Número de arquivos de backup a manter

# Certifique-se de que o diretório do arquivo de log existe
os.makedirs(
    os.path.dirname(LOG_FILE) if os.path.dirname(LOG_FILE) else '.',
    exist_ok=True,
)

# Configura o logger para gravar no arquivo e exibir no console
logger = logging.getLogger("PowerMonitor")
logger.setLevel(logging.INFO)

# Limpa os manipuladores existentes para evitar duplicação
if logger.handlers:
    logger.handlers.clear()

# Adiciona o manipulador de arquivo com rotação
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=LOG_MAX_SIZE,
    backupCount=LOG_BACKUP_COUNT,
    encoding='utf-8',
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Adiciona o manipulador de console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Constantes
CONFIG_FILE = "service_config.json"
STATUS_FILE = "power_status.json"

# Intervalo de verificação (em segundos)
CHECK_INTERVAL = 60


def load_service_config():
    """
    Carrega a configuração do serviço do arquivo JSON.

    Returns:
        dict: Configuração do serviço.
    """
    default_config = {
        "battery_threshold": 25,
        "time_without_charger": 10,  # minutos
        "delay_after_power_restore": 2,  # minutos
        "last_execution": None,
        "power_failure_detected": False,
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Garante que todas as chaves padrão existam
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except json.JSONDecodeError:
            logger.error(
                "Erro ao ler %s. Usando configuração padrão.",
                CONFIG_FILE,
            )
            return default_config
    else:
        # Cria um arquivo de configuração padrão
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config


def save_service_config(config):
    """
    Salva a configuração do serviço no arquivo JSON.

    Args:
        config (dict): Configuração do serviço.
    """
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def load_power_status():
    """
    Carrega o status de energia do arquivo JSON.

    Returns:
        dict: Status de energia.
    """
    default_status = {
        "last_check": None,
        "on_battery_since": None,
        "shutdown_executed": False,
        "computers_to_wake": [],
    }

    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                status = json.load(f)
                # Garante que todas as chaves padrão existam
                for key, value in default_status.items():
                    if key not in status:
                        status[key] = value
                return status
        except json.JSONDecodeError:
            logger.error("Erro ao ler %s. Usando status padrão.", STATUS_FILE)
            return default_status
    else:
        # Cria um arquivo de status padrão
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_status, f, indent=4)
        return default_status


def save_power_status(status):
    """
    Salva o status de energia no arquivo JSON.

    Args:
        status (dict): Status de energia.
    """
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=4)


def get_battery_status():  # pylint: disable=too-many-return-statements
    """
    Obtém o status da bateria do sistema.

    Returns:
        tuple: (porcentagem_bateria, conectado_energia)
    """
    system = platform.system()

    if system == "Windows":
        try:
            # Verifica se existe uma bateria
            battery = psutil.sensors_battery()
            if battery:
                return battery.percent, battery.power_plugged
            else:
                logger.error("Não foi possível obter o status da bateria (sem bateria).")
                return (
                    None,
                    True,
                )  # Assume conectado à energia se não houver bateria
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Erro ao obter status da bateria: %s", e)
            return None, True

    elif system == "Linux":
        try:
            # Verifica se existe uma bateria
            battery_path = "/sys/class/power_supply/BAT0"
            if not os.path.exists(battery_path):
                battery_path = "/sys/class/power_supply/BAT1"
                if not os.path.exists(battery_path):
                    logger.error("Não foi possível encontrar informações da bateria.")
                    return None, True

            # Obtém o status atual
            with open(f"{battery_path}/status", 'r', encoding='utf-8') as f:
                status = f.read().strip()

            # Obtém a porcentagem da bateria
            with open(f"{battery_path}/capacity", 'r', encoding='utf-8') as f:
                capacity = int(f.read().strip())

            # Verifica se está conectado à energia
            connected = status in {"Charging", "Full"}

            return capacity, connected
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Erro ao obter status da bateria: %s", e)
            return None, True

    else:
        logger.error("Sistema operacional não suportado: %s", system)
        return None, True


def should_shutdown(power_status, service_config):
    """
    Verifica se deve desligar os computadores com base no status da bateria.

    Args:
        power_status (dict): Status de energia atual.
        service_config (dict): Configuração do serviço.

    Returns:
        bool: True se deve desligar, False caso contrário.
    """
    # Se já executou o desligamento, não precisa fazer de novo
    if power_status["shutdown_executed"]:
        return False

    battery_percent, on_power = get_battery_status()

    # Se estiver conectado à energia elétrica, não precisa desligar
    if on_power:
        # Reseta o tempo sem carregador
        power_status["on_battery_since"] = None
        return False

    current_time = datetime.datetime.now().isoformat()

    # Se acabou de desconectar da energia
    if power_status["on_battery_since"] is None:
        power_status["on_battery_since"] = current_time
        logger.info("Desconectado da energia elétrica. Iniciando monitoramento.")
        return False

    # Verifica quanto tempo está sem energia
    on_battery_since = datetime.datetime.fromisoformat(power_status["on_battery_since"])
    time_on_battery = (
        datetime.datetime.now() - on_battery_since
    ).total_seconds() / 60  # em minutos

    # Condições para desligamento:
    # 1. Bateria abaixo do limite configurado
    # 2. Tempo sem energia acima do limite configurado
    if (
        battery_percent is not None and battery_percent <= service_config["battery_threshold"]
    ) or (time_on_battery >= service_config["time_without_charger"]):
        logger.warning(
            "Condição para desligamento atingida: "
            "Bateria: %s%% (limite: %s%%), "
            "Tempo sem energia: %.1f min (limite: %s min)",
            battery_percent,
            service_config['battery_threshold'],
            time_on_battery,
            service_config['time_without_charger'],
        )
        return True

    return False


def should_poweron(power_status, service_config):
    """
    Verifica se deve ligar os computadores após restauração de energia.

    Args:
        power_status (dict): Status de energia atual.
        service_config (dict): Configuração do serviço.

    Returns:
        bool: True se deve ligar, False caso contrário.
    """
    # Se não executou o desligamento, não precisa ligar
    if not power_status["shutdown_executed"]:
        return False

    _, on_power = get_battery_status()

    # Se não estiver conectado à energia elétrica, não pode ligar
    if not on_power:
        return False

    # Verifica se já passou o tempo de atraso após a restauração da energia
    if power_status.get("power_restored_time") is None:
        # Primeira vez que detecta a restauração da energia
        power_status["power_restored_time"] = datetime.datetime.now().isoformat()
        logger.info(
            "Energia restaurada." "Aguardando %s minutos para ligar os computadores.",
            service_config["delay_after_power_restore"],
        )
        return False

    # Calcula quanto tempo passou desde a restauração da energia
    power_restored_time = datetime.datetime.fromisoformat(power_status["power_restored_time"])
    time_since_restore = (
        datetime.datetime.now() - power_restored_time
    ).total_seconds() / 60  # em minutos

    # Verifica se já passou o tempo de atraso
    if time_since_restore >= service_config["delay_after_power_restore"]:
        return True

    return False


def main_loop():
    """
    Loop principal do serviço de monitoramento.
    """
    logger.info("Iniciando serviço de monitoramento de energia...")
    logger.info(
        "Log configurado com rotação: tamanho máximo %.1fMB, mantendo %s backups",
        LOG_MAX_SIZE / 1024 / 1024,
        LOG_BACKUP_COUNT,
    )

    while True:
        try:
            # Carrega as configurações e o status atual
            service_config = load_service_config()
            power_status = load_power_status()

            # Atualiza o horário da última verificação
            power_status["last_check"] = datetime.datetime.now().isoformat()

            # Verifica o status da bateria
            battery_percent, on_power = get_battery_status()
            logger.info(
                "Status da bateria: %s%%, Conectado à energia: %s",
                battery_percent,
                on_power,
            )

            # Verifica se deve desligar os computadores
            if should_shutdown(power_status, service_config):
                logger.warning("Executando desligamento de emergência dos computadores...")

                # Executa o desligamento
                shutdown_count = shutdown_all_auto()

                # Atualiza o status
                power_status["shutdown_executed"] = True
                power_status["shutdown_time"] = datetime.datetime.now().isoformat()

                logger.info(
                    "%s computadores foram desligados devido à" " falha de energia.",
                    shutdown_count,
                )

            # Verifica se deve ligar os computadores
            elif should_poweron(power_status, service_config):
                logger.info("Ligando computadores após restauração de energia...")

                # Executa a ligação
                poweron_count = wake_on_lan_all_auto()

                # Reseta o status
                power_status["shutdown_executed"] = False
                power_status["power_restored_time"] = None
                power_status["on_battery_since"] = None

                logger.info(
                    "%s computadores foram ligados após a " "restauração de energia.",
                    poweron_count,
                )

            # Salva o status atual
            save_power_status(power_status)

            # Aguarda o próximo ciclo
            time.sleep(CHECK_INTERVAL)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Erro no ciclo de monitoramento: %s", e)
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logger.info("Serviço de monitoramento encerrado pelo usuário.")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Erro não tratado no serviço de monitoramento: %s", e)
