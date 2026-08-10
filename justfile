set dotenv-load := true

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# 编译 Docker 镜像
build:
    docker build -t my-pi-lab -f ../Dockerfile ..

# 进入 Docker 沙盒环境
lab:
    docker run -it --rm \
        -p 5174:5174 \
        -v "${PWD}:/workspace" \
        -v "${HOME}/.pi:/root/.pi" \
        -v "C:\projects\my-tech-notebook:/vault" \
        --env-file .env \
        -e OBSIDIAN_VAULT_PATH=/vault \
        my-pi-lab bash

# 加载 theme-cycler 环境
theme:
    pi -e .pi/extensions/theme-cycler.ts

theme-min:
    pi -e .pi/extensions/theme-cycler.ts -e extensions/minimal.ts

theme-damage-control:
    pi -e .pi/extensions/theme-cycler.ts -e extensions/damage-control.ts

tilldone:
    pi -e .pi/extensions/tilldone.ts
