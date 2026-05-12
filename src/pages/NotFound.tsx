import { Link } from "react-router";
import { Home, AlertTriangle } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-16 h-16 rounded-2xl bg-[#FE2C55]/10 flex items-center justify-center mb-6">
        <AlertTriangle className="w-8 h-8 text-[#FE2C55]" />
      </div>
      <h1 className="text-3xl font-bold text-white mb-2">404</h1>
      <p className="text-sm text-[#8A8B9A] mb-6">Page not found</p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 h-10 px-6 bg-[#FE2C55] hover:bg-[#FF4D6D] text-white font-medium rounded-lg transition-all hover:shadow-glow"
      >
        <Home className="w-4 h-4" />
        Go Home
      </Link>
    </div>
  );
}
