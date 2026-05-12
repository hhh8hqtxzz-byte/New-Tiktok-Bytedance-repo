import { useState } from "react";
import { trpc } from "@/providers/trpc";
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  ChevronLeft,
  ChevronRight,
  Clock,
  Globe,
  Hash,
} from "lucide-react";

export default function RequestLogs() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [appName, setAppName] = useState("");

  const { data, isLoading } = trpc.log.list.useQuery({
    page,
    limit: 50,
    status: status || undefined,
    appName: appName || undefined,
  });

  const { data: apps } = trpc.otp.getApps.useQuery();

  const uniqueApps = apps?.map((a) => a.name) || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Request Logs</h1>
        <p className="text-sm text-[#8A8B9A] mt-1">
          View and filter your OTP request history
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-2 bg-[#12121A] border border-[#2A2A3A] rounded-lg">
          <Filter className="w-4 h-4 text-[#5A5B6A]" />
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="bg-transparent text-sm text-white focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="flex items-center gap-2 px-3 py-2 bg-[#12121A] border border-[#2A2A3A] rounded-lg">
          <Globe className="w-4 h-4 text-[#5A5B6A]" />
          <select
            value={appName}
            onChange={(e) => {
              setAppName(e.target.value);
              setPage(1);
            }}
            className="bg-transparent text-sm text-white focus:outline-none"
          >
            <option value="">All Apps</option>
            {uniqueApps.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        {(status || appName) && (
          <button
            onClick={() => {
              setStatus("");
              setAppName("");
              setPage(1);
            }}
            className="px-3 py-2 text-sm text-[#FE2C55] hover:bg-[#FE2C55]/10 rounded-lg transition-colors"
          >
            Clear filters
          </button>
        )}

        <div className="ml-auto text-xs text-[#5A5B6A]">
          {data?.total || 0} total requests
        </div>
      </div>

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left border-b border-[#2A2A3A]">
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  App
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Domain
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Type
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Proxy
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Time
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Response
                </th>
                <th className="px-4 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center">
                    <div className="w-5 h-5 border-2 border-[#FE2C55] border-t-transparent rounded-full animate-spin mx-auto" />
                  </td>
                </tr>
              )}
              {data?.logs?.map((log) => (
                <tr
                  key={log.id}
                  className="border-t border-[#2A2A3A] hover:bg-[#222230] transition-colors"
                >
                  <td className="px-4 py-3">
                    {log.status === "success" ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#25F4EE]/10 text-[#25F4EE] text-xs font-medium rounded-md">
                        <CheckCircle2 className="w-3 h-3" />
                      </span>
                    ) : log.status === "failed" ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#FF4444]/10 text-[#FF4444] text-xs font-medium rounded-md">
                        <XCircle className="w-3 h-3" />
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#FFD700]/10 text-[#FFD700] text-xs font-medium rounded-md">
                        <AlertCircle className="w-3 h-3" />
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-white whitespace-nowrap">
                    {log.appName}
                  </td>
                  <td className="px-4 py-3 text-xs text-[#8A8B9A] font-mono max-w-[150px] truncate">
                    {log.domainUsed}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-xs text-[#8A8B9A]">
                      <Hash className="w-3 h-3" />
                      {log.typeCode}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-[#5A5B6A] font-mono max-w-[100px] truncate">
                    {log.proxyUsed || "-"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 text-xs text-[#8A8B9A]">
                      <Clock className="w-3 h-3" />
                      {log.responseTimeMs}ms
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-[#5A5B6A] max-w-[200px] truncate">
                    {log.errorMessage || "OK"}
                  </td>
                  <td className="px-4 py-3 text-xs text-[#5A5B6A] whitespace-nowrap">
                    {new Date(log.createdAt).toLocaleString()}
                  </td>
                </tr>
              ))}
              {!isLoading && (!data?.logs || data.logs.length === 0) && (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-8 text-center text-sm text-[#5A5B6A]"
                  >
                    No logs found. Send some OTP requests to see them here.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {data && data.totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-[#2A2A3A]">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="flex items-center gap-1 px-3 py-2 text-sm text-[#8A8B9A] hover:text-white disabled:text-[#5A5B6A] disabled:hover:text-[#5A5B6A] transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            <span className="text-sm text-[#5A5B6A]">
              Page {page} of {data.totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(data.totalPages, p + 1))}
              disabled={page >= data.totalPages}
              className="flex items-center gap-1 px-3 py-2 text-sm text-[#8A8B9A] hover:text-white disabled:text-[#5A5B6A] disabled:hover:text-[#5A5B6A] transition-colors"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
