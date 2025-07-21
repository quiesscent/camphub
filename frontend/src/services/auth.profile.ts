import { jwtDecode } from "jwt-decode";

interface DecodedToken {
  email: string;
  username: string;
  role: string;
  is_subscribed: boolean;
  exp: number;
  iat: number;
  [key: string]: any;
}

export const getUserFromToken = (): DecodedToken | null => {
  const token = localStorage.getItem("wellbot_access_token");

  if (!token) return null;


  try {
    const decoded: DecodedToken = jwtDecode(token);

    return decoded;
  } catch (error) {
    console.error("Invalid token", error);
    return null;
  }
};