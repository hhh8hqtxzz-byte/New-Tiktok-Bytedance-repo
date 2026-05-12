import { eq, desc } from "drizzle-orm";
import { getDb } from "./connection";
import { apiKeys } from "@db/schema";

export async function findApiKeysByUser(userId: number) {
  const db = getDb();
  return db
    .select()
    .from(apiKeys)
    .where(eq(apiKeys.userId, userId))
    .orderBy(desc(apiKeys.createdAt));
}

export async function findApiKeyById(id: number) {
  const db = getDb();
  const rows = await db.select().from(apiKeys).where(eq(apiKeys.id, id)).limit(1);
  return rows[0] || null;
}

export async function findApiKeyByPrefix(prefix: string) {
  const db = getDb();
  const rows = await db
    .select()
    .from(apiKeys)
    .where(eq(apiKeys.keyPrefix, prefix))
    .limit(1);
  return rows[0] || null;
}

export async function createApiKey(data: {
  userId: number;
  name: string;
  keyHash: string;
  keyPrefix: string;
}) {
  const db = getDb();
  const result = await db.insert(apiKeys).values(data);
  return result;
}

export async function updateApiKeyStatus(id: number, status: "active" | "revoked") {
  const db = getDb();
  return db.update(apiKeys).set({ status }).where(eq(apiKeys.id, id));
}

export async function deleteApiKey(id: number) {
  const db = getDb();
  return db.delete(apiKeys).where(eq(apiKeys.id, id));
}

export async function incrementApiKeyUsage(id: number) {
  const db = getDb();
  const key = await findApiKeyById(id);
  if (!key) return;
  return db
    .update(apiKeys)
    .set({
      requestsCount: (key.requestsCount || 0) + 1,
      lastUsedAt: new Date(),
    })
    .where(eq(apiKeys.id, id));
}
