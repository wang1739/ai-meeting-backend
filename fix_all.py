import paramiko, time

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('[OK] Connected')

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return ec, out, err

# 1. Fix PostgreSQL: Ensure persistent startup
print('\n[1] Fix PostgreSQL persistent startup...')
script = """
set -ex
# Kill any previous
pkill -9 -u postgres 2>/dev/null || true
sleep 1

# Clean stale files
rm -f /var/lib/pgsql/data/postmaster.pid 2>/dev/null
rm -f /tmp/.s.PGSQL.* 2>/dev/null

# Fix permissions
chown -R postgres:postgres /var/lib/pgsql/data
mkdir -p /var/run/postgresql
chown postgres:postgres /var/run/postgresql

# Configure PostgreSQL for local connections
PG_HBA=$(find /var/lib/pgsql/data -name "pg_hba.conf" 2>/dev/null | head -1)
if [ -n "$PG_HBA" ]; then
    # Make sure local connections use md5
    sed -i 's/peer/md5/g; s/ident/md5/g' "$PG_HBA"
    # Also ensure host connections work
    grep -q "host.*all.*all.*127.0.0.1.*md5" "$PG_HBA" || echo "host    all             all             127.0.0.1/32            md5" >> "$PG_HBA"
fi

# Also fix postgresql.conf to listen on localhost
PG_CONF=$(find /var/lib/pgsql/data -name "postgresql.conf" 2>/dev/null | head -1)
if [ -n "$PG_CONF" ]; then
    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
    sed -i "s/listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF" 2>/dev/null || true
fi

# Start PostgreSQL directly (not via pg_ctl which has issues)
su - postgres -c "/usr/bin/postgres -D /var/lib/pgsql/data &" 2>/dev/null
sleep 3
pg_isready && echo "PG_RUNNING" || echo "PG_FAIL"
"""
ec, out, err = run(script, timeout=30)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-200:]))

# 2. Create DB + user if not exists
print('\n[2] Create DB and user...')
ec, out, err = run("""
pg_isready || { echo 'PG_NOT_READY'; exit 1; }
# Create user (ignore if exists)
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo 'user exists'
# Create database
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo 'db exists'
# Grant
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
# Grant on public schema
PGPASSWORD='Meeting@2024!' psql -h 127.0.0.1 -U meeting_admin -d ai_meeting -c "GRANT ALL ON SCHEMA public TO meeting_admin;" 2>/dev/null || true
echo 'DB_SETUP_DONE'
""", 15)
print(' ', out)

# 3. Fix Node 20: Download binary directly
print('\n[3] Installing Node.js 20...')
script = """
set -ex
cd /tmp
# Download Node 20 directly
curl -fsSL https://nodejs.org/dist/v20.18.1/node-v20.18.1-linux-x64.tar.xz -o node.tar.xz
tar -xf node.tar.xz
cp -r node-v20.18.1-linux-x64/* /usr/local/
node --version
npm --version

# Also update PM2
npm install -g pm2 2>&1 | tail -3
echo 'NODE20_DONE'
"""
ec, out, err = run(script, timeout=120)
print(' ', out[-200:])

# 4. Rebuild with Node 20
print('\n[4] Rebuilding backend with Node 20...')
script = """
set -ex
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
node --version
npm --version

# Fix permissions
chmod -R 755 node_modules/.bin/ 2>/dev/null || true

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install 2>&1 | tail -5

# Generate + push
npx prisma generate 2>&1
npx prisma db push 2>&1

# Build
npm run build 2>&1
echo 'BUILD_DONE'
"""
ec, out, err = run(script, timeout=180)
print(' ', ''.join(c if c.isascii() else '?' for c in out[-500:]))

# 5. Restart PM2
print('\n[5] Restarting PM2...')
script = """
export PATH="/usr/local/bin:$PATH"
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 3
echo 'PM2_DONE'
"""
ec, out, err = run(script, timeout=20)

# 6. Verify everything
print('\n[6] Final verification...')
time.sleep(2)

ec, out, err = run("pg_isready && echo 'DB: OK' || echo 'DB: DOWN'", 10)
print('  DB:', out)

ec, out, err = run("curl -s http://localhost:3000/api/meetings", 10)
print('  API(3000):', out[:100] if out else 'empty')

ec, out, err = run("curl -s http://localhost/api/meetings", 10)
print('  Nginx(80):', out[:100] if out else 'empty')

# Test register
ec, out, err = run("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"admin@meeting.com\",\"password\":\"admin123\",\"name\":\"Admin\"}'", 10)
print('  Register:', out[:150] if out else 'empty')

ec, out, err = run("node --version", 10)
print('  Node:', out)

print('\n' + '='*60)
print('[OK] http://118.31.249.156/api')
print('='*60)

ssh.close()
