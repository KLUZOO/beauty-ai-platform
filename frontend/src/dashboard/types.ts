export type Lang = "ua" | "en";
export type AuthRole = "client" | "master" | "admin";
export type MockUser = {
  name: string;
  email: string;
  role: AuthRole;
  avatar?: string | null;
};

export type BookingConfirmation = {
  appointment: {
    id: number;
    master: number;
    salon: number;
    service: number;
    promo_id?: number | null;
    start: string;
    end: string;
    status: string;
    created_at: string;
  };
  masterName: string;
  salonName: string;
  serviceName: string;
};
