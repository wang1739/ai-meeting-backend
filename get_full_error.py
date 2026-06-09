import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Clear logs
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && pm2 flush 2>/dev/null; echo ok", timeout=5)
print(stdout.read().decode(errors='replace').strip())

# Trigger error
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"z@z.com\",\"password\":\"z123456\",\"name\":\"Z\"}'", timeout=10)
print('Response:', stdout.read().decode(errors='replace').strip()[:100])

time.sleep(2)

# Get full error from PM2 error log
stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/ai-meeting-backend-error-0.log 2>/dev/null | tail -60", timeout=10)
print('Full error:\n' + stdout.read().decode(errors='replace').strip()[:1500])

# Also check out log
stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/ai-meeting-backend-out-0.log 2>/dev/null | tail -20", timeout=10)
print('Out log:\n' + stdout.read().decode(errors='replace').strip()[:500])

ssh.close()
