/** Simulates network latency so loading states are exercised during development. */
export const delay = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));
