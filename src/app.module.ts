import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { MeetingModule } from './meeting/meeting.module';
import { MeetingReviewModule } from './meeting-review/meeting-review.module';
import { AiModule } from './ai/ai.module';
import { ChatModule } from './chat/chat.module';
import { TranscriptModule } from './transcript/transcript.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    PrismaModule,
    AuthModule,
    MeetingModule,
    MeetingReviewModule,
    AiModule,
    ChatModule,
    TranscriptModule,
  ],
})
export class AppModule {}
