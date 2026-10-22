import CookieConsent from "react-cookie-consent";

export function CookieBanner() {
  return (
    <CookieConsent
      location="bottom"
      cookieName="kangaroo-cookie-consent"
      buttonText="Accept"
      containerClasses="flex flex-wrap items-center gap-4 border-t border-border bg-surface p-4 text-sm text-fg-secondary"
      contentClasses="flex-1"
      buttonClasses="rounded bg-fg px-4 py-2 font-medium text-surface hover:bg-fg-secondary"
    >
      This site uses cookies to keep you signed in and remember your settings.
    </CookieConsent>
  );
}
