export const typeDefs = `#graphql

  # ─── SCALARS ───────────────────────────────
  scalar DateTime

  # ─── USER DOMAIN (Spring Boot) ─────────────
  type User {
    id: ID!
    username: String!
    email: String!
    role: Role!
    createdAt: DateTime
  }

  enum Role {
    ADMIN
    USER
    VIEWER
  }

  # ─── DASHBOARD DOMAIN (FastAPI) ────────────
  type DashboardStats {
    totalUsers: Int!
    activeUsers: Int!
    totalRequests: Int!
    avgResponseTime: Float!
  }

  type HealthStatus {
    service: String!
    status: String!
    uptime: Float
  }

  # ─── LLM DOMAIN (LLM Gateway) ──────────────
  type LLMResponse {
    id: ID!
    prompt: String!
    response: String!
    model: String!
    latencyMs: Int!
    cached: Boolean!
  }

  # ─── QUERIES ───────────────────────────────
  type Query {
    # Auth required
    me: User

    # Dashboard
    dashboardStats: DashboardStats!
    servicesHealth: [HealthStatus!]!

    # Users (Spring Boot)
    users: [User!]!
    user(id: ID!): User

    # LLM
    llmHistory(limit: Int = 10): [LLMResponse!]!
  }

  # ─── MUTATIONS ─────────────────────────────
  type Mutation {
    # Auth
    login(username: String!, password: String!): AuthPayload!

    # Users
    createUser(input: CreateUserInput!): User!
    updateUser(id: ID!, input: UpdateUserInput!): User!
    deleteUser(id: ID!): Boolean!

    # LLM
    sendPrompt(prompt: String!, model: LLMModel): LLMResponse!
  }

  # ─── SUBSCRIPTIONS (Kafka futuro) ──────────
  type Subscription {
    userCreated: User!
    dashboardUpdated: DashboardStats!
  }

  # ─── INPUT TYPES ───────────────────────────
  input CreateUserInput {
    username: String!
    email: String!
    password: String!
    role: Role = USER
  }

  input UpdateUserInput {
    username: String
    email: String
    role: Role
  }

  # ─── AUTH ──────────────────────────────────
  type AuthPayload {
    token: String!
    user: User!
  }

  enum LLMModel {
    GEMINI
    OLLAMA
    OPENAI
  }
`;
