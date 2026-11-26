export type UserRole = "operator" | "field_officer" | "viewer";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  initials: string;
  role: UserRole;
  station: string;
  district: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  role: UserRole;
}
