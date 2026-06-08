import { Module } from '@nestjs/common';
import { TranscriptController } from './transcript.controller';
import { TranscriptService } from './transcript.service';
import { PrismaModule } from '../prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [TranscriptController],
  providers: [TranscriptService],
})
export class TranscriptModule {}
