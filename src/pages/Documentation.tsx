import { useState } from "react";
import {
  BookOpen,
  Code2,
  Shield,
  AlertTriangle,
  Zap,
  Copy,
  Check,
} from "lucide-react";

const endpoints = [
  {
    method: "POST",
    path: "/api/trpc/otp.send",
    description: "Send an OTP request to a ByteDance app",
    auth: "API Key or Session",
    body: `{
  "phone": "+1234567890",
  "appKey": "tiktok",
  "typeCode": 3635,
  "proxy": "http://proxy:port"
}`,
    response: `{
  "success": true,
  "message": "OTP sent successfully",
  "data": { "message": "success" },
  "timeMs": 245,
  "domain": "www.tiktok.com",
  "method": "web_endpoint"
}`,
  },
  {
    method: "QUERY",
    path: "/api/trpc/otp.getApps",
    description: "Get list of available apps and their configurations",
    auth: "Session",
    body: null,
    response: `[
  {
    "key": "tiktok",
    "name": "TikTok Global",
    "aid": 1233,
    "typeCodes": [3635, 3637, 3634]
  }
]`,
  },
  {
    method: "QUERY",
    path: "/api/trpc/otp.getStats",
    description: "Get your OTP request statistics",
    auth: "Session",
    body: null,
    response: `{
  "total": 150,
  "success": 142,
  "today": 23,
  "successRate": 95,
  "hourly": [...],
  "appStats": [...]
}`,
  },
  {
    method: "QUERY",
    path: "/api/trpc/apiKey.list",
    description: "List all your API keys",
    auth: "Session",
    body: null,
    response: `[{ "id": 1, "name": "Production", "prefix": "tk_a1b2c3d4", "status": "active" }]`,
  },
  {
    method: "MUTATION",
    path: "/api/trpc/apiKey.create",
    description: "Create a new API key",
    auth: "Session",
    body: `{ "name": "Production" }`,
    response: `{ "key": "tk_xxxxxxxxxxxx", "prefix": "tk_xxxx" }`,
  },
  {
    method: "QUERY",
    path: "/api/trpc/log.list",
    description: "Get paginated request logs",
    auth: "Session",
    body: null,
    response: `{
  "logs": [...],
  "total": 150,
  "page": 1,
  "totalPages": 3
}`,
  },
];

const errorCodes = [
  { code: "400", message: "Bad Request", description: "Invalid parameters provided" },
  { code: "401", message: "Unauthorized", description: "Authentication required" },
  { code: "403", message: "Forbidden", description: "Invalid API key or insufficient permissions" },
  { code: "404", message: "Not Found", description: "App or resource not found" },
  { code: "429", message: "Too Many Requests", description: "Rate limit exceeded" },
  { code: "500", message: "Internal Error", description: "Server error occurred" },
];

