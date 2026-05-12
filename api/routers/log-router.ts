import { z } from "zod";
import { createRouter, authedQuery } from "../middleware";
import {
  findOtpLogsByUserWithFilters,
  countOtpLogsByUser,
} from "../queries/otp-logs";

export const logRouter = createRouter({
  list: authedQuery
    .input(
      z.object({
        page: z.number().default(1),
        limit: z.number().default(50),
        appName: z.string().optional(),
        status: z.string().optional(),
        startDate: z.string().optional(),
        endDate: z.string().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      const offset = (input.page - 1) * input.limit;
      const filters: any = {};
      if (input.appName) filters.appName = input.appName;
      if (input.status) filters.status = input.status;
      if (input.startDate) filters.startDate = new Date(input.startDate);
      if (input.endDate) filters.endDate = new Date(input.endDate);

      const [logs, total] = await Promise.all([
        findOtpLogsByUserWithFilters(ctx.user.id, filters, input.limit, offset),
        countOtpLogsByUser(ctx.user.id),
      ]);

      return {
        logs: logs.map((l) => ({
          id: l.id,
          appName: l.appName,
          status: l.status,
          domainUsed: l.domainUsed,
          typeCode: l.typeCode,
          proxyUsed: l.proxyUsed,
          responseTimeMs: l.responseTimeMs,
          errorMessage: l.errorMessage,
          createdAt: l.createdAt,
        })),
        total,
        page: input.page,
        totalPages: Math.ceil(total / input.limit),
      };
    }),
});
