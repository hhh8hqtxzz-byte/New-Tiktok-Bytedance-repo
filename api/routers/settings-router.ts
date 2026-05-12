import { z } from "zod";
import { createRouter, authedQuery } from "../middleware";
import {
  findUserSettings,
  upsertUserSettings,
} from "../queries/user-settings";

export const settingsRouter = createRouter({
  get: authedQuery.query(async ({ ctx }) => {
    const settings = await findUserSettings(ctx.user.id);
    return {
      webhookUrl: settings?.webhookUrl || "",
      defaultProxy: settings?.defaultProxy || "",
      rateLimitPerMinute: settings?.rateLimitPerMinute || 60,
    };
  }),

  update: authedQuery
    .input(
      z.object({
        webhookUrl: z.string().optional(),
        defaultProxy: z.string().optional(),
        rateLimitPerMinute: z.number().min(1).max(10000).optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      await upsertUserSettings({
        userId: ctx.user.id,
        webhookUrl: input.webhookUrl,
        defaultProxy: input.defaultProxy,
        rateLimitPerMinute: input.rateLimitPerMinute,
      });
      return { success: true };
    }),
});
