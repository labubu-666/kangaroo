"""A small JQL-like filter language for choosing which work items a board shows.

The language is documented in docs/filter-language.md.

Examples:
    project.name == 'foo'
    project.name == 'foo' and status != 'done'
    type == 'task' and (title ~ 'bug' or status in ['open', 'in_progress'])
    labels contains 'derstandard' and labels is not empty
    trashed == false

Text fields: title, description, status, statusCategory, type, typeLevel,
parent_id, project.id, project.name
List fields: labels
True/false field: trashed (compared with true or false, unquoted)

Filters are parsed into predicates and never evaluated, so stored text is safe.
"""

import re
from collections.abc import Callable, Mapping

from kangaroo.errors import InvalidFilterError

TEXT_FIELDS = frozenset(
    {
        "title",
        "description",
        "status",
        "statusCategory",
        "type",
        "typeLevel",
        "parent_id",
        "project.id",
        "project.name",
    }
)
# status and type match a project's status or type by id or by name. The id is
# read from this record key.
ID_KEYS = {"status": "status_id", "type": "type_id"}
LIST_FIELDS = frozenset({"labels"})
BOOL_FIELDS = frozenset({"trashed"})
FIELDS = TEXT_FIELDS | LIST_FIELDS | BOOL_FIELDS

Record = Mapping[str, str | list[str] | None]
Predicate = Callable[[Record], bool]
Token = tuple[str, str]

_SPACES = re.compile(r"\s*")
_TOKEN = re.compile(
    r"""(?:(?P<string>'[^']*'|"[^"]*")|(?P<op>==|!=|~)|(?P<punct>[()\[\],])"""
    r"""|(?P<word>[A-Za-z_][\w.]*))"""
)


def parse_filter(text: str | None) -> Predicate:
    """Compile a filter into a predicate over a flattened work item record.

    A missing or blank filter matches every record.

    Raises:
        InvalidFilterError: If the filter text is not valid.
    """
    if text is None or not text.strip():
        return lambda _record: True
    return _Parser(_tokenize(text)).parse()


def _skip_spaces(text: str, pos: int) -> int:
    match = _SPACES.match(text, pos)
    # \s* always matches (possibly empty), so this is never None.
    if match is None:
        return pos
    return match.end()


def _tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    pos = _skip_spaces(text, 0)
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if match is None:
            raise InvalidFilterError(
                f"Unexpected character {text[pos]!r} at position {pos}"
            )
        kind = match.lastgroup or ""
        value = match.group(kind)
        if kind == "string":
            value = value[1:-1]
        tokens.append((kind, value))
        pos = _skip_spaces(text, match.end())
    return tokens


