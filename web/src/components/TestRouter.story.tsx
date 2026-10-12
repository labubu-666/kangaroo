import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
  useLocation,
} from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import type { BreadcrumbItem } from "./breadcrumbs/Breadcrumbs";
import {
  BreadcrumbsProvider,
  useBreadcrumbs,
} from "./breadcrumbs/BreadcrumbsContext";

// Publishes breadcrumbs the way a page does
function PublishBreadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  useBreadcrumbs(items);
  return null;
}

// Shows the current router location so tests can assert on navigation
function LocationProbe() {
  const location = useLocation();
  return (
    <span data-testid="location">{location.pathname + location.searchStr}</span>
  );
}

// Test-only wrapper: TanStack Link requires a router context.
// `children` render above the routed page, `breadcrumbs` are published for it.
export function TestRouter({
  children,
  breadcrumbs = [],
  paths = ["/"],
  initialPath = "/",
  initialEntries = [initialPath],
  showLocation = false,
}: {
  children?: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  paths?: string[];
  initialPath?: string;
  initialEntries?: string[];
  showLocation?: boolean;
}) {
  const rootRoute = createRootRoute({
    component: () => (
      <BreadcrumbsProvider>
        <PublishBreadcrumbs items={breadcrumbs} />
        {children}
        <Outlet />
      </BreadcrumbsProvider>
    ),
  });
  const routes = paths.map((path) =>
    createRoute({
      getParentRoute: () => rootRoute,
      path,
      component: () => (showLocation ? <LocationProbe /> : null),
    }),
  );
  const router = createRouter({
    routeTree: rootRoute.addChildren(routes),
    history: createMemoryHistory({ initialEntries }),
  });
  const queryClient = new QueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}
