import { useState } from "react";
import { trpc } from "@/providers/trpc";
import {
  Send,
  Copy,
  Check,
  Globe,
  Smartphone,
  Code2,
  Terminal,
  Loader2,
} from "lucide-react";

export default function Playground() {
  const { data: apps } = trpc.otp.getApps.useQuery();
  const { data: apiKeys } = trpc.apiKey.list.useQuery();
  const sendOtp = trpc.otp.send.useMutation();

  const [phone, setPhone] = useState("");
  const [selectedApp, setSelectedApp] = useState("");
  const [typeCode, setTypeCode] = useState("");
  const [proxy, setProxy] = useState("");
  const [selectedKey, setSelectedKey] = useState("");
  const [response, setResponse] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const activeApp = apps?.find((a) => a.key === selectedApp);
  const typeCodes = activeApp?.typeCodes || [];

  const handleSend = async () => {
    if (!phone || !selectedApp) return;
    setResponse(null);
    try {
      const result = await sendOtp.mutateAsync({
        phone,
        appKey: selectedApp,
        typeCode: typeCode ? parseInt(typeCode) : undefined,
        proxy: proxy || undefined,
        apiKey: selectedKey || undefined,
      });
      setResponse(result);
    } catch (err: any) {
      setResponse({ error: err.message || "Request failed" });
    }
  };

  const getCurlCode = () => {
    const key = selectedKey || "tk_your_api_key";
    const tc = typeCode || "auto";
    return `curl -X POST "https://api.otpapi.com/v1/send" \\
  -H "X-API-Key: ${key}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "phone": "${phone || "+1234567890"}",
    "app": "${selectedApp || "tiktok"}",
    "typeCode": ${tc}
  }'`;
  };

  const getJsCode = () => {
    return `const response = await fetch("https://api.otpapi.com/v1/send", {
  method: "POST",
  headers: {
    "X-API-Key": "${selectedKey || "tk_your_api_key"}",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    phone: "${phone || "+1234567890"}",
    app: "${selectedApp || "tiktok"}",
    typeCode: ${typeCode || "3635"},
  }),
});

const data = await response.json();
console.log(data);`;
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-6">
        <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <Send className="w-5 h-5 text-[#FE2C55]" />
            <h2 className="text-base font-semibold text-white">Send OTP</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#8A8B9A] mb-2">
                Phone Number
              </label>
              <div className="relative">
                <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5B6A]" />
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1234567890"
                  className="w-full h-10 pl-10 pr-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white placeholder-[#5A5B6A] focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#8A8B9A] mb-2">
                Target App
              </label>
              <select
                value={selectedApp}
                onChange={(e) => {
                  setSelectedApp(e.target.value);
                  setTypeCode("");
                }}
                className="w-full h-10 px-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all appearance-none"
              >
                <option value="">Select an app</option>
                {apps?.map((app) => (
                  <option key={app.key} value={app.key}>
                    {app.name} ({app.aid})
                  </option>
                ))}
              </select>
            </div>

            {typeCodes.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-[#8A8B9A] mb-2">
                  Type Code{" "}
                  <span className="text-xs text-[#5A5B6A]">(optional)</span>
                </label>
                <select
                  value={typeCode}
                  onChange={(e) => setTypeCode(e.target.value)}
                  className="w-full h-10 px-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all appearance-none"
                >
                  <option value="">Auto select</option>
                  {typeCodes.map((tc: number) => (
                    <option key={tc} value={tc}>
                      {tc}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-[#8A8B9A] mb-2">
                Proxy{" "}
                <span className="text-xs text-[#5A5B6A]">(optional)</span>
              </label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5A5B6A]" />
                <input
                  type="text"
                  value={proxy}
                  onChange={(e) => setProxy(e.target.value)}
                  placeholder="http://proxy:port"
                  className="w-full h-10 pl-10 pr-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white placeholder-[#5A5B6A] focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all"
                />
              </div>
            </div>

            {apiKeys && apiKeys.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-[#8A8B9A] mb-2">
                  API Key{" "}
                  <span className="text-xs text-[#5A5B6A]">(optional)</span>
                </label>
                <select
                  value={selectedKey}
                  onChange={(e) => setSelectedKey(e.target.value)}
                  className="w-full h-10 px-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all appearance-none"
                >
                  <option value="">Use session auth</option>
                  {apiKeys
                    .filter((k) => k.status === "active")
                    .map((key) => (
                      <option key={key.id} value={key.prefix}>
                        {key.name} ({key.prefix}...)
                      </option>
                    ))}
                </select>
              </div>
            )}

            <button
              onClick={handleSend}
              disabled={!phone || !selectedApp || sendOtp.isPending}
              className="w-full h-12 bg-[#FE2C55] hover:bg-[#FF4D6D] disabled:bg-[#2A2A3A] disabled:text-[#5A5B6A] text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-glow flex items-center justify-center gap-2"
            >
              {sendOtp.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
              {sendOtp.isPending ? "Sending..." : "Send OTP"}
            </button>
          </div>
        </div>

        {response && (
          <div
            className={`bg-[#12121A] border rounded-2xl p-6 ${
              response.success || response.error
                ? response.success
                  ? "border-[#25F4EE]/30"
                  : "border-[#FF4444]/30"
                : "border-[#2A2A3A]"
            }`}
          >
            <div className="flex items-center gap-2 mb-4">
              <Terminal className="w-5 h-5 text-[#8A8B9A]" />
              <h2 className="text-base font-semibold text-white">Response</h2>
              <span
                className={`ml-auto text-xs px-2 py-1 rounded-md ${
                  response.success
                    ? "bg-[#25F4EE]/10 text-[#25F4EE]"
                    : response.error
                    ? "bg-[#FF4444]/10 text-[#FF4444]"
                    : "bg-[#2A2A3A] text-[#5A5B6A]"
                }`}
              >
                {response.success
                  ? "Success"
                  : response.error
                  ? "Error"
                  : "Pending"}
              </span>
            </div>
            <div className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-4 overflow-x-auto">
              <pre className="text-xs font-mono text-[#8A8B9A]">
                {JSON.stringify(response, null, 2)}
              </pre>
            </div>
            {response.timeMs && (
              <p className="mt-2 text-xs text-[#5A5B6A]">
                Response time: {response.timeMs}ms | Domain:{" "}
                {response.domain}
              </p>
            )}
          </div>
        )}
      </div>

      <div className="space-y-6">
        <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Code2 className="w-5 h-5 text-[#8A8B9A]" />
            <h2 className="text-base font-semibold text-white">Code Preview</h2>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-[#5A5B6A]">cURL</span>
                <button
                  onClick={() => copyCode(getCurlCode())}
                  className="p-1 rounded-md text-[#5A5B6A] hover:text-[#8A8B9A] hover:bg-[#222230] transition-colors"
                >
                  {copied ? (
                    <Check className="w-3 h-3 text-[#25F4EE]" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
              </div>
              <div className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-4 overflow-x-auto">
                <pre className="text-xs font-mono text-[#8A8B9A]">
                  {getCurlCode()}
                </pre>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-[#5A5B6A]">
                  JavaScript
                </span>
                <button
                  onClick={() => copyCode(getJsCode())}
                  className="p-1 rounded-md text-[#5A5B6A] hover:text-[#8A8B9A] hover:bg-[#222230] transition-colors"
                >
                  {copied ? (
                    <Check className="w-3 h-3 text-[#25F4EE]" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
              </div>
              <div className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-4 overflow-x-auto">
                <pre className="text-xs font-mono text-[#8A8B9A]">
                  {getJsCode()}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {activeApp && (
          <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white mb-4">
              App Info: {activeApp.name}
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-[#5A5B6A]">AID</span>
                <span className="text-white font-mono">{activeApp.aid}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5A5B6A]">App Name</span>
                <span className="text-white font-mono">
                  {activeApp.appName}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5A5B6A]">Type Codes</span>
                <span className="text-white font-mono">
                  {activeApp.typeCodes?.join(", ")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#5A5B6A]">Web Endpoint</span>
                <span
                  className={
                    activeApp.webEndpoint ? "text-[#25F4EE]" : "text-[#5A5B6A]"
                  }
                >
                  {activeApp.webEndpoint ? "Yes" : "No"}
                </span>
              </div>
              <div className="mt-3">
                <span className="text-[#5A5B6A]">Domains</span>
                <div className="mt-1 space-y-1">
                  {activeApp.domains?.slice(0, 5).map((d: string) => (
                    <div
                      key={d}
                      className="text-xs text-[#8A8B9A] font-mono bg-[#0A0A0F] px-2 py-1 rounded"
                    >
                      {d}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
