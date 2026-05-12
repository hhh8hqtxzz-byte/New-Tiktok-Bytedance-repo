import { z } from "zod";
import { createRouter, authedQuery } from "../middleware";
import { findAllAppConfigs, findAppConfigByKey, seedAppConfigs } from "../queries/app-configs";
import {
  getOtpStatsByUser,
  getHourlyStats,
  getAppStats,
  createOtpLog,
} from "../queries/otp-logs";
import { incrementApiKeyUsage, findApiKeyByPrefix } from "../queries/api-keys";
import crypto from "crypto";

function hashPhone(phone: string) {
  return crypto.createHash("sha256").update(phone).digest("hex");
}

function encryptPhone(phone: string) {
  let encrypted = "";
  for (const char of phone) {
    const encryptedByte = char.charCodeAt(0) ^ 5;
    encrypted += encryptedByte.toString(16).padStart(2, "0");
  }
  return encrypted;
}

async function sendWebOtp(
  phone: string,
  app: any,
  typeCode: number,
  _proxy?: string
) {
  const encrypted = encryptPhone(phone);
  const domain = app.domainsJson
    ? JSON.parse(app.domainsJson)[0]
    : "www.tiktok.com";

  const body = new URLSearchParams({
    mobile: encrypted,
    type: String(typeCode),
    aid: String(app.aid),
    app_name: app.appName,
    account_sdk_source: "web",
    mix_mode: "1",
    auto_read: "0",
  });

  const url = `https://${domain}/passport/web/send_code/?aid=${app.aid}&app_name=${app.appName}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    Accept: "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    Origin: `https://${domain}`,
    Referer: `https://${domain}/`,
    "X-SS-DP": String(app.aid),
  };

  const startTime = Date.now();
  try {
    const fetchInit: RequestInit = {
      method: "POST",
      headers,
      body: body.toString(),
      redirect: "follow",
    };

    if (_proxy) {
      // Proxy support would need additional configuration
      // For now, we send directly
      void _proxy;
    }

    const response = await fetch(url, fetchInit);
    const elapsed = Date.now() - startTime;
    const text = await response.text();

    let data: any = {};
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text.slice(0, 500) };
    }

    const success = data.message === "success" || data.data?.message === "success";

    return {
      success,
      statusCode: response.status,
      data,
      timeMs: elapsed,
      domain,
      method: "web_endpoint",
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.message || "Request failed",
      timeMs: Date.now() - startTime,
      domain,
      method: "web_endpoint",
    };
  }
}

async function sendUnsignedMobileOtp(
  phone: string,
  app: any,
  typeCode: number,
  _proxy?: string
) {
  const encrypted = encryptPhone(phone);
  const domains = app.domainsJson ? JSON.parse(app.domainsJson) : ["api16-normal-c-useast2a.tiktokv.com"];
  const domain = domains[Math.floor(Math.random() * domains.length)];
  const timestamp = Math.floor(Date.now() / 1000);
  const deviceId = String(Math.floor(Math.random() * 9e15) + 1e15);
  const iid = String(Math.floor(Math.random() * 9e15) + 1e15);

  const commonParams: Record<string, string> = {
    aid: String(app.aid),
    app_name: app.appName,
    version_code: app.versionCode,
    version_name: app.versionName,
    device_platform: "android",
    os: "android",
    device_id: deviceId,
    iid: iid,
    ssmix: "a",
    carrier_region: "US",
    "passport-sdk-version": "50559",
    ts: String(timestamp),
    _rticket: String(timestamp * 1000),
  };

  const bodyParams: Record<string, string> = { ...commonParams };
  bodyParams.mobile = encrypted;
  bodyParams.type = String(typeCode);
  bodyParams.auto_read = "0";
  bodyParams.account_sdk_source = "app";
  bodyParams.unbind_exist = "35";
  bodyParams.mix_mode = "1";

  const url = `https://${domain}/passport/mobile/send_code/v1/?${new URLSearchParams(commonParams).toString()}`;
  const body = new URLSearchParams(bodyParams).toString();

  const headers: Record<string, string> = {
    Host: domain,
    "User-Agent": `${app.package}/${app.versionCode} (Linux; U; Android 13; en_US; SM-G991B; Build/UP1A.231005.007)`,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept-Encoding": "gzip, deflate",
    "X-SS-DP": String(app.aid),
    "sdk-version": "2",
    "passport-sdk-version": "50559",
  };

  const startTime = Date.now();
  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body,
      redirect: "follow",
    });
    const elapsed = Date.now() - startTime;
    const text = await response.text();

    let data: any = {};
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text.slice(0, 500) };
    }

    const success = data.message === "success" || data.data?.message === "success";

    return {
      success,
      statusCode: response.status,
      data,
      timeMs: elapsed,
      domain,
      method: "unsigned_mobile",
    };
  } catch (error: any) {
    return {
      success: false,
      error: error.message || "Request failed",
      timeMs: Date.now() - startTime,
      domain,
      method: "unsigned_mobile",
    };
  }
}

