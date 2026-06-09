import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)

# Check built files for API URL
stdin, stdout, stderr = ssh.exec_command("grep -o 'VITE_API_URL[^\"]*\"' /usr/share/nginx/html/ai-meeting/assets/*.js 2>/dev/null | head -5; echo '---'; grep -o \"'[^']*auth/login[^']*'\" /usr/share/nginx/html/ai-meeting/assets/*.js 2>/dev/null | head -5; echo '---'; grep -o '\"/api/auth[^\"]*' /usr/share/nginx/html/ai-meeting/assets/*.js 2>/dev/null | head -5", timeout=10)
print(stdout.read().decode(errors='replace').strip()[:1000])

# Also check locals js files
stdin, stdout, stderr = ssh.exec_command("ls /usr/share/nginx/html/ai-meeting/assets/", timeout=5)
print('\nAssets:', stdout.read().decode(errors='replace').strip())

ssh.close()
