import paramiko, sys, time

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('[OK] Connected')

def bash(script, timeout=60):
    stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=timeout)
    stdin.write(script)
    stdin.close()
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# Check PostgreSQL logs
print('\n[1] PostgreSQL error log:')
ec, out = bash("tail -50 /var/log/pgsql.log 2>/dev/null || tail -50 /var/lib/pgsql/data/log/*.log 2>/dev/null || echo 'no log found'", 30)
print(' ', out[-500:])

# Check why it can't start
print('\n[2] Try direct start:')
ec, out = bash("""
set -ex
chown -R postgres:postgres /var/lib/pgsql/data /var/run/postgresql 2>/dev/null || true
mkdir -p /var/run/postgresql
chown postgres:postgres /var/run/postgresql
# Try starting
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -l /var/log/pgsql.log start" 2>&1
sleep 3
pg_isready && echo "PG_OK" || echo "PG_NOT_OK"
# Also check if port 5432 is in use
ss -tlnp | grep 5432 || echo "PORT_NOT_USED"
""", 30)
print(' ', out[-500:])

# If still failing, try with different approach
print('\n[3] Alternative start approach:')
ec, out = bash("""
set -ex
# Check if there's an existing postmaster.pid (stale lock)
rm -f /var/lib/pgsql/data/postmaster.pid 2>/dev/null || true
# Try starting PostgreSQL directly
su - postgres -c "pg_ctl -D /var/lib/pgsql/data -w -t 30 start" 2>&1 || true
sleep 2
pg_isready && echo "PG_RUNNING" || echo "PG_STILL_DOWN"

if ! pg_isready; then
    # Try starting as postgres directly
    su - postgres -c "postgres -D /var/lib/pgsql/data &" 2>/dev/null &
    sleep 3
    pg_isready && echo "PG_STARTED_DIRECT" || echo "PG_CANT_START"
fi
""", 30)
print(' ', out[-500:])

# Final status
print('\n[4] Status check:')
ec, out = bash("pg_isready && echo 'DB: OK' || echo 'DB: DOWN'", 10)
print(' ', out)
ec, out = bash("curl -s http://localhost/api/meetings", 10)
print('  Nginx:', out[:80] if out else 'empty')
ec, out = bash("ss -tlnp | grep -E ':(80|3000|5432)'", 10)
print('  Ports:', out[:200])

ssh.close()
