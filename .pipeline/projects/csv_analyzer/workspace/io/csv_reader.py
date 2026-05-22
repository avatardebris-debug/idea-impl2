"""CsvReader — reads CSV files into pandas DataFrames with flexible options."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Any


class CsvReader:
    """Read CSV files into pandas DataFrames.

    Parameters
    ----------
    delimiter : str, optional
        Delimiter to use for parsing. Default is ','.
    encoding : str, optional
        File encoding. Default is 'utf-8'.
    header : int, optional
        Row number to use as column names. Default is 0.
    names : list, optional
        Column names to use. Required if header=None.
    usecols : list, optional
        Columns to read.
    na_values : list, optional
        Additional strings to recognize as NA/NaN.
    dtype : dict, optional
        Data types for columns.
    """

    def __init__(
        self,
        delimiter: str = ",",
        encoding: str = "utf-8",
        header: int = 0,
        names: list[str] | None = None,
        usecols: list[str] | None = None,
        na_values: list[str] | None = None,
        dtype: dict[str, str] | None = None,
    ) -> None:
        """Initialize the CsvReader with parsing options.

        Parameters
        ----------
        delimiter : str, optional
            Delimiter to use for parsing. Default is ','.
        encoding : str, optional
            File encoding. Default is 'utf-8'.
        header : int, optional
            Row number to use as column names. Default is 0.
        names : list, optional
            Column names to use. Required if header=None.
        usecols : list, optional
            Columns to read.
        na_values : list, optional
            Additional strings to recognize as NA/NaN.
        dtype : dict, optional
            Data types for columns.
        """
        self.delimiter = delimiter
        self.encoding = encoding
        self.header = header
        self.names = names
        self.usecols = usecols
        self.na_values = na_values
        self.dtype = dtype

    def read(self, filepath: str | Path) -> pd.DataFrame:
        """Read a CSV file into a DataFrame.

        Parameters
        ----------
        filepath : str | Path
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            The parsed DataFrame.

        Raises
        -------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the path is not a file or is empty.
        """
        path = Path(filepath)

        # Check if file exists
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        # Check if path is a file
        if not path.is_file():
            raise ValueError(f"Path is not a file: {filepath}")

        # Read the file
        try:
            df = pd.read_csv(
                path,
                delimiter=self.delimiter,
                encoding=self.encoding,
                header=self.header,
                names=self.names,
                usecols=self.usecols,
                na_values=self.na_values,
                dtype=self.dtype,
            )
            return df
        except pd.errors.EmptyDataError:
            # Re-raise EmptyDataError for empty files
            raise
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file: {e}")

    def read_batch(self, filepaths: list[str | Path]) -> list[pd.DataFrame]:
        """Read multiple CSV files into a list of DataFrames.

        Parameters
        ----------
        filepaths : list[str | Path]
            List of paths to CSV files.

        Returns
        -------
        list[pd.DataFrame]
            List of parsed DataFrames.
        """
        return [self.read(fp) for fp in filepaths]

    @classmethod
    def read_with_type_inference(cls, filepath: str | Path) -> pd.DataFrame:
        """Read a CSV file with automatic type inference.

        Parameters
        ----------
        filepath : str | Path
            Path to the CSV file.

        Returns
        -------
        pd.DataFrame
            The parsed DataFrame with inferred types.
        """
        reader = cls()
        return reader.read(filepath)

    def read_chunked(
        self,
        filepath: str | Path,
        chunksize: int = 10000,
    ) -> pd.DataFrame:
        """Read a CSV file in chunks.

        Parameters
        ----------
        filepath : str | Path
            Path to the CSV file.
        chunksize : int, optional
            Number of rows per chunk. Default is 10000.

        Returns
        -------
        pd.DataFrame
            The complete DataFrame (chunks concatenated).
        """
        chunks = pd.read_csv(
            filepath,
            delimiter=self.delimiter,
            encoding=self.encoding,
            header=self.header,
            names=self.names,
            usecols=self.usecols,
            na_values=self.na_values,
            dtype=self.dtype,
            chunksize=chunksize,
        )

        # Concatenate all chunks
        return pd.concat(chunks, ignore_index=True)
