import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# Check auth.service.ts source
stdin, stdout, stderr = ssh.exec_command("cat /root/ai-meeting-backend/src/auth/auth.service.ts", timeout=5)
print('auth.service.ts:\n' + stdout.read().decode(errors='replace').strip())

ssh.close()
