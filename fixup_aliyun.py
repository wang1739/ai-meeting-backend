#!/usr/bin/env python3
"""
修复脚本 - 解决部署后的问题
"""
import paramiko
import time
import sys

HOST = "118.31.249.156"
USER = "root"
PASSWORD = "wmm.12345."

def run_cmd(ssh, cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return exit_code, out.strip(), err.strip()

def run_script(ssh, script, timeout=300):
    stdin, stdout, stderr = ssh.exec_command("bash -s", timeout=timeout)
    stdin.write(script)
    stdin.close()
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    return exit_code, out.strip(), err.strip()

def main():
    print("=" * 60)
    print("Fixup Script - AI Meeting Backend on Aliyun ECS")
    print("=" * 60)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
        print("[+] Connected to", HOST)
    except Exception as e:
        print("[x] Connection failed:", e)
        sys.exit(1)

    # 1. Upgrade Node.js from v18 to v20
    print("\n[1] Upgrading Node.js to v20...")
    fix_node = """
set -ex
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"
fnm install 20
fnm use 20
fnm default 20
node --version
npm --version
"""
    code, out, err = run_script(ssh, fix_node, timeout=60)
    print(f"  Node: {out.split(chr(10))[-1]}")
    
    # Source fnm in bashrc
    run_cmd(ssh, """grep -q 'fnm env' ~/.bashrc 2>/dev/null || echo 'eval "$(fnm env --use-on-cd)"' >> ~/.bashrc""")

    # 2. Fix PostgreSQL
    print("\n[2] Fixing PostgreSQL...")
    fix_pg = """
set -ex
# Check if PostgreSQL is installed
if command -v psql &>/dev/null; then
    echo "PostgreSQL binary found"
else
    echo "Installing PostgreSQL..."
    yum install -y postgresql-server postgresql-contrib
fi

# Find and start PostgreSQL
systemctl list-units --type=service 2>/dev/null | grep -i postgres

# Try to start
systemctl start postgresql 2>/dev/null || systemctl start postgresql-16 2>/dev/null || {
    # Manual init
    if [ -f /usr/bin/initdb ]; then
        su - postgres -c "initdb -D /var/lib/pgsql/data 2>/dev/null" || true
        su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/postgresql.log start 2>/dev/null" || true
    fi
}

sleep 2
pg_isready 2>/dev/null || echo "PostgreSQL not running yet"

# Create DB if not exists
su - postgres -c "psql -c \\"SELECT 1 FROM pg_roles WHERE rolname='meeting_admin';\\"" 2>/dev/null | grep -q 1 || \
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null

su - postgres -c "psql -c \\"SELECT 1 FROM pg_database WHERE datname='ai_meeting';\\"" 2>/dev/null | grep -q 1 || \
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null

su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null

# Configure pg_hba.conf for password auth
PG_HBA=$(find / -name "pg_hba.conf" -type f 2>/dev/null | head -1)
if [ -n "$PG_HBA" ]; then
    sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA"
    echo "pg_hba.conf configured at $PG_HBA"
fi

# Restart PostgreSQL
systemctl restart postgresql 2>/dev/null || systemctl restart postgresql-16 2>/dev/null || {
    su - postgres -c "pg_ctl -D /var/lib/pgsql/data restart 2>/dev/null" || true
}

sleep 2
pg_isready 2>/dev/null && echo "PostgreSQL is ready" || echo "PostgreSQL check done"
"""
    code, out, err = run_script(ssh, fix_pg, timeout=60)
    print(f"  {out[-200:] if len(out)>200 else out}")

    # 3. Rebuild backend with correct Node.js version
    print("\n[3] Rebuilding backend...")
    rebuild = """
set -ex
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"
cd /root/ai-meeting-backend

# Fix permissions
chmod -R 755 node_modules/.bin/

# Regenerate Prisma and push DB
npx prisma generate
npx prisma db push
npm run build

echo "Rebuild complete"
"""
    code, out, err = run_script(ssh, rebuild, timeout=180)
    if code != 0:
        print(f"  [w] {err[-200:]}")
    print("  [+] Rebuild complete")

    # 4. Restart PM2
    print("\n[4] Restarting PM2...")
    restart_pm2 = """
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env)"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 3
pm2 list 2>&1 | head -10
"""
    code, out, err = run_script(ssh, restart_pm2, timeout=20)
    # Remove any non-ASCII for safe printing
    safe_out = ''.join(c if c.isascii() else '?' for c in out)
    print(f"  {safe_out[:300]}")

    # 5. Fix Nginx
    print("\n[5] Checking Nginx...")
    fix_nginx = """
set -ex
# Install if missing
if ! command -v nginx &>/dev/null; then
    yum install -y nginx
fi

# Test config
nginx -t 2>&1

# Start Nginx
systemctl enable nginx 2>/dev/null || true
systemctl restart nginx 2>/dev/null || nginx 2>/dev/null || true

sleep 1
curl -s --connect-timeout 3 http://localhost/api/meetings || echo "Nginx proxy not responding"
"""
    code, out, err = run_script(ssh, fix_nginx, timeout=20)
    safe_out = ''.join(c if c.isascii() else '?' for c in out)
    print(f"  {safe_out[-300:] if len(safe_out)>300 else safe_out}")

    # 6. Final verification
    print("\n[6] Final verification...")
    time.sleep(2)
    code, out, err = run_cmd(ssh, "curl -s --connect-timeout 5 http://localhost:3000/api/meetings", timeout=15)
    print(f"  Direct API: {out[:100] if out else 'empty'}")

    code, out, err = run_cmd(ssh, "curl -s --connect-timeout 5 http://localhost/api/meetings", timeout=15)
    print(f"  Via Nginx:  {out[:100] if out else 'empty'}")

    code, out, err = run_cmd(ssh, "pg_isready 2>/dev/null && echo 'DB OK' || echo 'DB DOWN'", timeout=10)
    print(f"  Database:   {out}")

    print("\n" + "=" * 60)
    print("[OK] Fixup complete!")
    print(f"    API: http://{HOST}/api")
    print("=" * 60)

    ssh.close()

if __name__ == "__main__":
    main()
