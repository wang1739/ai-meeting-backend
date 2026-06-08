import { Controller, Get, Param, Patch, Body, UseGuards, Request } from '@nestjs/common';
import { MeetingReviewService } from './meeting-review.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { UpdateActionItemDto } from './dto/update-action-item.dto';

@Controller('meetings')
@UseGuards(JwtAuthGuard)
export class MeetingReviewController {
  constructor(private readonly reviewService: MeetingReviewService) {}

  @Get(':id/summary')
  getSummary(@Param('id') id: string, @Request() req) {
    return this.reviewService.getSummary(id, req.user.id);
  }

  @Get(':id/action-items')
  getActionItems(@Param('id') id: string, @Request() req) {
    return this.reviewService.getActionItems(id, req.user.id);
  }

  @Patch(':id/action-items/:itemId')
  updateActionItem(
    @Param('id') id: string,
    @Param('itemId') itemId: string,
    @Body() dto: UpdateActionItemDto,
  ) {
    return this.reviewService.updateActionItemStatus(id, itemId, dto.status);
  }
}
