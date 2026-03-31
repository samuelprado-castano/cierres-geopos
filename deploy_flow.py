from prefect.client.schemas.schedules import CronSchedule
from src.flows.etl_cierres_flow import etl_cierres_flow
from src.flows.missing_cierres_flow import missing_cierres_flow

PROJECT_PATH = "C:/ST_BI/PROYECTOS_PREFECT/RUBI_V3"
PYTHON_EXE = f"{PROJECT_PATH}/.venv/Scripts/python.exe"
COMMON_JOB_VARS = {
    "env": {"PYTHONPATH": PROJECT_PATH},
    "command": f"{PYTHON_EXE} -m prefect.engine",
    "working_directory": PROJECT_PATH
}


def deploy_etl_cierres():
    """Deploy ETL diario de cierres - 11 PM todos los dias"""
    cron_schedule = "0 23 * * *"

    etl_cierres_flow.from_source(
        source=PROJECT_PATH,
        entrypoint="src/flows/etl_cierres_flow.py:etl_cierres_flow"
    ).deploy(
        name="etl-cierres-geopos-deploy",
        version="1",
        work_pool_name="mi-pool-windows",
        schedule=CronSchedule(cron=cron_schedule, timezone="America/Santiago"),
        tags=["geopos", "etl", "nightly"],
        work_queue_name="default",
        job_variables=COMMON_JOB_VARS
    )

    print(f"Deploy 'etl-cierres-geopos' creado con CronSchedule: {cron_schedule}")


def deploy_missing_cierres():
    """Deploy reporte de cierres faltantes - 8 AM todos los dias"""
    cron_schedule = "0 8 * * *"

    missing_cierres_flow.from_source(
        source=PROJECT_PATH,
        entrypoint="src/flows/missing_cierres_flow.py:missing_cierres_flow"
    ).deploy(
        name="missing-cierres-check-deploy",
        version="1",
        work_pool_name="mi-pool-windows",
        schedule=CronSchedule(cron=cron_schedule, timezone="America/Santiago"),
        tags=["geopos", "missing-cierres", "daily"],
        work_queue_name="default",
        job_variables=COMMON_JOB_VARS
    )

    print(f"Deploy 'missing-cierres-check' creado con CronSchedule: {cron_schedule}")


if __name__ == "__main__":
    deploy_etl_cierres()
    deploy_missing_cierres()
