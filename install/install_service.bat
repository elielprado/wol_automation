@echo off
:: Script para instalar o serviço de monitoramento como uma tarefa agendada no Windows
:: Precisa ser executado como administrador

echo Instalando o serviço de monitoramento de energia como tarefa agendada...

:: Obtém o diretório atual (da pasta install)
set "INSTALL_DIR=%cd%"
:: Diretório principal do projeto (um nível acima)
set "PROJECT_DIR=%INSTALL_DIR%\.."

:: Verificar se Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python não foi encontrado. Por favor, instale o Python antes de continuar.
    goto :end
)

:: Verificar dependências necessárias
echo Verificando dependências...
python -c "import importlib.util; sys.exit(0 if 'psutil' in sys.modules or importlib.util.find_spec('psutil') is not None else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependência: psutil
    pip install psutil
)

python -c "import importlib.util; sys.exit(0 if 'paramiko' in sys.modules or importlib.util.find_spec('paramiko') is not None else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependência: paramiko
    pip install paramiko
)

python -c "import importlib.util; sys.exit(0 if 'jinja2' in sys.modules or importlib.util.find_spec('jinja2') is not None else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependência: jinja2
    pip install jinja2
)

python -c "import importlib.util; sys.exit(0 if 'requests' in sys.modules or importlib.util.find_spec('requests') is not None else 1)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependência: requests
    pip install requests
)

:: Criar pastas necessárias caso não existam
if not exist "%PROJECT_DIR%\assets" mkdir "%PROJECT_DIR%\assets"
if not exist "%PROJECT_DIR%\templates" mkdir "%PROJECT_DIR%\templates"

:: Nome da tarefa
set "TASK_NAME=WoLAutomationService"

:: Cria um arquivo XML temporário para a definição da tarefa
set "TEMP_XML=%TEMP%\wol_automation_task.xml"

echo ^<?xml version="1.0" encoding="UTF-16"?^> > "%TEMP_XML%"
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^> >> "%TEMP_XML%"
echo   ^<RegistrationInfo^> >> "%TEMP_XML%"
echo     ^<Description^>WoL Automation - Serviço de monitoramento de energia para desligamento/inicialização automática de computadores^</Description^> >> "%TEMP_XML%"
echo   ^</RegistrationInfo^> >> "%TEMP_XML%"
echo   ^<Triggers^> >> "%TEMP_XML%"
echo     ^<BootTrigger^> >> "%TEMP_XML%"
echo       ^<Enabled^>true^</Enabled^> >> "%TEMP_XML%"
echo     ^</BootTrigger^> >> "%TEMP_XML%"
echo   ^</Triggers^> >> "%TEMP_XML%"
echo   ^<Principals^> >> "%TEMP_XML%"
echo     ^<Principal id="Author"^> >> "%TEMP_XML%"
echo       ^<LogonType^>InteractiveToken^</LogonType^> >> "%TEMP_XML%"
echo       ^<RunLevel^>HighestAvailable^</RunLevel^> >> "%TEMP_XML%"
echo     ^</Principal^> >> "%TEMP_XML%"
echo   ^</Principals^> >> "%TEMP_XML%"
echo   ^<Settings^> >> "%TEMP_XML%"
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^> >> "%TEMP_XML%"
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^> >> "%TEMP_XML%"
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^> >> "%TEMP_XML%"
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^> >> "%TEMP_XML%"
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^> >> "%TEMP_XML%"
echo     ^<RunOnlyIfNetworkAvailable^>false^</RunOnlyIfNetworkAvailable^> >> "%TEMP_XML%"
echo     ^<IdleSettings^> >> "%TEMP_XML%"
echo       ^<StopOnIdleEnd^>false^</StopOnIdleEnd^> >> "%TEMP_XML%"
echo       ^<RestartOnIdle^>false^</RestartOnIdle^> >> "%TEMP_XML%"
echo     ^</IdleSettings^> >> "%TEMP_XML%"
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^> >> "%TEMP_XML%"
echo     ^<Enabled^>true^</Enabled^> >> "%TEMP_XML%"
echo     ^<Hidden^>false^</Hidden^> >> "%TEMP_XML%"
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^> >> "%TEMP_XML%"
echo     ^<WakeToRun^>false^</WakeToRun^> >> "%TEMP_XML%"
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^> >> "%TEMP_XML%"
echo     ^<Priority^>7^</Priority^> >> "%TEMP_XML%"
echo     ^<RestartOnFailure^> >> "%TEMP_XML%"
echo       ^<Interval^>PT1M^</Interval^> >> "%TEMP_XML%"
echo       ^<Count^>3^</Count^> >> "%TEMP_XML%"
echo     ^</RestartOnFailure^> >> "%TEMP_XML%"
echo   ^</Settings^> >> "%TEMP_XML%"
echo   ^<Actions Context="Author"^> >> "%TEMP_XML%"
echo     ^<Exec^> >> "%TEMP_XML%"
echo       ^<Command^>python.exe^</Command^> >> "%TEMP_XML%"
echo       ^<Arguments^>"%PROJECT_DIR%\monitor_service.py"^</Arguments^> >> "%TEMP_XML%"
echo       ^<WorkingDirectory^>%PROJECT_DIR%^</WorkingDirectory^> >> "%TEMP_XML%"
echo     ^</Exec^> >> "%TEMP_XML%"
echo   ^</Actions^> >> "%TEMP_XML%"
echo ^</Task^> >> "%TEMP_XML%"

:: Cria a tarefa usando o arquivo XML
schtasks /Create /TN "%TASK_NAME%" /XML "%TEMP_XML%" /F

:: Verifica se a criação foi bem-sucedida
if %ERRORLEVEL% EQU 0 (
    echo Tarefa agendada "%TASK_NAME%" criada com sucesso.
    echo.
    echo Para iniciar a tarefa manualmente: schtasks /Run /TN "%TASK_NAME%"
    echo Para verificar o status: schtasks /Query /TN "%TASK_NAME%"
    
    :: Inicia a tarefa
    schtasks /Run /TN "%TASK_NAME%"
    echo Tarefa iniciada.
    
    echo.
    echo Nota: Esse script baixará automaticamente o PSTools se necessário
    echo ao executar operações de desligamento remoto em computadores Windows.
) else (
    echo Erro ao criar a tarefa agendada. Verifique se você está executando como administrador.
)

:: Remove o arquivo XML temporário
del "%TEMP_XML%"

:end
pause