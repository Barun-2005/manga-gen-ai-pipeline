// API configuration
// Uses environment variable in production, falls back to localhost for dev
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
