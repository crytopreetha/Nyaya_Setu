import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import NewCase from "./pages/NewCase";
import Processing from "./pages/Processing";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import BecomeLawyer from "./pages/BecomeLawyer";
import LawyerDashboard from "./pages/LawyerDashboard";
import RequireAuth from "./components/RequireAuth";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route
        path="/new"
        element={
          <RequireAuth>
            <NewCase />
          </RequireAuth>
        }
      />
      <Route
        path="/cases/:caseId/processing"
        element={
          <RequireAuth>
            <Processing />
          </RequireAuth>
        }
      />
      <Route
        path="/cases/:caseId"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/history"
        element={
          <RequireAuth>
            <History />
          </RequireAuth>
        }
      />
      <Route
        path="/become-lawyer"
        element={
          <RequireAuth>
            <BecomeLawyer />
          </RequireAuth>
        }
      />
      <Route
        path="/lawyer"
        element={
          <RequireAuth>
            <LawyerDashboard />
          </RequireAuth>
        }
      />
    </Routes>
  );
}
