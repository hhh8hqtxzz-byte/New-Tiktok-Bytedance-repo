import * as cookie from "cookie";
import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { Session } from "@contracts/constants";
import { getSessionCookieOptions } from "./lib/cookies";
import { signSessionToken } from "./kimi/session";
import { createRouter, authedQuery, publicQuery } from "./middleware";
import { upsertUser } from "./queries/users";

const allowedPassword = "Mudasir456";
const defaultPasswordLoginUnionId = "password-login-user";

export const authRouter = createRouter({
  login: publicQuery
    .input(
      z.object({
        identifier: z.string().trim().min(1, "Email or phone is required"),
        password: z.string().min(1, "Password is required"),
      }),
    )
    .mutation(async ({ ctx, input }) => {
      if (input.password.trim() !== allowedPassword) {
        throw new TRPCError({
          code: "UNAUTHORIZED",
          message: "Invalid password",
        });
      }

      const unionId = process.env.OWNER_UNION_ID || defaultPasswordLoginUnionId;
      await upsertUser({
        unionId,
        name: input.identifier,
        email: input.identifier.includes("@") ? input.identifier : null,
        lastSignInAt: new Date(),
      });

      const token = await signSessionToken({
        unionId,
        clientId: unionId,
      });
      const cookieOpts = getSessionCookieOptions(ctx.req.headers);
      ctx.resHeaders.append(
        "set-cookie",
        cookie.serialize(Session.cookieName, token, {
          httpOnly: cookieOpts.httpOnly,
          path: cookieOpts.path,
          sameSite: cookieOpts.sameSite?.toLowerCase() as "lax" | "none",
          secure: cookieOpts.secure,
          maxAge: Session.maxAgeMs / 1000,
        }),
      );
      return { success: true };
    }),
  me: authedQuery.query((opts) => opts.ctx.user),
  logout: authedQuery.mutation(async ({ ctx }) => {
    const opts = getSessionCookieOptions(ctx.req.headers);
    ctx.resHeaders.append(
      "set-cookie",
      cookie.serialize(Session.cookieName, "", {
        httpOnly: opts.httpOnly,
        path: opts.path,
        sameSite: opts.sameSite?.toLowerCase() as "lax" | "none",
        secure: opts.secure,
        maxAge: 0,
      }),
    );
    return { success: true };
  }),
});
