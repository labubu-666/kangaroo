import pytest

from kangaroo.errors import InvalidFilterError
from kangaroo.filters import parse_filter

RECORD = {
    "title": "Fix login bug",
    "description": None,
    "status": "Open",
    "status_id": "s-0",
    "statusCategory": "todo",
    "type": "Task",
    "type_id": "t-0",
    "typeLevel": "standard",
    "parent_id": None,
    "project.id": "p1",
    "project.name": "foo",
    "labels": [],
    "trashed": "false",
}


def matches(text, **overrides):
    return parse_filter(text)({**RECORD, **overrides})


def test_blank_filter_matches_everything():
    assert matches(None)
    assert matches("   ")


def test_equality_on_project_name():
    assert matches("project.name == 'foo'")
    assert not matches("project.name == 'bar'")


def test_double_quotes_and_not_equal():
    assert matches('status != "done"')
    assert not matches('status != "open"')


def test_substring_is_case_insensitive():
    assert matches("title ~ 'LOGIN'")
    assert not matches("title ~ 'signup'")


def test_null_field_does_not_match_substring():
    assert not matches("description ~ 'x'")


def test_in_and_not_in_lists():
    assert matches("status in ['open', 'in_progress']")
    assert not matches("status in []")
    assert matches("status not in ['done']")
    assert not matches("status not in ['open']")


def test_and_or_not_with_precedence():
    assert matches("project.name == 'foo' and status == 'open'")
    assert matches("project.name == 'bar' or status == 'open'")
    # "and" binds tighter than "or": false and true or true -> true
    assert matches("project.name == 'bar' and status == 'done' or type == 'task'")
    assert matches("not project.name == 'bar'")
    assert matches("type == 'task' and (title ~ 'bug' or status == 'done')")
    assert not matches("type == 'subtask' and (title ~ 'bug' or status == 'open')")


LABELED = {"labels": ["derstandard", "derstandard:3000000344207", "news"]}


def test_contains_one_label_is_exact():
    """contains matches a whole label, so 'derstandard' does not match a longer one."""
    assert matches("labels contains 'derstandard'", **LABELED)
    assert not matches("labels contains 'derstand'", **LABELED)
    assert not matches("labels contains 'politik'", **LABELED)
    assert matches("labels not contains 'politik'", **LABELED)
    assert not matches("labels not contains 'news'", **LABELED)


def test_contains_list_means_all_of_them():
    """A list in contains means the item must have every label in the list."""
    assert matches("labels contains ['derstandard', 'news']", **LABELED)
    assert not matches("labels contains ['derstandard', 'politik']", **LABELED)
    assert matches("labels not contains ['derstandard', 'politik']", **LABELED)
    assert not matches("labels not contains ['derstandard', 'news']", **LABELED)


def test_in_on_labels_means_any_of_them():
    """in on a list field matches when any listed label is present."""
    assert matches("labels in ['politik', 'news']", **LABELED)
    assert not matches("labels in ['politik', 'sport']", **LABELED)
    assert matches("labels not in ['politik', 'sport']", **LABELED)
    assert not matches("labels not in ['politik', 'news']", **LABELED)


def test_tilde_on_labels_matches_any_label_text():
    """~ on a list field is a case-insensitive substring match on any label."""
    assert matches("labels ~ 'DERSTANDARD:'", **LABELED)
    assert not matches("labels ~ 'kurier'", **LABELED)


def test_is_empty_for_lists_and_text():
    """is empty works for list fields and for blank or missing text."""
    assert matches("labels is empty", labels=[])
    assert not matches("labels is empty", **LABELED)
    assert matches("labels is not empty", **LABELED)
    assert matches("description is empty")
    assert matches("description is empty", description="   ")
    assert not matches("title is empty")
    assert matches("title is not empty")


def test_labels_combine_with_other_fields():
    """List conditions combine with text conditions and grouping."""
    assert matches(
        "labels contains 'derstandard' and (status == 'open' or type == 'subtask')",
        **LABELED,
    )
    assert not matches("labels contains 'derstandard' and status == 'done'", **LABELED)
    assert matches("not labels contains 'politik'", **LABELED)


def test_list_fields_reject_equality():
    """== and != are not allowed on list fields, with a helpful message."""
    with pytest.raises(InvalidFilterError, match="use 'contains' or 'in'"):
        parse_filter("labels == 'news'")
    with pytest.raises(InvalidFilterError, match="use 'contains' or 'in'"):
        parse_filter("labels != 'news'")


def test_contains_rejects_text_fields():
    """contains is only for list fields, so it is rejected on text fields."""
    with pytest.raises(InvalidFilterError, match="only works on list fields"):
        parse_filter("title contains 'bug'")


def test_trashed_compares_true_and_false():
    """trashed is a true/false field, written without quotes."""
    assert matches("trashed == false")
    assert not matches("trashed == true")
    assert matches("trashed != true")
    assert matches("trashed == true", trashed="true")
    assert not matches("trashed == false", trashed="true")


@pytest.mark.parametrize(
    "text",
    [
        "trashed == 'true'",
        "trashed == yes",
        "trashed ~ 'tru'",
        "trashed contains 'true'",
        "trashed",
        "project.name = 'foo'",
        "unknown == 'x'",
        "status == open",
        "status in ['open'",
        "status == 'open' and",
        "(status == 'open'",
        "status == 'open')",
        "status 'open'",
        "project.name == 'foo' #",
        "labels contains",
        "labels is maybe empty",
        "title is empty extra",
    ],
)
def test_invalid_filters_raise(text):
    with pytest.raises(InvalidFilterError):
        parse_filter(text)


NAMED = {
    "status": "In Progress",
    "status_id": "s-1",
    "statusCategory": "in_progress",
    "type": "Bug Report",
    "type_id": "t-1",
    "typeLevel": "standard",
}


@pytest.mark.parametrize(
    "value", ["In Progress", "in progress", "in_progress", "in-progress", "IN_PROGRESS"]
)
def test_status_matches_name_ignoring_case_and_separators(value):
    assert matches(f"status == '{value}'", **NAMED)
    assert not matches(f"status != '{value}'", **NAMED)


def test_status_and_type_match_by_id():
    assert matches("status == 's-1'", **NAMED)
    assert matches("type == 't-1'", **NAMED)
    assert not matches("status == 's-2'", **NAMED)


def test_type_matches_name_with_any_separator():
    assert matches("type == 'bug_report'", **NAMED)
    assert matches("type == 'bug-report'", **NAMED)
    assert not matches("type == 'bug'", **NAMED)


def test_status_in_and_not_in_use_names_and_ids():
    assert matches("status in ['open', 'in-progress']", **NAMED)
    assert matches("status in ['s-1']", **NAMED)
    assert not matches("status in ['open', 'done']", **NAMED)
    assert matches("status not in ['open', 'done']", **NAMED)
    assert not matches("status not in ['in_progress']", **NAMED)


def test_status_category_and_type_level_are_exact_fields():
    assert matches("statusCategory == 'in_progress'", **NAMED)
    assert not matches("statusCategory == 'done'", **NAMED)
    assert matches("typeLevel == 'standard'", **NAMED)
    assert matches("typeLevel != 'subtask'", **NAMED)
    assert matches("statusCategory in ['todo', 'in_progress']", **NAMED)


def test_status_substring_still_works():
    assert matches("status ~ 'progress'", **NAMED)
