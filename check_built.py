import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Check built auth module
stdin, stdout, stderr = ssh.exec_command("cat /root/ai-meeting-backend/dist/auth/auth.module.js | head -30", timeout=5)
print('Built auth.module.js:\n' + stdout.read().decode(errors='replace').strip()[:800])

# Check source again
stdin, stdout, stderr = ssh.exec_command("cat /root/ai-meeting-backend/src/auth/auth.module.ts", timeout=5)
print('\nSource auth.module.ts:\n' + stdout.read().decode(errors='replace').strip())

# Check the actual PM2 error to confirm it's jwt
stdin, stdout, stderr = ssh.exec_command("cat /root/.pm2/logs/ai-meeting-backend-error-0.log 2>/dev/null | grep -i 'expiresIn\|expires_in\|JWT' | tail -5", timeout=5)
print('\nJWT errors:\n' + stdout.read().decode(errors='replace').strip()[:500])

ssh.close()
