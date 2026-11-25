import { request, requestPublic } from "./client";
import type { AuthUser } from "@/lib/auth";

export type { AuthUser }; // re-export so @/lib/api consumers still get the type

export type LoginResponse = {
  access_token: string;
  token_type: string;
  redirect_to: string;
  user: { id: number; name: string; role: string; email: string; job_title?: string };
};

/**
 * Pública: el login no necesita sesión, y con `request` una sesión vieja guardada
 * convertía «contraseña incorrecta» (401) en «sesión expirada».
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
  return requestPublic<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export type GoogleLoginConfig = { enabled: boolean; client_id: string };

export async function getGoogleLoginConfig(): Promise<GoogleLoginConfig> {
  return requestPublic<GoogleLoginConfig>("/auth/google/config");
}

export async function loginWithGoogle(credential: string): Promise<LoginResponse> {
  return requestPublic<LoginResponse>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export async function getMe(): Promise<AuthUser> {
  return request<AuthUser>("/auth/me");
}

export async function updateMyProfile(payload: { full_name?: string | null; job_title?: string | null }): Promise<{ message: string }> {
  return request<{ message: string }>("/auth/profile", { method: "PATCH", body: JSON.stringify(payload) });
}

export async function changeMyPassword(payload: { current_password: string; new_password: string }): Promise<{ message: string }> {
  return request<{ message: string }>("/auth/change-password", { method: "POST", body: JSON.stringify(payload) });
}
