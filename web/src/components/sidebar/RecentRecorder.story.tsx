import { useRecordRecent, type RecentEntry } from "../../lib/recent";

// Records an entry the way a detail page does once its data has loaded
export function RecentRecorder({ entry }: { entry: RecentEntry }) {
  useRecordRecent(entry);
  return null;
}
