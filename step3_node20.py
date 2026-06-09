import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

print('\n[1] Download Node.js 20...')
script = """
set -ex
cd /tmp
curl -fsSL --connect-timeout 30 --max-time 120 https://nodejs.org/dist/v20.18.1/node-v20.18.1-linux-x64.tar.xz -o node.tar.xz
ls -lh node.tar.xz
echo 'DOWNLOAD_DONE'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=180)
sin.write(script)
sin.close()
out = sout.read().decode(errors='replace').strip()
print(' ', out[-200:])

print('\n[2] Extract and install...')
script = """
set -ex
cd /tmp
tar -xf node.tar.xz
cp -rf node-v20.18.1-linux-x64/* /usr/local/
/usr/local/bin/node --version
/usr/local/bin/npm --version
echo 'INSTALL_DONE'
"""
sin, sout, serr = ssh.exec_command('bash -s', timeout=30)
sin.write(script)
sin.close()
print(' ', sout.read().decode(errors='replace').strip()[-100:])

# Verify
_, out, _ = ssh.exec_command("/usr/local/bin/node --version", timeout=10)
print('\n  Node:', out.read().decode(errors='replace').strip())

ssh.close()
