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
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

# Step 1: Fix yum repos
print('\n[1/6] Fixing yum repos for Alibaba Cloud Linux 3...')
script = """
set -ex
# Check what OS we have
cat /etc/redhat-release 2>/dev/null || cat /etc/system-release 2>/dev/null
rpm -q alinux-release 2>/dev/null && echo "ALINUX" || echo "NOT_ALINUX"

# Use Alibaba Cloud Linux 3's own repos
dnf clean all 2>/dev/null || yum clean all 2>/dev/null || true

# Enable PowerTools/CRB repo for nginx dependencies
dnf config-manager --set-enabled powertools 2>/dev/null || 
dnf config-manager --set-enabled PowerTools 2>/dev/null || 
dnf config-manager --set-enabled ol8_codeready_builder 2>/dev/null || true

# Try installing nginx from alinux repos
yum install -y nginx 2>&1 | tail -5
which nginx && echo "NGINX_OK" || echo "NGINX_NO"
"""
ec, out, err = bash(script, timeout=60)
print(' ', out[-200:])

# Step 2: Try alternative nginx install
print('\n[2/6] Alternative nginx install...')
script = """
set -ex
# Try dnf
dnf install -y nginx 2>&1 | tail -5 || true
if ! command -v nginx &>/dev/null; then
    # Download static binary
    cd /tmp
    curl -sL https://nginx.org/download/nginx-1.24.0.tar.gz -o nginx.tar.gz 2>/dev/null || true
    # Try nginx from EPEL
    yum install -y epel-release 2>&1 | tail -3
    yum install -y nginx 2>&1 | tail -5
fi
which nginx && echo "NGINX_OK" || echo "NGINX_NO"
"""
ec, out, err = bash(script, timeout=60)
print(' ', out[-200:])

# Step 3: Install PostgreSQL
print('\n[3/6] Installing PostgreSQL...')
script = """
set -ex
# Remove broken pgdg repo if exists
rm -f /etc/yum.repos.d/pgdg*.repo 2>/dev/null || true

# Try from appstream/alinux repos
yum install -y postgresql-server postgresql-contrib 2>&1 | tail -5 || true

if ! command -v psql &>/dev/null; then
    # Try EPEL
    yum install -y epel-release 2>&1 | tail -3
    yum install -y postgresql-server postgresql-contrib 2>&1 | tail -5 || true
fi

which psql && echo "PSQL_OK" || echo "PSQL_NO"
"""
ec, out, err = bash(script, timeout=120)
print(' ', out[-200:])

# Step 4: Setup PostgreSQL + init
print('\n[4/6] Initializing PostgreSQL...')
script = """
set -ex
if command -v psql &>/dev/null; then
    # Init database
    if [ ! -d "/var/lib/pgsql/data" ]; then
        postgresql-setup initdb 2>/dev/null || su - postgres -c "initdb -D /var/lib/pgsql/data" 2>/dev/null || echo "INIT_DONE"
    fi
    # Start
    su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start" 2>/dev/null || systemctl start postgresql 2>/dev/null || true
    sleep 2
    pg_isready && echo "PG_OK" || echo "PG_NO"
    # Create DB
    if pg_isready; then
        su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo "user_ok"
        su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo "db_ok"
        su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
        PG_HBA=$(find / -type f -name "pg_hba.conf" 2>/dev/null | head -1)
        [ -n "$PG_HBA" ] && sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA" && su - postgres -c "pg_ctl reload -D /var/lib/pgsql/data" 2>/dev/null || true
        echo "DB_SETUP_DONE"
    fi
fi
echo "PG_SETUP_COMPLETE"
"""
ec, out, err = bash(script, timeout=30)
print(' ', out[-300:])

# Step 5: Rebuild backend (update .env + prisma push)
print('\n[5/6] Rebuilding backend...')
script = """
set -ex
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$FNM_DIR:$PATH"
eval "$($FNM_DIR/fnm env --use-on-cd 2>/dev/null)" || true

cd /root/ai-meeting-backend

# Check node version
echo "Node: $(node --version)"
echo "NPM: $(npm --version)"

# Rebuild
npx prisma generate 2>&1 | tail -3
npx prisma db push 2>&1 | tail -3
npm run build 2>&1 | tail -3
echo "BUILD_DONE"
"""
ec, out, err = bash(script, timeout=180)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-300:]))

# Step 6: Restart PM2 + Nginx
print('\n[6/6] Restarting services...')
script = """
set -ex
export FNM_DIR="$HOME/.local/share/fnm"
export PATH="$FNM_DIR:$PATH"
eval "$($FNM_DIR/fnm env --use-on-cd 2>/dev/null)" || true

# PM2
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1 2>/dev/null
pm2 save 2>/dev/null

# Nginx config (if installed)
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
    nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
fi

sleep 2
echo "SERVICES_DONE"
"""
ec, out, err = bash(script, timeout=20)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-300:]))

# Final check
print('\n' + '='*50)
print('FINAL CHECK')
print('='*50)
time.sleep(2)

ec, out, err = bash("curl -s --connect-timeout 5 http://localhost:3000/api/meetings", 10)
print('  API(3000):', out[:80] if out else 'empty')

ec, out, err = bash("curl -s --connect-timeout 5 http://localhost/api/meetings", 10)
print('  API(80):   ', out[:80] if out else 'empty')

ec, out, err = bash("pg_isready 2>/dev/null && echo 'DB:OK' || echo 'DB:DOWN'", 5)
print('  ', out)

ec, out, err = bash("systemctl is-active nginx 2>/dev/null || nginx -v 2>&1 || echo 'no nginx'", 5)
print('  Nginx:', out[:50])

ec, out, err = bash("node --version 2>/dev/null", 5)
print('  Node:', out)

print(f'\n[OK] Done! API: http://{HOST}/api')
ssh.close()
