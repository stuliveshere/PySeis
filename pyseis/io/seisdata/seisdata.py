import pandas as pd
import dask.dataframe as dd
import yaml
from typing import Optional, Union, Dict, Any
import os

class SeisData:
    """
    A class to manage seismic data including sources, receivers, traces,
    and common metadata using Pandas and Dask for efficient data handling.
    The DataFrame schemas are defined in an external YAML file.
    """

    def __init__(self, schema_file: str, use_dask: bool = False):
        """
        Initialize the SeismicData object with empty DataFrames based on a YAML schema.

        Parameters:
        - schema_file (str): Path to the YAML schema file.
        - use_dask (bool): If True, initializes Dask DataFrames for traces.
        """
        self.use_dask = use_dask

        # Load schema from YAML
        if not os.path.exists(schema_file):
            raise FileNotFoundError(f"Schema file '{schema_file}' does not exist.")

        with open(schema_file, 'r') as file:
            schema = yaml.safe_load(file)

        # Initialize DataFrames based on schema
        self.sources = self._initialize_dataframe(schema['dataframes']['source']['columns'], 'source')
        self.receivers = self._initialize_dataframe(schema['dataframes']['receiver']['columns'], 'receiver')
        self.trace_headers = self._initialize_dataframe(schema['dataframes']['trace_header']['columns'], 'trace_header')
        self.trace_data = self._initialize_traces(schema['dataframes']['trace_data']['columns'])
        self.signatures = self._initialize_dataframe(schema['dataframes']['signature']['columns'], 'signature')

        # Initialize metadata DataFrames
        self.properties = self._initialize_dataframe(schema['dataframes']['properties']['columns'], 'properties')
        self.survey = self._initialize_dataframe(schema['dataframes']['survey']['columns'], 'survey')
        self.instrument = self._initialize_dataframe(schema['dataframes']['instrument']['columns'], 'instrument')
        self.job = self._initialize_dataframe(schema['dataframes']['job']['columns'], 'job')

    def _initialize_dataframe(self, columns: Dict[str, Dict[str, str]], df_name: str) -> pd.DataFrame:
        """
        Initialize a Pandas DataFrame based on column definitions.

        Parameters:
        - columns (Dict[str, Dict[str, str]]): Column definitions with data types.
        - df_name (str): Name of the DataFrame for error messages.

        Returns:
        - pd.DataFrame: Initialized empty DataFrame.
        """
        dtype_mapping = {col: self._get_dtype(info['dtype']) for col, info in columns.items()}
        return pd.DataFrame(columns=columns.keys()).astype(dtype_mapping)

    def _initialize_traces(self, columns: Dict[str, Dict[str, str]]) -> Union[pd.DataFrame, dd.DataFrame]:
        """
        Initialize the Traces DataFrame as either Pandas or Dask based on use_dask flag.

        Parameters:
        - columns (Dict[str, Dict[str, str]]): Column definitions for traces.

        Returns:
        - Union[pd.DataFrame, dd.DataFrame]: Initialized empty Traces DataFrame.
        """
        dtype_mapping = {col: self._get_dtype(info['dtype']) for col, info in columns.items()}
        traces_pd = pd.DataFrame(columns=columns.keys()).astype(dtype_mapping)
        if self.use_dask:
            return dd.from_pandas(traces_pd, npartitions=4)  # Adjust npartitions as needed
        else:
            return traces_pd

    def _get_dtype(self, dtype_str: str) -> Any:
        """
        Map YAML dtype strings to actual pandas/numpy dtypes.

        Parameters:
        - dtype_str (str): Data type as a string from YAML.

        Returns:
        - Any: Corresponding pandas/numpy dtype.
        """
        # Handle array types (e.g., 'float32[]' or 'float32[][]')
        base_dtype = dtype_str.rstrip('[]')  # Remove all array indicators
        is_array = base_dtype != dtype_str   # True if any [] were removed

        dtype_mapping = {
            'string': 'object',
            'int32': 'int32',
            'float32': 'float32',
            'bool': 'bool',
            'dict': 'object',  # Dictionaries stored as objects
            'uint': 'uint32',  # For SU trace header fields
        }

        if base_dtype not in dtype_mapping:
            raise ValueError(f"Unsupported dtype '{dtype_str}' in schema.")
        
        # For any array types (single or multi-dimensional), return object dtype
        if is_array:
            return 'object'
        
        return dtype_mapping[base_dtype]

    def add_source(self, source_data: Dict[str, Any]) -> None:
        """
        Add a source entry to the sources DataFrame.

        Parameters:
        - source_data (Dict[str, Any]): Dictionary containing source metadata.
        """
        required_columns = self.sources.columns.tolist()
        missing = set(required_columns) - set(source_data.keys())
        if missing:
            raise ValueError(f"Missing columns in source_data: {missing}")

        # Ensure data types match
        for col, dtype in self.sources.dtypes.items():
            if col in source_data:
                source_data[col] = self._cast_dtype(source_data[col], dtype)

        self.sources = self.sources.append(source_data, ignore_index=True)

    def add_receiver(self, receiver_data: Dict[str, Any]) -> None:
        """
        Add a receiver entry to the receivers DataFrame.

        Parameters:
        - receiver_data (Dict[str, Any]): Dictionary containing receiver metadata.
        """
        required_columns = self.receivers.columns.tolist()
        missing = set(required_columns) - set(receiver_data.keys())
        if missing:
            raise ValueError(f"Missing columns in receiver_data: {missing}")

        # Ensure data types match
        for col, dtype in self.receivers.dtypes.items():
            if col in receiver_data:
                receiver_data[col] = self._cast_dtype(receiver_data[col], dtype)

        self.receivers = self.receivers.append(receiver_data, ignore_index=True)

    def add_trace(self, trace_data: Dict[str, Any]) -> None:
        """
        Add a trace entry to the traces DataFrame.

        Parameters:
        - trace_data (Dict[str, Any]): Dictionary containing trace metadata.
        """
        trace_columns = self.trace_data.columns.tolist()
        missing = set(trace_columns) - set(trace_data.keys())
        if missing:
            raise ValueError(f"Missing columns in trace_data: {missing}")

        # Ensure data types match
        for col, dtype in self.trace_data.dtypes.items():
            if col in trace_data:
                trace_data[col] = self._cast_dtype(trace_data[col], dtype)

        if self.use_dask:
            # Convert the trace_data dict to a single-row DataFrame and append
            trace_df = pd.DataFrame([trace_data]).astype(self.trace_data.dtypes.to_dict())
            self.trace_data = dd.concat([self.trace_data, dd.from_pandas(trace_df, npartitions=1)], interleave_partitions=True)
        else:
            self.trace_data = self.trace_data.append(trace_data, ignore_index=True)

    def _cast_dtype(self, value: Any, dtype: Any) -> Any:
        """
        Cast a value to a specified dtype, handling conversion errors.

        Parameters:
        - value (Any): The value to cast.
        - dtype (Any): The target dtype.

        Returns:
        - Any: The casted value.
        """
        try:
            if pd.api.types.is_bool_dtype(dtype):
                return bool(value)
            elif pd.api.types.is_integer_dtype(dtype):
                return int(value)
            elif pd.api.types.is_float_dtype(dtype):
                return float(value)
            elif pd.api.types.is_object_dtype(dtype):
                return value  # For strings and dicts
            else:
                return value
        except (ValueError, TypeError):
            raise ValueError(f"Cannot cast value '{value}' to dtype '{dtype}'.")

    def set_common_metadata(self, metadata_type: str, metadata: Dict[str, Any]) -> None:
        """
        Set common metadata (datum_terms, instrument_terms, survey_terms).

        Parameters:
        - metadata_type (str): Type of metadata ('datum', 'instrument', 'survey').
        - metadata (Dict[str, Any]): Dictionary containing the metadata.
        """
        metadata_df = None
        if metadata_type == 'datum':
            metadata_df = self.properties
        elif metadata_type == 'instrument':
            metadata_df = self.instrument
        elif metadata_type == 'survey':
            metadata_df = self.survey
        else:
            raise ValueError("Invalid metadata_type. Choose from 'datum', 'instrument', 'survey'.")

        required_columns = metadata_df.columns.tolist()
        missing = set(required_columns) - set(metadata.keys())
        if missing:
            raise ValueError(f"Missing columns in {metadata_type}_metadata: {missing}")

        # Ensure data types match
        for col, dtype in metadata_df.dtypes.items():
            if col in metadata:
                metadata[col] = self._cast_dtype(metadata[col], dtype)

        # Update the metadata DataFrame (assumes only one row)
        self._update_metadata_dataframe(metadata_df, metadata)

    def _update_metadata_dataframe(self, metadata_df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
        """
        Update a single-row metadata DataFrame with new data.

        Parameters:
        - metadata_df (pd.DataFrame): The metadata DataFrame to update.
        - metadata (Dict[str, Any]): The new metadata values.
        """
        if metadata_df.empty:
            # Insert the first row
            new_row = pd.Series(metadata)
            metadata_df.loc[0] = new_row
        else:
            # Update the first row
            for key, value in metadata.items():
                metadata_df.at[0, key] = value

    def set_common_metadata_bulk(self, metadata: Dict[str, Dict[str, Any]]) -> None:
        """
        Set multiple common metadata terms at once.

        Parameters:
        - metadata (Dict[str, Dict[str, Any]]): Dictionary containing metadata types and their data.
        """
        for metadata_type, data in metadata.items():
            self.set_common_metadata(metadata_type, data)

    def save_to_hdf5(self, file_path: str) -> None:
        """
        Save the seismic data to an HDF5 file.
        """
        with pd.HDFStore(file_path, 'w') as store:
            # Save DataFrames
            store.put('source', self.sources, format='table', data_columns=True)
            store.put('receiver', self.receivers, format='table', data_columns=True)
            store.put('trace_header', self.trace_headers, format='table', data_columns=True)
            if self.use_dask:
                store.put('trace_data', self.trace_data.compute(), format='table', data_columns=True)
            else:
                store.put('trace_data', self.trace_data, format='table', data_columns=True)
            store.put('signature', self.signatures, format='table', data_columns=True)

            # Save metadata
            store.put('properties', self.properties, format='table')
            store.put('survey', self.survey, format='table')
            store.put('instrument', self.instrument, format='table')
            store.put('job', self.job, format='table')

    def load_from_hdf5(self, file_path: str) -> None:
        """
        Load seismic data from an HDF5 file.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"HDF5 file '{file_path}' does not exist.")

        with pd.HDFStore(file_path, 'r') as store:
            self.sources = store['source']
            self.receivers = store['receiver']
            self.trace_headers = store['trace_header']
            self.trace_data = store['trace_data']
            self.signatures = store['signature']
            self.properties = store['properties']
            self.survey = store['survey']
            self.instrument = store['instrument']
            self.job = store['job']

        if self.use_dask:
            self.trace_data = dd.from_pandas(self.trace_data, npartitions=4)

    def to_dask(self) -> None:
        """
        Convert the traces DataFrame to a Dask DataFrame for out-of-memory processing.
        """
        if not self.use_dask:
            self.trace_data = dd.from_pandas(self.trace_data, npartitions=4)  # Adjust npartitions as needed
            self.use_dask = True
            print("Converted traces to Dask DataFrame.")
        else:
            print("Traces are already using Dask DataFrame.")

    def from_dask(self) -> None:
        """
        Convert the traces Dask DataFrame back to a Pandas DataFrame.
        """
        if self.use_dask:
            self.trace_data = self.trace_data.compute()
            self.use_dask = False
            print("Converted traces back to Pandas DataFrame.")
        else:
            print("Traces are already using Pandas DataFrame.")

    def query_traces_by_source(self, source_id: str) -> pd.DataFrame:
        """
        Retrieve all traces associated with a given source_id.

        Parameters:
        - source_id (str): The source_id to query.

        Returns:
        - pd.DataFrame: DataFrame containing the filtered traces.
        """
        if self.use_dask:
            return self.trace_data[self.trace_data['source_id'] == source_id].compute()
        else:
            return self.trace_data[self.trace_data['source_id'] == source_id]

    def query_traces_by_receiver(self, receiver_id: str) -> pd.DataFrame:
        """
        Retrieve all traces associated with a given receiver_id.

        Parameters:
        - receiver_id (str): The receiver_id to query.

        Returns:
        - pd.DataFrame: DataFrame containing the filtered traces.
        """
        if self.use_dask:
            return self.trace_data[self.trace_data['receiver_id'] == receiver_id].compute()
        else:
            return self.trace_data[self.trace_data['receiver_id'] == receiver_id]

    def display_sources(self) -> None:
        """Display the sources DataFrame."""
        print("\nSources DataFrame:")
        print(self.sources)

    def display_receivers(self) -> None:
        """Display the receivers DataFrame."""
        print("\nReceivers DataFrame:")
        print(self.receivers)

    def display_traces(self, num_rows: int = 5) -> None:
        """
        Display the traces DataFrame.

        Parameters:
        - num_rows (int): Number of rows to display.
        """
        if self.use_dask:
            print("\nTraces DataFrame (Dask):")
            print(self.trace_data.head(num_rows))
        else:
            print("\nTraces DataFrame:")
            print(self.trace_data.head(num_rows))

    def display_common_metadata(self) -> None:
        """
        Display all common metadata DataFrames.
        """
        print("\nProperties:")
        print(self.properties)
        print("\nSurvey:")
        print(self.survey)
        print("\nInstrument:")
        print(self.instrument)
        print("\nJob:")
        print(self.job)

    def get_common_metadata(self) -> Dict[str, pd.DataFrame]:
        """
        Retrieve all common metadata.

        Returns:
        - Dict[str, pd.DataFrame]: Dictionary containing common metadata DataFrames.
        """
        return {
            'properties': self.properties,
            'survey': self.survey,
            'instrument': self.instrument,
            'job': self.job
        }

    def clean_data(self) -> None:
        """
        Perform basic data cleaning operations:
        - Remove duplicate entries.
        - Handle missing values by filling or dropping.
        """
        # Remove duplicates in sources and receivers
        self.sources.drop_duplicates(subset='source_id', inplace=True)
        self.receivers.drop_duplicates(subset='receiver_id', inplace=True)

        # Handle missing values in traces
        if self.use_dask:
            self.trace_data = self.trace_data.fillna(0)
        else:
            self.trace_data.fillna(0, inplace=True)

        # Handle missing values in common metadata
        self.properties.fillna('', inplace=True)
        self.survey.fillna('', inplace=True)
        self.instrument.fillna('', inplace=True)
        self.job.fillna('', inplace=True)

        print("Data cleaning completed.")

    def _initialize_metadata_dataframe(self, metadata_df: pd.DataFrame, metadata: Dict[str, Any]) -> None:
        """
        Update a single-row metadata DataFrame with new data.

        Parameters:
        - metadata_df (pd.DataFrame): The metadata DataFrame to update.
        - metadata (Dict[str, Any]): The new metadata values.
        """
        if metadata_df.empty:
            # Insert the first row
            new_row = pd.Series(metadata)
            metadata_df.loc[0] = new_row
        else:
            # Update the first row
            for key, value in metadata.items():
                metadata_df.at[0, key] = value

# Example usage
if __name__ == "__main__":
    import os

    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct path to schema file relative to this script
    schema_path = os.path.join(current_dir, "seisdata_schema.yaml")
    
    print(f"Looking for schema file at: {schema_path}")
    
    try:
        seismic_data = SeismicData(schema_file=schema_path)

        # Display the empty DataFrames
        print("\n=== Empty SeismicData Instance ===")
        print("\nSources:")
        print(seismic_data.sources)
        
        print("\nReceivers:")
        print(seismic_data.receivers)
        
        print("\nTrace Headers:")
        print(seismic_data.trace_headers)
        
        print("\nTrace Data:")
        print(seismic_data.trace_data)
        
        print("\nSignatures:")
        print(seismic_data.signatures)
        
        print("\nMetadata DataFrames:")
        print("\nProperties:")
        print(seismic_data.properties)
        
        print("\nSurvey:")
        print(seismic_data.survey)
        
        print("\nInstrument:")
        print(seismic_data.instrument)
        
        print("\nJob:")
        print(seismic_data.job)
    except FileNotFoundError as e:
        print(f"Error: {e}")
