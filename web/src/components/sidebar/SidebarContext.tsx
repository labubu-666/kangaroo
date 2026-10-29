import { createContext, useContext, useState, type ReactNode } from "react";

const STORAGE_KEY = "kangaroo-sidebar";

interface SidebarContextValue {
  collapsed: boolean;
  toggleCollapsed: () => void;
  expand: () => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

const SidebarContext = createContext<SidebarContextValue | null>(null);

// Desktop collapse is remembered; the mobile drawer always starts closed
export function SidebarProvider({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(
    () => localStorage.getItem(STORAGE_KEY) === "collapsed",
  );
  const [mobileOpen, setMobileOpen] = useState(false);

  const setCollapsedAndSave = (next: boolean) => {
    if (next) localStorage.setItem(STORAGE_KEY, "collapsed");
    else localStorage.removeItem(STORAGE_KEY);
    setCollapsed(next);
  };

  return (
    <SidebarContext.Provider
      value={{
        collapsed,
        toggleCollapsed: () => setCollapsedAndSave(!collapsed),
        expand: () => setCollapsedAndSave(false),
        mobileOpen,
        setMobileOpen,
      }}
    >
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (!context)
    throw new Error("useSidebar must be used inside SidebarProvider");
  return context;
}
