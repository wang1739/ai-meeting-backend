import { PrismaService } from '../prisma/prisma.service';
import { CreateMeetingDto } from './dto';
export declare class MeetingService {
    private prisma;
    constructor(prisma: PrismaService);
    getActionItemsStats(userId: string): Promise<{
        totalCount: number;
    }>;
    delete(id: string, userId: string): Promise<{
        message: string;
    }>;
    endMeeting(id: string, userId: string): Promise<{
        id: string;
        createdAt: Date;
        updatedAt: Date;
        title: string;
        date: string | null;
        startTime: Date | null;
        endTime: Date | null;
        status: string;
        backgroundInfo: string | null;
        agenda: string | null;
        creatorId: string;
    }>;
    create(dto: CreateMeetingDto, userId: string): Promise<{
        creator: {
            email: string;
            name: string;
            id: string;
        };
        participants: ({
            user: {
                email: string;
                name: string;
                id: string;
            };
        } & {
            id: string;
            createdAt: Date;
            role: string;
            isSpeaker: boolean;
            userId: string;
            meetingId: string;
        })[];
    } & {
        id: string;
        createdAt: Date;
        updatedAt: Date;
        title: string;
        date: string | null;
        startTime: Date | null;
        endTime: Date | null;
        status: string;
        backgroundInfo: string | null;
        agenda: string | null;
        creatorId: string;
    }>;
    findAll(userId: string): Promise<({
        creator: {
            email: string;
            name: string;
            id: string;
        };
        participants: ({
            user: {
                email: string;
                name: string;
                id: string;
            };
        } & {
            id: string;
            createdAt: Date;
            role: string;
            isSpeaker: boolean;
            userId: string;
            meetingId: string;
        })[];
    } & {
        id: string;
        createdAt: Date;
        updatedAt: Date;
        title: string;
        date: string | null;
        startTime: Date | null;
        endTime: Date | null;
        status: string;
        backgroundInfo: string | null;
        agenda: string | null;
        creatorId: string;
    })[]>;
    findOne(id: string, userId: string): Promise<{
        creator: {
            email: string;
            name: string;
            id: string;
        };
        participants: ({
            user: {
                email: string;
                name: string;
                id: string;
            };
        } & {
            id: string;
            createdAt: Date;
            role: string;
            isSpeaker: boolean;
            userId: string;
            meetingId: string;
        })[];
    } & {
        id: string;
        createdAt: Date;
        updatedAt: Date;
        title: string;
        date: string | null;
        startTime: Date | null;
        endTime: Date | null;
        status: string;
        backgroundInfo: string | null;
        agenda: string | null;
        creatorId: string;
    }>;
    getStats(userId: string): Promise<{
        todayCount: number;
        weekTotalHours: string;
    }>;
}