class _Parser:
    """Recursive descent parser. Grammar, lowest precedence first:

    or_expr    := and_expr ("or" and_expr)*
    and_expr   := not_expr ("and" not_expr)*
    not_expr   := "not" not_expr | primary
    primary    := "(" or_expr ")" | comparison
    comparison := TEXT_FIELD ("==" | "!=" | "~") STRING
                | BOOL_FIELD ("==" | "!=") ("true" | "false")
                | TEXT_FIELD ["not"] "in" LIST
                | LIST_FIELD ["not"] "contains" (STRING | LIST)
                | LIST_FIELD ["not"] "in" LIST
                | LIST_FIELD "~" STRING
                | FIELD "is" ["not"] "empty"
    LIST       := "[" [STRING ("," STRING)*] "]"
    """

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def parse(self) -> Predicate:
        predicate = self._or_expr()
        leftover = self._peek()
        if leftover is not None:
            raise InvalidFilterError(f"Unexpected {leftover[1]!r}")
        return predicate

    def _peek(self) -> Token | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _next(self) -> Token:
        token = self._peek()
        if token is None:
            raise InvalidFilterError("Unexpected end of filter")
        self._pos += 1
        return token

    def _accept(self, token: Token) -> bool:
        if self._peek() == token:
            self._pos += 1
            return True
        return False

    def _expect(self, token: Token) -> None:
        if not self._accept(token):
            raise InvalidFilterError(f"Expected {token[1]!r}")

    def _or_expr(self) -> Predicate:
        predicates = [self._and_expr()]
        while self._accept(("word", "or")):
            predicates.append(self._and_expr())
        return _any_of(predicates)

    def _and_expr(self) -> Predicate:
        predicates = [self._not_expr()]
        while self._accept(("word", "and")):
            predicates.append(self._not_expr())
        return _all_of(predicates)

    def _not_expr(self) -> Predicate:
        if self._accept(("word", "not")):
            return _negate(self._not_expr())
        return self._primary()

    def _primary(self) -> Predicate:
        if self._accept(("punct", "(")):
            predicate = self._or_expr()
            self._expect(("punct", ")"))
            return predicate
        return self._comparison()

    def _comparison(self) -> Predicate:
        kind, field = self._next()
        if kind != "word" or field not in FIELDS:
            raise InvalidFilterError(f"Unknown field {field!r}")
        if field in BOOL_FIELDS:
            return self._bool_comparison(field)
        kind, op = self._next()
        if (kind, op) == ("word", "is"):
            negated = self._accept(("word", "not"))
            self._expect(("word", "empty"))
            return _empty(field, negated)
        if field in LIST_FIELDS:
            return self._list_comparison(field, kind, op)
        if kind == "op":
            return _compare(field, op, self._string())
        if (kind, op) == ("word", "in"):
            return _member(field, self._list(), negated=False)
        if (kind, op) == ("word", "not"):
            self._expect(("word", "in"))
            return _member(field, self._list(), negated=True)
        if (kind, op) == ("word", "contains"):
            raise InvalidFilterError(
                f"'contains' only works on list fields, not {field!r}"
            )
        raise InvalidFilterError(f"Expected an operator after {field!r}")

    def _bool_comparison(self, field: str) -> Predicate:
        kind, op = self._next()
        if (kind, op) not in {("op", "=="), ("op", "!=")}:
            raise InvalidFilterError(f"{field!r} is true/false: use '==' or '!='")
        kind, value = self._next()
        if kind != "word" or value not in ("true", "false"):
            raise InvalidFilterError(f"Expected true or false, got {value!r}")
        return _compare(field, op, value)

    def _list_comparison(self, field: str, kind: str, op: str) -> Predicate:
        if kind == "op":
            if op == "~":
                return _label_contains_text(field, self._string())
            raise InvalidFilterError(
                f"{field!r} is a list field: use 'contains' or 'in' instead of {op!r}"
            )
        if (kind, op) == ("word", "contains"):
            return _has_all(field, self._contains_values(), negated=False)
        if (kind, op) == ("word", "in"):
            return _has_any(field, self._list(), negated=False)
        if (kind, op) == ("word", "not"):
            if self._accept(("word", "in")):
                return _has_any(field, self._list(), negated=True)
            self._expect(("word", "contains"))
            return _has_all(field, self._contains_values(), negated=True)
        raise InvalidFilterError(f"Expected an operator after {field!r}")

    def _contains_values(self) -> list[str]:
        """A single value, or a list meaning every value must be present."""
        if self._peek() == ("punct", "["):
            return self._list()
        return [self._string()]

    def _string(self) -> str:
        kind, value = self._next()
        if kind != "string":
            raise InvalidFilterError(f"Expected a quoted string, got {value!r}")
        return value

    def _list(self) -> list[str]:
        self._expect(("punct", "["))
        values: list[str] = []
        if self._accept(("punct", "]")):
            return values
        values.append(self._string())
        while self._accept(("punct", ",")):
            values.append(self._string())
        self._expect(("punct", "]"))
        return values


def _normalize(text: str) -> str:
    """Ignore case and treat ``_``, ``-`` and spaces as the same."""
    return re.sub(r"[\s_-]+", " ", text.strip()).lower()


def _named(field: str, value: str) -> Predicate:
    """Match a status or type by id, or by name ignoring case and ``_``/``-``/space."""
    wanted = _normalize(value)
    id_key = ID_KEYS[field]

    def named(record: Record) -> bool:
        if record.get(id_key) == value:
            return True
        name = record[field]
        return isinstance(name, str) and _normalize(name) == wanted

    return named


def _compare(field: str, op: str, value: str) -> Predicate:
    if field in ID_KEYS and op in ("==", "!="):
        named = _named(field, value)
        return named if op == "==" else _negate(named)
    if op == "~":
        needle = value.lower()
        return lambda record: needle in (record[field] or "").lower()
    if op == "==":
        return lambda record: record[field] == value
    return lambda record: record[field] != value


def _member(field: str, values: list[str], negated: bool) -> Predicate:
    if field in ID_KEYS:
        predicates = [_named(field, value) for value in values]
        return _negate(_any_of(predicates)) if negated else _any_of(predicates)
    options = frozenset(values)
    if negated:
        return lambda record: record[field] not in options
    return lambda record: record[field] in options


def _labels(record: Record, field: str) -> list[str]:
    value = record[field]
    return value if isinstance(value, list) else []


def _has_all(field: str, values: list[str], negated: bool) -> Predicate:
    def has_all(record: Record) -> bool:
        present = _labels(record, field)
        return all(value in present for value in values) != negated

    return has_all


def _has_any(field: str, values: list[str], negated: bool) -> Predicate:
    def has_any(record: Record) -> bool:
        present = _labels(record, field)
        return any(value in present for value in values) != negated

    return has_any


def _label_contains_text(field: str, text: str) -> Predicate:
    needle = text.lower()
    return lambda record: any(
        needle in label.lower() for label in _labels(record, field)
    )


def _empty(field: str, negated: bool) -> Predicate:
    def is_empty(record: Record) -> bool:
        value = record[field]
        if isinstance(value, list):
            empty = not value
        else:
            empty = value is None or not value.strip()
        return empty != negated

    return is_empty


def _any_of(predicates: list[Predicate]) -> Predicate:
    return lambda record: any(predicate(record) for predicate in predicates)


def _all_of(predicates: list[Predicate]) -> Predicate:
    return lambda record: all(predicate(record) for predicate in predicates)


def _negate(predicate: Predicate) -> Predicate:
    return lambda record: not predicate(record)
