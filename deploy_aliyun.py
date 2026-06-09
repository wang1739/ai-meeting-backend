#!/usr/bin/env python3
"""
阿里云 ECS 一键部署脚本 - AI 会议助手后端（含 PostgreSQL 自建）
"""
import paramiko
import time
import sys

HOST = "118.31.249.156"
USER = "root"
PASSWORD = "wmm.12345."

def run_cmd(ssh, cmd, timeout=120):
    """执行命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return exit_code, out.strip(), err.strip()

def run_script(ssh, script, timeout=300):
    """执行一段 shell 脚本"""
    stdin, stdout, stderr = ssh.exec_command("bash -s", timeout=timeout)
    stdin.write(script)
    stdin.close()
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return exit_code, out.strip(), err.strip()

def main():
    print("=" * 60)
    print("Aliyun ECS Deploy - AI Meeting Backend")
    print("=" * 60)

    # 连接 SSH
    print("\n[1/7] Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        print(f"  [+] Connected to {HOST}")
    except Exception as e:
        print(f"  [x] Connection failed: {e}")
        sys.exit(1)

    # 检测系统类型
    code, os_type, _ = run_cmd(ssh, "cat /etc/os-release 2>/dev/null | head -3")
    print(f"  OS: {os_type[:80]}")

    # ====== 安装 Node.js 20 ======
    print("\n[2/7] Installing Node.js 20 + PM2...")
    code, out, _ = run_cmd(ssh, "node --version 2>/dev/null || echo 'not_found'")
    if "not_found" in out:
        print("  -> Installing Node.js 20...")
        install_script = """
set -e
curl -fsSL https://fnm.vercel.app/install | bash
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"
fnm install 20
fnm use 20
fnm default 20
echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc
node --version
"""
        code, out, err = run_script(ssh, install_script, timeout=120)
        print(f"  [+] Node.js {out}")
        # 安装 PM2
        run_cmd(ssh, 'export PATH="$HOME/.local/share/fnm:$PATH" && npm install -g pm2', timeout=60)
        print("  [+] PM2 installed")
    else:
        print(f"  [+] Node.js already installed: {out}")
        run_cmd(ssh, 'export PATH="$HOME/.local/share/fnm:$PATH" && npm install -g pm2 2>/dev/null', timeout=30)

    # ====== 安装 PostgreSQL ======
    print("\n[3/7] Installing PostgreSQL...")
    code, out, _ = run_cmd(ssh, "psql --version 2>/dev/null || echo 'not_found'")
    if "not_found" in out:
        pg_install = """
set -ex
if [ -f /etc/redhat-release ]; then
    dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm 2>/dev/null || \
    yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm 2>/dev/null || true
    dnf install -y postgresql16-server 2>/dev/null || yum install -y postgresql16-server 2>/dev/null || true
elif [ -f /etc/debian_version ]; then
    apt-get update && apt-get install -y postgresql postgresql-client
fi
if ! command -v psql &>/dev/null; then
    yum install -y postgresql-server postgresql-contrib 2>/dev/null || \
    apt-get install -y postgresql postgresql-client 2>/dev/null || true
fi
"""
        run_script(ssh, pg_install, timeout=180)
        time.sleep(3)

        # 初始化并启动 PostgreSQL
        init_cmds = """
if command -v postgresql-16-setup &>/dev/null; then
    postgresql-16-setup initdb
    systemctl enable postgresql-16
    systemctl start postgresql-16
elif command -v postgresql-setup &>/dev/null; then
    postgresql-setup initdb
    systemctl enable postgresql
    systemctl start postgresql
else
    systemctl enable postgresql 2>/dev/null || true
    systemctl start postgresql 2>/dev/null || true
fi
sleep 2
systemctl status postgresql 2>/dev/null || systemctl status postgresql-16 2>/dev/null || pg_isready || echo "checking..."
"""
        run_script(ssh, init_cmds, timeout=30)

        # 创建数据库和用户
        create_db = """
set -ex
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || true
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || true
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
echo "DB setup done"
"""
        run_script(ssh, create_db, timeout=15)

        # 配置 pg_hba.conf 允许密码登录
        config_pg = """
set -ex
PG_HBA=$(find / -name "pg_hba.conf" -type f 2>/dev/null | head -1)
if [ -n "$PG_HBA" ]; then
    sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA"
    systemctl restart postgresql 2>/dev/null || systemctl restart postgresql-16 2>/dev/null
    echo "pg_hba configured"
