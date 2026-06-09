import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Fix: main.js is at dist/main.js, not dist/src/main.js
script = """
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 4
curl -s http://localhost:3000/api/meetings
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=20)
stdin.write(script)
stdin.close()
out = stdout.read().decode(errors='replace').strip()
print('PM2 start:', out[:300])

time.sleep(2)

# Test register
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"real@demo.com\",\"password\":\"demo123456\",\"name\":\"RealUser\"}'", timeout=10)
print('\nRegister:', stdout.read().decode(errors='replace').strip())

# Test login
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"real@demo.com\",\"password\":\"demo123456\"}'", timeout=10)
print('Login:', stdout.read().decode(errors='replace').strip()[:150])

# Test nginx
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost/api/meetings", timeout=10)
print('Nginx:', stdout.read().decode(errors='replace').strip()[:100])

print('\n[Done] Open http://118.31.249.156')
ssh.close()
