import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../prisma/prisma.service';
export declare class AiService {
    private prisma;
    private config;
    constructor(prisma: PrismaService, config: ConfigService);
    generateSummary(meetingId: string, userId: string): Promise<{
        oneLineSummary: any;
        detailedSummary: any;
        keyDecisions: string[];
        keywords: string[];
        actionItems: {
            id: any;
            description: any;
            assignee: any;
            dueDate: any;
            status: any;
        }[];
    }>;
    private buildPrompt;
    private parseAgenda;
    private callOpenAI;
    private getMockSummary;
    private buildResponse;
}
