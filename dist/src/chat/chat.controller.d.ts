import { ChatService } from './chat.service';
import { CreateMessageDto } from './dto';
import type { Request } from 'express';
export declare class ChatController {
    private readonly chatService;
    constructor(chatService: ChatService);
    create(meetingId: string, dto: CreateMessageDto, req: Request): Promise<{
        id: string;
        createdAt: Date;
        userId: string;
        meetingId: string;
        content: string;
        userName: string;
    }>;
    findAll(meetingId: string): Promise<{
        id: string;
        createdAt: Date;
        userId: string;
        meetingId: string;
        content: string;
        userName: string;
    }[]>;
}
