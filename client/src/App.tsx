import { Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { Layout } from "./components/Layout";
import { ReportSearch } from "./pages/ReportSearch";
import { RequestTracker } from "./pages/RequestTracker";

function App() {
  return (
    <>
      <Layout>
        <Routes>
          <Route path="/" element={<ReportSearch />} />
          <Route path="/requests" element={<RequestTracker />} />
        </Routes>
      </Layout>
      <Toaster position="top-right" richColors />
    </>
  );
}

export default App;
