import { Header } from "./components/layout/Header";
import { Dashboard } from "./components/dashboard/Dashboard";

function App() {
  return (
    <div className="h-screen w-full flex flex-col bg-white overflow-hidden font-sans antialiased text-gray-900">
      <Header />
      <Dashboard />
    </div>
  );
}

export default App;
