import { eq } from "drizzle-orm";
import { getDb } from "./connection";
import { userSettings } from "@db/schema";

export async function findUserSettings(userId: number) {
  const db = getDb();
  const rows = await db
    .select()
    .from(userSettings)
    .where(eq(userSettings.userId, userId))
    .limit(1);
  return rows[0] || null;
}

export async function upsertUserSettings(data: {
  userId: number;
  webhookUrl?: string;
  defaultProxy?: string;
  rateLimitPerMinute?: number;
}) {
  const db = getDb();
  const existing = await findUserSettings(data.userId);

  if (existing) {
    return db
      .update(userSettings)
      .set({
        webhookUrl: data.webhookUrl ?? existing.webhookUrl,
        defaultProxy: data.defaultProxy ?? existing.defaultProxy,
        rateLimitPerMinute: data.rateLimitPerMinute ?? existing.rateLimitPerMinute,
        updatedAt: new Date(),
      })
      .where(eq(userSettings.id, existing.id));
  }

  return db.insert(userSettings).values({
    userId: data.userId,
    webhookUrl: data.webhookUrl,
    defaultProxy: data.defaultProxy,
    rateLimitPerMinute: data.rateLimitPerMinute ?? 60,
  });
}
