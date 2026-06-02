/**
 * GraphQL Gateway — Entry Point
 *
 * Single API layer for the Angular dashboard frontend.
 * Unifies FastAPI (Python), Spring Boot (Java), and Express Analytics (Node.js)
 * behind one GraphQL endpoint — consistent auth, consistent error format,
 * one URL for the client to talk to.
 *
 * DataSources injected via context on every request:
 * - fastapi:    Dashboard stats, auth (Python/FastAPI)
 * - springboot: User management (Java/Spring Boot)
 * - analytics:  LLM inference metrics from MongoDB (Node.js/Express)
 *
 * Schema is split by domain — each domain owns its typeDefs and resolvers.
 * Apollo Server merges them at startup via array spread.
 *
 * Port: 4000
 * Introspection: enabled (dev) — disable in production
 */

import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';

import { typeDefs } from './schema/typeDefs.js';
import { analyticsTypeDefs } from './schema/analyticsTypeDefs.js';

import { resolvers } from './resolvers/index.js';
import { analyticsResolvers } from './resolvers/analyticsResolvers.js';

import { FastAPIDataSource } from './datasources/fastapi.js';
import { SpringBootDataSource } from './datasources/springboot.js';
import { AnalyticsDataSource } from './datasources/analytics.js';

import { extractUser } from './utils/auth.js';

const server = new ApolloServer({
  // Merge domain schemas — base + analytics
  // Apollo Server accepts an array of typeDefs and merges them automatically
  typeDefs: [typeDefs, analyticsTypeDefs],

  // Merge domain resolvers — spread pattern keeps each domain isolated
  resolvers: [resolvers, analyticsResolvers],

  introspection: true, // disable in production
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
  context: async ({ req }) => {
    const user  = extractUser(req);
    const token = req?.headers?.authorization?.replace('Bearer ', '');

    return {
      user,
      fastapi:    new FastAPIDataSource(token),
      springboot: new SpringBootDataSource(token),
      // AnalyticsDataSource needs no token — metrics are not user-scoped
      analytics:  new AnalyticsDataSource(),
    };
  },
});

console.log(`🚀 GraphQL Gateway ready at ${url}`);