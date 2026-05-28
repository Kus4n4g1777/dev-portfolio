import { GraphQLError } from 'graphql';
import { requireAuth, requireRole } from '../utils/auth.js';

export const resolvers = {
  Query: {
    me: (_, __, context) => {
      requireAuth(context);
      return context.springboot.getUserById(context.user.id);
    },

    dashboardStats: async (_, __, context) => {
      requireAuth(context);
      return context.fastapi.getDashboardStats();
    },

    servicesHealth: async (_, __, context) => {
      const services = [
        { name: 'fastapi', url: 'http://dashboard_backend:8000/health' },
        { name: 'springboot', url: 'http://springboot_backend:8081/actuator/health' },
        { name: 'llm-gateway', url: 'http://llm-gateway:8000/health' },
      ];

      return Promise.all(
        services.map(async (s) => {
          try {
            const res = await fetch(s.url);
            return { service: s.name, status: res.ok ? 'UP' : 'DOWN' };
          } catch {
            return { service: s.name, status: 'UNREACHABLE' };
          }
        })
      );
    },

    users: async (_, __, context) => {
      requireRole(context, 'ADMIN');
      return context.springboot.getUsers();
    },

    user: async (_, { id }, context) => {
      requireAuth(context);
      return context.springboot.getUserById(id);
    },

    llmHistory: async (_, { limit }, context) => {
      requireAuth(context);
      // Placeholder — conectar al LLM gateway cuando esté listo
      return [];
    },
  },

  Mutation: {
    login: async (_, { username, password }, context) => {
      const result = await context.fastapi.login(username, password);
      return result;
    },

    createUser: async (_, { input }, context) => {
      requireRole(context, 'ADMIN');
      return context.springboot.createUser(input);
    },

    updateUser: async (_, { id, input }, context) => {
      requireAuth(context);
      return context.springboot.updateUser(id, input);
    },

    deleteUser: async (_, { id }, context) => {
      requireRole(context, 'ADMIN');
      return context.springboot.deleteUser(id);
    },

    sendPrompt: async (_, { prompt, model = 'GEMINI' }, context) => {
      requireAuth(context);
      const res = await fetch('http://llm-gateway:8000/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, model: model.toLowerCase() }),
      });
      if (!res.ok) throw new GraphQLError('LLM Gateway error');
      return res.json();
    },
  },

  // Subscriptions — Kafka integration (futuro)
  Subscription: {
    userCreated: {
      subscribe: () => {
        // TODO: conectar PubSub a Kafka consumer
        throw new GraphQLError('Subscriptions coming soon — Kafka integration pending');
      },
    },
    dashboardUpdated: {
      subscribe: () => {
        throw new GraphQLError('Subscriptions coming soon — Kafka integration pending');
      },
    },
  },
};
