import { jwtDecode } from "jwt-decode";

interface DecodedToken {
  email: string;
  username: string;
  exp: number;
  iat: number;
  [key: string]: any;
}

export const getUserFromToken = (): DecodedToken | null => {
  const token = localStorage.getItem("camphub_user_access");

  if (!token) return null;


  try {
    const decoded: DecodedToken = jwtDecode(token);

    return decoded;
  } catch (error) {
    console.error("Invalid token", error);
    return null;
  }
};