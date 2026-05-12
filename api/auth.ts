import * as cookie from "cookie";
import { TRPCError } from "@trpc/server";
import { Session } from "@contracts/constants";
import { findUserByUnionId } from "./queries/users";
import { verifySessionToken } from "./kimi/session";

export async function authenticateRequest(headers: Headers) {
  const cookies = cookie.parse(headers.get("cookie") || "");
  const token = cookies[Session.cookieName];
  if (!token) {
    console.warn("[auth] No session cookie found in request.");
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "Invalid authentication token.",
    });
  }
  const claim = await verifySessionToken(token);
  if (!claim) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "Invalid authentication token.",
    });
  }
  const user = await findUserByUnionId(claim.unionId);
  if (!user) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "User not found. Please re-login.",
    });
  }
  return user;
}
