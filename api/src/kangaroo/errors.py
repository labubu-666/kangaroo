"""Domain errors shared by the repositories, the service layer and the app.

All of them subclass ValueError so code that catches ValueError keeps working.
"""


class NotFoundError(ValueError):
    """A work item, project or board with the given ID does not exist."""


class ConflictError(ValueError):
    """The action would break a rule, such as deleting something that still has children."""


class InvalidReferenceError(ValueError):
    """The request refers to a project or parent that is missing or not allowed."""


class InvalidFilterError(ValueError):
    """A board filter is not valid filter syntax."""


class InvalidSortError(ValueError):
    """A sort field is not one the list can be sorted by."""


class InvalidTemplateError(ValueError):
    """The project template name does not match any template."""


class InvalidBackupError(ValueError):
    """The uploaded file is not a valid backup of this schema."""
