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

# 1. Check TypeScript version
print('\n[1] TypeScript version:')
ec, out = run("export PATH=/usr/local/bin:$PATH && cd /root/ai-meeting-backend && npx tsc --version 2>&1", 10)
print(' ', out)

# 2. Check full tsconfig
print('\n[2] Full tsconfig.json:')
ec, out = run("cat /root/ai-meeting-backend/tsconfig.json", 5)
print(out[:600])

# 3. Try basic tsc compile - just one file
print('\n[3] Try basic compile:')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
npx tsc src/main.ts --outDir /tmp/test_dist --skipLibCheck 2>&1
echo "EC=$?"
ls -la /tmp/test_dist/ 2>/dev/null || echo 'EMPTY'
""", 20)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:500])

# 4. Check if @nestjs deps are correctly installed
print('\n[4] NestJS deps:')
ec, out = run("ls /root/ai-meeting-backend/node_modules/@nestjs/core/package.json 2>/dev/null && echo 'CORE_OK' || echo 'CORE_MISSING'", 5)
print(' ', out)

# 5. Try local build and copy
print('\n[5] Build locally approach:')
ec, out = run("""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
# Remove deleteOutDir which deletes the dist
sed -i 's/"deleteOutDir": true/"deleteOutDir": false/' nest-cli.json 2>/dev/null || true
cat nest-cli.json
echo "---"
# Try compile again
npx tsc --outDir dist --skipLibCheck --pretty false 2>&1
echo "tsc exit: $?"
ls -la dist/ 2>/dev/null | head -5
""", 30)
safe = ''.join(c if c.isascii() else '?' for c in out)
print(' ', safe[:600])

ssh.close()
