"""Iterate over extracted docx content.

:author: Shay Hill
:created: 6/28/2019

This package extracts docx text as::

    [  # tables (full document contents)
        [  # table
            [  # row
                [  # cell
                    "" or [""] or Par # paragraph
                ]
            ]
        ]
    ]

These functions help manipulate that deep nest without deep indentation.

"""

from __future__ import annotations

import copy
from typing import (
    Any,
    Iterable,
    Iterator,
    List,
    Literal,
    TypeVar,
    Union,
    cast,
    overload,
)

TablesList = List[List[List[List[Any]]]]

# A collapsed TablesList
CollTL = List[Union[str, "CollTL"]]


_T = TypeVar("_T")
_U = TypeVar("_U")

IndexedItem = str

TextTable = List[List[List[List[List[str]]]]]


# TODO: remove depth argument from join_leaves. Make it join_runs
def join_leaves(
    joint: str, str_tree: CollTL, to_depth: int, _depth: int = 0
) -> CollTL | str:
    """Join the leaves of a nested list of strings at a certain depth.

    :param joint: string to join leaves
    :param str_tree: a nested list of strings with all strings at the same depth
    :param to_depth: depth at which to join strings. This has to be explicit, because
        all strings are at the same depth, but this depth cannot necessarily be
        inferred, because the tree may have no leaves at all. The `to_depth` argument
        is the depth the tree will be collapsed TO. So, if `to_depth` is 0, the tree
        will be collapsed to a single string. If `to_depth` is 1, the tree will be
        collapsed to a list of strings. If `to_depth` is 2, the tree will be
        collapsed to a list of lists of strings, etc.

        You can only collapse one depth, and that depth must be explicated. Remember
        that in a tree, the depth is the shortest path from the root to a leaf. So
        the top node is at depth 0, its children are at depth 1, their children are
        at depth 2, etc.
    :param _depth: for recursion. Do not enter this argument.

    The most common use in this project will be to collapse nested lists of runs into
    nested lists of paragraphs.

    runs = [
        [
            [
                [
                    [
                        "run1", "run2"
                    ],
                    [
                        "run3", "run4"
                    ]
                ]
            ]
        ]
    ]

    `_join_leaves("", runs, 3)` =>

    [
        [
            [
                [
                    "run1run2",
                    "run3run4"
                ]
            ]
        [
    ]
    """
    if _depth == to_depth:
        return joint.join(cast(List[str], str_tree))
    return [join_leaves(joint, cast(CollTL, b), to_depth, _depth + 1) for b in str_tree]


@overload
def enum_at_depth(
    nested: Iterable[_T], depth: Literal[1]
) -> Iterator[tuple[tuple[int,], _T]]:
    ...


@overload
def enum_at_depth(
    nested: Iterable[Iterable[_T]], depth: Literal[2]
) -> Iterator[tuple[tuple[int, int], _T]]:
    ...


@overload
def enum_at_depth(
    nested: Iterable[Iterable[Iterable[_T]]], depth: Literal[3]
) -> Iterator[tuple[tuple[int, int, int], _T]]:
    ...


@overload
def enum_at_depth(
    nested: Iterable[Iterable[Iterable[Iterable[_T]]]], depth: Literal[4]
) -> Iterator[tuple[tuple[int, int, int, int], _T]]:
    ...


@overload
def enum_at_depth(
    nested: Iterable[Iterable[Iterable[Iterable[Iterable[_T]]]]], depth: Literal[5]
) -> Iterator[tuple[tuple[int, int, int, int, int], _T]]:
    ...


