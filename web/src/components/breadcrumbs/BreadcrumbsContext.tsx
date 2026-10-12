import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Breadcrumbs, type BreadcrumbItem } from "./Breadcrumbs";

interface BreadcrumbsContextValue {
  items: BreadcrumbItem[];
  setItems: (items: BreadcrumbItem[]) => void;
}

const BreadcrumbsContext = createContext<BreadcrumbsContextValue | null>(null);

// Holds the breadcrumbs of the current page so the shared layout can render them
export function BreadcrumbsProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<BreadcrumbItem[]>([]);
  return (
    <BreadcrumbsContext.Provider value={{ items, setItems }}>
      {children}
    </BreadcrumbsContext.Provider>
  );
}

// Called by a page to publish its breadcrumbs; they are cleared when the page unmounts
export function useBreadcrumbs(items: BreadcrumbItem[]) {
  const context = useContext(BreadcrumbsContext);
  if (!context)
    throw new Error("useBreadcrumbs must be used inside BreadcrumbsProvider");
  const { setItems } = context;
  // Compare by value so pages can pass a new array on every render without looping
  const serialized = JSON.stringify(items);
  useEffect(() => {
    setItems(JSON.parse(serialized));
    return () => setItems([]);
  }, [serialized, setItems]);
}

export function PageBreadcrumbs() {
  const context = useContext(BreadcrumbsContext);
  if (!context || context.items.length === 0) return null;
  return (
    <div className="px-4 pt-4">
      <Breadcrumbs items={context.items} />
    </div>
  );
}
