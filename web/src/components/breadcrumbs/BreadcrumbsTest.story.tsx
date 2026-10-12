import { Component, type ReactNode } from "react";
import { useBreadcrumbs } from "./BreadcrumbsContext";

// Test-only: renders the error message so a spec can assert on what React threw
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { message: string | null }
> {
  state = { message: null };

  static getDerivedStateFromError(error: Error) {
    return { message: error.message };
  }

  render() {
    if (this.state.message) return <p role="alert">{this.state.message}</p>;
    return this.props.children;
  }
}

// Test-only: calls the hook with no BreadcrumbsProvider above it
export function PublishWithoutProvider() {
  useBreadcrumbs([{ label: "Projects", to: "/projects" }]);
  return <p>rendered</p>;
}
