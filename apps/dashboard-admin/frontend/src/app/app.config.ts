/**
 * Application Configuration — Entry Point for Providers
 *
 * Angular 20 standalone architecture: no NgModule.
 * All providers are registered here and injected into the app
 * via bootstrapApplication() in main.ts.
 *
 * Apollo Client setup:
 * provideApollo() registers the Apollo Client as a singleton
 * injectable throughout the app. HttpLink connects Apollo to
 * the GraphQL gateway via Angular's HttpClient — this means
 * Apollo requests go through Angular's HTTP interceptor chain,
 * giving us auth headers, error handling, and testing for free.
 *
 * GraphQL Gateway URL:
 * Points to Apollo Server running in the Docker stack (:4000).
 * In production, NGINX proxies /graphql to the gateway service.
 */

import { ApplicationConfig, provideBrowserGlobalErrorListeners, provideZoneChangeDetection, inject } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideApollo } from 'apollo-angular';
import { HttpLink } from 'apollo-angular/http';
import { InMemoryCache } from '@apollo/client/core';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),

    // HttpClient — required by Apollo's HttpLink
    provideHttpClient(),

    // Apollo Client — connects to the GraphQL gateway
    // InMemoryCache: Apollo's normalized cache — avoids duplicate
    // requests for the same data within a session
    provideApollo(() => {
      const httpLink = inject(HttpLink);
      return {
        link: httpLink.create({ uri: 'http://localhost:4000/graphql' }),
        cache: new InMemoryCache(),
      };
    }),
  ],
};