export default function Documentation() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [activeSection, setActiveSection] = useState("endpoints");

  const copyCode = (code: string, index: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const curlExample = `curl -X POST "https://api.otpapi.com/api/trpc/otp.send" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer tk_your_api_key" \\
  -d '{
    "phone": "+1234567890",
    "appKey": "tiktok"
  }'`;

  const jsExample = `import { createTRPCProxyClient, httpBatchLink } from '@trpc/client';

const client = createTRPCProxyClient({
  links: [httpBatchLink({ url: 'https://api.otpapi.com/api/trpc' })],
});

const result = await client.otp.send.mutate({
  phone: '+1234567890',
  appKey: 'tiktok',
});`;

  const sections = [
    { id: "endpoints", label: "Endpoints", icon: <Code2 className="w-4 h-4" /> },
    { id: "auth", label: "Authentication", icon: <Shield className="w-4 h-4" /> },
    { id: "errors", label: "Error Codes", icon: <AlertTriangle className="w-4 h-4" /> },
    { id: "examples", label: "Examples", icon: <Zap className="w-4 h-4" /> },
  ];

  return (
    <div className="flex gap-8">
      <aside className="hidden lg:block w-48 flex-shrink-0">
        <nav className="sticky top-8 space-y-1">
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${
                activeSection === s.id
                  ? "bg-[#FE2C55]/10 text-[#FE2C55]"
                  : "text-[#8A8B9A] hover:bg-[#222230] hover:text-white"
              }`}
            >
              {s.icon}
              {s.label}
            </button>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0 space-y-8">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-5 h-5 text-[#FE2C55]" />
            <h1 className="text-xl font-bold text-white">API Documentation</h1>
          </div>
          <p className="text-sm text-[#8A8B9A]">
            Complete reference for the TikTok OTP API Service
          </p>
        </div>

        {activeSection === "endpoints" && (
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-white">Endpoints</h2>
            {endpoints.map((ep, i) => (
              <div
                key={i}
                className="bg-[#12121A] border border-[#2A2A3A] rounded-xl p-5"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span
                    className={`px-2 py-1 text-xs font-bold rounded ${
                      ep.method === "POST" || ep.method === "MUTATION"
                        ? "bg-[#FE2C55]/15 text-[#FE2C55]"
                        : "bg-[#25F4EE]/15 text-[#25F4EE]"
                    }`}
                  >
                    {ep.method}
                  </span>
                  <code className="text-sm font-mono text-white">
                    {ep.path}
                  </code>
                </div>
                <p className="text-sm text-[#8A8B9A] mb-3">{ep.description}</p>
                <p className="text-xs text-[#5A5B6A] mb-3">
                  Auth: {ep.auth}
                </p>

                {ep.body && (
                  <div className="mb-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-[#5A5B6A]">Request Body</span>
                      <button
                        onClick={() => copyCode(ep.body!, i * 2)}
                        className="text-[#5A5B6A] hover:text-[#8A8B9A]"
                      >
                        {copiedIndex === i * 2 ? (
                          <Check className="w-3 h-3 text-[#25F4EE]" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                    <pre className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-3 text-xs font-mono text-[#8A8B9A] overflow-x-auto">
                      {ep.body}
                    </pre>
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-[#5A5B6A]">Response</span>
                    <button
                      onClick={() => copyCode(ep.response, i * 2 + 1)}
                      className="text-[#5A5B6A] hover:text-[#8A8B9A]"
                    >
                      {copiedIndex === i * 2 + 1 ? (
                        <Check className="w-3 h-3 text-[#25F4EE]" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                  <pre className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-3 text-xs font-mono text-[#8A8B9A] overflow-x-auto">
                    {ep.response}
                  </pre>
                </div>
              </div>
            ))}
          </section>
        )}

        {activeSection === "auth" && (
          <section className="space-y-6">
            <h2 className="text-lg font-semibold text-white">Authentication</h2>

            <div className="bg-[#12121A] border border-[#2A2A3A] rounded-xl p-5">
              <h3 className="text-base font-semibold text-white mb-3">
                API Key Authentication
              </h3>
              <p className="text-sm text-[#8A8B9A] mb-4">
                Include your API key in the request headers. You can create API
                keys from the API Keys page.
              </p>
              <div className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-4">
                <code className="text-sm font-mono text-[#8A8B9A]">
                  X-API-Key: tk_your_api_key_here
                </code>
              </div>
            </div>

            <div className="bg-[#12121A] border border-[#2A2A3A] rounded-xl p-5">
              <h3 className="text-base font-semibold text-white mb-3">
                Session Authentication
              </h3>
              <p className="text-sm text-[#8A8B9A] mb-4">
                When using the API Playground or logged-in dashboard, session
                cookies are used automatically.
              </p>
            </div>

            <div className="bg-[#12121A] border border-[#2A2A3A] rounded-xl p-5">
              <h3 className="text-base font-semibold text-white mb-3">
                Rate Limiting
              </h3>
              <p className="text-sm text-[#8A8B9A] mb-4">
                Rate limits are applied per API key. Default is 60 requests per
                minute. Contact support to increase your limit.
              </p>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-[#0A0A0F] rounded-lg p-4 text-center">
                  <p className="text-lg font-bold text-white">Free</p>
                  <p className="text-xs text-[#5A5B6A]">60 req/min</p>
                </div>
                <div className="bg-[#0A0A0F] rounded-lg p-4 text-center">
                  <p className="text-lg font-bold text-white">Pro</p>
                  <p className="text-xs text-[#5A5B6A]">300 req/min</p>
                </div>
                <div className="bg-[#0A0A0F] rounded-lg p-4 text-center">
                  <p className="text-lg font-bold text-white">Enterprise</p>
                  <p className="text-xs text-[#5A5B6A]">Unlimited</p>
                </div>
              </div>
            </div>
          </section>
        )}

        {activeSection === "errors" && (
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-white">Error Codes</h2>
            <div className="bg-[#12121A] border border-[#2A2A3A] rounded-xl overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[#2A2A3A]">
                    <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase text-left">
                      Code
                    </th>
                    <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase text-left">
                      Status
                    </th>
                    <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase text-left">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {errorCodes.map((err) => (
                    <tr
                      key={err.code}
                      className="border-t border-[#2A2A3A] hover:bg-[#222230]"
                    >
                      <td className="px-4 py-3">
                        <span className="text-sm font-mono font-bold text-[#FE2C55]">
                          {err.code}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-white">
                        {err.message}
                      </td>
                      <td className="px-4 py-3 text-sm text-[#8A8B9A]">
                        {err.description}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {activeSection === "examples" && (
          <section className="space-y-6">
            <h2 className="text-lg font-semibold text-white">Code Examples</h2>

            <div className="bg-[#12121A] border border-[#2A2A3A] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white mb-3">cURL</h3>
              <div className="relative">
                <pre className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-4 text-xs font-mono text-[#8A8B9A] overflow-x-auto">
                  {curlExample}
                </pre>
                <button
                  onClick={() => copyCode(curlExample, 100)}
                  className="absolute top-3 right-3 p-1.5 rounded-md bg-[#1A1A25] text-[#5A5B6A] hover:text-[#8A8B9A]"
                >
                  {copiedIndex === 100 ? (
                    <Check className="w-3.5 h-3.5 text-[#25F4EE]" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>

            <div className="bg-[#12121A] border border-[#2A2A3A] rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white mb-3">
                JavaScript / TypeScript
              </h3>
              <div className="relative">
                <pre className="bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg p-4 text-xs font-mono text-[#8A8B9A] overflow-x-auto">
                  {jsExample}
                </pre>
                <button
                  onClick={() => copyCode(jsExample, 101)}
                  className="absolute top-3 right-3 p-1.5 rounded-md bg-[#1A1A25] text-[#5A5B6A] hover:text-[#8A8B9A]"
                >
                  {copiedIndex === 101 ? (
                    <Check className="w-3.5 h-3.5 text-[#25F4EE]" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
