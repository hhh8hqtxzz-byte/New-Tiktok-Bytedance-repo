import { useAuth } from "@/hooks/useAuth";
import {
  LayoutDashboard,
  Play,
  KeyRound,
  ScrollText,
  BookOpen,
  Settings,
  LogOut,
  Music2,
  ChevronLeft,
  ChevronRight,
  Bell,
  Search,
} from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router";
import type { ReactNode } from "react";

const navItems = [
  { path: "/", label: "Dashboard", icon: LayoutDashboard },
  { path: "/playground", label: "API Playground", icon: Play },
  { path: "/keys", label: "API Keys", icon: KeyRound },
  { path: "/logs", label: "Request Logs", icon: ScrollText },
  { path: "/docs", label: "Documentation", icon: BookOpen },
  { path: "/settings", label: "Settings", icon: Settings },
];

export default function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-[#0A0A0F]">
      <aside
        className={`flex-shrink-0 bg-[#12121A] border-r border-[#2A2A3A] flex flex-col transition-all duration-200 ${
          collapsed ? "w-16" : "w-60"
        }`}
      >
        <div className="h-14 flex items-center px-4 border-b border-[#2A2A3A]">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#FE2C55] to-[#25F4EE] flex items-center justify-center flex-shrink-0">
            <Music2 className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="ml-3 text-base font-bold text-white">OTP API</span>
          )}
        </div>

        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 h-10 rounded-lg transition-all duration-150 ${
                  collapsed ? "justify-center px-0" : "px-3"
                } ${
                  isActive
                    ? "bg-[#FE2C55]/10 text-[#FE2C55] border-l-[3px] border-[#FE2C55]"
                    : "text-[#8A8B9A] hover:bg-[#222230] hover:text-white"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className="w-[18px] h-[18px] flex-shrink-0" />
                {!collapsed && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-[#2A2A3A]">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex items-center justify-center w-full h-8 rounded-lg text-[#5A5B6A] hover:bg-[#222230] hover:text-[#8A8B9A] transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
          <div
            className={`mt-3 flex items-center gap-3 ${collapsed ? "justify-center" : ""}`}
          >
            {user?.avatar ? (
              <img
                src={user.avatar}
                alt=""
                className="w-8 h-8 rounded-full flex-shrink-0"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-[#2A2A3A] flex items-center justify-center flex-shrink-0">
                <span className="text-xs text-white font-medium">
                  {user?.name?.charAt(0)?.toUpperCase() || "U"}
                </span>
              </div>
            )}
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{user?.name || "User"}</p>
                <p className="text-xs text-[#5A5B6A] truncate">
                  {user?.email || "user@example.com"}
                </p>
              </div>
            )}
            {!collapsed && (
              <button
                onClick={logout}
                className="p-1.5 rounded-md text-[#5A5B6A] hover:bg-[#222230] hover:text-[#FF4444] transition-colors"
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 flex-shrink-0 bg-[#12121A]/80 backdrop-blur-md border-b border-[#2A2A3A] flex items-center justify-between px-6">
          <h1 className="text-base font-semibold text-white">
            {navItems.find((n) => n.path === location.pathname)?.label ||
              "Dashboard"}
          </h1>
          <div className="flex items-center gap-3">
            <button className="p-2 rounded-lg text-[#5A5B6A] hover:bg-[#222230] hover:text-[#8A8B9A] transition-colors">
              <Search className="w-[18px] h-[18px]" />
            </button>
            <button className="p-2 rounded-lg text-[#5A5B6A] hover:bg-[#222230] hover:text-[#8A8B9A] transition-colors relative">
              <Bell className="w-[18px] h-[18px]" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#FE2C55]" />
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-[1400px] mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
