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

# 1. Check OS and install Nginx
print('\n[1] Check OS and install Nginx + PostgreSQL...')
script = """
set -ex
echo "=== OS ==="
cat /etc/os-release | head -5
echo "=== YUM REPOS ==="
yum repolist 2>/dev/null | head -5
echo "=== INSTALLING NGINX ==="
yum install -y nginx 2>&1 | tail -3
echo "=== INSTALLING POSTGRESQL ==="
yum install -y postgresql-server postgresql-contrib 2>&1 | tail -3
echo "=== DONE ==="
which nginx 2>/dev/null && echo "NGINX_OK" || echo "NGINX_NO"
which psql 2>/dev/null && echo "PSQL_OK" || echo "PSQL_NO"
"""
ec, out, err = bash(script, timeout=120)
print(' ', out[-500:])

# 2. Configure Nginx
print('\n[2] Configure Nginx...')
script = """
set -ex
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
nginx -t 2>&1 && echo "CONFIG_OK" || echo "CONFIG_FAIL"
nginx 2>/dev/null || systemctl start nginx 2>/dev/null || true
sleep 1
curl -s --connect-timeout 3 http://localhost/api/meetings && echo "PROXY_OK" || echo "PROXY_FAIL"
"""
ec, out, err = bash(script, timeout=15)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-300:]))

# 3. PostgreSQL setup
print('\n[3] Setup PostgreSQL...')
script = """
set -ex
# Init if needed
if [ ! -d "/var/lib/pgsql/data" ]; then
    postgresql-setup initdb 2>/dev/null || su - postgres -c "initdb -D /var/lib/pgsql/data" 2>/dev/null || echo "INIT_FAILED"
fi
# Start
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start" 2>/dev/null || systemctl start postgresql 2>/dev/null || echo "START_FAILED"
sleep 2
pg_isready 2>/dev/null && echo "PG_OK" || echo "PG_NO"
"""
ec, out, err = bash(script, timeout=20)
print(' ', out[-200:])

# 4. Create database
print('\n[4] Create database...')
script = """
set -ex
pg_isready 2>/dev/null || { echo "PG_NOT_RUNNING"; exit 0; }
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo "USER_EXISTS"
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo "DB_EXISTS"
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
PG_HBA=$(find / -type f -name "pg_hba.conf" 2>/dev/null | head -1)
[ -n "$PG_HBA" ] && sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA" && echo "HBA_FIXED"
su - postgres -c "pg_ctl reload -D /var/lib/pgsql/data" 2>/dev/null || true
echo "DB_DONE"
"""
ec, out, err = bash(script, timeout=15)
print(' ', out[-200:])

# 5. Install Node.js 20 via fnm
print('\n[5] Install Node.js 20...')
script = """
set -ex
export PATH="$HOME/.local/share/fnm:$PATH"
if ! command -v fnm &>/dev/null; then
    curl -fsSL https://fnm.vercel.app/install | bash
    export PATH="$HOME/.local/share/fnm:$PATH"
fi
eval "$(fnm env --use-on-cd)"
fnm install 20 --force 2>&1 | tail -3
fnm use 20 2>&1
fnm default 20 2>&1
echo "NODE_VER: $(node --version)"
echo "NPM_VER: $(npm --version)"
"""
ec, out, err = bash(script, timeout=60)
print(' ', out[-200:])

# 6. Rebuild with Node.js 20
print('\n[6] Rebuild backend...')
script = """
set -ex
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
cd /root/ai-meeting-backend
which node
node --version
chmod -R 755 node_modules/.bin/ 2>/dev/null || true
npm install 2>&1 | tail -5
npx prisma generate 2>&1 | tail -3
npx prisma db push 2>&1 | tail -3
npm run build 2>&1 | tail -5
echo "BUILD_DONE"
"""
ec, out, err = bash(script, timeout=180)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-400:]))

# 7. Restart PM2
print('\n[7] Restart PM2...')
script = """
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1 2>/dev/null
pm2 save 2>/dev/null
sleep 2
echo "PM2_DONE"
"""
ec, out, err = bash(script, timeout=20)

# 8. Verify
time.sleep(2)
ec, out, err = bash("curl -s --connect-timeout 5 http://localhost:3000/api/meetings", 10)
print('\n[8] Final check:')
print('  Direct:', out[:80] if out else 'empty')

ec, out, err = bash("curl -s --connect-timeout 5 http://localhost/api/meetings", 10)
print('  Nginx: ', out[:80] if out else 'empty')

ec, out, err = bash("pg_isready 2>/dev/null && echo 'DB: OK' || echo 'DB: DOWN'", 5)
print('  ', out)

ec, out, err = bash("node --version 2>/dev/null", 5)
print('  Node:', out)

print(f'\n[OK] All done! API: http://{HOST}/api')
ssh.close()
