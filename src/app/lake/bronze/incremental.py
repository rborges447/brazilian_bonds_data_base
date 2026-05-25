"""Incremental bronze loads based on hive partition presence."""



from __future__ import annotations



from app.core.partitioning import SNAPSHOT_VALUE, get_partition_spec, is_snapshot_dataset

from app.lake.bronze.reader import list_partition_values

from app.lake.bronze.storage import partition_artifact_exists





def missing_partition_values(dataset: str, candidate_values: list[str]) -> list[str]:

    """

    Return partition values still missing a non-empty artifact.



    For snapshot datasets, candidate_values is ignored; checks snapshot=1 once.

    """

    spec = get_partition_spec(dataset)

    if is_snapshot_dataset(dataset):

        if partition_artifact_exists(

            dataset, spec.partition_key, SNAPSHOT_VALUE, spec.artifact_ext

        ):

            return []

        return [SNAPSHOT_VALUE]



    missing: list[str] = []

    for value in candidate_values:

        if not partition_artifact_exists(

            dataset, spec.partition_key, value, spec.artifact_ext

        ):

            missing.append(value)

    return missing





list_existing_partition_values = list_partition_values



__all__ = [

    "missing_partition_values",

    "list_partition_values",

    "list_existing_partition_values",

]

