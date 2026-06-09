import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

def run(cmd, timeout=60):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    return ec, out

# 1. Run tsc with noEmit to see errors
print('\n[1] tsc --noEmit (check errors):')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx tsc --noEmit --noErrorTruncation 2>&1 | head -30
""", 60)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(safe[:800])

# 2. Try building and check what happens
print('\n[2] Build and track output:')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx tsc -p tsconfig.build.json 2>&1
echo "EXIT_CODE=$?"
ls dist/src/ 2>/dev/null | head -10 || echo 'DIST_EMPTY'
""", 60)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:500])

# 3. Check source files are complete
print('\n[3] All source files:')
ec, out = run("find /root/ai-meeting-backend/src -name '*.ts' 2>/dev/null | head -30", 5)
print(' ', out[:500])

ssh.close()
