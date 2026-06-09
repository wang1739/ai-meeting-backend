import paramiko, sys, time

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('[OK] Connected')

def bash(script, timeout=120):
    stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=timeout)
    stdin.write(script)
    stdin.close()
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Start PostgreSQL + create DB
print('\n[1/3] Starting PostgreSQL + creating database...')
script = """
set -ex
# Init if needed
if [ ! -d "/var/lib/pgsql/data/base" ]; then
    su - postgres -c "initdb -D /var/lib/pgsql/data" 2>/dev/null || echo "init done"
fi
# Start
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start" 2>/dev/null || true
sleep 2
pg_isready && echo "PG_OK" || echo "PG_NO"
# Create user and DB
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo "user exists"
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo "db exists"
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
# Fix pg_hba for password auth
PG_HBA=$(find / -type f -name "pg_hba.conf" 2>/dev/null | head -1)
if [ -n "$PG_HBA" ]; then
    sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA"
    su - postgres -c "pg_ctl reload -D /var/lib/pgsql/data" 2>/dev/null || true
    echo "PG_HBA fixed: $PG_HBA"
fi
echo "DONE"
"""
ec, out = bash(script, timeout=30)
print(' ', out[-300:])

# 2. Install Nginx (from EPEL or local)
print('\n[2/3] Installing Nginx...')
script = """
set -ex
# Try dnf first (Alibaba Cloud Linux 3 uses dnf)
dnf install -y nginx 2>/dev/null && { echo "NGINX_OK"; exit 0; }
# Try yum
yum install -y nginx 2>/dev/null && { echo "NGINX_OK"; exit 0; }
# Try EPEL
yum install -y epel-release 2>/dev/null || true
yum install -y nginx 2>/dev/null && { echo "NGINX_OK"; exit 0; }
# If still not found, install from alinux baseos
dnf install -y --nogpgcheck nginx 2>/dev/null && { echo "NGINX_OK"; exit 0; }
echo "NGINX_FAIL"
"""
ec, out = bash(script, timeout=60)
print(' ', out[-200:])

# If still failed, install by downloading RPM directly
if 'NGINX_FAIL' in out:
    print('  Trying direct RPM install...')
    script = """
set -ex
cd /tmp
# Install EPEL for nginx
yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm 2>/dev/null || true
# Try to install nginx from EPEL
yum install -y nginx 2>/dev/null && { echo "NGINX_OK"; exit 0; }
# Last resort: download RPM directly
rpm -ivh http://nginx.org/packages/centos/8/x86_64/RPMS/nginx-1.24.0-1.el8.ngx.x86_64.rpm 2>/dev/null || \
rpm -ivh http://nginx.org/packages/rhel/8/x86_64/RPMS/nginx-1.24.0-1.el8.ngx.x86_64.rpm 2>/dev/null || true
which nginx && echo "NGINX_OK" || echo "NGINX_FAIL"
"""
    ec, out = bash(script, timeout=60)
    print(' ', out[-200:])

# 3. Configure Nginx and start
print('\n[3/3] Configuring Nginx + restarting PM2...')
script = """
set -ex
# Configure nginx if installed
if command -v nginx &>/dev/null; then
    rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true
    cat > /etc/nginx/conf.d/ai-meeting.conf << 'EOF'
server {
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
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
EOF
    nginx -t 2>&1
    nginx 2>/dev/null || systemctl start nginx 2>/dev/null || true
    sleep 1
    echo "NGINX_CONFIGURED"
else
    echo "NGINX_SKIP"
fi

# Restart PM2
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$FNM_DIR:$PATH"
eval "$($FNM_DIR/fnm env --use-on-cd 2>/dev/null)" || true
cd /root/ai-meeting-backend

# Prisma push (ensure DB is synced)
npx prisma db push 2>&1 | tail -3

# Restart app
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1 2>/dev/null
pm2 save 2>/dev/null
sleep 2
echo "ALL_DONE"
"""
ec, out = bash(script, timeout=60)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-400:]))

# Final verification
print('\n' + '='*50)
print('FINAL VERIFICATION')
print('='*50)
time.sleep(2)

ec, out = bash("curl -s --connect-timeout 5 http://localhost:3000/api/meetings", 10)
print('  API(3000):', out[:80] if out else 'empty')

ec, out = bash("curl -s --connect-timeout 5 http://localhost/api/meetings", 10)
print('  Nginx(80):', out[:80] if out else 'empty')

ec, out = bash("pg_isready 2>/dev/null && echo 'DB: OK' || echo 'DB: DOWN'", 5)
print('  ', out)

ec, out = bash("command -v nginx && echo 'NGINX: installed' || echo 'NGINX: not installed'", 5)
print('  ', out)

print(f'\n[OK] API: http://{HOST}/api')
ssh.close()
