import { createFileRoute } from "@tanstack/react-router";
import { useBreadcrumbs } from "../../components/breadcrumbs/BreadcrumbsContext";
import { ProfileDetails } from "../../components/profile/ProfileDetails";

export const Route = createFileRoute("/profile/")({
  component: ProfilePage,
});

function ProfilePage() {
  useBreadcrumbs([{ label: "Profile" }]);

  return (
    <div className="space-y-6 p-4 sm:p-8">
      <h1 className="text-2xl font-bold">Profile</h1>
      <ProfileDetails />
    </div>
  );
}
