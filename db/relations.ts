import { relations } from "drizzle-orm";
import { users, apiKeys, otpLogs, userSettings } from "./schema";

export const usersRelations = relations(users, ({ many, one }) => ({
  apiKeys: many(apiKeys),
  otpLogs: many(otpLogs),
  settings: one(userSettings),
}));

export const apiKeysRelations = relations(apiKeys, ({ one, many }) => ({
  user: one(users, { fields: [apiKeys.userId], references: [users.id] }),
  otpLogs: many(otpLogs),
}));

export const otpLogsRelations = relations(otpLogs, ({ one }) => ({
  user: one(users, { fields: [otpLogs.userId], references: [users.id] }),
  apiKey: one(apiKeys, {
    fields: [otpLogs.apiKeyId],
    references: [apiKeys.id],
  }),
}));

export const userSettingsRelations = relations(userSettings, ({ one }) => ({
  user: one(users, {
    fields: [userSettings.userId],
    references: [users.id],
  }),
}));
