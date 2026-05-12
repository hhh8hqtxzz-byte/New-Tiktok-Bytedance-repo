import { useState, useEffect } from "react";
import { trpc } from "@/providers/trpc";
import { useAuth } from "@/hooks/useAuth";
import {
  Webhook,
  Globe,
  Gauge,
  Save,
  Loader2,
  User,
  Shield,
} from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const utils = trpc.useUtils();
  const { data: settings } = trpc.settings.get.useQuery();
  const updateSettings = trpc.settings.update.useMutation({
    onSuccess: () => {
      utils.settings.get.invalidate();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    },
  });

  const [webhookUrl, setWebhookUrl] = useState("");
  const [defaultProxy, setDefaultProxy] = useState("");
  const [rateLimit, setRateLimit] = useState(60);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setWebhookUrl(settings.webhookUrl || "");
      setDefaultProxy(settings.defaultProxy || "");
      setRateLimit(settings.rateLimitPerMinute || 60);
    }
  }, [settings]);

  const handleSave = () => {
    updateSettings.mutate({
      webhookUrl: webhookUrl || undefined,
      defaultProxy: defaultProxy || undefined,
      rateLimitPerMinute: rateLimit,
    });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Settings</h1>
        <p className="text-sm text-[#8A8B9A] mt-1">
          Manage your account preferences
        </p>
      </div>

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-[#2A2A3A] flex items-center justify-center">
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt=""
                className="w-10 h-10 rounded-full"
              />
            ) : (
              <User className="w-5 h-5 text-[#8A8B9A]" />
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-white">{user?.name || "User"}</p>
            <p className="text-xs text-[#5A5B6A]">{user?.email || "user@example.com"}</p>
          </div>
          <span
            className={`ml-auto px-2 py-1 text-xs font-medium rounded-md ${
              user?.role === "admin"
                ? "bg-[#FE2C55]/10 text-[#FE2C55]"
                : "bg-[#25F4EE]/10 text-[#25F4EE]"
            }`}
          >
            <Shield className="w-3 h-3 inline mr-1" />
            {user?.role || "user"}
          </span>
        </div>
      </div>

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Webhook className="w-5 h-5 text-[#FE2C55]" />
          <h2 className="text-base font-semibold text-white">Webhook URL</h2>
        </div>
        <p className="text-sm text-[#8A8B9A] mb-4">
          Receive POST callbacks when OTP requests complete. Leave empty to
          disable.
        </p>
        <input
          type="url"
          value={webhookUrl}
          onChange={(e) => setWebhookUrl(e.target.value)}
          placeholder="https://your-app.com/webhook"
          className="w-full h-10 px-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white placeholder-[#5A5B6A] focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all"
        />
      </div>

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Globe className="w-5 h-5 text-[#25F4EE]" />
          <h2 className="text-base font-semibold text-white">Default Proxy</h2>
        </div>
        <p className="text-sm text-[#8A8B9A] mb-4">
          Set a default proxy for all OTP requests. Can be overridden per
          request.
        </p>
        <input
          type="text"
          value={defaultProxy}
          onChange={(e) => setDefaultProxy(e.target.value)}
          placeholder="http://proxy.example.com:8080"
          className="w-full h-10 px-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white placeholder-[#5A5B6A] focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all"
        />
      </div>

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-6">
          <Gauge className="w-5 h-5 text-[#FFD700]" />
          <h2 className="text-base font-semibold text-white">Rate Limit</h2>
        </div>
        <p className="text-sm text-[#8A8B9A] mb-4">
          Maximum requests per minute for your API keys.
        </p>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min={10}
            max={1000}
            step={10}
            value={rateLimit}
            onChange={(e) => setRateLimit(parseInt(e.target.value))}
            className="flex-1 h-2 bg-[#2A2A3A] rounded-lg appearance-none cursor-pointer accent-[#FE2C55]"
          />
          <span className="text-sm font-mono text-white w-16 text-right">
            {rateLimit}
          </span>
          <span className="text-xs text-[#5A5B6A]">req/min</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={updateSettings.isPending}
          className="h-10 px-6 bg-[#FE2C55] hover:bg-[#FF4D6D] disabled:bg-[#2A2A3A] text-white font-medium rounded-lg transition-all hover:shadow-glow flex items-center gap-2"
        >
          {updateSettings.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Changes
        </button>
        {saved && (
          <span className="text-sm text-[#25F4EE]">Settings saved!</span>
        )}
      </div>
    </div>
  );
}
