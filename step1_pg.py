import paramiko

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('[OK]')

_, out, _ = ssh.exec_command("pg_isready && echo 'OK' || echo 'DOWN'")
out = out.read().decode(errors='replace').strip()
print('PG:', out)

_, out, _ = ssh.exec_command("ss -tlnp | grep 5432")
out = out.read().decode(errors='replace').strip()
print('Port 5432:', out[:200])

# If not running, try to start
if 'OK' not in out:
    print('Starting PG...')
    script = """
set -ex
pkill -9 -u postgres 2>/dev/null || true
sleep 1
rm -f /var/lib/pgsql/data/postmaster.pid
rm -f /tmp/.s.PGSQL.*
chown -R postgres:postgres /var/lib/pgsql/data
mkdir -p /var/run/postgresql && chown postgres:postgres /var/run/postgresql
su - postgres -c "/usr/bin/postgres -D /var/lib/pgsql/data > /dev/null 2>&1 &"
sleep 3
pg_isready && echo "PG_OK" || echo "PG_FAIL"
"""
    stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=30)
    stdin.write(script)
    stdin.close()
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    print(out)
else:
    print('PG already running')

# Verify again
_, out, _ = ssh.exec_command("pg_isready && echo 'OK' || echo 'DOWN'")
print('Final:', out.read().decode(errors='replace').strip())

ssh.close()
