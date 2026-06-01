/**
 * MongoDB Connection
 *
 * Establishes and exports the Mongoose connection to MongoDB.
 * Called once on app startup — Mongoose handles connection pooling internally.
 *
 * Why a dedicated module instead of connecting in index.js?
 * Separation of concerns — index.js orchestrates startup order,
 * this module owns the database connection lifecycle. Any service
 * that needs to interact with the connection directly imports from here.
 *
 * Retry logic:
 * Mongoose retries automatically on transient failures via its
 * built-in serverSelectionTimeoutMS. The docker-compose healthcheck
 * ensures MongoDB is ready before this service starts, but lazy
 * reconnection handles any post-startup drops gracefully.
 */

import mongoose from 'mongoose';

export const connect = async () => {
  const url = process.env.MONGO_URL;

  if (!url) {
    throw new Error('MONGO_URL environment variable is not set');
  }

  try {
    await mongoose.connect(url);
    console.log('✅ MongoDB connected');
  } catch (err) {
    console.error('❌ MongoDB connection error:', err.message);
    process.exit(1);
  }
};