export const otpRouter = createRouter({
  getApps: authedQuery.query(async () => {
    let apps = await findAllAppConfigs();
    if (apps.length === 0) {
      await seedAppConfigs();
      apps = await findAllAppConfigs();
    }
    return apps.map((a) => ({
      key: a.key,
      name: a.name,
      aid: a.aid,
      appName: a.appName,
      typeCodes: a.typeCodesJson ? JSON.parse(a.typeCodesJson) : [],
      domains: a.domainsJson ? JSON.parse(a.domainsJson) : [],
      category: a.category,
      webEndpoint: a.webEndpoint,
      voiceEndpoint: a.voiceEndpoint,
      unsignedMobile: a.unsignedMobile,
    }));
  }),

  getStats: authedQuery.query(async ({ ctx }) => {
    const [stats, hourly, appStats] = await Promise.all([
      getOtpStatsByUser(ctx.user.id),
      getHourlyStats(ctx.user.id),
      getAppStats(ctx.user.id),
    ]);

    return {
      ...stats,
      successRate: stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0,
      hourly,
      appStats: appStats.map((a) => ({
        appName: a.appName,
        total: a.total,
        successRate: a.total > 0 ? Math.round((a.success / a.total) * 100) : 0,
      })),
    };
  }),

  send: authedQuery
    .input(
      z.object({
        phone: z.string().min(5).max(20),
        appKey: z.string().min(1),
        typeCode: z.number().optional(),
        proxy: z.string().optional(),
        domain: z.string().optional(),
        apiKey: z.string().optional(),
      })
    )
    .mutation(async ({ ctx, input }) => {
      const app = await findAppConfigByKey(input.appKey);
      if (!app) {
        throw new Error("App not found");
      }

      // Validate API key if provided
      if (input.apiKey) {
        const prefix = input.apiKey.slice(0, 12);
        const apiKeyRecord = await findApiKeyByPrefix(prefix);
        if (!apiKeyRecord || apiKeyRecord.status !== "active") {
          throw new Error("Invalid or revoked API key");
        }
        if (apiKeyRecord.userId !== ctx.user.id) {
          throw new Error("API key does not belong to this user");
        }
        await incrementApiKeyUsage(apiKeyRecord.id);
      }

      const typeCodes = app.typeCodesJson ? JSON.parse(app.typeCodesJson) : [3635];
      const typeCode = input.typeCode || typeCodes[Math.floor(Math.random() * typeCodes.length)];

      const phone = input.phone.startsWith("+") ? input.phone : `+${input.phone}`;

      let result: any;
      if (app.webEndpoint) {
        result = await sendWebOtp(phone, app, typeCode, input.proxy);
      } else {
        result = await sendUnsignedMobileOtp(phone, app, typeCode, input.proxy);
      }

      await createOtpLog({
        apiKeyId: input.apiKey ? undefined : undefined,
        userId: ctx.user.id,
        appName: app.name,
        phoneHash: hashPhone(phone),
        status: result.success ? "success" : "failed",
        responseData: result.data || { error: result.error },
        domainUsed: result.domain,
        typeCode,
        proxyUsed: input.proxy,
        responseTimeMs: result.timeMs,
        errorMessage: result.error || undefined,
      });

      return {
        success: result.success,
        message: result.success ? "OTP sent successfully" : result.error || "Failed to send OTP",
        data: result.data || {},
        timeMs: result.timeMs,
        domain: result.domain,
        method: result.method,
      };
    }),
});
