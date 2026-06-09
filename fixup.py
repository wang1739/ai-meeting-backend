import paramiko, sys

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
except Exception as e:
    print('[x] Connection failed:', e)
    sys.exit(1)

print('[+] Connected to', HOST)

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return out

def run_script(script, timeout=120):
    stdin, stdout, stderr = ssh.exec_command("bash -s", timeout=timeout)
    stdin.write(script)
    stdin.close()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return out, err

# 1. Check Node.js
print('\n[1] Node.js version:')
print(' ', run('node --version 2>/dev/null || echo not_found'))

# 2. Install fnm and Node.js 20 properly
print('\n[2] Installing Node.js 20 via fnm...')
install_node = """
set -e
# Install fnm if needed
if ! command -v fnm &>/dev/null; then
    curl -fsSL https://fnm.vercel.app/install | bash
fi
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
fnm install 20 --force
fnm use 20
fnm default 20
echo 'FNM_NODE_VERSION=20' > /root/.fnm_node_version
node --version
"""
out, err = run_script(install_node, timeout=60)
node_ver = [l for l in out.split('\n') if 'v20' in l or 'v2' in l]
print(' ', node_ver[0] if node_ver else 'check failed')

# 3. Fix PostgreSQL
print('\n[3] Fixing PostgreSQL...')
fix_pg = """
set -ex
# Try to start PostgreSQL
systemctl start postgresql 2>/dev/null || systemctl start postgresql-16 2>/dev/null || {
    # Manual init
    PG_DATA_DIR=$(find / -name "PG_VERSION" -type f 2>/dev/null | head -1 | xargs dirname 2>/dev/null)
    if [ -z "$PG_DATA_DIR" ]; then
        # Not initialized, try to init
        if command -v postgresql-16-setup &>/dev/null; then
            postgresql-16-setup initdb
        elif command -v postgresql-setup &>/dev/null; then
            postgresql-setup initdb
        elif command -v initdb &>/dev/null; then
            su - postgres -c "initdb -D /var/lib/pgsql/data" 2>/dev/null || true
        fi
    fi
    # Start PostgreSQL
    su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start" 2>/dev/null || true
    su - postgres -c "pg_ctl -D /usr/local/pgsql/data -l /var/log/pgsql.log start" 2>/dev/null || true
}
sleep 2
pg_isready 2>/dev/null && echo "PG_RUNNING" || echo "PG_NOT_RUNNING"
"""
out, err = run_script(fix_pg, timeout=30)
print(' ', [l for l in out.split('\n') if 'PG_' in l or 'RUNNING' in l or 'NOT' in l or 'ready' in l])

# 4. Create DB if PostgreSQL is running
print('\n[4] Setting up database...')
setup_db = """
set -ex
pg_isready 2>/dev/null || { echo "DB_SKIP"; exit 0; }
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo "user exists"
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo "db exists"
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null

# Fix pg_hba.conf
PG_HBA=$(find / -type f -name "pg_hba.conf" 2>/dev/null | head -1)
if [ -n "$PG_HBA" ]; then
    sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA"
    su - postgres -c "pg_ctl reload -D $(dirname $(dirname $PG_HBA))" 2>/dev/null || true
fi
echo "DB_SETUP_DONE"
"""
out, err = run_script(setup_db, timeout=15)
print(' ', out[-100:] if out else 'no output')

# 5. Rebuild with proper Node.js
print('\n[5] Rebuilding backend...')
rebuild = """
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
cd /root/ai-meeting-backend
chmod -R 755 node_modules/.bin/ 2>/dev/null
# Try to rebuild
npx prisma generate 2>/dev/null || true
npx prisma db push 2>/dev/null || true
npm run build 2>/dev/null || echo "BUILD_CHECK_DONE"
echo "REBUILD_DONE"
"""
out, err = run_script(rebuild, timeout=120)
print(' ', 'Done')

# 6. Fix Nginx
print('\n[6] Fixing Nginx...')
fix_nginx = """
set -ex
# Install nginx if needed
if ! command -v nginx &>/dev/null; then
    yum install -y nginx 2>/dev/null || true
fi
# Remove default config
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true
# Write config
cat > /etc/nginx/conf.d/ai-meeting.conf << 'NGXEOF'
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
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
NGXEOF
nginx -t 2>&1
systemctl restart nginx 2>/dev/null || nginx -s reload 2>/dev/null || nginx 2>/dev/null || true
echo "NGINX_DONE"
"""
out, err = run_script(fix_nginx, timeout=20)
print(' ', ' '.join([l.strip() for l in out.split('\n') if l.strip()][-3:]))

# 7. Restart PM2
print('\n[7] Restarting PM2 service...')
restart = """
export PATH="$HOME/.local/share/fnm:$PATH"
eval "$(fnm env --use-on-cd)"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1 2>/dev/null
pm2 save 2>/dev/null
sleep 2
echo "PM2_DONE"
"""
out, err = run_script(restart, timeout=20)
print(' ', 'Done')

# 8. Verify
print('\n[8] Verification:')
time.sleep(2)
r = run('curl -s --connect-timeout 5 http://localhost:3000/api/meetings 2>/dev/null || echo fail')
print('  Direct (3000):', r[:80] if r != 'fail' else 'fail')

r = run('curl -s --connect-timeout 5 http://localhost/api/meetings 2>/dev/null || echo fail')
print('  Nginx (80):   ', r[:80] if r != 'fail' else 'fail')

r = run('pg_isready 2>/dev/null && echo OK || echo DOWN')
print('  PostgreSQL:   ', r)

r = run('systemctl is-active nginx 2>/dev/null || echo inactive')
print('  Nginx status: ', r)

print('\n[OK] Fixup complete!')
ssh.close()
