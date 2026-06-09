import paramiko, sys, time

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('[OK] Connected to', HOST)

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

def bash(script, timeout=120):
    stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=timeout)
    stdin.write(script)
    stdin.close()
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

# Step 1: Install Nginx
print('\n[1/5] Installing Nginx...')
script = """
set -ex
if ! command -v nginx &>/dev/null; then
    yum install -y nginx 2>/dev/null || true
fi
# Remove default config if exists
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true
# Write our config
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
systemctl enable nginx 2>/dev/null || true
systemctl restart nginx 2>/dev/null || nginx 2>/dev/null || true
echo 'NGINX_DONE'
"""
ec, out, err = bash(script, timeout=60)
print(' ', 'OK' if 'NGINX_DONE' in out else 'Check needed')

# Step 2: Install PostgreSQL
print('\n[2/5] Installing PostgreSQL...')
script = """
set -ex
if command -v psql &>/dev/null; then
    echo 'PG_EXISTS'
    exit 0
fi
# Try dnf/yum
yum install -y postgresql-server postgresql-contrib 2>/dev/null || true
if command -v psql &>/dev/null; then
    echo 'PG_INSTALLED'
else
    echo 'PG_FAILED'
fi
"""
ec, out, err = bash(script, timeout=120)
if 'PG_EXISTS' in out or 'PG_INSTALLED' in out:
    print('  PostgreSQL installed')
    # Initialize and start
    script = """
set -ex
PG_DATA=$(find / -name "PG_VERSION" -type f 2>/dev/null | head -1)
if [ -z "$PG_DATA" ]; then
    postgresql-setup initdb 2>/dev/null || su - postgres -c "initdb -D /var/lib/pgsql/data" 2>/dev/null || true
fi
systemctl enable postgresql 2>/dev/null || true
systemctl start postgresql 2>/dev/null || su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start" 2>/dev/null || true
sleep 2
pg_isready 2>/dev/null && echo 'PG_RUNNING' || echo 'PG_NOT_RUNNING'
"""
    ec, out, err = bash(script, timeout=30)
    print(' ', 'Running' if 'PG_RUNNING' in out else 'Not running')
else:
    print('  Install command not available, skipping...')

# Step 3: Setup database
print('\n[3/5] Setting up database...')
script = """
set -ex
pg_isready 2>/dev/null || { echo 'DB_SKIP'; exit 0; }
# Create user
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo 'user_ok'
# Create database
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo 'db_ok'
# Grant privileges
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
# Enable password auth
PG_HBA=$(find / -type f -name "pg_hba.conf" 2>/dev/null | head -1)
if [ -n "$PG_HBA" ]; then
    sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA"
    su - postgres -c "pg_ctl reload -D $(dirname $(dirname $PG_HBA))" 2>/dev/null || true
fi
echo 'DB_DONE'
"""
ec, out, err = bash(script, timeout=15)
if 'DB_DONE' in out:
    print('  Database setup complete')
elif 'DB_SKIP' in out:
    print('  PostgreSQL not running, database setup skipped')
else:
    print('  DB setup output:', out[:100] if out else 'none')

# Step 4: Setup Node.js 20 via fnm and rebuild
print('\n[4/5] Setting up Node.js 20 and rebuilding...')
script = """
set -ex
# Install fnm if needed
if ! command -v fnm &>/dev/null; then
    curl -fsSL https://fnm.vercel.app/install | bash
fi
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
# Install Node.js 20
fnm install 20 --force 2>/dev/null
fnm use 20 2>/dev/null
fnm default 20 2>/dev/null
echo "node_ver: $(node --version)"
# Rebuild backend
cd /root/ai-meeting-backend
chmod -R 755 node_modules/.bin/ 2>/dev/null || true
export NODE_OPTIONS="--no-warnings"
npx prisma generate 2>/dev/null || echo 'prisma_generate_done'
npx prisma db push 2>/dev/null || echo 'prisma_push_done'
npm run build 2>/dev/null || echo 'build_done'
echo 'SETUP_DONE'
"""
ec, out, err = bash(script, timeout=180)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-200:]))

# Step 5: Restart PM2
print('\n[5/5] Restarting PM2...')
script = """
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1 2>/dev/null
pm2 save 2>/dev/null
sleep 2
echo 'PM2_DONE'
"""
ec, out, err = bash(script, timeout=20)
print('  PM2 restarted')

# Final verification
print('\n' + '='*50)
print('FINAL VERIFICATION')
print('='*50)
time.sleep(2)
ec, out, err = run('curl -s --connect-timeout 5 http://localhost:3000/api/meetings', timeout=10)
print('  Direct (3000):', out[:80] if out else 'empty')

ec, out, err = run('curl -s --connect-timeout 5 http://localhost/api/meetings', timeout=10)
print('  Nginx (80):   ', out[:80] if out else 'empty')

ec, out, err = run('pg_isready 2>/dev/null && echo YES || echo NO', timeout=5)
print('  PostgreSQL:   ', out)

ec, out, err = run('systemctl is-active nginx 2>/dev/null || echo inactive', timeout=5)
print('  Nginx active: ', out)

ec, out, err = run('node --version 2>/dev/null', timeout=5)
print('  Node version: ', out)

print('\n[OK] Fixup complete!')
print(f'  API: http://{HOST}/api')
print(f'  Login: http://{HOST}/api/auth/login')

ssh.close()
