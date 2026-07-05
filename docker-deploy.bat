@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 闲鱼自动回复系统 Docker 部署脚本 (Windows版本)
REM 支持快速部署和管理

title 闲鱼自动回复系统 Docker 部署

REM 项目配置
set PROJECT_NAME=xianyu-auto-reply
set COMPOSE_FILE=docker-compose.yml

REM 颜色定义（Windows CMD不支持ANSI颜色，使用echo代替）
set "INFO_PREFIX=[INFO]"
set "SUCCESS_PREFIX=[SUCCESS]"
set "WARNING_PREFIX=[WARNING]"
set "ERROR_PREFIX=[ERROR]"

REM 检查依赖
echo %INFO_PREFIX% 检查系统依赖...

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR_PREFIX% Docker 未安装，请先安装 Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

where docker-compose >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR_PREFIX% Docker Compose 未安装，请先安装 Docker Compose
    pause
    exit /b 1
)

echo %SUCCESS_PREFIX% 系统依赖检查通过

REM 初始化配置
echo %INFO_PREFIX% 初始化配置文件...

REM 检查关键文件
if not exist "entrypoint.sh" (
    echo %ERROR_PREFIX% entrypoint.sh 文件不存在，Docker容器将无法启动
    echo %INFO_PREFIX% 请确保项目文件完整
    pause
    exit /b 1
) else (
    echo %SUCCESS_PREFIX% entrypoint.sh 文件已存在
)

if not exist "global_config.yml" (
    echo %ERROR_PREFIX% global_config.yml 配置文件不存在
    echo %INFO_PREFIX% 请确保配置文件存在
    pause
    exit /b 1
) else (
    echo %SUCCESS_PREFIX% global_config.yml 配置文件已存在
)

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
if not exist "static\uploads\images" mkdir static\uploads\images
echo %SUCCESS_PREFIX% 已创建必要的目录

REM 处理命令行参数
if "%1"=="" goto quick_deploy
if "%1"=="help" goto show_help
if "%1"=="start" goto start_services
if "%1"=="stop" goto stop_services
if "%1"=="restart" goto restart_services
if "%1"=="status" goto show_status
if "%1"=="logs" goto show_logs
if "%1"=="build" goto build_image
if "%1"=="cleanup" goto cleanup
goto unknown_command

:quick_deploy
echo %INFO_PREFIX% 快速部署模式
goto build_and_start

:build_image
echo %INFO_PREFIX% 构建 Docker 镜像...
set /p use_cn="是否使用国内镜像源？(y/n): "
if /i "!use_cn!"=="y" (
    docker-compose -f docker-compose-cn.yml build --no-cache
) else (
    docker-compose build --no-cache
)
if %errorlevel% neq 0 (
    echo %ERROR_PREFIX% 镜像构建失败
    pause
    exit /b 1
)
echo %SUCCESS_PREFIX% 镜像构建完成
goto end

:build_and_start
call :build_image
if %errorlevel% neq 0 exit /b 1

:start_services
echo %INFO_PREFIX% 启动服务...
docker-compose up -d
if %errorlevel% neq 0 (
    echo %ERROR_PREFIX% 服务启动失败
    docker-compose logs
    pause
    exit /b 1
)

echo %SUCCESS_PREFIX% 服务启动完成

REM 等待服务就绪
echo %INFO_PREFIX% 等待服务就绪...
timeout /t 10 /nobreak >nul

REM 检查服务状态
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo %SUCCESS_PREFIX% 服务运行正常
    call :show_access_info
) else (
    echo %ERROR_PREFIX% 服务启动失败
    docker-compose logs
    pause
    exit /b 1
)
goto end

:stop_services
echo %INFO_PREFIX% 停止服务...
docker-compose down
echo %SUCCESS_PREFIX% 服务已停止
goto end

:restart_services
echo %INFO_PREFIX% 重启服务...
docker-compose restart
echo %SUCCESS_PREFIX% 服务已重启
goto end

:show_status
echo %INFO_PREFIX% 服务状态:
docker-compose ps
echo.
echo %INFO_PREFIX% 资源使用:
for /f "tokens=*" %%i in ('docker-compose ps -q') do (
    docker stats --no-stream %%i
)
goto end

:show_logs
if "%2"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %2
)
goto end

:cleanup
echo %WARNING_PREFIX% 这将删除所有容器、镜像和数据，确定要继续吗？
set /p confirm="请输入 y 确认: "
if /i "!confirm!"=="y" (
    echo %INFO_PREFIX% 清理环境...
    docker-compose down -v --rmi all
    rmdir /s /q data logs backups 2>nul
    echo %SUCCESS_PREFIX% 环境清理完成
) else (
    echo %INFO_PREFIX% 取消清理操作
)
goto end

:show_access_info
echo.
echo %SUCCESS_PREFIX% 🎉 部署完成！
echo.
echo 📱 访问地址:
echo    HTTP: http://localhost:8080
echo.
echo 🔐 默认登录信息:
echo    用户名: admin
echo    密码:   admin123
echo.
echo 📊 管理命令:
echo    查看状态: %~nx0 status
echo    查看日志: %~nx0 logs
echo    重启服务: %~nx0 restart
echo    停止服务: %~nx0 stop
echo.
goto :eof

:show_help
echo 闲鱼自动回复系统 Docker 部署脚本 (Windows版本)
echo.
echo 用法: %~nx0 [命令]
echo.
echo 命令:
echo   start     启动服务
echo   stop      停止服务
echo   restart   重启服务
echo   status    查看服务状态
echo   logs      查看日志
echo   build     构建镜像
echo   cleanup   清理环境
echo   help      显示帮助信息
echo.
echo 示例:
echo   %~nx0         # 快速部署
echo   %~nx0 start   # 启动服务
echo   %~nx0 logs    # 查看日志
echo.
goto end

:unknown_command
echo %ERROR_PREFIX% 未知命令: %1
call :show_help
exit /b 1

:end
if "%1"=="" (
    echo.
    echo 按任意键退出...
    pause >nul
)
