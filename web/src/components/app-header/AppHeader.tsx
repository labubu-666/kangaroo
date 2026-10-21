import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useId, useState } from "react";
import { fetchCurrentUser } from "../../lib/user";
import { useDismiss } from "../../lib/use-dismiss";
import { SearchBar } from "./SearchBar";

export function AppHeader() {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuId = useId();
  const menuRef = useDismiss<HTMLDivElement>(menuOpen, () =>
    setMenuOpen(false),
  );
  const { data: user } = useQuery({
    queryKey: ["user"],
    queryFn: fetchCurrentUser,
  });

  return (
    <nav className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-gray-200 p-4">
      <Link
        to="/"
        aria-label="Home"
        className="flex h-8 items-center text-xl leading-none hover:scale-110 transition-transform"
      >
        <span aria-hidden="true">🦘</span>
      </Link>
      <SearchBar />
      <div ref={menuRef} className="relative ml-auto flex">
        <button
          type="button"
          aria-label="Profile menu"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          aria-controls={menuId}
          onClick={() => setMenuOpen((open) => !open)}
          className="h-8 w-8 cursor-pointer overflow-hidden bg-gray-300 hover:bg-gray-400"
        >
          {user && (
            <img
              src={user.avatar_url}
              alt=""
              className="h-full w-full border border-gray-200"
            />
          )}
        </button>
        {menuOpen && (
          <div
            id={menuId}
            role="menu"
            aria-label="Profile"
            className="absolute right-0 z-10 mt-2 flex min-w-32 flex-col rounded border border-gray-200 bg-white py-1 shadow-lg"
          >
            {user && (
              <div className="border-b border-gray-200 px-3 py-2">
                <p className="font-medium">{user.username}</p>
                {user.email && (
                  <p className="text-sm text-gray-500">{user.email}</p>
                )}
              </div>
            )}
            <Link
              to="/admin"
              role="menuitem"
              onClick={() => setMenuOpen(false)}
              className="px-3 py-2 font-medium hover:bg-gray-100"
              activeProps={{ className: "text-blue-600" }}
            >
              Admin
            </Link>
            <Link
              to="/about"
              role="menuitem"
              onClick={() => setMenuOpen(false)}
              className="px-3 py-2 font-medium hover:bg-gray-100"
              activeProps={{ className: "text-blue-600" }}
            >
              About
            </Link>
            {/* Served by the API, not the SPA router, so submit a plain form */}
            <form method="post" action="/auth/logout">
              <button
                type="submit"
                role="menuitem"
                className="w-full px-3 py-2 text-left font-medium hover:bg-gray-100"
              >
                Logout
              </button>
            </form>
          </div>
        )}
      </div>
    </nav>
  );
}
