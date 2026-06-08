import { Controller, Get, UseGuards } from '@nestjs/common';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('api/schedule')
export class ScheduleController {
  @UseGuards(JwtAuthGuard)
  @Get()
  getSchedule() {
    return { message: 'ok' };
  }
}
