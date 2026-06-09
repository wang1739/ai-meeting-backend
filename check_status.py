import paramiko, sys, time

HOST = '118.31.249.156'
USER = 'root'
PASSWORD = 'wmm.12345.'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
print('Connected')

def run(cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    return exit_code, out, err

# Check what's running
ec, out, err = run('ss -tlnp | grep -E ":(80|3000)" ')
print('\nListening ports:\n', out[:500])

# Check PM2
ec, out, err = run('pm2 list 2>/dev/null')
print('\nPM2 processes:\n', ''.join(c if c.isascii() else '?' for c in out[:300]))

# Check PostgreSQL
ec, out, err = run('systemctl status postgresql 2>/dev/null; pg_isready 2>/dev/null')
print('\nPostgreSQL status:\n', ''.join(c if c.isascii() else '?' for c in out[:300]))

# Check nginx
ec, out, err = run('systemctl status nginx 2>/dev/null')
print('\nNginx status:\n', ''.join(c if c.isascii() else '?' for c in out[:300]))

# Test API locally
ec, out, err = run('curl -s --connect-timeout 3 http://localhost:3000/api/meetings')
print('\nLocal API test:\n', out[:100] if out else 'empty')

ec, out, err = run('curl -s --connect-timeout 3 http://localhost/api/meetings')
print('\nNginx proxy test:\n', out[:100] if out else 'empty')

# Check port 80 firewall
ec, out, err = run('firewall-cmd --list-all 2>/dev/null || iptables -L INPUT -n 2>/dev/null | head -20')
print('\nFirewall rules:\n', ''.join(c if c.isascii() else '?' for c in out[:500]))

ssh.close()
