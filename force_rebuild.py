import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Check built auth module for expiresIn
stdin, stdout, stderr = ssh.exec_command("grep -i 'expires\|604800\|7d' /root/ai-meeting-backend/dist/auth/auth.module.js", timeout=5)
print('dist auth.module.js expiresIn:', stdout.read().decode(errors='replace').strip()[:200])

# 2. Force clean rebuild
print('\n[2] Force clean rebuild...')
script = """
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
rm -rf dist
npx tsc -p tsconfig.build.json --outDir dist --skipLibCheck 2>&1
echo 'DONE'
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=30)
stdin.write(script)
stdin.close()
print(stdout.read().decode(errors='replace').strip()[-100:])

# 3. Verify
stdin, stdout, stderr = ssh.exec_command("grep -i 'expires\|604800' /root/ai-meeting-backend/dist/auth/auth.module.js", timeout=5)
print('\n[3] New dist expiresIn:', stdout.read().decode(errors='replace').strip()[:200])

# 4. Restart PM2
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && pm2 restart ai-meeting-backend && sleep 3 && echo 'done'", timeout=15)
stdout.read()

# 5. Test
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"final@demo.com\",\"password\":\"demo123456\",\"name\":\"FinalTest\"}'", timeout=10)
print('Register:', stdout.read().decode(errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"final@demo.com\",\"password\":\"demo123456\"}'", timeout=10)
print('Login:', stdout.read().decode(errors='replace').strip()[:150])

ssh.close()
