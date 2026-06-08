import { Controller, Get, Post, Patch, Delete, Body, Param, UseGuards, Req } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { MeetingService } from './meeting.service';
import type { CreateMeetingDto } from './dto';

@Controller('meetings')
@UseGuards(AuthGuard('jwt'))
export class MeetingController {
  constructor(private meetingService: MeetingService) {}

  @Post()
  async create(@Body() dto: CreateMeetingDto, @Req() req: any) {
    return this.meetingService.create(dto, req.user.id);
  }

  @Get()
  async findAll(@Req() req: any) {
    return this.meetingService.findAll(req.user.id);
  }

  @Get('action-items/stats')
  async getActionItemsStats(@Req() req: any) {
    return this.meetingService.getActionItemsStats(req.user.id);
  }

  @Get('stats')
  async getStats(@Req() req: any) {
    return this.meetingService.getStats(req.user.id);
  }

  @Get(':id')
  async findOne(@Param('id') id: string, @Req() req: any) {
    return this.meetingService.findOne(id, req.user.id);
  }

  @Patch(':id/end')
  async endMeeting(@Param('id') id: string, @Req() req: any) {
    return this.meetingService.endMeeting(id, req.user.id);
  }

  @Delete(':id')
  async delete(@Param('id') id: string, @Req() req: any) {
    return this.meetingService.delete(id, req.user.id);
  }
}
