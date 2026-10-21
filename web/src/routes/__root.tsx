import { Outlet, createRootRoute } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { AppFooter } from "../components/app-footer/AppFooter";
import { AppHeader } from "../components/app-header/AppHeader";
import { CookieBanner } from "../components/CookieBanner";
import {
  BreadcrumbsProvider,
  PageBreadcrumbs,
} from "../components/breadcrumbs/BreadcrumbsContext";
import { SectionNav } from "../components/SectionNav";

export const Route = createRootRoute({
  component: () => (
    <BreadcrumbsProvider>
      <div className="flex min-h-screen flex-col">
        <AppHeader />
        <SectionNav />
        <PageBreadcrumbs />
        <Outlet />
        <AppFooter />
      </div>
      <CookieBanner />
      <TanStackRouterDevtools />
    </BreadcrumbsProvider>
  ),
});
