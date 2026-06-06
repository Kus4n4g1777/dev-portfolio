import { Routes } from '@angular/router';
import { AnalyticsComponent } from './features/analytics/analytics.component';

export const routes: Routes = [
  { path: '', redirectTo: 'analytics', pathMatch: 'full' },
  { path: 'analytics', component: AnalyticsComponent },
];
