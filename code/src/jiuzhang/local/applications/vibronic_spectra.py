"""Local molecular vibronic-spectra application helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.local.applications._deps import optional_dependency

__all__ = [
    "FormicAcidData",
    "VibronicParameters",
    "load_formic_acid",
    "sample_vibronic_spectrum",
    "vibronic_energies",
    "vibronic_parameters",
]


@dataclass(frozen=True)
class FormicAcidData:
    """Formic-acid molecular data for local vibronic-spectrum demos."""

    ground_frequencies: npt.NDArray[np.float64]
    excited_frequencies: npt.NDArray[np.float64]
    duschinsky_matrix: npt.NDArray[np.float64]
    displacement: npt.NDArray[np.float64]
    _backend_data: Any


@dataclass(frozen=True)
class VibronicParameters:
    """GBS parameters derived from molecular vibronic data."""

    temperature_factors: npt.NDArray[np.float64]
    interferometer_1: npt.NDArray[np.complex128]
    squeezing: npt.NDArray[np.float64]
    interferometer_2: npt.NDArray[np.complex128]
    displacement: npt.NDArray[np.complex128]


def load_formic_acid() -> FormicAcidData:
    """Load bundled formic-acid molecular data.

    Returns:
        Frequencies, Duschinsky matrix, displacement vector, and private data
        source used by local vibronic calculations.
    """
    data = optional_dependency("strawberryfields.apps.data")
    raw = data.Formic()
    return FormicAcidData(
        ground_frequencies=np.asarray(raw.w, dtype=np.float64),
        excited_frequencies=np.asarray(raw.wp, dtype=np.float64),
        duschinsky_matrix=np.asarray(raw.Ud, dtype=np.float64),
        displacement=np.asarray(raw.delta, dtype=np.float64),
        _backend_data=raw,
    )


def vibronic_parameters(
    molecule: FormicAcidData, *, temperature: float = 0.0
) -> VibronicParameters:
    """Convert molecular data into local GBS vibronic parameters.

    Args:
        molecule: Molecular data returned by ``load_formic_acid``.
        temperature: Temperature in Kelvin used by the vibronic model.

    Returns:
        GBS parameters used by the local vibronic sampler.
    """
    qchem = optional_dependency("strawberryfields.apps.qchem")
    t, u1, r, u2, alpha = qchem.vibronic.gbs_params(
        molecule.ground_frequencies,
        molecule.excited_frequencies,
        molecule.duschinsky_matrix,
        molecule.displacement,
        temperature,
    )
    return VibronicParameters(
        temperature_factors=np.asarray(t, dtype=np.float64),
        interferometer_1=np.asarray(u1, dtype=np.complex128),
        squeezing=np.asarray(r, dtype=np.float64),
        interferometer_2=np.asarray(u2, dtype=np.complex128),
        displacement=np.asarray(alpha, dtype=np.complex128),
    )


def vibronic_energies(
    molecule_or_samples: Any, molecule: FormicAcidData | None = None
) -> npt.NDArray[np.float64]:
    """Compute vibronic transition energies.

    Args:
        molecule_or_samples: Either ``FormicAcidData`` for bundled samples or a
            two-dimensional sample array.
        molecule: Required molecular data when ``molecule_or_samples`` is a
            sample array.

    Returns:
        One-dimensional energy array.
    """
    qchem = optional_dependency("strawberryfields.apps.qchem")
    if isinstance(molecule_or_samples, FormicAcidData):
        source = molecule_or_samples._backend_data
        mol = molecule_or_samples
    else:
        if molecule is None:
            raise TypeError("molecule is required when computing energies from samples")
        source = np.asarray(molecule_or_samples, dtype=np.int_).tolist()
        mol = molecule
    return np.asarray(
        qchem.vibronic.energies(source, mol.ground_frequencies, mol.excited_frequencies),
        dtype=np.float64,
    )


def sample_vibronic_spectrum(
    parameters: VibronicParameters,
    *,
    shots: int = 10,
) -> npt.NDArray[np.int_]:
    """Generate local vibronic samples.

    Args:
        parameters: Parameters returned by ``vibronic_parameters``.
        shots: Number of vibronic samples generated.

    Returns:
        Two-dimensional integer sample array.
    """
    qchem = optional_dependency("strawberryfields.apps.qchem")
    samples = qchem.vibronic.sample(
        parameters.temperature_factors,
        parameters.interferometer_1,
        parameters.squeezing,
        parameters.interferometer_2,
        parameters.displacement,
        shots,
    )
    return np.asarray(samples, dtype=np.int_)
