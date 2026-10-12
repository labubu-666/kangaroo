# Filter language

A filter chooses which work items to show. A board's filter only considers
work items in the board's own project. Leave the filter empty to show every
work item in the project.

Statuses and types belong to a project, so a status or type name only means
something inside one project. Two projects can each have a status called
"In Progress" with different IDs. Filter on `project.id` whenever you filter on
a status or type (see [Status and type in a project](#status-and-type-in-a-project)).

## Example

```
labels contains 'derstandard' and statusCategory != 'done'
```

## Values

- Text values are quoted with single or double quotes: `'Open'` or `"Open"`.
- A list is written in square brackets: `['Open', 'In Progress']`.
- `true` and `false` are written without quotes.

## Fields

| Field            | Type    | Notes                              |
| ---------------- | ------- | ---------------------------------- |
| `title`          | text    |                                    |
| `description`    | text    | Empty when missing or blank        |
| `status`         | text    | The status name, or its ID         |
| `statusCategory` | text    | `todo`, `in_progress` or `done`    |
| `type`           | text    | The type name, or its ID           |
| `typeLevel`      | text    | `standard` or `subtask`            |
| `parent_id`      | text    | The parent's ID. Empty for tasks   |
| `project.id`     | text    |                                    |
| `project.name`   | text    |                                    |
| `labels`         | list    | The labels on the work item        |
| `trashed`        | boolean | `true` or `false`                  |

`status` and `type` accept either the name or the ID of a status or type. Names
ignore case, and `_`, `-` and spaces count as the same, so
`status == 'in_progress'`, `status == 'In Progress'` and `status == 'in-progress'`
all match the status named "In Progress". Use `statusCategory` to match every
status in a category, whatever the status is called.

A name that matches no status is not an error. The filter simply matches no
items. Use `statusCategory` or an ID when the name might differ between projects.

`typeLevel` tells standard items (`standard`) from subtasks (`subtask`), whatever
their types are called.

## Operators on text fields

| Filter                              | Matches when                               |
| ----------------------------------- | ------------------------------------------ |
| `status == 'Open'`                  | the value is exactly the same              |
| `status != 'Open'`                  | the value is different                     |
| `title ~ 'bug'`                     | the value contains the text, ignoring case |
| `status in ['Open', 'In Progress']` | the value is one of the listed values      |
| `status not in ['Done']`            | the value is none of the listed values     |

`contains` is not allowed on text fields. Use `~` instead.

## Operators on list fields

A list field such as `labels` has its own operators. `==` and `!=` are not
allowed on list fields, because an exact match on a whole list is rarely what
you want.

| Filter                           | Matches when                               |
| -------------------------------- | ------------------------------------------ |
| `labels contains 'a'`            | the item has label `a`                     |
| `labels contains ['a', 'b']`     | the item has **all** of the labels         |
| `labels not contains 'a'`        | the item does not have label `a`           |
| `labels not contains ['a', 'b']` | the item is missing **at least one** label |
| `labels in ['a', 'b']`           | the item has **any** of the labels         |
| `labels not in ['a', 'b']`       | the item has **none** of the labels        |
| `labels ~ 'derstandard:'`        | any label contains the text, ignoring case |
| `labels is empty`                | the item has no labels                     |
| `labels is not empty`            | the item has at least one label            |

Note the difference between `contains [...]` (all of the values) and `in [...]`
(any of the values).

`contains` matches a whole label. `labels contains 'derstand'` does not match a
label called `derstandard`. Use `~` for partial matches.

## Empty values

`is empty` and `is not empty` work on every field:

- A list is empty when it has no items.
- A text field is empty when it is missing or contains only spaces.

```
description is empty
labels is not empty
```

## Combining conditions

- `and`, `or` and `not` combine conditions.
- Parentheses group conditions.
- `not` binds tightest, then `and`, then `or`. So `a or b and c` means
  `a or (b and c)`.

```
labels contains 'derstandard' and (status == 'Open' or typeLevel == 'subtask')
not labels contains 'sport'
```

## Errors

Invalid filters are rejected with a 422 error that explains the problem:

| Filter                 | Error                                    |
| ---------------------- | ---------------------------------------- |
| `labels == 'news'`     | 'labels' is a list field: use 'contains' or 'in' instead of '==' |
| `title contains 'bug'` | 'contains' only works on list fields, not 'title' |
| `unknown == 'x'`       | Unknown field 'unknown'                  |
| `status == open`       | Expected a quoted string, got 'open'      |

## Work item lists

The work item list uses the same language. Trashed items are included unless
the filter leaves them out:

```
trashed == false
```

Use `trashed == true` to see only trashed items.

## Status and type in a project

The list page's status picker only appears when the filter names one project.
Its choices are that project's statuses. Choosing one adds a `status` condition
to the filter, next to the project condition, with the status's ID:

```
project.id == '01a1…' and status == '01a2…'
```

Choosing "All statuses" removes the `status` condition and keeps the rest of the
filter. The picker never adds a status to a filter without a project, so a status
can't match across projects through the picker.

By hand, you can write the status by name instead of ID, as long as the filter
also names the project:

```
project.id == '01a1…' and status == 'In Progress'
```

A status name in a filter without `project.id` can match statuses in any
project that share the name. Prefer `statusCategory` for cross-project lists.

## Examples

| Board shows                                         | Filter                                       |
| --------------------------------------------------- | -------------------------------------------- |
| Articles imported from derStandard                  | `labels contains 'derstandard'`              |
| Open items with a bug in the title                  | `status == 'Open' and title ~ 'bug'`         |
| Items tagged with both `derstandard` and `politik`  | `labels contains ['derstandard', 'politik']` |
| Items tagged with either `derstandard` or `politik` | `labels in ['derstandard', 'politik']`       |
| Items with no label                                 | `labels is empty`                            |
| Items still to start, in any project                | `statusCategory == 'todo'`                   |
| Items in progress in one project                    | `project.id == '01a1…' and statusCategory == 'in_progress'` |
| Subtasks only                                       | `typeLevel == 'subtask'`                     |
| Items in one project's "In Progress" status         | `project.id == '01a1…' and status == 'In Progress'` |

The operators work on every field in the table above.