fi
"""
        run_script(ssh, config_pg, timeout=15)
        print("  [+] PostgreSQL installed, database ai_meeting created")
    else:
        print(f"  [+] PostgreSQL already installed: {out}")

    # ====== 拉取代码 ======
    print("\n[4/7] Pulling code from GitHub...")
    run_cmd(ssh, "rm -rf /root/ai-meeting-backend")
    code, out, err = run_cmd(ssh, "cd /root && git clone https://github.com/wang1739/ai-meeting-backend.git", timeout=120)
    if code != 0:
        print(f"  [x] Clone failed: {err}")
        sys.exit(1)
    print("  [+] Code cloned")

    # ====== 配置环境变量 ======
    print("\n[5/7] Configuring environment variables...")

    code, pg_status, _ = run_cmd(ssh, "systemctl is-active postgresql 2>/dev/null || systemctl is-active postgresql-16 2>/dev/null || echo 'unknown'")
    print(f"  PostgreSQL status: {pg_status}")

    db_url = "postgresql://meeting_admin:Meeting@2024!@localhost:5432/ai_meeting?schema=public"

    env_content = f"""DATABASE_URL={db_url}
JWT_SECRET=ai-meeting-jwt-secret-key-2024
JWT_EXPIRES_IN=7d
PORT=3000
NODE_ENV=production
"""
    run_cmd(ssh, "cat > /root/ai-meeting-backend/.env << 'ENVEOF'\n" + env_content + "ENVEOF")
    print(f"  [+] .env configured\n  DATABASE_URL: {db_url}")

    # ====== 安装依赖 + Prisma 迁移 ======
    print("\n[6/7] Installing deps + DB migration + Build...")

    setup_script = """
set -ex
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"
cd /root/ai-meeting-backend
npm install
npx prisma generate
npx prisma db push
npm run build
echo "Build complete"
"""
    code, out, err = run_script(ssh, setup_script, timeout=300)
    if code != 0:
        print(f"  [w] Some warnings: {err[-300:]}")
    print("  [+] Dependencies installed, DB initialized, Build complete")

    # ====== PM2 + Nginx ======
    print("\n[7/7] PM2 start + Nginx reverse proxy...")

    pmd_script = """
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
pm2 startup systemd -u root --hp /root 2>/dev/null || true
"""
    run_script(ssh, pmd_script, timeout=30)
    time.sleep(3)

    # 安装并配置 Nginx
    nginx_setup = """
set -ex
if ! command -v nginx &>/dev/null; then
    yum install -y nginx 2>/dev/null || apt-get install -y nginx 2>/dev/null || true
fi
"""
    run_script(ssh, nginx_setup, timeout=60)

    nginx_conf = """server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    location /health {
        proxy_pass http://127.0.0.1:3000/api/meetings;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
"""
    run_cmd(ssh, "cat > /etc/nginx/conf.d/ai-meeting.conf << 'NGINXEOF'\n" + nginx_conf + "NGINXEOF")

    firewall_check = """
set -ex
if command -v firewall-cmd &>/dev/null; then
    firewall-cmd --add-port=80/tcp --permanent 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
fi
nginx -t
systemctl enable nginx 2>/dev/null || true
systemctl restart nginx
echo "Nginx restarted"
"""
    code, out, err = run_script(ssh, firewall_check, timeout=20)
    print(f"  Nginx: {out[-100:]}" if out else "  Nginx configured")

    # ====== 验证 ======
    print("\n" + "=" * 60)
    print("Verifying deployment...")
    time.sleep(3)

    code, out, err = run_cmd(ssh, "curl -s --connect-timeout 5 http://localhost:3000/api/meetings", timeout=15)
    print(f"  Local API test: {out[:150] if out else 'empty'}")

    code, out, err = run_cmd(ssh, "curl -s --connect-timeout 5 http://localhost/api/meetings", timeout=15)
    print(f"  Nginx proxy test: {out[:150] if out else 'empty'}")

    code, out, err = run_cmd(ssh, "pm2 list", timeout=10)
    print(f"  PM2 status:\n{out}")

    print("\n" + "=" * 60)
    print("[OK] Aliyun ECS Deployment Complete!")
    print(f"    Backend API: http://{HOST}/api")
    print(f"    WebSocket: ws://{HOST}/socket.io")
    print("=" * 60)
    print("\nIMPORTANT:")
    print("  1. Open port 80 in Aliyun security group")
    print("     Login Aliyun Console -> Security Group -> Add Rule")
    print("     CIDR: 0.0.0.0/0  Port: 80  Protocol: TCP")
    print("  2. For HTTPS, configure SSL cert later")

    ssh.close()

if __name__ == "__main__":
    main()
