import {
  Controller, Get, Post, Param, Body, UseGuards, HttpCode, HttpStatus,
} from '@nestjs/common';
import { TranscriptService } from './transcript.service';
import { CreateTranscriptDto } from './dto/create-transcript.dto';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('meetings/:id/transcripts')
@UseGuards(JwtAuthGuard)
export class TranscriptController {
  constructor(private readonly transcriptService: TranscriptService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(@Param('id') meetingId: string, @Body() dto: CreateTranscriptDto | CreateTranscriptDto[]) {
    if (Array.isArray(dto)) {
      return this.transcriptService.createBatch(meetingId, dto);
    }
    return this.transcriptService.create(meetingId, dto);
  }

  @Get()
  async findAll(@Param('id') meetingId: string) {
    return this.transcriptService.findAll(meetingId);
  }
}
