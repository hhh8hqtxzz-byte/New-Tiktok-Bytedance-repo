import { useState } from "react";
import { trpc } from "@/providers/trpc";
import {
  KeyRound,
  Plus,
  Copy,
  Check,
  Trash2,
  Ban,
  Loader2,
  Eye,
  EyeOff,
} from "lucide-react";

export default function ApiKeys() {
  const utils = trpc.useUtils();
  const { data: keys, isLoading } = trpc.apiKey.list.useQuery();
  const createKey = trpc.apiKey.create.useMutation({
    onSuccess: () => {
      utils.apiKey.list.invalidate();
      setShowNewKey(true);
    },
  });
  const revokeKey = trpc.apiKey.revoke.useMutation({
    onSuccess: () => utils.apiKey.list.invalidate(),
  });
  const deleteKey = trpc.apiKey.delete.useMutation({
    onSuccess: () => utils.apiKey.list.invalidate(),
  });

  const [newKeyName, setNewKeyName] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newKeyValue, setNewKeyValue] = useState("");
  const [showNewKey, setShowNewKey] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [showKeyId, setShowKeyId] = useState<number | null>(null);

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    const result = await createKey.mutateAsync({ name: newKeyName.trim() });
    setNewKeyValue(result.key);
    setNewKeyName("");
    setShowCreateForm(false);
  };

  const copyToClipboard = (text: string, id: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">API Keys</h1>
          <p className="text-sm text-[#8A8B9A] mt-1">
            Manage your API keys for programmatic access
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="h-10 px-4 bg-[#FE2C55] hover:bg-[#FF4D6D] text-white font-medium rounded-lg transition-all hover:shadow-glow flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Key
        </button>
      </div>

      {showNewKey && newKeyValue && (
        <div className="bg-[#12121A] border border-[#25F4EE]/30 rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-3">
            <KeyRound className="w-5 h-5 text-[#25F4EE]" />
            <h3 className="text-base font-semibold text-white">
              API Key Created
            </h3>
          </div>
          <p className="text-sm text-[#8A8B9A] mb-4">
            Copy this key now. You won't be able to see it again.
          </p>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-[#0A0A0F] border border-[#2A2A3A] rounded-lg px-4 py-3 font-mono text-sm text-[#25F4EE] break-all">
              {newKeyValue}
            </div>
            <button
              onClick={() => copyToClipboard(newKeyValue, -1)}
              className="h-10 px-4 bg-[#25F4EE]/10 hover:bg-[#25F4EE]/20 text-[#25F4EE] rounded-lg transition-colors flex items-center gap-2"
            >
              {copiedId === -1 ? (
                <Check className="w-4 h-4" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
              Copy
            </button>
            <button
              onClick={() => {
                setShowNewKey(false);
                setNewKeyValue("");
              }}
              className="h-10 px-4 bg-[#2A2A3A] hover:bg-[#3A3A4A] text-[#8A8B9A] rounded-lg transition-colors"
            >
              Done
            </button>
          </div>
        </div>
      )}

      {showCreateForm && (
        <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl p-6">
          <h3 className="text-base font-semibold text-white mb-4">
            Create New API Key
          </h3>
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g., Production, Development)"
              className="flex-1 h-10 px-4 bg-[#1A1A25] border border-[#2A2A3A] rounded-lg text-sm text-white placeholder-[#5A5B6A] focus:outline-none focus:border-[#FE2C55] focus:shadow-glow transition-all"
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <button
              onClick={handleCreate}
              disabled={createKey.isPending || !newKeyName.trim()}
              className="h-10 px-6 bg-[#FE2C55] hover:bg-[#FF4D6D] disabled:bg-[#2A2A3A] disabled:text-[#5A5B6A] text-white font-medium rounded-lg transition-all flex items-center gap-2"
            >
              {createKey.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              Create
            </button>
            <button
              onClick={() => {
                setShowCreateForm(false);
                setNewKeyName("");
              }}
              className="h-10 px-4 bg-[#2A2A3A] hover:bg-[#3A3A4A] text-[#8A8B9A] rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="bg-[#12121A] border border-[#2A2A3A] rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left border-b border-[#2A2A3A]">
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Key
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Requests
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Created
                </th>
                <th className="px-6 py-3 text-xs font-medium text-[#5A5B6A] uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <Loader2 className="w-5 h-5 animate-spin text-[#5A5B6A] mx-auto" />
                  </td>
                </tr>
              )}
              {keys?.map((key) => (
                <tr
                  key={key.id}
                  className="border-t border-[#2A2A3A] hover:bg-[#222230] transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-white font-medium">
                    {key.name}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-[#8A8B9A]">
                        {showKeyId === key.id
                          ? key.prefix + "..."
                          : key.prefix + "************************"}
                      </span>
                      <button
                        onClick={() =>
                          setShowKeyId(
                            showKeyId === key.id ? null : key.id
                          )
                        }
                        className="text-[#5A5B6A] hover:text-[#8A8B9A] transition-colors"
                      >
                        {showKeyId === key.id ? (
                          <EyeOff className="w-3 h-3" />
                        ) : (
                          <Eye className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-md ${
                        key.status === "active"
                          ? "bg-[#25F4EE]/10 text-[#25F4EE]"
                          : "bg-[#FF4444]/10 text-[#FF4444]"
                      }`}
                    >
                      {key.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-[#8A8B9A]">
                    {key.requestsCount.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-xs text-[#5A5B6A]">
                    {new Date(key.createdAt).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => copyToClipboard(key.prefix, key.id)}
                        className="p-1.5 rounded-md text-[#5A5B6A] hover:text-[#8A8B9A] hover:bg-[#222230] transition-colors"
                        title="Copy prefix"
                      >
                        {copiedId === key.id ? (
                          <Check className="w-3.5 h-3.5 text-[#25F4EE]" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                      {key.status === "active" && (
                        <button
                          onClick={() => revokeKey.mutate({ id: key.id })}
                          disabled={revokeKey.isPending}
                          className="p-1.5 rounded-md text-[#5A5B6A] hover:text-[#FFD700] hover:bg-[#222230] transition-colors"
                          title="Revoke"
                        >
                          <Ban className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm("Delete this API key permanently?")) {
                            deleteKey.mutate({ id: key.id });
                          }
                        }}
                        disabled={deleteKey.isPending}
                        className="p-1.5 rounded-md text-[#5A5B6A] hover:text-[#FF4444] hover:bg-[#222230] transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {!isLoading && (!keys || keys.length === 0) && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-8 text-center text-sm text-[#5A5B6A]"
                  >
                    No API keys yet. Create your first key to get started.
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
