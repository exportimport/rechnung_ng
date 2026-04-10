import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Plans from "./pages/Plans";
import PlanForm from "./pages/PlanForm";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="plans" element={<Plans />} />
        <Route path="plans/:id" element={<PlanForm />} />
      </Route>
    </Routes>
  );
}
