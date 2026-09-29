import { Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';

import Landing from '@/pages/Landing';
import Login from '@/pages/Login';
import Signup from '@/pages/Signup';
import NotFound from '@/pages/NotFound';
import Deferred from '@/pages/Deferred';

import AppHome from '@/pages/app/AppHome';
import SearchConsole from '@/pages/app/SearchConsole';
import SearchDetail from '@/pages/app/SearchDetail';
import SupplierDetail from '@/pages/app/SupplierDetail';
import Compare from '@/pages/app/Compare';
import RFQList from '@/pages/app/RFQList';
import RFQDetail from '@/pages/app/RFQDetail';
import Watchlists from '@/pages/app/Watchlists';
import Alerts from '@/pages/app/Alerts';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Protected app */}
      <Route path="/app" element={<ProtectedRoute><AppHome /></ProtectedRoute>} />
      <Route path="/app/search" element={<ProtectedRoute><SearchConsole /></ProtectedRoute>} />
      <Route path="/app/search/:searchId" element={<ProtectedRoute><SearchDetail /></ProtectedRoute>} />
      <Route path="/app/suppliers/:id" element={<ProtectedRoute><SupplierDetail /></ProtectedRoute>} />
      <Route path="/app/compare" element={<ProtectedRoute><Compare /></ProtectedRoute>} />
      <Route path="/app/rfq" element={<ProtectedRoute><RFQList /></ProtectedRoute>} />
      <Route path="/app/rfq/:id" element={<ProtectedRoute><RFQDetail /></ProtectedRoute>} />
      <Route path="/app/watchlists" element={<ProtectedRoute><Watchlists /></ProtectedRoute>} />
      <Route path="/app/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />

      {/* Deferred: backend has no working endpoint for these. */}
      <Route
        path="/app/outreach"
        element={
          <ProtectedRoute>
            <Deferred
              title="Outreach"
              note="The backend's outreach router is miswired and manages RFQs, not outreach. Outreach messaging is not available."
            />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/quotes"
        element={
          <ProtectedRoute>
            <Deferred
              title="Quotes"
              note="Quote creation and retrieval are not exposed by the backend yet."
            />
          </ProtectedRoute>
        }
      />

      <Route path="/404" element={<NotFound />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}