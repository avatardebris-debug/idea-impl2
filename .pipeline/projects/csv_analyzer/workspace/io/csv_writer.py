"""CsvWriter — writes pandas DataFrames to CSV files with flexible options."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Any


class CsvWriter:
    """Write pandas DataFrames to CSV files.

    Parameters
    ----------
    delimiter : str, optional
        Delimiter to use for writing. Default is ','.
    encoding : str, optional
        File encoding. Default is 'utf-8'.
    index : bool, optional
        Whether to write row indices. Default is True.
    na_rep : str, optional
        String representation for NA values. Default is ''.
    quotechar : str, optional
        Character to use for quoting. Default is '"'.
    quoting : int, optional
        Quote style. Default is csv.QUOTE_MINIMAL.
    """

    def __init__(
        self,
        delimiter: str = ",",
        encoding: str = "utf-8",
        index: bool = True,
        na_rep: str = "",
        quotechar: str = '"',
        quoting: int = 0,
    ) -> None:
        """Initialize the CsvWriter with writing options.

        Parameters
        ----------
        delimiter : str, optional
            Delimiter to use for writing. Default is ','.
        encoding : str, optional
            File encoding. Default is 'utf-8'.
        index : bool, optional
            Whether to write row indices. Default is True.
        na_rep : str, optional
            String representation for NA values. Default is ''.
        quotechar : str, optional
            Character to use for quoting. Default is '"'.
        quoting : int, optional
            Quote style. Default is csv.QUOTE_MINIMAL.
        """
        import csv

        self.delimiter = delimiter
        self.encoding = encoding
        self.index = index
        self.na_rep = na_rep
        self.quotechar = quotechar
        self.quoting = quoting

    def write(
        self,
        df: pd.DataFrame,
        filepath: str | Path,
        overwrite: bool = False,
    ) -> Path:
        """Write a DataFrame to a CSV file.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to write.
        filepath : str | Path
            Path to the output CSV file.
        overwrite : bool, optional
            Whether to overwrite existing files. Default is False.

        Returns
        -------
        Path
            Path to the written file.

        Raises
        -------
        FileExistsError
            If the file exists and overwrite=False.
        """
        path = Path(filepath)

        # Check if file exists
        if path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {filepath}")

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        df.to_csv(
            path,
            index=self.index,
            encoding=self.encoding,
            sep=self.delimiter,
            na_rep=self.na_rep,
            quotechar=self.quotechar,
            quoting=self.quoting,
        )

        return path

    def write_batch(
        self,
        dfs: list[pd.DataFrame],
        filepaths: list[str | Path],
        overwrite: bool = False,
    ) -> list[Path]:
        """Write multiple DataFrames to CSV files.

        Parameters
        ----------
        dfs : list[pd.DataFrame]
            List of DataFrames to write.
        filepaths : list[str | Path]
            List of output file paths.
        overwrite : bool, optional
            Whether to overwrite existing files. Default is False.

        Returns
        -------
        list[Path]
            List of paths to written files.
        """
        if len(dfs) != len(filepaths):
            raise ValueError("Number of DataFrames must match number of filepaths")

        return [self.write(df, fp, overwrite) for df, fp in zip(dfs, filepaths)]

    def append(
        self,
        df: pd.DataFrame,
        filepath: str | Path,
        header: bool = False,
    ) -> Path:
        """Append a DataFrame to an existing CSV file.

        Parameters
        ----------
        df : pd.DataFrame
            The DataFrame to append.
        filepath : str | Path
            Path to the existing CSV file.
        header : bool, optional
            Whether to write column headers. Default is False.

        Returns
        -------
        Path
            Path to the updated file.
        """
        path = Path(filepath)

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        # Append the DataFrame
        df.to_csv(
            path,
            mode="a",
            index=self.index,
            encoding=self.encoding,
            sep=self.delimiter,
            na_rep=self.na_rep,
            quotechar=self.quotechar,
            quoting=self.quoting,
            header=header,
        )

        return path
