/** Auth client facade re-exporting unified token and login helpers. */

export { loginApi as login, type TokenResponse } from "../../api/auth";
export { clearToken, getStoredToken, storeToken } from "../../api/client";
