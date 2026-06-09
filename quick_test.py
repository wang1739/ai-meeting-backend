import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)

# Check PM2 status and backend
stdin, stdout, stderr = ssh.exec_command('curl -s http://localhost:3000/api/meetings 2>&1; echo "---"; curl -s -X POST http://localhost:3000/api/auth/login -H "Content-Type: application/json" -d "{\"email\":\"wang@qq.com\",\"password\":\"123456\"}" 2>&1', timeout=10)
print(stdout.read().decode(errors='replace').strip()[:500])

ssh.close()
