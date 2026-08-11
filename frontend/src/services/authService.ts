// Google OAuth service for handling authentication

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api';

export interface GoogleAuthResponse {
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  scope?: string;
  error?: string;
}

export interface AuthTokenPayload {
  id_token: string;
}

/**
 * Send Google ID token to backend for authentication
 */
export const sendGoogleTokenToBackend = async (idToken: string) => {
  try {
    const payload: AuthTokenPayload = {
      id_token: idToken,
    };

    const response = await fetch(`${API_BASE_URL}/users/google-login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Authentication failed');
    }

    const data = await response.json();

    // Store authentication token if provided
    if (data.token) {
      localStorage.setItem('authToken', data.token);
    }

    // Store access/refresh tokens if returned
    if (data.access && data.refresh) {
      storeTokens(data.access, data.refresh);
    }

    // Store user info if provided
    if (data.user) {
      localStorage.setItem('user', JSON.stringify(data.user));
    }

    return data;
  } catch (error) {
    console.error('Error sending token to backend:', error);
    throw error;
  }
};

export interface RegisterPayload {
  email: string;
  password: string;
}

export interface ExtendedRegisterPayload extends RegisterPayload {
  first_name: string;
  last_name: string;
  phone: string;
  phone_number?: string;
  password1?: string;
  password2?: string;
  password_confirmation?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export type LoginResponse =
  | {
      access: string;
      refresh: string;
    }
  | {
      access_token: string;
    }
  | {
      token: string;
    };

const storeTokens = (access: string, refresh: string) => {
  localStorage.setItem('authToken', access);
  localStorage.setItem('refreshToken', refresh);
};

const storeAccessToken = (access: string) => {
  localStorage.setItem('authToken', access);
};

const parseErrorResponse = async (response: Response) => {
  const contentType = response.headers.get('content-type') ?? '';
  const responseText = await response.text().catch(() => '');

  if (contentType.includes('application/json')) {
    try {
      const errorData = JSON.parse(responseText);
      return (
        errorData?.message ||
        errorData?.detail ||
        errorData?.error ||
        (typeof errorData === 'string'
          ? errorData
          : JSON.stringify(errorData)) ||
        response.statusText ||
        `Request failed with status ${response.status}`
      );
    } catch {
      // fall through to text fallback
    }
  }

  if (responseText) {
    if (/<(html|!doctype)/i.test(responseText)) {
      return `Server error ${response.status} ${response.statusText}. Backend is unavailable.`;
    }
    return responseText;
  }

  return `Request failed with status ${response.status} ${response.statusText}`;
};

export const getRefreshToken = () => {
  return localStorage.getItem('refreshToken');
};

export const refreshAccessToken = async () => {
  const refresh = getRefreshToken();

  if (!refresh) {
    throw new Error('Refresh token is missing');
  }

  const response = await fetch(`${API_BASE_URL}/users/token/refresh/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail ||
        errorData?.message ||
        `Refresh token failed with status ${response.status}`,
    );
  }

  const data = await response.json();

  if (data.access) {
    storeAccessToken(data.access);
  }

  return data;
};

export const verifyToken = async (token?: string) => {
  const jwt = token || getAuthToken();

  if (!jwt) {
    throw new Error('Token is missing');
  }

  const response = await fetch(`${API_BASE_URL}/users/token/verify/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token: jwt }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail ||
        errorData?.message ||
        `Token verification failed with status ${response.status}`,
    );
  }

  return true;
};

export const verifyEmail = async (uidb64: string, token: string) => {
  const response = await fetch(`${API_BASE_URL}/users/verify-email/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ uidb64, token }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(
      errorData?.detail ||
        errorData?.message ||
        `Email verification failed with status ${response.status}`,
    );
  }

  return response.json().catch(() => null);
};

export const registerUser = async (payload: ExtendedRegisterPayload) => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorMessage = await parseErrorResponse(response);
      throw new Error(errorMessage);
    }

    const data = await response.json();

    if ('access' in data && 'refresh' in data) {
      storeTokens(data.access, data.refresh);
    } else if ('access' in data) {
      storeAccessToken(data.access);
    } else if ('access_token' in data) {
      storeAccessToken(data.access_token);
    } else if ('token' in data && data.token) {
      localStorage.setItem('authToken', data.token);
    }

    if ('user' in data && data.user) {
      localStorage.setItem('user', JSON.stringify(data.user));
    }

    return data;
  } catch (error) {
    console.error('Error registering user:', error);
    throw error;
  }
};

export const loginUser = async (payload: LoginPayload) => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/token/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(
        errorData?.detail ||
          errorData?.message ||
          `Login failed with status ${response.status}`,
      );
    }

    const data: LoginResponse = await response.json();
    if ('access' in data && 'refresh' in data) {
      storeTokens(data.access, data.refresh);
    } else if ('access_token' in data) {
      storeAccessToken(data.access_token);
    } else if ('token' in data && data.token) {
      localStorage.setItem('authToken', data.token);
    }
    return data;
  } catch (error) {
    console.error('Error logging in user:', error);
    throw error;
  }
};

export const resetDatabase = async () => {
  const response = await fetch(`${API_BASE_URL}/reset_db/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const responseText = await response.text().catch(() => null);
    const errorMessage = responseText
      ? responseText
      : `Database reset failed with status ${response.status}`;
    throw new Error(errorMessage);
  }

  const contentType = response.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return null;
};

/**
 * Get stored authentication token
 */
export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

/**
 * Get stored user info
 */
export const getUserInfo = () => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};

/**
 * Logout and clear stored data
 */
export const logout = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user');
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('authToken');
};
