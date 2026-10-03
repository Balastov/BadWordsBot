import {http} from './client';
import type {TokenResponse} from './types';

export const authApi = {
  register: (username: string, email: string, password: string) =>
    http.post<TokenResponse>('/auth/register', {username, email, password}).then(r => r.data),

  login: (email: string, password: string) =>
    http.post<TokenResponse>('/auth/login', {email, password}).then(r => r.data),

  changePassword: (current_password: string, new_password: string) =>
    http
      .post<{ok: boolean}>('/users/me/password', {current_password, new_password})
      .then(r => r.data),
};
