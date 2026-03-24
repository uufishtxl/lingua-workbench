/**
 * JWT Token Utilities
 * 
 * Utilities for decoding and checking JWT token expiration.
 * Note: These functions only decode the token, they do NOT verify signatures.
 */

interface JWTPayload {
    exp: number;  // Expiration time (Unix timestamp in seconds)
    iat?: number; // Issued at time
    user_id?: number;
    [key: string]: unknown;
}

/**
 * Decode a JWT token payload without verifying the signature.
 * JWT format: header.payload.signature (base64url encoded)
 */
export function decodeJWT(token: string): JWTPayload | null {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) {
            return null;
        }

        // Decode base64url (replace - with +, _ with /)
        const base64Payload = parts[1]?.replace(/-/g, '+').replace(/_/g, '/');
        if (!base64Payload) return null;
        const payload = atob(base64Payload);
        return JSON.parse(payload);
    } catch {
        return null;
    }
}

/**
 * Get the expiration time of a JWT token as a Date object.
 */
export function getTokenExpiration(token: string): Date | null {
    const payload = decodeJWT(token);
    if (!payload?.exp) {
        return null;
    }
    // exp is in seconds, Date expects milliseconds
    return new Date(payload.exp * 1000);
}

function getTimeString(date: Date): string {
    const month = date.getMonth() + 1
    const _date = date.getDate()
    const hour = date.getHours()
    const minute = date.getMinutes()
    return `${month}/${_date} ${hour}:${minute}`
}

/**
 * Get the time remaining until the token expires in milliseconds.
 * Returns negative value if token is already expired.
 */
export function getTimeUntilExpiration(token: string): number | null {
    const expiration = getTokenExpiration(token);
    if (!expiration) {
        return null;
    }
    console.log('Will Expire at', getTimeString(expiration), 'in', Math.floor((expiration.getTime() - Date.now()) / 1000 / 60 / 60), 'hours');
    return expiration.getTime() - Date.now();
}

/**
 * Check if the token will expire within a given number of minutes.
 */
export function willExpireWithin(token: string, minutes: number): boolean {
    const remaining = getTimeUntilExpiration(token);
    if (remaining === null) {
        return false;
    }
    // console.log('Will expire within', minutes, 'minutes', remaining < minutes * 60 * 1000);
    return remaining < minutes * 60 * 1000;
}

/**
 * Check if the token is already expired.
 */
export function isTokenExpired(token: string): boolean {
    const remaining = getTimeUntilExpiration(token);
    if (remaining === null) {
        return true; // Invalid token is considered expired
    }
    return remaining <= 0;
}
