import os
import shutil
import platform
import subprocess
import yaml

# 定义一些常量
NEBULA_BINARIES_CERT = {
    "darwin": "nebula-darwin/nebula-cert",
    "linux": "nebula-linux-amd64/nebula-cert",
    "windows": "nebula-windows-amd64/nebula-cert.exe",
}

NEBULA_BINARIES_BIN = {
    "darwin": "nebula-darwin/nebula",
    "linux": "nebula-linux-amd64/nebula",
    "windows": "nebula-windows-amd64/nebula.exe",
}

CONFIG_TEMPLATE = "config.yml"
NODES_DIR = "nodes"
NODE_INFO_FILE = "node_info.txt"

# 确保目录和文件存在
if not os.path.exists(NODES_DIR):
    os.makedirs(NODES_DIR)

if not os.path.exists(NODE_INFO_FILE):
    with open(NODE_INFO_FILE, "w") as f:
        pass

# 检查系统类型
system_type = platform.system().lower()
nebula_binary = NEBULA_BINARIES_CERT.get(system_type, "nebula-linux-amd64/nebula-cert")

# 询问用户初始化还是创建节点
action = input("请选择操作: 1) 初始化 2) 创建节点 (输入 1 或 2): ")

if action == "1":
    ca_name = input("请输入CA名称 (默认: MyNebulaCA): ") or "MyNebulaCA"
    subprocess.run([nebula_binary, "ca", "-name", ca_name], check=True)
    print("CA 已初始化")

elif action == "2":
    node_name = input("请输入节点名称: ")
    node_ip = input("请输入节点IP地址: ")
    is_lighthouse = input("是否为lighthouse节点? (y/n): ").lower() == "y"

    node_dir = os.path.join(NODES_DIR, node_name)
    if not os.path.exists(node_dir):
        os.makedirs(node_dir)

    # 生成节点证书
    subprocess.run(
        [nebula_binary, "sign", "-name", node_name, "-ip", node_ip], check=True
    )
    shutil.move(f"{node_name}.crt", f"{node_dir}/host.crt")
    shutil.move(f"{node_name}.key", f"{node_dir}/host.key")
    shutil.copyfile("ca.crt", f"{node_dir}/ca.crt")

    # 拷贝nebula二进制文件，并设置可执行权限
    for bin_name, bin_path in NEBULA_BINARIES_BIN.items():
        if os.path.exists(bin_path):
            if bin_name == "windows":
                dest_path = os.path.join(node_dir, "nebula-windows.exe")
            else:
                dest_path = os.path.join(node_dir, f"nebula-{bin_name.split('/')[0]}")

            shutil.copyfile(bin_path, dest_path)
            if system_type != "windows":
                os.chmod(dest_path, 0o755)  # 设置可执行权限

    # 创建并修改配置文件
    with open(CONFIG_TEMPLATE, "r") as config_file:
        config_data = yaml.safe_load(config_file)

    # 修改配置文件中的字段
    config_data["pki"]["ca"] = "ca.crt"
    config_data["pki"]["cert"] = "host.crt"
    config_data["pki"]["key"] = "host.key"

    if is_lighthouse:
        config_data["static_host_map"] = {}
        config_data["lighthouse"] = {"am_lighthouse": True}
    else:
        lighthouse_ip = input("请输入lighthouse的IP地址: ")
        lighthouse_public_ip = input("请输入lighthouse的真实开放IP地址: ")
        config_data["static_host_map"] = {
            lighthouse_ip: [f"{lighthouse_public_ip}:4242"]
        }
        config_data["lighthouse"] = {
            "am_lighthouse": False,
            "interval": 60,
            "hosts": [lighthouse_ip],
        }

    with open(os.path.join(node_dir, "config.yml"), "w") as config_file:
        yaml.safe_dump(config_data, config_file)

    # 记录节点信息
    with open(NODE_INFO_FILE, "a") as info_file:
        info_file.write(
            f"{node_name} {node_ip} {'lighthouse' if is_lighthouse else 'node'}\n"
        )

    # 创建属性记录文件
    with open(os.path.join(node_dir, "node_info.txt"), "w") as info_file:
        info_file.write(f"名称: {node_name}\n")
        info_file.write(f"IP地址: {node_ip}\n")
        info_file.write(f"类型: {'lighthouse' if is_lighthouse else 'node'}\n")

    # 创建启动脚本
    with open(os.path.join(node_dir, "start.sh"), "w") as start_file:
        start_file.write(f"#!/bin/bash\n")
        start_file.write(f'case "$(uname -s)" in\n')
        start_file.write(
            f"  Linux*)   exec sudo ./nebula-linux -config config.yml ;;\n"
        )
        start_file.write(
            f"  Darwin*)  exec sudo ./nebula-darwin -config config.yml ;;\n"
        )
        start_file.write(
            f"  CYGWIN*|MINGW32*|MSYS*|MINGW*) exec ./nebula-windows.exe -config config.yml ;;\n"
        )
        start_file.write(f'  *)        echo "Unknown OS" ;;\n')
        start_file.write(f"esac\n")
    os.chmod(os.path.join(node_dir, "start.sh"), 0o755)

    # 创建 Windows 启动脚本
    with open(os.path.join(node_dir, "start.bat"), "w") as start_file:
        start_file.write(f"@echo off\n")
        start_file.write(
            f"if not exist C:\\Program Files\\TAP-Windows\\bin\\tapinstall.exe (\n"
        )
        start_file.write(
            f"    echo TAP-Windows 驱动程序未安装. 请先安装 TAP-Windows 驱动程序.\n"
        )
        start_file.write(f"    exit /b 1\n")
        start_file.write(f")\n")
        start_file.write(f"nebula-windows.exe -config config.yml\n")

    print(f"节点 {node_name} 已创建")
else:
    print("无效的操作")
