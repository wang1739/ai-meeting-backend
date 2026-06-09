import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=10):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Check nginx is running
print('\n[1] Nginx:')
ec, out = run('systemctl is-active nginx 2>/dev/null || nginx -v 2>&1 | head -1')
print(' ', out)

# 2. Check PM2
print('\n[2] PM2:')
ec, out = run('pm2 list 2>/dev/null | head -5')
print(' ', ''.join(c if c.isascii() else '?' for c in out[:200]))

# 3. Test frontend
print('\n[3] Frontend:')
ec, out = run('curl -s -o /dev/null -w "%{http_code}" http://localhost/')
print('  HTTP:', out)

# 4. Test API
print('\n[4] API:')
ec, out = run('curl -s -o /dev/null -w "%{http_code}" http://localhost/api/meetings')
print('  HTTP:', out)

# 5. Check nginx config
print('\n[5] Nginx config:')
ec, out = run('cat /etc/nginx/conf.d/ai-meeting.conf')
print(out[:500])

# 6. Check if port 80 is listening
ec, out = run('ss -tlnp | grep :80')
print('\n[6] Port 80:', out[:100])

ssh.close()
