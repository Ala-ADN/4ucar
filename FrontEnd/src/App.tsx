/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Overview } from './pages/Overview';
import { Institutions } from './pages/Institutions';
import { InstitutionDetail } from './pages/InstitutionDetail';
import { MapView } from './pages/MapView';
import { Alerts } from './pages/Alerts';
import { Analytics } from './pages/Analytics';
import { Rankings } from './pages/Rankings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Overview />} />
          <Route path="/institutions" element={<Institutions />} />
          <Route path="/institutions/:code" element={<InstitutionDetail />} />
          <Route path="/conventions" element={<MapView />} />
          <Route path="/alertes" element={<Alerts />} />
          <Route path="/reports" element={<Analytics />} />
          <Route path="/finance" element={<Rankings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

