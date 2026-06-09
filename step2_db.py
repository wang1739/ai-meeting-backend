import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Create DB and user
print('\n[1] DB setup...')
script = """
set -ex
su - postgres -c "psql -c \\"CREATE USER meeting_admin WITH PASSWORD 'Meeting@2024!';\\"" 2>/dev/null || echo 'user_ok'
su - postgres -c "psql -c \\"CREATE DATABASE ai_meeting OWNER meeting_admin;\\"" 2>/dev/null || echo 'db_ok'
su - postgres -c "psql -c \\"GRANT ALL PRIVILEGES ON DATABASE ai_meeting TO meeting_admin;\\"" 2>/dev/null || true
echo 'DB_DONE'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=15)
sin.write(script)
sin.close()
print(' ', sout.read().decode(errors='replace').strip()[-200:])

# 2. Test connection with meeting_admin
print('\n[2] Test meeting_admin connection...')
_, out, _ = ssh.exec_command("PGPASSWORD='Meeting@2024!' psql -h 127.0.0.1 -U meeting_admin -d ai_meeting -c 'SELECT 1;' 2>&1", timeout=10)
print(' ', out.read().decode(errors='replace').strip())

ssh.close()