def enum_at_depth(
    nested: (
        Iterable[_T]
        | Iterable[Iterable[_T]]
        | Iterable[Iterable[Iterable[_T]]]
        | Iterable[Iterable[Iterable[Iterable[_T]]]]
        | Iterable[Iterable[Iterable[Iterable[Iterable[_T]]]]]
    ),
    depth: Literal[1, 2, 3, 4, 5],
) -> (
    Iterator[tuple[tuple[int,], _T]]
    | Iterator[tuple[tuple[int, int], _T]]
    | Iterator[tuple[tuple[int, int, int], _T]]
    | Iterator[tuple[tuple[int, int, int, int], _T]]
    | Iterator[tuple[tuple[int, int, int, int, int], _T]]
):
    """Enumerate over a nested sequence at depth.

    :param nested: a (nested) sequence
    :param depth: depth of iteration

        * ``1`` => ``((i,), nested[i])``
        * ``2`` => ``((i, j), nested[:][j])``
        * ``3`` => ``((i, j, k), nested[:][:][k])``
        * ...

    :return: tuples (tuple "address", item)
    :raise ValueError: if depth is less than 1 or more than 5. These hard limits (and
        very not-dry function) are how I return nice types and keep python 3.8
        compatibility. There are the only depths you will need for the return types
        in this project.

    >>> sequence = [
    ...     [[["a", "b"], ["c"]], [["d", "e"]]],
    ...     [[["f"], ["g", "h"]]]
    ... ]

    >>> for x in enum_at_depth(sequence, 1): print(x)
    ((0,), [[['a', 'b'], ['c']], [['d', 'e']]])
    ((1,), [[['f'], ['g', 'h']]])

    >>> for x in enum_at_depth(sequence, 2): print(x)
    ((0, 0), [['a', 'b'], ['c']])
    ((0, 1), [['d', 'e']])
    ((1, 0), [['f'], ['g', 'h']])

    >>> for x in enum_at_depth(sequence, 3): print(x)
    ((0, 0, 0), ['a', 'b'])
    ((0, 0, 1), ['c'])
    ((0, 1, 0), ['d', 'e'])
    ((1, 0, 0), ['f'])
    ((1, 0, 1), ['g', 'h'])

    >>> for x in enum_at_depth(sequence, 4): print(x)
    ((0, 0, 0, 0), 'a')
    ((0, 0, 0, 1), 'b')
    ((0, 0, 1, 0), 'c')
    ((0, 1, 0, 0), 'd')
    ((0, 1, 0, 1), 'e')
    ((1, 0, 0, 0), 'f')
    ((1, 0, 1, 0), 'g')
    ((1, 0, 1, 1), 'h')
    """
    if depth == 1:
        nested = cast(List[_T], nested)
        yield from (((i,), x) for i, x in enumerate(nested))
        return
    if depth == 2:
        nested = cast(List[List[_T]], nested)
        depth_minus_one = depth - 1
        for i, x in enumerate(nested):
            for j, y in enum_at_depth(x, depth_minus_one):
                yield ((i, *j), y)
    elif depth == 3:
        nested = cast(List[List[List[_T]]], nested)
        depth_minus_one = depth - 1
        for i, x in enumerate(nested):
            for j, y in enum_at_depth(x, depth_minus_one):
                yield ((i, *j), y)
    elif depth == 4:
        nested = cast(List[List[List[List[_T]]]], nested)
        depth_minus_one = depth - 1
        for i, x in enumerate(nested):
            for j, y in enum_at_depth(x, depth_minus_one):
                yield ((i, *j), y)
    elif depth == 5:
        nested = cast(List[List[List[List[List[_T]]]]], nested)
        depth_minus_one = depth - 1
        for i, x in enumerate(nested):
            for j, y in enum_at_depth(x, depth_minus_one):
                yield ((i, *j), y)
    else:
        msg = "depth argument must be 1, 2, 3, 4, or 5"
        raise ValueError(msg)


@overload
def iter_at_depth(nested: Iterable[_T], depth: Literal[1]) -> Iterator[_T]:
    ...


@overload
def iter_at_depth(nested: Iterable[Iterable[_T]], depth: Literal[2]) -> Iterator[_T]:
    ...


@overload
def iter_at_depth(
    nested: Iterable[Iterable[Iterable[_T]]], depth: Literal[3]
) -> Iterator[_T]:
    ...


