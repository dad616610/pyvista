"""Generic array-like type definitions.

Definitions here are loosely based on code in numpy._typing._array_like.
Some key differences include:

- Some npt._array_like definitions explicitly support dual-types for
  handling python and numpy scalar data types separately.
  Here, only a single generic type is used for simplicity.

- The npt._array_like definitions use a recursive _NestedSequence protocol.
  Here, finite sequences are used instead.

- The npt._array_like definitions use a generic _SupportsArray protocol.
  Here, we use `ndarray` directly.

- The npt._array_like definitions include scalar types (e.g. float, int).
  Here they are excluded (i.e. scalars are not considered to be arrays).

- The npt._array_like TypeVar is bound to np.generic. Here, the
  TypeVar is bound to a subset of numeric types only.

"""

import sys
import typing
from typing import TYPE_CHECKING, Any, List, Sequence, Tuple, TypeVar, Union

import numpy as np
import numpy.typing as npt

# Create alias of npt.NDArray bound to numeric types only
# TODO: remove # type: ignore once support for 3.8 is dropped
_NumberUnion = Union[np.floating, np.integer, np.bool_, float, int, bool]  # type: ignore[type-arg]
_NumberType = TypeVar(
    '_NumberType',
    bound=Union[np.floating, np.integer, np.bool_, float, int, bool],  # type: ignore[type-arg]
)
__NumberType = TypeVar(
    '__NumberType',
    bound=Union[np.floating, np.integer, np.bool_, float, int, bool],  # type: ignore[type-arg]
)
_PyNumberType = TypeVar('_PyNumberType', float, int, bool)
_NpNumberType = TypeVar('_NpNumberType', np.float64, np.int_, np.bool_)

_T = TypeVar('_T')
if not TYPE_CHECKING and sys.version_info < (3, 9, 0):
    # TODO: Remove this conditional block once support for 3.8 is dropped

    # Numpy's type annotations use a customized generic alias type for
    # python < 3.9.0 (defined in numpy.typing._generic_alias._GenericAlias)
    # which makes it incompatible with built-in generic alias types, e.g.
    # Sequence[NDArray[T]]. As a workaround, we define NDArray types using
    # the private typing._GenericAlias type instead
    np_dtype = typing._GenericAlias(np.dtype, _NumberType)
    _np_floating = typing._GenericAlias(np.floating, _T)
    _np_integer = typing._GenericAlias(np.integer, _T)
    np_dtype_floating = typing._GenericAlias(np.dtype, _np_floating[_T])
    np_dtype_integer = typing._GenericAlias(np.dtype, _np_integer[_T])
    NumpyArray = typing._GenericAlias(np.ndarray, (Any, np_dtype[_NumberType]))
else:
    np_dtype = np.dtype[_NumberType]
    np_dtype_floating = np.dtype[np.floating[Any]]
    np_dtype_integer = np.dtype[np.integer[Any]]
    NumpyArray = npt.NDArray[_NumberType]

_FiniteNestedList = Union[
    List[_NumberType],
    List[List[_NumberType]],
    List[List[List[_NumberType]]],
    List[List[List[List[_NumberType]]]],
]

_FiniteNestedTuple = Union[
    Tuple[_NumberType],
    Tuple[Tuple[_NumberType]],
    Tuple[Tuple[Tuple[_NumberType]]],
    Tuple[Tuple[Tuple[Tuple[_NumberType]]]],
]

_ArrayLike1D = Union[
    NumpyArray[_NumberType],
    Sequence[_NumberType],
    Sequence[NumpyArray[_NumberType]],
]
_ArrayLike2D = Union[
    NumpyArray[_NumberType],
    Sequence[Sequence[_NumberType]],
    Sequence[Sequence[NumpyArray[_NumberType]]],
]
_ArrayLike3D = Union[
    NumpyArray[_NumberType],
    Sequence[Sequence[Sequence[_NumberType]]],
    Sequence[Sequence[Sequence[NumpyArray[_NumberType]]]],
]
_ArrayLike4D = Union[
    NumpyArray[_NumberType],
    Sequence[Sequence[Sequence[Sequence[_NumberType]]]],
    Sequence[Sequence[Sequence[Sequence[NumpyArray[_NumberType]]]]],
]
_ArrayLike = Union[
    _ArrayLike1D[_NumberType],
    _ArrayLike2D[_NumberType],
    _ArrayLike3D[_NumberType],
    _ArrayLike4D[_NumberType],
]

_ArrayLikeOrScalar = Union[_NumberType, _ArrayLike[_NumberType]]
