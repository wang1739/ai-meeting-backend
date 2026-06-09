import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Start PM2
script = """
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 4
echo 'STARTED'
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=20)
stdin.write(script)
stdin.close()
out = stdout.read().decode(errors='replace').strip()
print('Start:', out[-100:])

# 2. Test
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:3000/api/meetings", timeout=10)
print('API:', stdout.read().decode(errors='replace').strip()[:100])

stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost:3000/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"ok@demo.com\",\"password\":\"demo123456\",\"name\":\"OkTest\"}'", timeout=10)
print('Register:', stdout.read().decode(errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"ok@demo.com\",\"password\":\"demo123456\"}'", timeout=10)
print('Login:', stdout.read().decode(errors='replace').strip()[:150])

# 3. Check nginx
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost/api/meetings", timeout=10)
print('Nginx:', stdout.read().decode(errors='replace').strip()[:100])

print('\n[Done] Try http://118.31.249.156')
ssh.close()
