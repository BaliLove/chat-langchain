import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { getCookie, setCookie } from "../utils/cookies";
import { USER_ID_COOKIE_NAME } from "../utils/constants";
import { useAuth } from "../contexts/AuthContextStable";

export function useUser() {
  const { user } = useAuth();
  const [userId, setUserId] = useState<string>();

  useEffect(() => {
    console.log("[USER DEBUG] useUser effect triggered. user?.id:", user?.id, "current userId:", userId);
    
    // If we have an authenticated user, use their Supabase ID
    if (user?.id) {
      console.log("[USER DEBUG] Using authenticated user ID:", user.id);
      setUserId(user.id);
      
      // Sync the cookie with the authenticated user ID to prevent mismatches
      const currentCookie = getCookie(USER_ID_COOKIE_NAME);
      if (currentCookie !== user.id) {
        console.log("[USER DEBUG] Syncing cookie from", currentCookie, "to", user.id);
        setCookie(USER_ID_COOKIE_NAME, user.id);
      }
      return;
    }

    // Fallback to cookie-based ID for unauthenticated users
    if (userId) {
      console.log("[USER DEBUG] User ID already set:", userId);
      return;
    }

    const userIdCookie = getCookie(USER_ID_COOKIE_NAME);
    if (userIdCookie) {
      console.log("[USER DEBUG] Using cookie user ID:", userIdCookie);
      setUserId(userIdCookie);
    } else {
      const newUserId = uuidv4();
      console.log("[USER DEBUG] Creating new user ID:", newUserId);
      setUserId(newUserId);
      setCookie(USER_ID_COOKIE_NAME, newUserId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  return {
    userId,
  };
}
