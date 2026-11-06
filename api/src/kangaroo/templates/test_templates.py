from kangaroo.templates import (
    DEFAULT_TEMPLATE_NAME,
    SOFTWARE_PROJECT,
    TEMPLATES,
    TO_DO_LIST,
)


def test_default_template_is_to_do_list():
    assert DEFAULT_TEMPLATE_NAME == "To Do List"
    assert TEMPLATES[DEFAULT_TEMPLATE_NAME] is TO_DO_LIST


def test_to_do_list_matches_current_setup():
    """The template reproduces today's fixed statuses and types."""
    assert [(t.name, t.position) for t in TO_DO_LIST.types] == [("Task", 0)]
    assert [(s.name, s.category, s.position) for s in TO_DO_LIST.statuses] == [
        ("To do", "todo", 0),
        ("In Progress", "in_progress", 1),
        ("Done", "done", 2),
    ]


def test_to_do_list_has_no_transitions():
    """With no transitions, any status can move to any other."""
    assert TO_DO_LIST.transitions == ()


def test_software_project_is_registered():
    assert TEMPLATES[SOFTWARE_PROJECT.name] is SOFTWARE_PROJECT


def test_software_project_statuses():
    assert [(s.name, s.category, s.position) for s in SOFTWARE_PROJECT.statuses] == [
        ("Open", "todo", 0),
        ("To do", "todo", 1),
        ("In progress", "in_progress", 2),
        ("Review", "in_progress", 3),
        ("Done", "done", 4),
        ("Won't do", "done", 5),
    ]
