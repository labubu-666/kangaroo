from kangaroo.templates import DEFAULT_TEMPLATE_NAME, TEMPLATES, TO_DO_LIST


def test_default_template_is_to_do_list():
    assert DEFAULT_TEMPLATE_NAME == "To Do List"
    assert TEMPLATES[DEFAULT_TEMPLATE_NAME] is TO_DO_LIST


def test_to_do_list_matches_current_setup():
    """The template reproduces today's fixed statuses and types."""
    assert [(t.name, t.level, t.position) for t in TO_DO_LIST.types] == [
        ("Task", "standard", 0),
        ("Subtask", "subtask", 1),
    ]
    assert [(s.name, s.category, s.position) for s in TO_DO_LIST.statuses] == [
        ("Open", "todo", 0),
        ("In Progress", "in_progress", 1),
        ("Done", "done", 2),
    ]


def test_to_do_list_has_no_transitions():
    """With no transitions, any status can move to any other."""
    assert TO_DO_LIST.transitions == ()
