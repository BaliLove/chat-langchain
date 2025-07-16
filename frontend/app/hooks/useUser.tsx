import { useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { getCookie, setCookie } from "../utils/cookies";
import { USER_ID_COOKIE_NAME } from "../utils/constants";

export function useUser() {
  const [userId, setUserId] = useState<string>();

  useEffect(() => {
    if (userId) {
      console.log("[DEBUG] User ID already set:", userId);
      return;
    }

    const userIdCookie = getCookie(USER_ID_COOKIE_NAME);
    if (userIdCookie) {
      console.log("[DEBUG] Found user ID in cookie:", userIdCookie);
      setUserId(userIdCookie);
    } else {
      const newUserId = uuidv4();
      console.log("[DEBUG] Creating new user ID:", newUserId);
      setUserId(newUserId);
      setCookie(USER_ID_COOKIE_NAME, newUserId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  console.log("[DEBUG] useUser hook returning userId:", userId);

  return {
    userId,
  };
}