@overload
def iter_at_depth(
    nested: Iterable[Iterable[Iterable[Iterable[_T]]]], depth: Literal[4]
) -> Iterator[_T]:
    ...


@overload
def iter_at_depth(
    nested: Iterable[Iterable[Iterable[Iterable[Iterable[_T]]]]], depth: Literal[5]
) -> Iterator[_T]:
    ...


def iter_at_depth(
    nested: (
        Iterable[_T]
        | Iterable[Iterable[_T]]
        | Iterable[Iterable[Iterable[_T]]]
        | Iterable[Iterable[Iterable[Iterable[_T]]]]
        | Iterable[Iterable[Iterable[Iterable[Iterable[_T]]]]]
    ),
    depth: Literal[1, 2, 3, 4, 5],
) -> Iterator[_T]:
    """Iterate over a nested sequence at depth.

    :param nested: a (nested) sequence
    :param depth: depth of iteration

        * ``1`` => ``nested[i]``
        * ``2`` => ``nested[:][j]``
        * ``3`` => ``nested[:][:][k]``
        * ...

    :return: sub-sequences or items in nested
    :raise ValueError: if depth is less than 1 or more than 5.

    >>> sequence = [
    ...     [[["a", "b"], ["c"]], [["d", "e"]]],
    ...     [[["f"], ["g", "h"]]]
    ... ]

    >>> for x in iter_at_depth(sequence, 1): print(x)
    [[['a', 'b'], ['c']], [['d', 'e']]]
    [[['f'], ['g', 'h']]]

    >>> for x in iter_at_depth(sequence, 2): print(x)
    [['a', 'b'], ['c']]
    [['d', 'e']]
    [['f'], ['g', 'h']]

    >>> for x in iter_at_depth(sequence, 3): print(x)
    ['a', 'b']
    ['c']
    ['d', 'e']
    ['f']
    ['g', 'h']

    >>> list(iter_at_depth(sequence, 4))
    ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    """
    if depth == 1:
        nested = cast(List[_T], nested)
        return (x for _, x in enum_at_depth(nested, depth))
    if depth == 2:
        nested = cast(List[List[_T]], nested)
        return (x for _, x in enum_at_depth(nested, depth))
    if depth == 3:
        nested = cast(List[List[List[_T]]], nested)
        return (x for _, x in enum_at_depth(nested, depth))
    if depth == 4:
        nested = cast(List[List[List[List[_T]]]], nested)
        return (x for _, x in enum_at_depth(nested, depth))
    if depth == 5:
        nested = cast(List[List[List[List[List[_T]]]]], nested)
        return (x for _, x in enum_at_depth(nested, depth))
    msg = "depth argument must be 1, 2, 3, 4, or 5"
    raise ValueError(msg)


def iter_tables(tables: Iterable[_T]) -> Iterator[_T]:
    """Iterate over ``tables[i]``

    Analog of iter_at_depth(tables, 1)

    :param tables: ``[[[[Par]]]]``
    :return: ``tables[0], tables[1], ... tables[i]``
    """
    return iter_at_depth(tables, 1)


def iter_rows(tables: Iterable[Iterable[_T]]) -> Iterator[_T]:
    """Iterate over ``tables[:][j]``

    Analog of iter_at_depth(tables, 2)

    :param tables: ``[[[[Par]]]]``
    :return: ``tables[0][0], tables[0][1], ... tables[i][j]``
    """
    return iter_at_depth(tables, 2)


def iter_cells(tables: Iterable[Iterable[Iterable[_T]]]) -> Iterator[_T]:
    """Iterate over ``tables[:][:][k]``

    Analog of iter_at_depth(tables, 3)

    :param tables: ``[[[[Par]]]]``
    :return: ``tables[0][0][0], tables[0][0][1], ... tables[i][j][k]``
    """
    return iter_at_depth(tables, 3)


def iter_paragraphs(tables: Iterable[Iterable[Iterable[Iterable[_T]]]]) -> Iterator[_T]:
    """Iterate over ``tables[:][:][:][l]``

    Analog of iter_at_depth(tables, 4)

    :param tables: ``[[[[Par]]]]``
    :return: ``tables[0][0][0][0], tables[0][0][0][1], ... tables[i][j][k][l]``
    """
    return iter_at_depth(tables, 4)


