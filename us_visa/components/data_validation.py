import json
import sys
import pandas as pd
from evidently.report import Report
from evidently.metrics import DataDriftTable
from pandas import DataFrame

from us_visa.exceptions import USvisaException
from us_visa.logger import logging
from us_visa.utils.main_utilz import read_yaml_file, write_yaml_file
from us_visa.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from us_visa.entity.config_entity import DataValidationConfig
from us_visa.constants import SCHEMA_FILE_PATH


class DataValidation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_config: DataValidationConfig):
        """
        :param data_ingestion_artifact: Output reference of data ingestion artifact stage
        :param data_validation_config: configuration for data validation
        """
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(file_path=SCHEMA_FILE_PATH)
        except Exception as e:
            raise USvisaException(e, sys)

    def validate_number_of_columns(self, dataframe: DataFrame) -> bool:
        """
        Method Name :   validate_number_of_columns
        Description :   This method validates the number of columns
        
        Output      :   Returns bool value based on validation results
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            status = len(dataframe.columns) == len(self._schema_config["columns"])
            logging.info(f"Is required column present: [{status}]")
            return status
        except Exception as e:
            raise USvisaException(e, sys)

    def is_column_exist(self, df: DataFrame) -> bool:
        """
        Method Name :   is_column_exist
        Description :   This method validates the existence of a numerical and categorical columns
        
        Output      :   Returns bool value based on validation results
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            dataframe_columns = df.columns
            missing_numerical_columns = []
            missing_categorical_columns = []
            for column in self._schema_config["numerical_columns"]:
                if column not in dataframe_columns:
                    missing_numerical_columns.append(column)

            if missing_numerical_columns:
                logging.info(f"Missing numerical column: {missing_numerical_columns}")

            for column in self._schema_config["categorical_columns"]:
                if column not in dataframe_columns:
                    missing_categorical_columns.append(column)

            if missing_categorical_columns:
                logging.info(f"Missing categorical column: {missing_categorical_columns}")

            return not (missing_numerical_columns or missing_categorical_columns)
        except Exception as e:
            raise USvisaException(e, sys)

    @staticmethod
    def read_data(file_path) -> DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise USvisaException(e, sys)

    def detect_dataset_drift(self, reference_df: DataFrame, current_df: DataFrame) -> bool:
        """
        Method Name :   detect_dataset_drift
        Description :   This method validates if drift is detected
        
        Output      :   Returns bool value based on validation results
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            # Ensure the input DataFrames are valid
            assert isinstance(reference_df, pd.DataFrame), "reference_df is not a valid DataFrame"
            assert isinstance(current_df, pd.DataFrame), "current_df is not a valid DataFrame"
            logging.info(f"reference_df shape: {reference_df.shape}")
            logging.info(f"current_df shape: {current_df.shape}")

            # Create a data drift report using Evidently
            data_drift_report = Report(metrics=[DataDriftTable()])
            data_drift_report.run(reference_data=reference_df, current_data=current_df)

            # Export the report as JSON
            report = data_drift_report.json()
            json_report = json.loads(report)

            # Debugging the JSON report structure
            # logging.info(f"Drift report content: {json.dumps(json_report, indent=4)}")

            # Check if the report contains the expected keys
            if "metrics" not in json_report or not json_report["metrics"]:
                logging.error("The report is missing the 'metrics' key or it's empty.")
                raise KeyError("Missing 'metrics' in the drift report.")
            
            # Save the drift report to a YAML file
            write_yaml_file(file_path=self.data_validation_config.drift_report_file_path, content=json_report)

            # Extract drift information from the JSON report
            result = json_report["metrics"][0].get("result", {})
            if not result:
                logging.error("The 'result' field is missing in the drift report.")
                raise KeyError("Missing 'result' field in drift report.")

            # Updated logic to handle the new structure
            n_features = result.get("number_of_columns")
            n_drifted_features = result.get("number_of_drifted_columns")

            if n_features is None or n_drifted_features is None:
                logging.error("Drift report keys 'number_of_columns' or 'number_of_drifted_columns' are missing.")
                raise KeyError("Missing keys in the drift report: 'number_of_columns' or 'number_of_drifted_columns'")

            # Log drift status
            logging.info(f"Total columns: {n_features}, Drifted columns: {n_drifted_features}")

            # Determine dataset drift status
            dataset_drift = result.get("dataset_drift", False)
            logging.info(f"Dataset drift detected: {dataset_drift}")

            return dataset_drift

        except KeyError as e:
            logging.error(f"KeyError: {str(e)}")
            raise USvisaException(e, sys)
        except Exception as e:
            logging.error(f"Exception in detecting dataset drift: {str(e)}")
            raise USvisaException(e, sys)


    def initiate_data_validation(self) -> DataValidationArtifact:
        """
        Method Name :   initiate_data_validation
        Description :   This method initiates the data validation component for the pipeline
        
        Output      :   Returns bool value based on validation results
        On Failure  :   Write an exception log and then raise an exception
        """
        try:
            validation_error_msg = ""
            logging.info("Starting data validation")
            train_df, test_df = (DataValidation.read_data(file_path=self.data_ingestion_artifact.trained_file_path),
                                 DataValidation.read_data(file_path=self.data_ingestion_artifact.test_file_path))

            status = self.validate_number_of_columns(dataframe=train_df)
            logging.info(f"All required columns present in training dataframe: {status}")
            if not status:
                validation_error_msg += f"Columns are missing in training dataframe."
            status = self.validate_number_of_columns(dataframe=test_df)

            logging.info(f"All required columns present in testing dataframe: {status}")
            if not status:
                validation_error_msg += f"Columns are missing in test dataframe."

            status = self.is_column_exist(df=train_df)

            if not status:
                validation_error_msg += f"Columns are missing in training dataframe."
            status = self.is_column_exist(df=test_df)

            if not status:
                validation_error_msg += f"Columns are missing in test dataframe."

            validation_status = len(validation_error_msg) == 0

            if validation_status:
                drift_status = self.detect_dataset_drift(train_df, test_df)
                if drift_status:
                    logging.info(f"Drift detected.")
                    validation_error_msg = "Drift detected"
                else:
                    validation_error_msg = "Drift not detected"
            else:
                logging.info(f"Validation_error: {validation_error_msg}")

            data_validation_artifact = DataValidationArtifact(
                validation_status=validation_status,
                message=validation_error_msg,
                drift_report_file_path=self.data_validation_config.drift_report_file_path
            )

            logging.info(f"Data validation artifact: {data_validation_artifact}")
            return data_validation_artifact
        except Exception as e:
            raise USvisaException(e, sys)
