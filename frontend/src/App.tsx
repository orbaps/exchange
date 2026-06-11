import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from './state/useAuthStore';
import { wsClient } from './services/websocket';

// Components
import { Sidebar } from './components/Sidebar';

// Pages
import { Login } from './pages/Login';
import { Overview } from './pages/Overview';
import { Leaderboard } from './pages/Leaderboard';
import { Tournament } from './pages/Tournament';
import { Deployments } from './pages/Deployments';
import { Analytics } from './pages/Analytics';
import { Operations } from './pages/Operations';
import { SubmissionDetail } from './pages/SubmissionDetail';
import { ReplayViewer } from './pages/ReplayViewer';
import GovernanceCenter from './pages/GovernanceCenter';
import ForecastCenter from './pages/ForecastCenter';
import RiskCenter from './pages/RiskCenter';
import SimulationStudio from './pages/SimulationStudio';
import StrategicCenter from './pages/StrategicCenter';
import MultiClusterView from './pages/MultiClusterView';
import RecoveryCenter from './pages/RecoveryCenter';
import PolicyHierarchyView from './pages/PolicyHierarchyView';
import CloudOperationsCenter from './pages/CloudOperationsCenter';
import DeploymentCenter from './pages/DeploymentCenter';
import BenchmarkCenter from './pages/BenchmarkCenter';
import PerformanceLab from './pages/PerformanceLab';
import CertificationCenter from './pages/CertificationCenter';
import ShowcaseCenter from './pages/ShowcaseCenter';
import ReleaseCenter from './pages/ReleaseCenter';

// Protected layout wrapper
const AppLayout: React.FC = () => {
  const { isAuthenticated, token } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && token) {
      // Auto-connect to WebSockets stream
      wsClient.connect(token);
    }
    return () => {
      wsClient.disconnect();
    };
  }, [isAuthenticated, token]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <main className="content-area">
        <Outlet />
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route element={<AppLayout />}>
          <Route path="/" element={<Overview />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/tournament" element={<Tournament />} />
          <Route path="/deployments" element={<Deployments />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/operations" element={<Operations />} />
          <Route path="/submission/:id" element={<SubmissionDetail />} />
          <Route path="/replay" element={<ReplayViewer />} />
          <Route path="/governance" element={<GovernanceCenter />} />
          <Route path="/forecast" element={<ForecastCenter />} />
          <Route path="/risks" element={<RiskCenter />} />
          <Route path="/simulation" element={<SimulationStudio />} />
          <Route path="/strategic" element={<StrategicCenter />} />
          <Route path="/multi-cluster" element={<MultiClusterView />} />
          <Route path="/recovery" element={<RecoveryCenter />} />
          <Route path="/policy-hierarchy" element={<PolicyHierarchyView />} />
          <Route path="/cloud-operations" element={<CloudOperationsCenter />} />
          <Route path="/deployments-gitops" element={<DeploymentCenter />} />
          <Route path="/benchmarking" element={<BenchmarkCenter />} />
          <Route path="/performance-lab" element={<PerformanceLab />} />
          <Route path="/certification" element={<CertificationCenter />} />
          <Route path="/showcase" element={<ShowcaseCenter />} />
          <Route path="/release" element={<ReleaseCenter />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
