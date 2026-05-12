import { trpc } from "@/providers/trpc";
import {
  Activity,
  TrendingUp,
  KeyRound,
  Zap,
  CheckCircle2,
  XCircle,
  Clock,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

export default function Dashboard() {
  const { data: stats } = trpc.otp.getStats.useQuery(undefined, {
    refetchInterval: 30000,
  });
  const { data: keys } = trpc.apiKey.list.useQuery();
  const { data: logsData } = trpc.log.list.useQuery({ limit: 10, page: 1 });

  const activeKeys = keys?.filter((k) => k.status === "active").length || 0;

  const hourlyData =
    stats?.hourly?.map((h: any) => ({
      time: h.hour?.slice(11, 16) || "",
      requests: h.count,
    })) || [];

  const appData = stats?.appStats || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Activity className="w-5 h-5" />}
          label="Today's Requests"
          value={stats?.today || 0}
          color="from-[#FE2C55] to-[#FF4D6D]"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Success Rate"
          value={`${stats?.successRate || 0}%`}
          color="from-[#25F4EE] to-[#5FF7F2]"
        />
        <StatCard
          icon={<KeyRound className="w-5 h-5" />}
          label="Active API Keys"
          value={activeKeys}
          color="from-[#8B5CF6] to-[#A78BFA]"
        />
        <StatCard
          icon={<Zap className="w-5 h-5" />}
          label="Total Requests"
          value={stats?.total || 0}
          color="from-[#FFD700] to-[#FFE44D]"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
          <h2 className="text-base font-semibold text-white mb-4">
            Request Volume (24h)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2A3A" />
                <XAxis dataKey="time" stroke="#5A5B6A" fontSize={11} />
                <YAxis stroke="#5A5B6A" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1A1A25",
                    border: "1px solid #2A2A3A",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "#8A8B9A" }}
                />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="#FE2C55"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: "#FE2C55" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
          <h2 className="text-base font-semibold text-white mb-4">
            Success Rate by App
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={appData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2A2A3A" />
                <XAxis
                  dataKey="appName"
                  stroke="#5A5B6A"
                  fontSize={10}
                  angle={-30}
                  textAnchor="end"
                  height={60}
                />
                <YAxis stroke="#5A5B6A" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1A1A25",
                    border: "1px solid #2A2A3A",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  formatter={(value: any) => [`${value}%`, "Success Rate"]}
                />
                <Bar dataKey="successRate" fill="#25F4EE" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3A] flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Recent Requests</h2>
          <span className="text-xs text-[#5A5B6A]">Last 10 requests</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left">
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  App
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Domain
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Type Code
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Response Time
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Time
                </th>
              </tr>
            </thead>
            <tbody>
              {logsData?.logs?.map((log) => (
                <tr
                  key={log.id}
                  className="border-t border-[#2A2A3A] hover:bg-[#222230] transition-colors"
                >
                  <td className="px-6 py-3">
                    {log.status === "success" ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#25F4EE]/10 text-[#25F4EE] text-xs font-medium rounded-md">
                        <CheckCircle2 className="w-3 h-3" />
                        Success
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#FF4444]/10 text-[#FF4444] text-xs font-medium rounded-md">
                        <XCircle className="w-3 h-3" />
                        Failed
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-3 text-sm text-white">{log.appName}</td>
                  <td className="px-6 py-3 text-sm text-[#8A8B9A] font-mono text-xs">
                    {log.domainUsed?.slice(0, 30)}...
                  </td>
                  <td className="px-6 py-3 text-sm text-[#8A8B9A]">{log.typeCode}</td>
                  <td className="px-6 py-3 text-sm text-[#8A8B9A]">
                    <span className="inline-flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {log.responseTimeMs}ms
                    </span>
                  </td>
                  <td className="px-6 py-3 text-xs text-[#5A5B6A]">
                    {new Date(log.createdAt).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {(!logsData?.logs || logsData.logs.length === 0) && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-8 text-center text-sm text-[#5A5B6A]"
                  >
                    No requests yet. Use the API Playground to send your first OTP.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-5 relative overflow-hidden">
      <div
        className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${color}`}
      />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-[#5A5B6A] mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
        <div
          className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center text-white`}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
