import {
  mysqlTable,
  mysqlEnum,
  serial,
  varchar,
  text,
  timestamp,
  int,
  json,
  boolean,
  bigint,
} from "drizzle-orm/mysql-core";

export const users = mysqlTable("users", {
  id: serial("id").primaryKey(),
  unionId: varchar("unionId", { length: 255 }).notNull().unique(),
  name: varchar("name", { length: 255 }),
  email: varchar("email", { length: 320 }),
  avatar: text("avatar"),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
  lastSignInAt: timestamp("lastSignInAt").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

export const apiKeys = mysqlTable("api_keys", {
  id: serial("id").primaryKey(),
  userId: bigint("userId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => users.id),
  name: varchar("name", { length: 255 }).notNull(),
  keyHash: varchar("keyHash", { length: 255 }).notNull(),
  keyPrefix: varchar("keyPrefix", { length: 16 }).notNull(),
  status: mysqlEnum("status", ["active", "revoked"]).default("active").notNull(),
  requestsCount: int("requestsCount").default(0).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  lastUsedAt: timestamp("lastUsedAt"),
});

export type ApiKey = typeof apiKeys.$inferSelect;

export const otpLogs = mysqlTable("otp_logs", {
  id: serial("id").primaryKey(),
  apiKeyId: bigint("apiKeyId", { mode: "number", unsigned: true }).references(
    () => apiKeys.id
  ),
  userId: bigint("userId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => users.id),
  appName: varchar("appName", { length: 100 }).notNull(),
  phoneHash: varchar("phoneHash", { length: 255 }).notNull(),
  status: mysqlEnum("status", ["success", "failed", "error"]).notNull(),
  responseData: json("responseData"),
  domainUsed: varchar("domainUsed", { length: 255 }),
  typeCode: int("typeCode"),
  proxyUsed: varchar("proxyUsed", { length: 255 }),
  responseTimeMs: int("responseTimeMs"),
  errorMessage: text("errorMessage"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type OtpLog = typeof otpLogs.$inferSelect;

export const appConfigs = mysqlTable("app_configs", {
  id: serial("id").primaryKey(),
  key: varchar("key", { length: 100 }).notNull().unique(),
  name: varchar("name", { length: 255 }).notNull(),
  aid: int("aid").notNull(),
  appName: varchar("appName", { length: 100 }).notNull(),
  package: varchar("package", { length: 255 }).notNull(),
  versionCode: varchar("versionCode", { length: 50 }).notNull(),
  versionName: varchar("versionName", { length: 50 }).notNull(),
  channel: varchar("channel", { length: 50 }).notNull(),
  typeCodesJson: text("typeCodesJson").notNull(),
  domainsJson: text("domainsJson").notNull(),
  needsProxy: boolean("needsProxy").default(false).notNull(),
  webEndpoint: boolean("webEndpoint").default(false).notNull(),
  voiceEndpoint: boolean("voiceEndpoint").default(false).notNull(),
  unsignedMobile: boolean("unsignedMobile").default(false).notNull(),
  isActive: boolean("isActive").default(true).notNull(),
  category: varchar("category", { length: 50 }).default("general").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type AppConfig = typeof appConfigs.$inferSelect;

export const userSettings = mysqlTable("user_settings", {
  id: serial("id").primaryKey(),
  userId: bigint("userId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => users.id)
    .unique(),
  webhookUrl: varchar("webhookUrl", { length: 500 }),
  defaultProxy: varchar("defaultProxy", { length: 255 }),
  rateLimitPerMinute: int("rateLimitPerMinute").default(60).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
});

export type UserSettings = typeof userSettings.$inferSelect;
