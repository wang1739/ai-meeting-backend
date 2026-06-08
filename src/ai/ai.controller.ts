import { Controller, Post, Param, UseGuards, Req } from '@nestjs/common';
import { AiService } from './ai.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('meetings')
@UseGuards(JwtAuthGuard)
export class AiController {
  constructor(private readonly aiService: AiService) {}

  @Post(':id/generate-summary')
  async generateSummary(@Param('id') id: string, @Req() req: any) {
    return this.aiService.generateSummary(id, req.user.id);
  }
}
