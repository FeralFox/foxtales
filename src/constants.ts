export const URL = import.meta.env.MODE === "production" ? "" : "http://localhost:8000";
console.log("Use backend at URL", URL)