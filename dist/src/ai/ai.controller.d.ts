import { AiService } from './ai.service';
export declare class AiController {
    private readonly aiService;
    constructor(aiService: AiService);
    generateSummary(id: string, req: any): Promise<{
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
}
