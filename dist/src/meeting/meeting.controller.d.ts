import { MeetingService } from './meeting.service';
import type { CreateMeetingDto } from './dto';
export declare class MeetingController {
    private meetingService;
    constructor(meetingService: MeetingService);
    create(dto: CreateMeetingDto, req: any): Promise<{
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
    findAll(req: any): Promise<({
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
    getActionItemsStats(req: any): Promise<{
        totalCount: number;
    }>;
    getStats(req: any): Promise<{
        todayCount: number;
        weekTotalHours: string;
    }>;
    findOne(id: string, req: any): Promise<{
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
    endMeeting(id: string, req: any): Promise<{
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
    delete(id: string, req: any): Promise<{
        message: string;
    }>;
}
