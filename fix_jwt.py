import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('118.31.249.156', username='root', password='wmm.12345.', timeout=15)
print('[OK]')

# 1. Check auth module code
stdin, stdout, stderr = ssh.exec_command("cat /root/ai-meeting-backend/src/auth/auth.module.ts", timeout=5)
print('auth.module.ts:\n' + stdout.read().decode(errors='replace').strip()[:600])

# 2. Check .env
stdin, stdout, stderr = ssh.exec_command("cat /root/ai-meeting-backend/.env", timeout=5)
print('\n.env:\n' + stdout.read().decode(errors='replace').strip()[:300])

# 3. Fix auth module to use correct JWT format
script = """
cat > /root/ai-meeting-backend/src/auth/auth.module.ts << 'MODEOF'
import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { AuthService } from './auth.service';
import { AuthController } from './auth.controller';
import { JwtStrategy } from './jwt.strategy';
import { PrismaModule } from '../prisma/prisma.module';

@Module({
  imports: [
    PrismaModule,
    PassportModule,
    JwtModule.register({
      secret: process.env.JWT_SECRET || 'default-secret',
      signOptions: { expiresIn: '604800s' },
    }),
  ],
  controllers: [AuthController],
  providers: [AuthService, JwtStrategy],
  exports: [AuthService],
})
export class AuthModule {}
MODEOF
echo 'UPDATED'
"""
stdin, stdout, stderr = ssh.exec_command('bash -s', timeout=5)
stdin.write(script)
stdin.close()
print('\n', stdout.read().decode(errors='replace').strip())

# 4. Rebuild
print('\n[4] Rebuild...')
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && cd /root/ai-meeting-backend && npx tsc -p tsconfig.build.json --outDir dist --skipLibCheck 2>&1 && echo 'OK'", timeout=30)
print(stdout.read().decode(errors='replace').strip()[-100:])

# 5. Restart PM2
print('\n[5] Restart...')
stdin, stdout, stderr = ssh.exec_command("export PATH=/usr/local/bin:$PATH && pm2 restart ai-meeting-backend && sleep 3 && echo 'done'", timeout=15)
stdout.read()

# 6. Test
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"new@demo.com\",\"password\":\"demo123456\",\"name\":\"Demo\"}'", timeout=10)
print('Register:', stdout.read().decode(errors='replace').strip())

stdin, stdout, stderr = ssh.exec_command("curl -s -X POST http://localhost/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"new@demo.com\",\"password\":\"demo123456\"}'", timeout=10)
print('Login:', stdout.read().decode(errors='replace').strip()[:150])

ssh.close()
