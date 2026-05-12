import { Routes, Route } from "react-router";
import Login from "./pages/Login";
import AuthLayout from "./layouts/AuthLayout";
import AppLayout from "./layouts/AppLayout";
import Dashboard from "./pages/Dashboard";
import Playground from "./pages/Playground";
import ApiKeys from "./pages/ApiKeys";
import RequestLogs from "./pages/RequestLogs";
import Documentation from "./pages/Documentation";
import SettingsPage from "./pages/Settings";
import NotFound from "./pages/NotFound";

function ProtectedRoutes() {
  return (
    <AuthLayout>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/keys" element={<ApiKeys />} />
          <Route path="/logs" element={<RequestLogs />} />
          <Route path="/docs" element={<Documentation />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AppLayout>
    </AuthLayout>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<ProtectedRoutes />} />
    </Routes>
  );
}
