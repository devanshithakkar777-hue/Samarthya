import type { MetadataRoute } from "next";
export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", allow: "/", disallow: ["/api/", "/dashboard", "/results", "/signin", "/study", "/applications", "/progress", "/for-you", "/build", "/connect/feedback", "/journey", "/learn/plan", "/companion", "/institution", "/connect/posts", "/parent", "/build/growth", "/live/wellness", "/admin", "/learn/notes", "/learn/concept-maps", "/learn/study-assistant", "/practise/mock-interview", "/connect/sessions", "/connect/mentor-dashboard", "/connect/employer", "/build/venture", "/build/credentials"] } };
}
