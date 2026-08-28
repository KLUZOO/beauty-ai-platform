export type Lang = "ua" | "en";
export type AuthRole = "client" | "master" | "admin";
export type MockUser = {
  name: string;
  email: string;
  role: AuthRole;
  avatar: string;
};
