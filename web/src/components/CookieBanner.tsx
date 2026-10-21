import CookieConsent from "react-cookie-consent";

export function CookieBanner() {
  return (
    <CookieConsent
      location="bottom"
      cookieName="kangaroo-cookie-consent"
      buttonText="Accept"
      containerClasses="flex flex-wrap items-center gap-4 border-t border-gray-200 bg-white p-4 text-sm text-gray-600"
      contentClasses="flex-1"
      buttonClasses="rounded bg-gray-900 px-4 py-2 font-medium text-white hover:bg-gray-700"
    >
      This site uses cookies to keep you signed in and remember your settings.
    </CookieConsent>
  );
}
