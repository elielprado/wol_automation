"""
Modulo para envio de notificacoes por email usando SMTP.
Suporta mensagens HTML formatadas com templates Jinja2.
"""

import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import datetime

# Constantes
EMAIL_CONFIG_FILE = "email_config.json"
TEMPLATES_DIR = "templates"
GENERATED_HTML = "notification.html"
LOGO_URL = "https://raw.githubusercontent.com/elielprado/wol_automation/main/wol_automation/assets/wol_logo.png"

# Verificar se a pasta de templates existe, senao criar
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)


def load_email_config():
    """Carrega a configuracao de email do arquivo JSON."""
    default_config = {
        "enabled": False,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "",
        "password": "",
        "from_address": "",
        "recipients": [],
        "notification_events": {
            "power_disconnected": True,
            "power_restored": True,
            "shutdown_initiated": True,
            "poweron_initiated": True,
            "low_battery": True,
        }
    }

    if os.path.exists(EMAIL_CONFIG_FILE):
        try:
            with open(EMAIL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Garantir que todas as chaves padrao existam
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    # Verificar campos aninhados (notification_events)
                    elif key == "notification_events" and isinstance(value, dict):
                        for event_key, event_value in value.items():
                            if event_key not in config[key]:
                                config[key][event_key] = event_value
                return config
        except json.JSONDecodeError:
            print("Erro ao ler {}. Usando configuracao padrao.".format(EMAIL_CONFIG_FILE))
            return default_config
    else:
        # Cria um arquivo de configuracao padrao
        with open(EMAIL_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config


def save_email_config(config):
    """Salva a configuracao de email no arquivo JSON."""
    with open(EMAIL_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)


def render_template(template_name, context):
    """
    Renderiza um template usando Jinja2.
    
    Args:
        template_name (str): Nome do arquivo de template
        context (dict): Variaveis para o template
        
    Returns:
        str: HTML renderizado
    """
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(template_name)
    return template.render(**context)


def create_default_template():
    """Cria um template padrao se nao existir."""
    template_path = os.path.join(TEMPLATES_DIR, GENERATED_HTML)
    if not os.path.exists(template_path):
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #fcfaf9; /* Cor de fundo atualizada */
        }
        .header {
            background-color: #f26522; /* Laranja da logo */
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            border: 1px solid #ddd;
            border-top: none;
            padding: 20px;
            border-radius: 0 0 5px 5px;
            background-color: #fff;
        }
        .info-row {
            margin-bottom: 10px;
            display: flex;
        }
        .info-label {
            width: 150px;
            font-weight: bold;
        }
        .footer {
            margin-top: 20px;
            font-size: 0.8em;
            text-align: center;
            color: #777;
        }
        .status-ok {
            color: #28a745;
            font-weight: bold;
        }
        .status-warning {
            color: #ffc107;
            font-weight: bold;
        }
        .status-critical {
            color: #dc3545;
            font-weight: bold;
        }
        .branding {
            text-align: center;
            margin: 20px 0 30px 0;
            padding-bottom: 15px;
            border-bottom: 1px solid #ddd;
        }
        .logo {
            max-width: 200px;
            height: auto;
        }
        h3 {
            color: #f26522; /* Laranja da logo para os títulos */
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        .event-title {
            color: #333;
            font-size: 22px;
            margin-top: 0;
            margin-bottom: 15px;
        }
        .message {
            background-color: #f5f5f5;
            padding: 10px 15px;
            border-left: 4px solid #f26522;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
    </div>
    
    <div class="content">
        <div class="branding">
            <img src="{{ logo_url }}" alt="WOL AUTOMATION" class="logo">
        </div>
        
        <h2 class="event-title">{{ event_type }}</h2>
        <div class="message">{{ message }}</div>
        
        {% if computers %}
        <h3>Computadores Afetados:</h3>
        <ul>
            {% for computer in computers %}
            <li>{{ computer.name }} ({{ computer.hostname }})</li>
            {% endfor %}
        </ul>
        {% endif %}
        
        <h3>Detalhes do Evento:</h3>
        <div class="info-row">
            <div class="info-label">Data/Hora:</div>
            <div>{{ timestamp }}</div>
        </div>
        <div class="info-row">
            <div class="info-label">Status de Energia:</div>
            <div class="{{ 'status-ok' if on_power else 'status-critical' }}">
                {{ "Conectado" if on_power else "Desconectado" }}
            </div>
        </div>
        {% if battery_percent is defined and battery_percent is not none %}
        <div class="info-row">
            <div class="info-label">Bateria:</div>
            <div class="
                {{ 'status-ok' if battery_percent > 50 else 
                  ('status-warning' if battery_percent > 20 else 'status-critical') }}">
                {{ battery_percent }}%
            </div>
        </div>
        {% endif %}
        {% if on_battery_time is defined and on_battery_time is not none %}
        <div class="info-row">
            <div class="info-label">Tempo sem energia:</div>
            <div>{{ on_battery_time }} minutos</div>
        </div>
        {% endif %}
    </div>
    
    <div class="footer">
        <p>Este é um email automático do sistema WoL Automation - não responda a este email.</p>
        <p>© Sistema de Gerenciamento de Energia Remota</p>
    </div>
</body>
</html>""")


def send_email(subject, template_name, context):
    """
    Envia um email usando SMTP com o template especificado.
    
    Args:
        subject (str): Assunto do email
        template_name (str): Nome do arquivo de template
        context (dict): Variaveis para o template
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrario
    """
    config = load_email_config()
    
    # Verifica se o envio de emails esta habilitado
    if not config["enabled"]:
        print("Envio de emails desabilitado nas configuracoes.")
        return False
    
    # Verifica se ha destinatarios
    if not config["recipients"]:
        print("Nenhum destinatario configurado para receber emails.")
        return False
    
    # Adiciona a URL da logo ao contexto
    if "logo_url" not in context:
        context["logo_url"] = LOGO_URL
    
    # Garante que variaveis opcionais estejam definidas como None se não existirem
    if "battery_percent" not in context:
        context["battery_percent"] = None
    
    if "on_battery_time" not in context:
        context["on_battery_time"] = None
    
    if "on_power" not in context:
        context["on_power"] = True
    
    # Tenta renderizar o template
    try:
        html_content = render_template(template_name, context)
    except Exception as e:  # pylint: disable=broad-except
        print("Erro ao renderizar o template de email: {}".format(e))
        return False
    
    # Configura a mensagem
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = config["from_address"]
    msg['To'] = ", ".join(config["recipients"])
    
    # Adiciona a versão HTML
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Tenta enviar o email
    try:
        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.ehlo()
        server.starttls()
        server.login(config["username"], config["password"])
        server.sendmail(config["from_address"], config["recipients"], msg.as_string())
        server.close()
        print("Email enviado com sucesso para: {}".format(", ".join(config["recipients"])))
        return True
    except Exception as e:  # pylint: disable=broad-except
        print("Erro ao enviar email: {}".format(e))
        return False


def send_notification(event_type, message, extra_context=None):
    """
    Envia uma notificacao por email para um evento especifico.
    
    Args:
        event_type (str): Tipo de evento (power_disconnected, power_restored, etc)
        message (str): Mensagem principal da notificacao
        extra_context (dict, optional): Contexto adicional para o template
        
    Returns:
        bool: True se a notificacao foi enviada, False caso contrario
    """
    config = load_email_config()
    
    # Verifica se o evento esta habilitado para notificacao
    if event_type not in config["notification_events"] or not config["notification_events"][event_type]:
        print("Notificacoes para o evento '{}' estao desabilitadas.".format(event_type))
        return False
    
    # Mapeia o tipo de evento para um titulo amigavel
    event_titles = {
        "power_disconnected": "Alerta: Energia Desconectada",
        "power_restored": "Informação: Energia Restaurada",
        "shutdown_initiated": "Alerta: Desligamento Iniciado",
        "poweron_initiated": "Informação: Inicialização Remota",
        "low_battery": "Alerta Crítico: Bateria Fraca"
    }
    
    title = event_titles.get(event_type, "Notificação do Sistema")
    subject = "WoL Automation - {}".format(title)
    
    # Prepara o contexto base para o template
    context = {
        "title": title,
        "event_type": title,
        "message": message,
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "logo_url": LOGO_URL,
        "battery_percent": None,
        "on_battery_time": None,
        "on_power": True
    }
    
    # Adiciona o contexto extra, se fornecido
    if extra_context:
        context.update(extra_context)
    
    # Cria o template padrao se nao existir
    create_default_template()
    
    # Envia a notificacao
    return send_email(subject, GENERATED_HTML, context)


def test_email_config():
    """
    Testa a configuracao de email enviando um email de teste.
    
    Returns:
        bool: True se o teste foi bem-sucedido, False caso contrario
    """
    print("Enviando email de teste...")
    
    context = {
        "title": "Teste de Configuração",
        "event_type": "Teste de Email",
        "message": "Esta é uma mensagem de teste para verificar a configuração de email.",
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "on_power": True,
        "battery_percent": 85,
        "logo_url": LOGO_URL
    }
    
    # Cria o template padrao se nao existir
    create_default_template()
    
    return send_email("WoL Automation - Teste de Email", GENERATED_HTML, context)


# Garante que o template padrao seja criado quando o modulo e importado
create_default_template()