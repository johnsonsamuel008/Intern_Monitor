export type UserRole = "admin" | "intern";

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
}

export interface DecodedToken {
  sub: string;
  role: UserRole;
  exp: number;
}
