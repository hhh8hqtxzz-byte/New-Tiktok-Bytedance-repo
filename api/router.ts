import { authRouter } from "./auth-router";
import { apiKeyRouter } from "./routers/api-key-router";
import { otpRouter } from "./routers/otp-router";
import { logRouter } from "./routers/log-router";
import { settingsRouter } from "./routers/settings-router";
import { createRouter, publicQuery } from "./middleware";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  auth: authRouter,
  apiKey: apiKeyRouter,
  otp: otpRouter,
  log: logRouter,
  settings: settingsRouter,
});

export type AppRouter = typeof appRouter;
