import { z } from "zod";
import { createRouter, authedQuery } from "../middleware";
import {
  findApiKeysByUser,
  findApiKeyById,
  createApiKey,
  updateApiKeyStatus,
  deleteApiKey,
} from "../queries/api-keys";
import crypto from "crypto";

function generateApiKey() {
  const prefix = "tk_";
  const random = crypto.randomBytes(24).toString("hex");
  return prefix + random;
}

function hashApiKey(key: string) {
  return crypto.createHash("sha256").update(key).digest("hex");
}

export const apiKeyRouter = createRouter({
  list: authedQuery.query(async ({ ctx }) => {
    const keys = await findApiKeysByUser(ctx.user.id);
    return keys.map((k) => ({
      id: k.id,
      name: k.name,
      prefix: k.keyPrefix,
      status: k.status,
      requestsCount: k.requestsCount,
      createdAt: k.createdAt,
      lastUsedAt: k.lastUsedAt,
    }));
  }),

  create: authedQuery
    .input(z.object({ name: z.string().min(1).max(100) }))
    .mutation(async ({ ctx, input }) => {
      const key = generateApiKey();
      const hash = hashApiKey(key);
      const prefix = key.slice(0, 12);

      await createApiKey({
        userId: ctx.user.id,
        name: input.name,
        keyHash: hash,
        keyPrefix: prefix,
      });

      return { key, prefix };
    }),

  revoke: authedQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ ctx, input }) => {
      const key = await findApiKeyById(input.id);
      if (!key || key.userId !== ctx.user.id) {
        throw new Error("API key not found");
      }
      await updateApiKeyStatus(input.id, "revoked");
      return { success: true };
    }),

  delete: authedQuery
    .input(z.object({ id: z.number() }))
    .mutation(async ({ ctx, input }) => {
      const key = await findApiKeyById(input.id);
      if (!key || key.userId !== ctx.user.id) {
        throw new Error("API key not found");
      }
      await deleteApiKey(input.id);
      return { success: true };
    }),
});
