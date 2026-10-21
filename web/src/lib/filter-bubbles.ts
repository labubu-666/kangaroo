// Turns a board filter into editable bubbles and back.
// The filter language is documented in docs/filter-language.md.

export const BOARD_FIELDS = [
  "title",
  "description",
  "project.id",
  "project.name",
] as const;

export const WORK_ITEM_FIELDS = [
  "title",
  "description",
  "status",
  "statusCategory",
  "type",
  "typeLevel",
  "parent_id",
  "project.id",
  "project.name",
  "labels",
] as const;

// Admin lists also filter on trashed, which is a true/false field
export const ADMIN_WORK_ITEM_FIELDS = [...WORK_ITEM_FIELDS, "trashed"] as const;

const BOOL_FIELDS: readonly string[] = ["trashed"];

export function isBoolField(field: string): boolean {
  return BOOL_FIELDS.includes(field);
}

const OPERATORS = [
  "==",
  "!=",
  "~",
  "in",
  "not in",
  "contains",
  "not contains",
  "is empty",
  "is not empty",
] as const;
export type Operator = (typeof OPERATORS)[number];

export interface Condition {
  field: string;
  op: Operator;
  values: string[];
}

const LIST_FIELDS: readonly string[] = ["labels"];
const PROJECT_FIELDS: readonly string[] = ["project.id", "project.name"];

// The operators the filter language allows on each kind of field
export function operatorsFor(field: string): Operator[] {
  if (isBoolField(field)) return ["==", "!="];
  return LIST_FIELDS.includes(field)
    ? ["contains", "not contains", "in", "not in", "is empty", "is not empty"]
    : ["==", "!=", "~", "in", "not in", "is empty", "is not empty"];
}

export function isProjectField(field: string): boolean {
  return PROJECT_FIELDS.includes(field);
}

export function isListOperator(op: Operator): boolean {
  return (
    op === "in" || op === "not in" || op === "contains" || op === "not contains"
  );
}

export function isEmptyOperator(op: Operator): boolean {
  return op === "is empty" || op === "is not empty";
}

const NAME = "[A-Za-z_][\\w.]*";
const STRING = `(?:'[^']*'|"[^"]*")`;
const LIST = `\\[\\s*(?:${STRING}(?:\\s*,\\s*${STRING})*)?\\s*\\]`;
const COMPARE = new RegExp(`^(${NAME})\\s*(==|!=|~)\\s*(${STRING})$`);
const BOOL_COMPARE = /^(\w+)\s*(==|!=)\s*(true|false)$/;
const EMPTY = new RegExp(`^(${NAME})\\s+is\\s+(not\\s+)?empty$`);
const MEMBER = new RegExp(`^(${NAME})\\s+(not\\s+)?in\\s+(${LIST})$`);
const CONTAINS = new RegExp(
  `^(${NAME})\\s+(not\\s+)?contains\\s+(${STRING}|${LIST})$`,
);
const STRINGS = new RegExp(STRING, "g");
const KEY_VALUE = /^([A-Za-z_][\w.]*)\s*:\s*(.+)$/;

function unquote(text: string): string {
  return text.slice(1, -1);
}

function makeCondition(
  field: string,
  op: Operator,
  values: string[],
  fields: readonly string[],
): Condition | null {
  return fields.includes(field) && operatorsFor(field).includes(op)
    ? { field, op, values }
    : null;
}

// Reads one simple condition such as `title ~ 'bug'`. Anything more complex
// (or, not, brackets, unknown fields) returns null and stays a text bubble.
export function parseCondition(
  text: string,
  fields: readonly string[] = BOARD_FIELDS,
): Condition | null {
  const t = text.trim();
  let m = BOOL_COMPARE.exec(t);
  if (m) return makeCondition(m[1], m[2] as Operator, [m[3]], fields);
  m = COMPARE.exec(t);
  if (m) return makeCondition(m[1], m[2] as Operator, [unquote(m[3])], fields);
  m = EMPTY.exec(t);
  if (m) {
    return makeCondition(m[1], m[2] ? "is not empty" : "is empty", [], fields);
  }
  m = MEMBER.exec(t);
  if (m) {
    const values = (m[3].match(STRINGS) ?? []).map(unquote);
    return makeCondition(m[1], m[2] ? "not in" : "in", values, fields);
  }
  m = CONTAINS.exec(t);
  if (m) {
    const values = (m[3].match(STRINGS) ?? []).map(unquote);
    return makeCondition(
      m[1],
      m[2] ? "not contains" : "contains",
      values,
      fields,
    );
  }
  return null;
}

