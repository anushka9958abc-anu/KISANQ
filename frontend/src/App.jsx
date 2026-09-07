import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import { Shell } from "./ui";
import Home from "./pages/Home";
import Login from "./pages/Login";
import BookSlot from "./pages/BookSlot";
import QueuePage from "./pages/QueuePage";
import StatusPage from "./pages/StatusPage";
import MapPage from "./pages/MapPage";
import AdminHome from "./pages/AdminHome";
import AdminAnalytics from "./pages/AdminAnalytics";

function Guard({ children, roles }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/app"
        element={
          <Guard roles={["farmer"]}>
            <Shell />
          </Guard>
        }
      >
        <Route path="book" element={<BookSlot />} />
        <Route path="queue" element={<QueuePage />} />
        <Route path="status" element={<StatusPage />} />
        <Route path="map" element={<MapPage />} />
      </Route>
      <Route
        path="/admin"
        element={
          <Guard roles={["admin", "officer"]}>
            <Shell admin />
          </Guard>
        }
      >
        <Route index element={<AdminHome />} />
        <Route path="analytics" element={<AdminAnalytics />} />
      </Route>
    </Routes>
  );
}
