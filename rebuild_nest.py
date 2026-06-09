import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Check what's in dist after previous build
stdin, stdout, stderr = ssh.exec_command("ls /root/ai-meeting-backend/dist/ 2>/dev/null | head -20; find /root/ai-meeting-backend/dist -name 'main.js' 2>/dev/null", timeout=5)
print('dist contents:', stdout.read().decode(errors='replace').strip()[:300])

# 2. Check tsconfig includes
stdin, stdout, stderr = ssh.exec_command("grep -A2 'include' /root/ai-meeting-backend/tsconfig.json 2>/dev/null; echo '---'; grep -A2 'include' /root/ai-meeting-backend/tsconfig.build.json 2>/dev/null", timeout=5)
print('\nInclude config:\n', stdout.read().decode(errors='replace').strip())

# 3. Run nest build (it knows the project structure)
print('\n[3] Run nest build...')
script = """
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
rm -rf dist
npx nest build 2>&1
echo 'BUILD_EXIT:' $?
find dist -name 'main.js' 2>/dev/null
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=60)
stdin.write(script)
stdin.close()
out = stdout.read().decode(errors='replace').strip()
print(out[-400:])

# 4. Verify and start
main_js = ''
stdin, stdout, stderr = ssh.exec_command("find /root/ai-meeting-backend/dist -name 'main.js' 2>/dev/null", timeout=5)
main_js = stdout.read().decode(errors='replace').strip()
print('\n[4] Main.js:', main_js)

if main_js:
    # Start PM2
    script = f"""
export PATH=/usr/local/bin:$PATH
cd /root/ai-meeting-backend
pm2 delete ai-meeting-backend 2>/dev/null || true
pm2 start dist/src/main.js --name ai-meeting-backend -i 1
pm2 save
sleep 4
curl -s http://localhost:3000/api/meetings
"""
    stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=20)
    stdin.write(script)
    stdin.close()
    print('PM2:', stdout.read().decode(errors='replace').strip()[:200])

time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"x@y.com\",\"password\":\"test123456\",\"name\":\"XY\"}'", timeout=10)
print('\nRegister:', stdout.read().decode(errors='replace').strip()[:100])

ssh.close()
