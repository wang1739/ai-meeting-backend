import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=30):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Test login
print('\n[1] Test login:')
ec, out = run("curl -s -X POST http://localhost/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@meeting.com\",\"password\":\"test123\"}'", 10)
print('  Login:', out[:200])

# 2. Test another register
print('\n[2] Test new register:')
ec, out = run("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"newuser@meeting.com\",\"password\":\"newuser123\",\"name\":\"NewUser\"}'", 10)
print('  Register:', out[:200])

# 3. Check PM2 error log
print('\n[3] PM2 error log:')
ec, out = run('cat /root/.pm2/logs/ai-meeting-backend-error*.log 2>/dev/null | tail -30', 5)
print(' ', out[:800])

# 4. What URL is frontend using?
print('\n[4] Frontend is at http://118.31.249.156')
print('  Try register from a different browser or incognito mode')

ssh.close()
