// V1 single-user authentication model.
// No auth middleware — every request is treated as the default user.
//
// V1.5 upgrade path: add a `users` table, issue a session token on login,
// and introduce an auth middleware that resolves the token to a user_id.
// Replace DEFAULT_USER_ID lookups with the resolved value from the token.

export const DEFAULT_USER_ID = "default";