// Quotes a value with whichever quote character it does not contain.
// The filter language has no escapes, so a value with both kinds cannot be
// written; the API then rejects the filter with a 422.
function quote(value: string): string {
  return value.includes("'") && !value.includes('"')
    ? `"${value}"`
    : `'${value}'`;
}

export function formatCondition(condition: Condition): string {
  const { field, op, values } = condition;
  if (isEmptyOperator(op)) return `${field} ${op}`;
  if (isBoolField(field)) return `${field} ${op} ${values[0] ?? "false"}`;
  if (isListOperator(op)) {
    return `${field} ${op} [${values.map(quote).join(", ")}]`;
  }
  return `${field} ${op} ${quote(values[0] ?? "")}`;
}

// A filter that shows only one project's items; undefined when the project is unknown
export function projectFilter(projectId?: string): string | undefined {
  if (!projectId) return undefined;
  return formatCondition({
    field: "project.id",
    op: "==",
    values: [projectId],
  });
}

// Splits a list value typed by the user: `a, 'b'` becomes ["a", "b"]
export function parseList(text: string): string[] {
  return text
    .split(",")
    .map((value) => value.trim().replace(/^(['"])(.*)\1$/, "$2"))
    .filter(Boolean);
}

// Text typed into the add box. `key:value` becomes an exact match on a known
// field; anything else is used as written.
export function parseInput(
  text: string,
  fields: readonly string[] = BOARD_FIELDS,
): string {
  const t = text.trim();
  const m = KEY_VALUE.exec(t);
  const field = m?.[1] ?? "";
  if (m && fields.includes(field)) {
    if (isBoolField(field)) {
      return formatCondition({ field, op: "==", values: [m[2].trim()] });
    }
    const op = LIST_FIELDS.includes(field) ? "contains" : "==";
    return formatCondition({ field, op, values: [m[2].trim()] });
  }
  return t;
}

export type Join = "and" | "or";

// A filter as conditions plus the join between each pair
export interface FilterParts {
  texts: string[];
  joins: Join[]; // joins[i] sits between texts[i] and texts[i + 1]
}

const SEPARATOR = /^\s(and|or)\s/;

// Splits text on top-level `and` / `or`: not inside quotes or brackets.
function splitTopLevel(text: string): FilterParts {
  const texts: string[] = [];
  const joins: Join[] = [];
  let depth = 0;
  let quoteChar: string | null = null;
  let start = 0;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoteChar) {
      if (ch === quoteChar) quoteChar = null;
    } else if (ch === "'" || ch === '"') {
      quoteChar = ch;
    } else if (ch === "(" || ch === "[") {
      depth++;
    } else if (ch === ")" || ch === "]") {
      depth--;
    } else if (depth === 0) {
      const match = SEPARATOR.exec(text.slice(i));
      if (match) {
        texts.push(text.slice(start, i).trim());
        joins.push(match[1] as Join);
        start = i + match[0].length;
        i = start - 1;
      }
    }
  }
  texts.push(text.slice(start).trim());
  return { texts, joins };
}

// Wraps text in brackets when it has a top-level and/or, so it stays one condition
function groupText(text: string): string {
  const t = text.trim();
  return splitTopLevel(t).texts.length > 1 ? `(${t})` : t;
}

// Mixed top-level `and` and `or` (e.g. `a or b and c`) means something other
// than reading the bubbles left to right, so that filter stays one text bubble.
export function splitFilter(filter?: string): FilterParts {
  const text = filter?.trim() ?? "";
  if (!text) return { texts: [], joins: [] };
  const parts = splitTopLevel(text);
  const mixed = parts.joins.some((join) => join !== parts.joins[0]);
  return mixed ? { texts: [text], joins: [] } : parts;
}

// Bubbles are read left to right, but the server binds `and` tighter than
// `or`. When the join changes, the expression so far is bracketed, so
// `a or b and c` is written `(a or b) and c`, as the bubbles show it.
export function joinFilter({ texts, joins }: FilterParts): string | undefined {
  if (texts.length === 0) return undefined;
  let expr = texts[0];
  for (let i = 1; i < texts.length; i++) {
    if (i > 1 && joins[i - 1] !== joins[i - 2]) expr = `(${expr})`;
    expr = `${expr} ${joins[i - 1]} ${texts[i]}`;
  }
  return expr;
}

export function addPart(parts: FilterParts, text: string): FilterParts {
  if (!text) return parts;
  return {
    texts: [...parts.texts, groupText(text)],
    joins: parts.texts.length ? [...parts.joins, "and"] : parts.joins,
  };
}

export function replacePart(
  parts: FilterParts,
  index: number,
  text: string,
): FilterParts {
  return {
    texts: parts.texts.map((existing, i) =>
      i === index ? groupText(text) : existing,
    ),
    joins: parts.joins,
  };
}

export function removePart(parts: FilterParts, index: number): FilterParts {
  const joinIndex = index === 0 ? 0 : index - 1;
  return {
    texts: parts.texts.filter((_, i) => i !== index),
    joins: parts.joins.filter((_, i) => i !== joinIndex),
  };
}

// Swaps a condition with its neighbour; joins stay in their positions
export function movePart(
  parts: FilterParts,
  index: number,
  delta: -1 | 1,
): FilterParts {
  const target = index + delta;
  if (target < 0 || target >= parts.texts.length) return parts;
  const texts = [...parts.texts];
  [texts[index], texts[target]] = [texts[target], texts[index]];
  return { texts, joins: parts.joins };
}

// Flips the join between texts[index] and texts[index + 1]
export function toggleJoin(parts: FilterParts, index: number): FilterParts {
  return {
    texts: parts.texts,
    joins: parts.joins.map((join, i) =>
      i === index ? (join === "and" ? "or" : "and") : join,
    ),
  };
}

// The status id from a top-level `status == '…'` condition, if the filter has one
export function statusIdFromFilter(filter?: string): string | undefined {
  const parts = splitFilter(filter);
  for (const text of parts.texts) {
    const condition = parseCondition(text, WORK_ITEM_FIELDS);
    if (condition?.field === "status" && condition.op === "==") {
      return condition.values[0];
    }
  }
  return undefined;
}

// Sets, or with no statusId removes, the `status == …` condition in a filter.
// Other conditions and their joins are kept as they are.
export function withStatus(
  filter: string | undefined,
  statusId: string | undefined,
): string | undefined {
  // A status only makes sense inside one project, so without a project
  // condition in the filter there is nothing to scope it to.
  if (statusId && !filter?.includes("project.id")) return filter;
  const parts = splitFilter(filter);
  const keep = parts.texts
    .map((text, index) => ({ text, index }))
    .filter(({ text }) => {
      const condition = parseCondition(text, WORK_ITEM_FIELDS);
      return !(condition?.field === "status" && condition.op === "==");
    });
  const kept: FilterParts = {
    texts: keep.map(({ text }) => text),
    joins: keep.slice(1).map(({ index }) => parts.joins[index - 1] ?? "and"),
  };
  const withStatusPart = statusId
    ? addPart(
        kept,
        formatCondition({ field: "status", op: "==", values: [statusId] }),
      )
    : kept;
  return joinFilter(withStatusPart);
}

// True when a filter names a status with this exact name in a top-level
// `status == …` or `status in […]` condition. Used before a status is renamed,
// since a filter that uses the old name stops matching after the rename.
export function filterUsesStatusName(
  filter: string | null | undefined,
  name: string,
): boolean {
  const parts = splitFilter(filter ?? "");
  return parts.texts.some((text) => {
    const condition = parseCondition(text, WORK_ITEM_FIELDS);
    if (condition?.field !== "status") return false;
    if (condition.op === "==") return condition.values[0] === name;
    if (condition.op === "in") return condition.values.includes(name);
    return false;
  });
}
