import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Test register with valid data
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"hello@demo.com\",\"password\":\"demo123456\",\"name\":\"Hello\"}'", timeout=10)
print('Register:', stdout.read().decode(errors='replace').strip())

time.sleep(1)

# Test login
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"hello@demo.com\",\"password\":\"demo123456\"}'", timeout=10)
print('Login:', stdout.read().decode(errors='replace').strip())

time.sleep(1)

# Check if there's error after these
stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/ai-meeting-backend-error-0.log 2>/dev/null | tail -30", timeout=5)
err = stdout.read().decode(errors='replace').strip()
if err:
    print('Errors:', err[:800])

ssh.close()
