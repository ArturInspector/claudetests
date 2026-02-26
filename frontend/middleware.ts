import { NextResponse, type NextRequest } from "next/server"

const PUBLIC_PATHS = ["/login", "/register", "/favicon.ico", "/"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (PUBLIC_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`))) {
    return NextResponse.next()
  }

  const token = request.cookies.get("access_token")?.value

  if (!token && pathname.startsWith("/chat")) {
    const loginUrl = request.nextUrl.clone()
    loginUrl.pathname = "/login"
    loginUrl.searchParams.set("next", pathname)
    return NextResponse.redirect(loginUrl)
  }

  if (token && (pathname.startsWith("/login") || pathname.startsWith("/register"))) {
    const chatUrl = request.nextUrl.clone()
    chatUrl.pathname = "/chat"
    chatUrl.searchParams.delete("next")
    return NextResponse.redirect(chatUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}











