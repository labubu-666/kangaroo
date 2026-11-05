import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ErrorBanner } from "../shared/ErrorBanner";
import { Loading } from "../shared/Loading";
import { fetchCurrentUser } from "../../lib/user";

export function ProfileDetails() {
  const {
    data: user,
    error,
    isLoading,
  } = useQuery({
    queryKey: ["user"],
    queryFn: fetchCurrentUser,
  });

  return (
    <div className="space-y-6">
      {isLoading && <Loading />}
      {error && <ErrorBanner>{error.message}</ErrorBanner>}
      {user && (
        <div className="flex items-center gap-4">
          <img
            src={user.avatar_url}
            alt=""
            className="h-16 w-16 border border-border"
          />
          <div>
            <p className="text-lg font-medium">{user.username}</p>
            <p className="text-fg-muted">{user.email ?? "No email"}</p>
          </div>
        </div>
      )}
      <section className="space-y-2 rounded border border-border p-4">
        <h2 className="text-lg font-medium">API keys</h2>
        <p className="text-fg-secondary">
          Create and revoke keys for scripts and services that call the API as
          you.
        </p>
        <Link
          to="/profile/api-keys"
          className="inline-block text-primary hover:underline"
        >
          Manage API keys →
        </Link>
      </section>
    </div>
  );
}
