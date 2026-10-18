import { useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import type { MouseEvent } from "react";
import { fetchDoc } from "../lib/docs";
import { useBreadcrumbs } from "./breadcrumbs/BreadcrumbsContext";
import { ErrorBanner } from "./shared/ErrorBanner";
import { Loading } from "./shared/Loading";

// Renders a Markdown doc from docs/ (HTML is sanitized by the API)
export function Doc({ name }: { name: string }) {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery({
    queryKey: ["docs", name],
    queryFn: () => fetchDoc(name),
  });

  // The index is the docs home; other pages show "Index > <Page>"
  const indexCrumb = {
    label: "Index",
    to: "/docs/$doc",
    params: { doc: "index" },
  };
  useBreadcrumbs(
    name === "index"
      ? [{ label: "Index" }]
      : [
          indexCrumb,
          {
            label: name
              .replace(/-/g, " ")
              .replace(/^./, (c) => c.toUpperCase()),
          },
        ],
  );

  // Links to other docs (e.g. ./filter-language) navigate inside the app
  function handleClick(event: MouseEvent<HTMLElement>) {
    const href = (event.target as HTMLElement)
      .closest("a")
      ?.getAttribute("href");
    if (!href || /^([a-z]+:|\/|#)/i.test(href)) return;
    event.preventDefault();
    navigate({
      to: "/docs/$doc",
      params: { doc: href.replace(/^\.\//, "").replace(/\.md$/, "") },
    });
  }

  if (isLoading) return <Loading />;
  if (error) return <ErrorBanner>{error.message}</ErrorBanner>;
  if (!data) return null;

  return (
    <article
      onClick={handleClick}
      className="space-y-3 px-4 pb-8 break-words text-gray-700 [&_a]:text-blue-600 [&_a]:underline [&_code]:rounded [&_code]:bg-gray-100 [&_code]:px-1 [&_h1]:text-3xl [&_h1]:font-bold [&_h2]:text-2xl [&_h2]:font-bold [&_h3]:text-xl [&_h3]:font-semibold [&_li]:ml-5 [&_ol]:list-decimal [&_pre]:overflow-x-auto [&_pre]:rounded [&_pre]:bg-gray-100 [&_pre]:p-2 [&_table]:w-full [&_table]:border-collapse [&_td]:border [&_td]:px-2 [&_th]:border [&_th]:px-2 [&_ul]:list-disc"
      dangerouslySetInnerHTML={{ __html: data.html }}
    />
  );
}
