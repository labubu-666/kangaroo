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
import { RecentSection } from "../components/sidebar/RecentSection";
import { Sidebar } from "../components/sidebar/Sidebar";
import { SidebarProvider } from "../components/sidebar/SidebarContext";
import { SidebarToggle } from "../components/sidebar/SidebarToggle";

export const Route = createRootRoute({
  component: () => (
    <BreadcrumbsProvider>
      <SidebarProvider>
        <div className="flex min-h-screen flex-col">
          <AppHeader />
          <SectionNav />
          <div className="flex flex-1">
            <Sidebar>
              <RecentSection />
            </Sidebar>
            <div className="flex min-w-0 flex-1 flex-col">
              <SidebarToggle />
              <PageBreadcrumbs />
              <Outlet />
              <AppFooter />
            </div>
          </div>
        </div>
      </SidebarProvider>
      <CookieBanner />
      <TanStackRouterDevtools />
    </BreadcrumbsProvider>
  ),
});