def enum_tables(tables: Iterable[_T]) -> Iterator[tuple[tuple[int], _T]]:
    """Enumerate over ``tables[i]``

    Analog of enum_at_depth(tables, 1)

    :param tables: ``[[[[Par]]]]``
    :return:
        ``((0, ), tables[0]) ... , ((i, ), tables[i])``
    """
    return enum_at_depth(tables, 1)


def enum_rows(tables: Iterable[Iterable[_T]]) -> Iterator[tuple[tuple[int, int], _T]]:
    """Enumerate over ``tables[:][j]``

    Analog of enum_at_depth(tables, 2)

    :param tables: ``[[[[Par]]]]``
    :return:
        ``((0, 0), tables[0][0]) ... , ((i, j), tables[i][j])``
    """
    return enum_at_depth(tables, 2)


def enum_cells(
    tables: Iterable[Iterable[Iterable[_T]]],
) -> Iterator[tuple[tuple[int, int, int], _T]]:
    """Enumerate over ``tables[:][:][k]``

    Analog of enum_at_depth(tables, 3)

    :param tables: ``[[[[Par]]]]``
    :return:
        ``((0, 0, 0), tables[0][0][0]) ... , ((i, j, k), tables[i][j][k])``
    """
    return enum_at_depth(tables, 3)


def enum_paragraphs(
    tables: Iterable[Iterable[Iterable[Iterable[_T]]]],
) -> Iterator[tuple[tuple[int, int, int, int], _T]]:
    """Enumerate over ``tables[:][:][:][l]``

    Analog of enum_at_depth(tables, 4)

    :param tables: ``[[[[Par]]]]``
    :return:
        ``((0, 0, 0, 0), tables[0][0][0][0]) ... , ((i, j, k, l), tables[i][j][k][l])``
    """
    return enum_at_depth(tables, 4)


# TODO: track down callers for html map and see if they are calling with runs or pars
def get_html_map(tables: TextTable) -> str:
    """Create a visual map in html format.

    :param tables: ``[[[[["str"]]]]]``
    :return: html to show all strings with index tuples

    Create an html string that can be rendered in a browser to show the relative
    location and index tuple of every paragraph in the document.

    * Each table will be a grid of cell boxes, outlined in black. * Each paragraph
    will be prepended with an index tuple. (e.g., ``[[[['text']]]]`` will appear as
    ``(0, 0, 0, 0) text``.
    """
    # prepend index tuple to each paragraph
    tables_4deep = cast(List[List[List[List[str]]]], copy.deepcopy(tables))
    for (i, j, k, m), paragraph in enum_at_depth(tables, 4):
        par_text = "".join(paragraph)
        tables_4deep[i][j][k][m] = " ".join([str((i, j, k, m)), par_text])

    # wrap each paragraph in <pre> tags
    tables_3deep = cast(List[List[List[str]]], tables_4deep)
    for (i, j, k), cell in enum_at_depth(tables_4deep, 3):
        cell_strs = (str(x) for x in cell)
        tables_3deep[i][j][k] = "".join([f"<pre>{x}</pre>" for x in cell_strs])

    # wrap each cell in <td> tags
    tables_2deep = cast(List[List[str]], tables_3deep)
    for (i, j), row in enum_at_depth(tables_3deep, 2):
        tables_2deep[i][j] = "".join([f"<td>{x}</td>" for x in row])

    # wrap each row in <tr> tags
    tables_1deep = cast(List[str], tables_2deep)
    for (i,), table in enum_at_depth(tables_2deep, 1):
        tables_1deep[i] = "".join(f"<tr>{x}</tr>" for x in table)

    # wrap each table in <table> tags
    tables_ = "".join([f'<table border="1">{x}</table>' for x in tables_1deep])

    return "<html><body>" + tables_ + "</body></html>"
