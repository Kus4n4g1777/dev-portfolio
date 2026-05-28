import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { typeDefs } from './schema/typeDefs.js';
import { resolvers } from './resolvers/index.js';
import { FastAPIDataSource } from './datasources/fastapi.js';
import { SpringBootDataSource } from './datasources/springboot.js';
import { extractUser } from './utils/auth.js';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: true, // habilitar en dev, deshabilitar en prod
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
  context: async ({ req }) => {
    const user = extractUser(req);
    const token = req?.headers?.authorization?.replace('Bearer ', '');

    return {
      user,
      fastapi: new FastAPIDataSource(token),
      springboot: new SpringBootDataSource(token),
    };
  },
});

console.log(`🚀 GraphQL Gateway ready at ${url}`);
