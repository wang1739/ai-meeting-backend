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

# 1. Check tsconfig
print('\n[1] tsconfig.json:')
ec, out = run("cat /root/ai-meeting-backend/tsconfig.json 2>/dev/null || echo MISSING", 5)
print(out[:400])

# 2. Check tsconfig.build.json  
print('\n[2] tsconfig.build.json:')
ec, out = run("cat /root/ai-meeting-backend/tsconfig.build.json 2>/dev/null || echo MISSING", 5)
print(out[:400])

# 3. Check nest-cli.json
print('\n[3] nest-cli.json:')
ec, out = run("cat /root/ai-meeting-backend/nest-cli.json 2>/dev/null || echo MISSING", 5)
print(out[:400])

# 4. Check source files exist
print('\n[4] Source files:')
ec, out = run("ls /root/ai-meeting-backend/src/*.ts 2>/dev/null", 5)
print(out[:300])

# 5. Try npx tsc directly  
print('\n[5] Try tsc:')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx tsc -p tsconfig.build.json 2>&1 | tail -20
""", 60)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:500])

# 6. Check what nest build actually does
print('\n[6] Try nest build with verbose:')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx nest build --path tsconfig.build.json 2>&1
ls -la dist/src/ 2>/dev/null | head -5 || echo 'NO DIST'
""", 60)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:500])

# 7. Check if @nestjs/cli is installed
print('\n[7] Nest CLI:')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
ls node_modules/@nestjs/cli 2>/dev/null && echo 'EXISTS' || echo 'MISSING'
npx nest --version 2>&1
""", 10)
print(' ', out[:200])

ssh.close()
