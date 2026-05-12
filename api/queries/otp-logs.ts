import { eq, and, desc, gte, lte, sql, count } from "drizzle-orm";
import { getDb } from "./connection";
import { otpLogs } from "@db/schema";

export async function findOtpLogsByUser(userId: number, limit: number = 50, offset: number = 0) {
  const db = getDb();
  return db
    .select()
    .from(otpLogs)
    .where(eq(otpLogs.userId, userId))
    .orderBy(desc(otpLogs.createdAt))
    .limit(limit)
    .offset(offset);
}

export async function findOtpLogsByUserWithFilters(
  userId: number,
  filters: {
    appName?: string;
    status?: string;
    startDate?: Date;
    endDate?: Date;
  },
  limit: number = 50,
  offset: number = 0
) {
  const db = getDb();
  const conditions = [eq(otpLogs.userId, userId)];

  if (filters.appName) {
    conditions.push(eq(otpLogs.appName, filters.appName));
  }
  if (filters.status) {
    conditions.push(eq(otpLogs.status, filters.status as "success" | "failed" | "error"));
  }
  if (filters.startDate) {
    conditions.push(gte(otpLogs.createdAt, filters.startDate));
  }
  if (filters.endDate) {
    conditions.push(lte(otpLogs.createdAt, filters.endDate));
  }

  return db
    .select()
    .from(otpLogs)
    .where(and(...conditions))
    .orderBy(desc(otpLogs.createdAt))
    .limit(limit)
    .offset(offset);
}

export async function countOtpLogsByUser(userId: number) {
  const db = getDb();
  const result = await db
    .select({ value: count() })
    .from(otpLogs)
    .where(eq(otpLogs.userId, userId));
  return result[0]?.value || 0;
}

export async function getOtpStatsByUser(userId: number) {
  const db = getDb();
  const totalResult = await db
    .select({ value: count() })
    .from(otpLogs)
    .where(eq(otpLogs.userId, userId));

  const successResult = await db
    .select({ value: count() })
    .from(otpLogs)
    .where(and(eq(otpLogs.userId, userId), eq(otpLogs.status, "success")));

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayResult = await db
    .select({ value: count() })
    .from(otpLogs)
    .where(and(eq(otpLogs.userId, userId), gte(otpLogs.createdAt, today)));

  return {
    total: totalResult[0]?.value || 0,
    success: successResult[0]?.value || 0,
    today: todayResult[0]?.value || 0,
    failed: (totalResult[0]?.value || 0) - (successResult[0]?.value || 0),
  };
}

export async function getHourlyStats(userId: number) {
  const db = getDb();
  const twentyFourHoursAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

  return db
    .select({
      hour: sql<string>`DATE_FORMAT(${otpLogs.createdAt}, '%Y-%m-%d %H:00')`,
      count: count(),
    })
    .from(otpLogs)
    .where(and(
      eq(otpLogs.userId, userId),
      gte(otpLogs.createdAt, twentyFourHoursAgo)
    ))
    .groupBy(sql`DATE_FORMAT(${otpLogs.createdAt}, '%Y-%m-%d %H')`)
    .orderBy(desc(sql`DATE_FORMAT(${otpLogs.createdAt}, '%Y-%m-%d %H')`));
}

export async function getAppStats(userId: number) {
  const db = getDb();
  return db
    .select({
      appName: otpLogs.appName,
      total: count(),
      success: sql<number>`SUM(CASE WHEN ${otpLogs.status} = 'success' THEN 1 ELSE 0 END)`,
    })
    .from(otpLogs)
    .where(eq(otpLogs.userId, userId))
    .groupBy(otpLogs.appName);
}

export async function createOtpLog(data: {
  apiKeyId?: number;
  userId: number;
  appName: string;
  phoneHash: string;
  status: "success" | "failed" | "error";
  responseData?: object;
  domainUsed?: string;
  typeCode?: number;
  proxyUsed?: string;
  responseTimeMs?: number;
  errorMessage?: string;
}) {
  const db = getDb();
  return db.insert(otpLogs).values(data);
}
