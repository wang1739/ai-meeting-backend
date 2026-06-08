"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AiService = void 0;
const common_1 = require("@nestjs/common");
const config_1 = require("@nestjs/config");
const prisma_service_1 = require("../prisma/prisma.service");
let AiService = class AiService {
    prisma;
    config;
    constructor(prisma, config) {
        this.prisma = prisma;
        this.config = config;
    }
    async generateSummary(meetingId, userId) {
        const meeting = await this.prisma.meeting.findUnique({
            where: { id: meetingId },
            include: {
                creator: { select: { id: true, name: true } },
            },
        });
        if (!meeting)
            throw new common_1.NotFoundException('会议不存在');
        const isCreator = meeting.creatorId === userId;
        const participant = await this.prisma.meetingParticipant.findUnique({
            where: { meetingId_userId: { meetingId, userId } },
        });
        if (!isCreator && !participant) {
            throw new common_1.ForbiddenException('无权访问此会议');
        }
        const existingSummaries = await this.prisma.meetingSummary.findMany({
            where: { meetingId },
        });
        const existingActionItems = await this.prisma.actionItem.findMany({
            where: { meetingId },
        });
        if (existingSummaries.length > 0) {
            return this.buildResponse(existingSummaries, existingActionItems);
        }
        const agendaText = this.parseAgenda(meeting.agenda);
        const transcriptSegments = await this.prisma.transcriptionSegment.findMany({
            where: { meetingId },
            orderBy: { startTimeMs: 'asc' },
        });
        const transcriptText = transcriptSegments
            .map((s) => `[${s.speakerLabel}] ${s.text}`)
            .join('\n');
        const prompt = this.buildPrompt(meeting.title, agendaText, transcriptText);
        let summaryData;
        const apiKey = this.config.get('OPENAI_API_KEY');
        if (apiKey) {
            try {
                summaryData = await this.callOpenAI(prompt, apiKey);
            }
            catch {
                summaryData = this.getMockSummary(meeting.title, agendaText, transcriptText);
            }
        }
        else {
            summaryData = this.getMockSummary(meeting.title, agendaText, transcriptText);
        }
        const [savedSummaries, savedActionItems] = await this.prisma.$transaction(async (tx) => {
            const recheckSummaries = await tx.meetingSummary.findMany({ where: { meetingId } });
            if (recheckSummaries.length > 0) {
                const existingItems = await tx.actionItem.findMany({ where: { meetingId } });
                return [recheckSummaries, existingItems];
            }
            await tx.meetingSummary.createMany({
                data: [
                    { meetingId, summaryType: 'one_line', content: summaryData.oneLineSummary },
                    { meetingId, summaryType: 'detailed', content: summaryData.detailedSummary },
                    { meetingId, summaryType: 'key_decisions', content: JSON.stringify(summaryData.keyDecisions) },
                    { meetingId, summaryType: 'keywords', content: JSON.stringify(summaryData.keywords) },
                ],
            });
            if (summaryData.actionItems.length > 0) {
                const existingDbItems = await tx.actionItem.findMany({
                    where: { meetingId },
                    select: { description: true },
                });
                const existingKeys = new Set(existingDbItems.map((i) => i.description.slice(0, 50)));
                const uniqueInPayload = summaryData.actionItems.filter((item, index, self) => index === self.findIndex((t) => t.description.slice(0, 50) === item.description.slice(0, 50)));
                const newItems = uniqueInPayload.filter((item) => !existingKeys.has(item.description.slice(0, 50))).slice(0, 5);
                console.log(`[AiService] 去重统计: 原始=${summaryData.actionItems.length}, 行内去重后=${uniqueInPayload.length}, DB去重后=${newItems.length}, DB已有=${existingDbItems.length}`);
                if (newItems.length > 0) {
                    await tx.actionItem.createMany({
                        data: newItems.map((item) => ({
                            meetingId,
                            description: item.description,
                            assigneeName: item.assignee,
                            assigneeUserId: userId,
                            dueDate: item.dueDate ? new Date(item.dueDate) : null,
                            status: 'open',
                        })),
                    });
                }
            }
            const summaries = await tx.meetingSummary.findMany({ where: { meetingId } });
            const items = await tx.actionItem.findMany({ where: { meetingId } });
            return [summaries, items];
        });
        return this.buildResponse(savedSummaries, savedActionItems);
    }
    buildPrompt(title, agenda, transcript) {
        return `你是一个专业的会议纪要助手。请根据以下会议内容生成会议摘要。

会议标题：${title}
${agenda ? `\n议程列表：\n${agenda}` : '本次会议没有预设议程，请根据标题推断合理的讨论内容。'}
${transcript ? `\n会议发言记录：\n${transcript}\n` : '\n提示：暂无会议发言记录，请仅根据议程生成合理的会议摘要。\n'}

必须遵守的规则：
1. 【会议背景】用1-2句话概括会议目的和背景，必须基于发言记录中的实际讨论内容
2. 【讨论要点】对每条议程，根据发言记录中的实际论述生成1条具体的讨论结果（不是"进行了深入讨论"，而是引用发言人提到的具体结论、方案、数据）
3. 【会议结论】根据发言人达成的共识总结2-3句话，引用发言记录中的具体观点
4. 【关键决策】每条决策必须是发言记录中实际确定的，不要杜撰
5. 【行动项】每条行动项必须来自发言记录中明确提出的待办事项，包含具体的产出物或交付标准
6. 【领域适配】根据发言记录中的行业术语自动调整语言风格，使用该领域通用的角色和词汇
7. 【禁止】讨论要点、决策和行动项必须与发言记录直接相关，不要使用模板化表述；行动项不超过5条；不要重复相同的行动项

请严格按照以下 JSON 格式返回，不要包含其他内容：
{
  "oneLineSummary": "一句话总结会议内容（不超过50字）",
  "detailedSummary": "分段详细摘要（使用Markdown格式，包含## 会议背景、## 讨论要点、## 会议结论等章节）",
  "keyDecisions": ["决策1", "决策2", "决策3"],
  "actionItems": [
    {"description": "任务描述（含产出物/交付标准）", "assignee": "负责人", "dueDate": "2026-06-10T18:00:00Z"}
  ],
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4"]
}`;
    }
    parseAgenda(agenda) {
        if (!agenda)
            return '';
        if (typeof agenda === 'string') {
            try {
                const parsed = JSON.parse(agenda);
                if (Array.isArray(parsed)) {
                    return parsed
                        .map((item, index) => {
                        const title = typeof item === 'string' ? item : item.title || item.name || '';
                        return `${index + 1}. ${title}`;
                    })
                        .join('\n');
                }
                return agenda;
            }
            catch {
                return agenda;
            }
        }
        if (Array.isArray(agenda)) {
            return agenda
                .map((item, index) => {
                const title = item.title || item.name || '';
                return `${index + 1}. ${title}`;
            })
                .join('\n');
        }
        return String(agenda);
    }
    async callOpenAI(prompt, apiKey) {
        const baseUrl = this.config.get('OPENAI_BASE_URL') || 'https://api.deepseek.com';
        const model = this.config.get('OPENAI_MODEL') || 'deepseek-chat';
        const response = await fetch(`${baseUrl}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`,
            },
            body: JSON.stringify({
                model,
                messages: [
                    { role: 'system', content: '你是一个专业的会议纪要助手，总是返回有效的JSON。' },
                    { role: 'user', content: prompt },
                ],
                temperature: 0.3,
            }),
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API error: ${response.status} ${errorText}`);
        }
        const data = await response.json();
        return JSON.parse(data.choices[0].message.content);
    }
    getMockSummary(title, agendaText, transcriptText) {
        const lines = agendaText.split('\n').filter(Boolean);
        const agendaItems = lines.map((l) => l.replace(/^\d+\.\s*/, '').trim()).filter(Boolean);
        const transcriptLines = transcriptText ? transcriptText.split('\n').filter(Boolean) : [];
        const hasTranscript = transcriptLines.length > 0;
        const topPhrases = hasTranscript
            ? transcriptLines.slice(0, Math.min(5, transcriptLines.length))
                .map((l) => l.replace(/^\[.*?\]\s*/, '').trim())
                .filter((l) => l.length > 5)
            : [];
        const discussionPoints = hasTranscript
            ? topPhrases.map((phrase) => `- ${phrase}`).join('\n')
            : agendaItems.length > 0
                ? agendaItems.map((item) => `- 针对「${item}」，与会人员达成了初步共识，明确了下一阶段的工作方向和重点任务，相关责任人将在规定时间内输出具体方案`)
                    .join('\n')
                : '- 与会人员就会议主题进行了充分讨论，确认了当前工作进展和存在的主要问题\n- 识别了跨部门协作的关键环节，制定了相应的协调机制\n- 风险评估显示各项任务整体可控，新增事项已指定负责人跟进';
        const decisions = hasTranscript
            ? topPhrases.slice(0, 3).map((p) => `根据发言内容确认「${p.slice(0, 20)}...」相关事项的推进方案`)
            : agendaItems.length > 0
                ? agendaItems.map((item) => {
                    const idx = agendaItems.indexOf(item);
                    const specificDecisions = [
                        `确认了「${item}」的实施方案和时间节点，采用分阶段推进方式，优先完成核心事项`,
                        `明确了「${item}」的执行方向和责任人，相关团队需在约定时间内完成调研并汇报结果`,
                    ];
                    return specificDecisions[idx % 2];
                })
                : [
                    '确认了各项工作采用分阶段推进模式，核心事项优先完成',
                    '明确了跨部门协作的对接流程和沟通机制',
                    '制定了风险应对策略：重点事项由专人跟进并定期同步进展',
                ];
        let actionItems = [];
        if (hasTranscript) {
            actionItems = topPhrases.slice(0, 3).map((p, i) => ({
                description: `跟进「${p.slice(0, 30)}」相关事项，输出执行方案和交付计划`,
                assignee: i === 0 ? '项目负责人' : i === 1 ? '执行负责人' : '相关责任人',
                dueDate: new Date(Date.now() + (i + 1) * 7 * 86400000).toISOString(),
            }));
        }
        else if (agendaItems.length > 0) {
            const specificTasks = [
                (item) => `输出「${item}」的实施方案文档，包含执行计划、资源配置和时间节点，提交团队评审`,
                (item) => `完成「${item}」的调研工作并输出调研报告，附带相关数据分析和建议方案`,
                (item) => `制定「${item}」的执行细则和操作流程，同步至所有相关成员`,
            ];
            actionItems = agendaItems.slice(0, 5).map((item, i) => ({
                description: specificTasks[i % 3](item),
                assignee: i === 0 ? '项目负责人' : i === 1 ? '执行负责人' : i === 2 ? '质量负责人' : '相关责任人',
                dueDate: new Date(Date.now() + (i + 1) * 7 * 86400000).toISOString(),
            }));
        }
        else {
            actionItems = [
                { description: '输出项目实施方案（含执行计划、资源配置和时间节点），提交团队评审', assignee: '项目负责人', dueDate: new Date(Date.now() + 7 * 86400000).toISOString() },
                { description: '完成分阶段执行计划的排期表，标注关键节点和依赖关系，同步各相关方', assignee: '执行负责人', dueDate: new Date(Date.now() + 3 * 86400000).toISOString() },
                { description: '处理已识别的高优先级事项，输出进展报告（含处理结果和后续计划）', assignee: '质量负责人', dueDate: new Date(Date.now() + 5 * 86400000).toISOString() },
            ];
        }
        return {
            oneLineSummary: `本次会议围绕「${title}」展开讨论，${agendaItems.length > 0 ? `就${agendaItems[0]}等${agendaItems.length}项议程达成一致` : '明确了当前进展和后续计划'}，确定了分阶段实施方案和责任人。`,
            detailedSummary: `## 会议背景\n本次会议议题为「${title}」${agendaItems.length > 0 ? `，涵盖${agendaItems.join('、')}等${agendaItems.length}项议程` : ''}。\n\n## 讨论要点\n${discussionPoints}\n\n## 会议结论\n经过充分讨论，团队就核心实施方案达成一致：采用分阶段推进模式确保核心事项优先完成；明确了各项工作的交付里程碑和验收标准；对识别出的关键事项已逐一指定责任人和应对方案。`,
            keyDecisions: decisions,
            actionItems,
            keywords: agendaItems.length > 0 ? agendaItems.concat([title, '会议纪要', '行动计划']).slice(0, 6) : [title, '会议纪要', '行动计划', '项目排期', '任务分配'],
        };
    }
    buildResponse(summaries, actionItems) {
        const findSummary = (type) => summaries.find((s) => s.summaryType === type)?.content || '';
        let keyDecisions = [];
        try {
            keyDecisions = JSON.parse(findSummary('key_decisions'));
        }
        catch {
            keyDecisions = [];
        }
        let keywords = [];
        try {
            keywords = JSON.parse(findSummary('keywords'));
        }
        catch {
            keywords = [];
        }
        return {
            oneLineSummary: findSummary('one_line'),
            detailedSummary: findSummary('detailed'),
            keyDecisions,
            keywords,
            actionItems: actionItems.map((item) => ({
                id: item.id,
                description: item.description,
                assignee: item.assigneeName,
                dueDate: item.dueDate,
                status: item.status,
            })),
        };
    }
};
exports.AiService = AiService;
exports.AiService = AiService = __decorate([
    (0, common_1.Injectable)(),
    __metadata("design:paramtypes", [prisma_service_1.PrismaService,
        config_1.ConfigService])
], AiService);
//# sourceMappingURL=ai.service.js.map