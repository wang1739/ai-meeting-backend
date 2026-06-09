import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Clear logs first
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && pm2 flush ai-meeting-backend 2>/dev/null; echo 'flushed'", timeout=5)
stdout.read()

# Trigger error
import time
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"a@b.com\",\"password\":\"abc123\",\"name\":\"T\"}'", timeout=10)
print('Response:', stdout.read().decode(errors='replace').strip()[:100])

time.sleep(2)

# Get full error
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && pm2 logs ai-meeting-backend --lines 50 --nostream 2>/dev/null | grep -A 30 'Error'", timeout=10)
print('Error:\n', stdout.read().decode(errors='replace').strip()[:1500])

ssh.close()
