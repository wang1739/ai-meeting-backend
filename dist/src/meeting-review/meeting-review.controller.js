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
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MeetingReviewController = void 0;
const common_1 = require("@nestjs/common");
const meeting_review_service_1 = require("./meeting-review.service");
const jwt_auth_guard_1 = require("../auth/jwt-auth.guard");
const update_action_item_dto_1 = require("./dto/update-action-item.dto");
let MeetingReviewController = class MeetingReviewController {
    reviewService;
    constructor(reviewService) {
        this.reviewService = reviewService;
    }
    getSummary(id, req) {
        return this.reviewService.getSummary(id, req.user.id);
    }
    getActionItems(id, req) {
        return this.reviewService.getActionItems(id, req.user.id);
    }
    updateActionItem(id, itemId, dto) {
        return this.reviewService.updateActionItemStatus(id, itemId, dto.status);
    }
};
exports.MeetingReviewController = MeetingReviewController;
__decorate([
    (0, common_1.Get)(':id/summary'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Request)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], MeetingReviewController.prototype, "getSummary", null);
__decorate([
    (0, common_1.Get)(':id/action-items'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Request)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], MeetingReviewController.prototype, "getActionItems", null);
__decorate([
    (0, common_1.Patch)(':id/action-items/:itemId'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Param)('itemId')),
    __param(2, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String, update_action_item_dto_1.UpdateActionItemDto]),
    __metadata("design:returntype", void 0)
], MeetingReviewController.prototype, "updateActionItem", null);
exports.MeetingReviewController = MeetingReviewController = __decorate([
    (0, common_1.Controller)('meetings'),
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    __metadata("design:paramtypes", [meeting_review_service_1.MeetingReviewService])
], MeetingReviewController);
//# sourceMappingURL=meeting-review.controller.js.map