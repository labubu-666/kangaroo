import { useRouter } from "@tanstack/react-router";

// Returns a function that goes back in history when there is a previous entry
// (e.g. the user came from a board), otherwise runs the fallback
// (e.g. the user opened a shared link and navigates somewhere explicit).
export function useGoBackOr() {
  const router = useRouter();
  return (fallback: () => void) => {
    if (router.history.canGoBack()) {
      router.history.back();
    } else {
      fallback();
    }
  };
}
