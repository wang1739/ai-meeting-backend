import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)

stdin, stdout, stderr = ssh.exec_command("PGPASSWORD='Meeting@2024!' psql -h 127.0.0.1 -U meeting_admin -d ai_meeting -c 'SELECT id, email, name, created_at FROM \"User\" ORDER BY created_at DESC;' 2>&1", timeout=10)
print(stdout.read().decode(errors='replace').strip())

ssh.close()
