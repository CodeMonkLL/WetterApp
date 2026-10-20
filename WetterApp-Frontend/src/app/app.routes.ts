import { Routes } from '@angular/router';

import { AnalysisComponent } from './pages/analysis/analysis.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'auswertung', component: AnalysisComponent },
  { path: '**', redirectTo: '' },
];
