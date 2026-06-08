import { PrismaService } from '../prisma/prisma.service';
import { CreateMessageDto } from './dto';
export declare class ChatService {
    private readonly prisma;
    constructor(prisma: PrismaService);
    create(meetingId: string, userId: string, dto: CreateMessageDto): Promise<{
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
