import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Plans from "./pages/Plans";
import PlanForm from "./pages/PlanForm";
import Customers from "./pages/Customers";
import CustomerForm from "./pages/CustomerForm";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="plans" element={<Plans />} />
        <Route path="plans/:id" element={<PlanForm />} />
        <Route path="customers" element={<Customers />} />
        <Route path="customers/:id" element={<CustomerForm />} />
      </Route>
    </Routes>
  );
}
