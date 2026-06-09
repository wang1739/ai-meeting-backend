import paramiko, sys, time

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

# Fix 1: Remove stale PID, fix log permissions, start PostgreSQL
print('\n[1] Starting PostgreSQL...')
script = """
set -ex
# Remove stale lock
rm -f /var/lib/pgsql/data/postmaster.pid 2>/dev/null

# Fix log permissions
touch /var/log/pgsql.log 2>/dev/null
chown postgres:postgres /var/log/pgsql.log 2>/dev/null
chmod 644 /var/log/pgsql.log 2>/dev/null

# Also fix run dir
mkdir -p /var/run/postgresql 2>/dev/null
chown -R postgres:postgres /var/run/postgresql 2>/dev/null

# Start PostgreSQL
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start -w -t 30" 2>&1
sleep 3
pg_isready && echo "PG_OK" || echo "PG_FAIL"
"""
ec, out, err = run(script, timeout=60)
print(' ', out[-400:])

# Fix 2: If still failing, check actual error
if 'PG_FAIL' in out:
    print('\n[2] Checking PG error...')
    # Try to read the real log
    ec, log_out, _ = run("""
    cat /var/lib/pgsql/data/log/*.log 2>/dev/null | tail -20 || 
    find /var/lib/pgsql/data -name "*.log" -exec tail -20 {} \; 2>/dev/null || 
    echo "no logs"
    """, 15)
    print('  Log:', log_out[-400:])

    # Try direct start with different approach
    print('\n[3] Alternative start...')
    ec, out, err = run("""
    set -ex
    # Start as postgres directly in background
    su - postgres -c "/usr/bin/postgres -D /var/lib/pgsql/data > /tmp/pg.log 2>&1 &" 2>/dev/null
    sleep 3
    pg_isready && echo "PG_OK" || echo "PG_FAIL"
    cat /tmp/pg.log 2>/dev/null | tail -10
    """, 30)
    print(' ', out[-300:])

# Final verification  
print('\n[Final] Status:')
ec, out, err = run("pg_isready && echo 'DB: OK' || echo 'DB: DOWN'", 10)
print('  ', out)
ec, out, err = run("curl -s http://localhost/api/meetings", 10)
print('  Nginx(80):', out[:80] if out else 'empty')
ec, out, err = run("ss -tlnp | grep -E ':(80|3000|5432)'", 10)
print('  Ports:', out[:300])

print(f'\n[Done] http://{HOST}/api')
ssh.close()
