import { useSyncExternalStore } from "react";

// "system" is stored as no saved value, so the pre-paint script in index.html
// can read the OS setting without any extra logic.
export type ThemeChoice = "system" | "light" | "dark";
export type Theme = Exclude<ThemeChoice, "system">;

const STORAGE_KEY = "kangaroo-theme";
const listeners = new Set<() => void>();

function readChoice(): ThemeChoice {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "light" || stored === "dark" ? stored : "system";
}

function resolve(choice: ThemeChoice): Theme {
  if (choice !== "system") return choice;
  return systemDark.matches ? "dark" : "light";
}

const systemDark = window.matchMedia("(prefers-color-scheme: dark)");

function subscribe(listener: () => void) {
  listeners.add(listener);
  // Re-apply on OS changes; a saved light or dark choice still wins in resolve()
  if (listeners.size === 1) systemDark.addEventListener("change", apply);
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) systemDark.removeEventListener("change", apply);
  };
}

function apply() {
  const theme = resolve(readChoice());
  document.documentElement.classList.toggle("dark", theme === "dark");
  listeners.forEach((listener) => listener());
}

export function setThemeChoice(choice: ThemeChoice) {
  if (choice === "system") localStorage.removeItem(STORAGE_KEY);
  else localStorage.setItem(STORAGE_KEY, choice);
  apply();
}

export function useTheme() {
  const choice = useSyncExternalStore(
    subscribe,
    readChoice,
    (): ThemeChoice => "system",
  );
  return { choice, theme: resolve(choice), setThemeChoice };
}
