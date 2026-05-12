import { useAuth } from "@/hooks/useAuth";
import { trpc } from "@/providers/trpc";
import { Globe, Lock, Music2, Shield, UserRound, Zap } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

export default function Login() {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const utils = trpc.useUtils();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const loginMutation = trpc.auth.login.useMutation({
    onSuccess: async () => {
      await utils.auth.me.invalidate();
      navigate("/");
    },
    onError: () => {
      setError("Password ghalat hai. Sirf Mudasir456 allowed hai.");
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/");
    }
  }, [isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0A0A0F] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#FE2C55] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    loginMutation.mutate({ identifier, password });
  };

  return (
    <div className="min-h-screen bg-[#0A0A0F] flex">
      <div className="flex-1 flex flex-col justify-center px-8 sm:px-16 lg:px-24">
        <div className="max-w-md mx-auto w-full">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#FE2C55] to-[#25F4EE] flex items-center justify-center">
              <Music2 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">OTP API</span>
          </div>

          <h1 className="text-4xl font-bold text-white mb-4">
            ByteDance OTP
            <br />
            <span className="bg-gradient-to-r from-[#FE2C55] to-[#25F4EE] bg-clip-text text-transparent">
              API Service
            </span>
          </h1>

          <p className="text-[#8A8B9A] text-lg mb-10">
            Send OTP requests to TikTok, Douyin, CapCut, Lemon8, and more.
            Developer-first API with real-time analytics.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="identifier" className="block text-sm font-medium text-white mb-2">
                Email or phone number
              </label>
              <div className="relative">
                <UserRound className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#5A5B6A]" />
                <input
                  id="identifier"
                  type="text"
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  placeholder="Email ya phone number"
                  className="w-full h-12 pl-11 pr-4 bg-[#12121A] border border-[#2A2A3A] rounded-lg text-white placeholder:text-[#5A5B6A] focus:outline-none focus:border-[#FE2C55]"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#5A5B6A]" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Password"
                  className="w-full h-12 pl-11 pr-4 bg-[#12121A] border border-[#2A2A3A] rounded-lg text-white placeholder:text-[#5A5B6A] focus:outline-none focus:border-[#FE2C55]"
                  required
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-[#FE2C55]" role="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="inline-flex items-center justify-center gap-2 h-12 w-full px-8 bg-[#FE2C55] hover:bg-[#FF4D6D] disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-[0_0_20px_rgba(254,44,85,0.3)]"
            >
              <Lock className="w-5 h-5" />
              {loginMutation.isPending ? "Logging in..." : "Login"}
            </button>
          </form>

          <div className="mt-16 grid grid-cols-3 gap-8">
            <Feature icon={<Zap className="w-5 h-5" />} label="Fast" desc="< 500ms response" />
            <Feature icon={<Globe className="w-5 h-5" />} label="Global" desc="Multi-region proxies" />
            <Feature icon={<Shield className="w-5 h-5" />} label="Secure" desc="API key auth" />
          </div>
        </div>
      </div>

      <div className="hidden lg:flex flex-1 bg-[#12121A] items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-[#FE2C55]/10 via-transparent to-[#25F4EE]/10" />
        <div className="relative z-10 p-12">
          <div className="bg-[#1A1A25] border border-[#2A2A3A] rounded-2xl p-8 max-w-md">
            <div className="flex items-center justify-between mb-6">
              <span className="text-sm font-mono text-[#8A8B9A]">API Request</span>
              <span className="px-2 py-1 bg-[#25F4EE]/10 text-[#25F4EE] text-xs font-mono rounded">POST</span>
            </div>
            <div className="font-mono text-sm text-[#8A8B9A] space-y-2">
              <p><span className="text-[#FE2C55]">curl</span> -X POST <span className="text-[#25F4EE]">"https://api.otpapi.com/v1/send"</span> \</p>
              <p>  -H <span className="text-[#25F4EE]">"X-API-Key: tk_xxxxxxxx"</span> \</p>
              <p>  -H <span className="text-[#25F4EE]">"Content-Type: application/json"</span> \</p>
              <p>  -d <span className="text-white">'{`{"phone":"+1234567890","app":"tiktok"}`}'</span></p>
            </div>
            <div className="mt-6 pt-6 border-t border-[#2A2A3A]">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-[#25F4EE]" />
                <span className="text-sm text-[#25F4EE]">200 OK</span>
                <span className="text-xs text-[#5A5B6A] ml-auto">124ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Feature({ icon, label, desc }: { icon: React.ReactNode; label: string; desc: string }) {
  return (
    <div>
      <div className="flex items-center gap-2 text-[#FE2C55] mb-1">
        {icon}
        <span className="text-sm font-semibold text-white">{label}</span>
      </div>
      <p className="text-xs text-[#5A5B6A]">{desc}</p>
    </div>
  );
}
