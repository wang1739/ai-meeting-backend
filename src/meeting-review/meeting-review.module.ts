import { Module } from '@nestjs/common';
import { MeetingReviewController } from './meeting-review.controller';
import { MeetingReviewService } from './meeting-review.service';

@Module({
  controllers: [MeetingReviewController],
  providers: [MeetingReviewService],
})
export class MeetingReviewModule {}
