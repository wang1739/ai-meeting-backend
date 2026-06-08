import {
  Controller, Get, Post, Param, Body, UseGuards, Req, HttpCode, HttpStatus,
} from '@nestjs/common';
import { ChatService } from './chat.service';
import { CreateMessageDto } from './dto';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import type { Request } from 'express';

@Controller('meetings/:id/messages')
@UseGuards(JwtAuthGuard)
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async create(@Param('id') meetingId: string, @Body() dto: CreateMessageDto, @Req() req: Request) {
    const userId = (req as any).user.sub ?? (req as any).user.id;
    return this.chatService.create(meetingId, userId, dto);
  }

  @Get()
  async findAll(@Param('id') meetingId: string) {
    return this.chatService.findAll(meetingId);
  }
}
