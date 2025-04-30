@echo off
:: Script para instalar o serviço de monitoramento como uma tarefa agendada no Windows
:: Precisa ser executado como administrador

echo Instalando o serviço de monitoramento de energia como tarefa agendada...

:: Obtém o diretório atual
set "CURRENT_DIR=%cd%"

:: Nome da tarefa
set "TASK_NAME=PowerMonitorService"

:: Cria um arquivo XML temporário para a definição da tarefa
set "TEMP_XML=%TEMP%\power_monitor_task.xml"

echo ^<?xml version="1.0" encoding="UTF-16"?^> > "%TEMP_XML%"
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^> >> "%TEMP_XML%"
echo   ^<RegistrationInfo^> >> "%TEMP_XML%"
echo     ^<Description^>Serviço de monitoramento de energia para desligamento automático de computadores^</Description^> >> "%TEMP_XML%"
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
echo       ^<Arguments^>"%CURRENT_DIR%\monitor_service.py"^</Arguments^> >> "%TEMP_XML%"
echo       ^<WorkingDirectory^>%CURRENT_DIR%^</WorkingDirectory^> >> "%TEMP_XML%"
echo     ^</Exec^> >> "%TEMP_XML%"
echo   ^</Actions^> >> "%TEMP_XML%"
echo ^</Task^> >> "%TEMP_XML%"

:: Cria a tarefa usando o arquivo XML
schtasks /Create /TN "%TASK_NAME%" /XML "%TEMP_XML%" /F

:: Verifica se a criação foi bem-sucedida
if %ERRORLEVEL% EQU 0 (
    echo Tarefa agendada "%TASK_NAME%" criada com sucesso.
    echo Para iniciar a tarefa manualmente: schtasks /Run /TN "%TASK_NAME%"
    echo Para verificar o status: schtasks /Query /TN "%TASK_NAME%"
    
    :: Inicia a tarefa
    schtasks /Run /TN "%TASK_NAME%"
    echo Tarefa iniciada.
) else (
    echo Erro ao criar a tarefa agendada. Verifique se você está executando como administrador.
)

:: Remove o arquivo XML temporário
del "%TEMP_XML%"

pause