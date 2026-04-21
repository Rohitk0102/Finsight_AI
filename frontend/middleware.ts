import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/predictor(.*)",
  "/news(.*)",
  "/screener(.*)",
  "/portfolio(.*)",
  "/settings(.*)",
]);

const isBackendApiRoute = createRouteMatcher(["/api/backend(.*)"]);

export default clerkMiddleware(async (auth, req) => {
  // Handle both Clerk middleware signatures: auth as function vs auth as object
  const isAuthFunction = typeof auth === "function";

  if (isProtectedRoute(req)) {
    if (!isAuthFunction && typeof (auth as any).protect === "function") {
      await (auth as any).protect();
    } else {
      const authObj = await (auth as any)();
      if (typeof authObj.protect === "function") {
        await authObj.protect();
      } else if (typeof (auth as any).protect === "function") {
        await (auth as any).protect();
      }
    }
  }

  // Intercept requests directed to the Python backend to inject the Clerk JWT
  if (isBackendApiRoute(req)) {
    let token = null;
    try {
      if (isAuthFunction) {
        const authObj = await (auth as any)();
        token = await authObj.getToken();
      } else {
        token = await (auth as any).getToken();
      }
    } catch (e) {
      console.error("Failed to get Clerk token in middleware:", e);
    }

    if (token) {
      const requestHeaders = new Headers(req.headers);
      requestHeaders.set("Authorization", `Bearer ${token}`);

      return NextResponse.next({
        request: {
          headers: requestHeaders,
        },
      });
    }
  }

  return NextResponse.next();
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
