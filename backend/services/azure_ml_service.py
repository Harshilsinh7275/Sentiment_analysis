import os
import uuid
import traceback
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential
from azure.ai.ml.entities import CommandJob, Environment

from ..config import (
    AZURE_SUBSCRIPTION_ID,
    AZURE_RESOURCE_GROUP,
    AZURE_ML_WORKSPACE,
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME,
)

# ML Client
ml_client = MLClient(
    DefaultAzureCredential(),
    AZURE_SUBSCRIPTION_ID,
    AZURE_RESOURCE_GROUP,
    AZURE_ML_WORKSPACE
)


async def trigger_aml_pipeline(analysis_type: str, blob_name: str, user_email: str):
    """
    Creates CommandJob in Python (no YAML loading).
    """

    try:
        # Define environment
        env = Environment(
            name="sentiment-aml-env",
            image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
            conda_file="azure_ml/env.yml"
        )

        job_id = f"sentiment-job-{uuid.uuid4()}"

        # Build job programmatically
        job = CommandJob(
            code="azure_ml",
            command=(
                f"python run_analysis.py "
                f"--analysis_type {analysis_type} "
                f"--blob_name {blob_name} "
                f"--user_email {user_email} "
                f"--storage_conn_str '{AZURE_STORAGE_CONNECTION_STRING}' "
                f"--container_name {AZURE_CONTAINER_NAME}"
            ),
            environment=env,
            compute="cpu-cluster1",
            display_name="sentiment-analysis",
            experiment_name="sentiment-poc"
        )

        # Submit job to Azure ML
        submitted = ml_client.jobs.create_or_update(job, name=job_id)
        print("AML JOB SUBMITTED:", submitted.name)

        return submitted.name

    except Exception as e:
        print(" ERROR triggering AML job:")
        print("Exception type:", type(e))
        print("Traceback:")
        print(traceback.format_exc())
        raise RuntimeError(str(e))
