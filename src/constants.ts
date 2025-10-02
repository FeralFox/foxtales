export const URL = import.meta.env.MODE === "production" ? "" : "http://localhost:8000";
console.log("Use backend at URL", URL)

export function authHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token')
    if (token) {
        return { 'Authorization': `Bearer ${token}` }
    }
    // Return an empty Headers object to satisfy HeadersInit when no token is present
    return new Headers()
}