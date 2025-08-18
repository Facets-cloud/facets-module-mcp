import json
import time
import uuid

from swagger_client.api.ui_deployment_controller_api import UiDeploymentControllerApi
from swagger_client.api.ui_dropdowns_controller_api import UiDropdownsControllerApi
from swagger_client.api.ui_stack_controller_api import UiStackControllerApi
from swagger_client.models.facets_resource import FacetsResource
from swagger_client.models.hotfix_deployment_recipe import HotfixDeploymentRecipe
from swagger_client.rest import ApiException

from facets_mcp.config import mcp
from facets_mcp.utils.client_utils import ClientUtils


@mcp.tool()
def list_test_projects() -> str:
    """
    Retrieve and return the names of all available test projects for the user to choose from.

    Returns:
        str: A JSON string containing success message and list of all test projects or error message
    """
    api_instance = UiStackControllerApi(ClientUtils.get_client())
    stacks = api_instance.get_stacks()
    stack_names = [stack.name for stack in stacks if stack.preview_modules_allowed]
    if stack_names:
        return json.dumps(
            {
                "success": True,
                "instructions": "If there are multiple projects available, ask the user to choose a test project from the project list. Do not pick one by yourself.",
                "data": {"project_list": stack_names},
            },
            indent=2,
        )
    else:
        return json.dumps(
            {
                "success": False,
                "error": "No test projects found. Ask the user to create one from the Facets UI.",
            },
            indent=2,
        )


@mcp.tool()
def test_already_previewed_module(
    project_name: str,
    intent: str,
    flavor: str,
    version: str,
    environment_name: str | None = None,
) -> str:
    """
    Test a module that has been previewed by asking the user for the project_name where it needs to be tested.


    This tool checks if the project exists, verifies if it supports preview modules,
    and then does terraform apply. You can check logs for the apply using get_deployment_logs, and check the status of the deployment using check_deployment_status.

    Args:
        project_name (str): The name of the test project (stack) to deploy to
        intent (str): The intent of the module to deploy
        flavor (str): The flavor of the module to deploy
        version (str): The version of the module to deploy
        environment_name (str, optional): The specific environment name to deploy to. Provide this only if the user has asked you to.

    Returns:
        str: Result of the deployment operation as a JSON string
    """
    try:
        # Initialize API clients
        api_client = ClientUtils.get_client()
        stack_api = UiStackControllerApi(api_client)
        dropdowns_api = UiDropdownsControllerApi(api_client)
        deployment_api = UiDeploymentControllerApi(api_client)

        # Step 1: Check if the project (stack) exists and supports preview modules
        try:
            stack_info = stack_api.get_stack(stack_name=project_name)

            # Check if allowPreviewModules is enabled
            if not stack_info.preview_modules_allowed:
                return json.dumps(
                    {
                        "success": False,
                        "instructions": f"Project '{project_name}' does not allow preview modules. Ask the user to enable this feature in the project settings by marking it as a Test Project.",
                    },
                    indent=2,
                )

        except ApiException as e:
            if e.status == 404:
                return json.dumps(
                    {
                        "success": False,
                        "instructions": f"Inform User: Project '{project_name}' does not exist.",
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "instructions": f"Inform User: Error accessing project '{project_name}': {e!s}",
                    },
                    indent=2,
                )

        # Step 2: Get the running environments (clusters) of the project
        try:
            clusters = stack_api.get_clusters_overview(stack_name=project_name)
            running_clusters = [c for c in clusters if c.cluster_state == "RUNNING"]

            if not running_clusters:
                return json.dumps(
                    {
                        "success": False,
                        "instructions": f"Inform User: No running environments found in project '{project_name}'. Launch an environment first.",
                    },
                    indent=2,
                )

            # Handle environment selection based on whether environment_name is provided
            if environment_name:
                # If environment_name is specified, find that specific environment
                target_cluster = None
                for cluster in running_clusters:
                    if cluster.cluster.name == environment_name:
                        target_cluster = cluster
                        break

                if not target_cluster:
                    available_envs = [c.cluster.name for c in running_clusters]
                    return json.dumps(
                        {
                            "success": False,
                            "instructions": f"Inform User: Environment '{environment_name}' not found or not running in project '{project_name}'. Available running environments: {', '.join(available_envs)}",
                        },
                        indent=2,
                    )

                cluster_id = target_cluster.cluster.id
                cluster_name = target_cluster.cluster.name
            else:
                # If environment_name is not specified
                if len(running_clusters) > 1:
                    cluster_names = [c.cluster.name for c in running_clusters]
                    return json.dumps(
                        {
                            "success": False,
                            "instructions": f"Inform User: Multiple running environments found: {', '.join(cluster_names)}. Please specify the environment_name parameter to choose which environment to deploy to.",
                        },
                        indent=2,
                    )

                # Only one running environment, use it
                cluster_id = running_clusters[0].cluster.id
                cluster_name = running_clusters[0].cluster.name

        except ApiException as e:
            return json.dumps(
                {
                    "success": False,
                    "instructions": f"Inform User: Error getting environment information for '{project_name}': {e!s}",
                },
                indent=2,
            )

        # Step 3: Get all resources for the cluster
        try:
            resources = dropdowns_api.get_all_resources_by_cluster(
                cluster_id=cluster_id
            )

            # Filter resources by the specified intent (resourceType)
            matching_resources = []
            for resource in resources:
                if resource.resource_type == intent:
                    # Check if the resource has "info" field with matching flavor and version
                    if hasattr(resource, "info") and resource.info:
                        info = resource.info
                        if (
                            info.flavour == flavor
                            and info.version == version
                            and not info.disabled
                        ):
                            matching_resources.append(resource)

            if not matching_resources:
                return json.dumps(
                    {
                        "success": False,
                        "instructions": f"Inform User: No matching resource with intent='{intent}', flavor='{flavor}', version='{version}' found in the running environment.",
                    },
                    indent=2,
                )

        except ApiException as e:
            return json.dumps(
                {
                    "success": False,
                    "instructions": f"Inform User: Error retrieving resources for environment '{cluster_id}': {e!s}",
                },
                indent=2,
            )

        # Step 4: Deploy the module by triggering hotfix deployment
        try:
            # Generate a unique release trace ID
            release_trace_id = str(uuid.uuid4())

            # Create facets resources for all matching resources
            facets_resources = []
            for selected_resource in matching_resources:
                facets_resource = FacetsResource()
                facets_resource.resource_name = selected_resource.resource_name
                facets_resource.resource_type = selected_resource.resource_type
                facets_resources.append(facets_resource)

            # Create hotfix deployment recipe with all resources
            recipe = HotfixDeploymentRecipe()
            recipe.resource_list = facets_resources

            # Call hotfix deployment API with release trace ID
            result = deployment_api.run_hotfix_deployment_recipe(
                body=recipe,
                cluster_id=cluster_id,
                allow_destroy=False,
                force_release=True,
                is_plan=False,
                can_queue=True,
                release_trace_id=release_trace_id,
            )

            # Get the initial status from the result
            initial_status = result.status if hasattr(result, "status") else None

            # Creating resource_names for display in the success message
            resource_names = [r.resource_name for r in matching_resources]

            return json.dumps(
                {
                    "success": True,
                    "message": f"Successfully triggered deployment of {len(matching_resources)} modules with intent='{intent}', flavor='{flavor}', version='{version}' to environment '{cluster_name}' in project '{project_name}'.",
                    "instructions": f"Use check_deployment_status(cluster_id='{cluster_id}', release_trace_id='{release_trace_id}') to monitor progress. Use get_deployment_logs(cluster_id='{cluster_id}', release_trace_id='{release_trace_id}') to get logs.",
                    "data": {
                        "resources_deployed": len(matching_resources),
                        "resource_names": resource_names,
                        "release_trace_id": release_trace_id,
                        "status": initial_status,
                        "cluster_id": cluster_id,
                        "cluster_name": cluster_name,
                        "project_name": project_name,
                    },
                },
                indent=2,
            )

        except ApiException as e:
            return json.dumps(
                {
                    "success": False,
                    "instructions": f"Inform User: Error deploying modules with intent='{intent}', flavor='{flavor}', version='{version}' to environment '{cluster_name}': {e!s}",
                },
                indent=2,
            )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Error in test_already_previewed_module tool: {e!s}",
            },
            indent=2,
        )


@mcp.tool()
def check_deployment_status(
    cluster_id: str,
    release_trace_id: str,
    wait: bool = False,
    timeout_seconds: int = 300,
    poll_interval_seconds: int = 5,
) -> str:
    """
    Check the status of a deployment.

    Args:
        cluster_id (str): The ID of the environment where the deployment is running
        release_trace_id (str): The release trace ID of the deployment to check
        wait (bool): If True, wait for the deployment to complete (either succeed or fail)
        timeout_seconds (int): Maximum time to wait for completion in seconds (default: 300s / 5min)
        poll_interval_seconds (int): Time between status checks in seconds (default: 5s)

    Returns:
        str: JSON with deployment status information
    """
    # Define in-progress states
    IN_PROGRESS_STATES = {"IN_PROGRESS", "STARTED", "QUEUED"}

    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        deployment_api = UiDeploymentControllerApi(api_client)

        # Start time for timeout calculation
        start_time = time.time()
        elapsed_time = 0

        # Initial status check
        try:
            deployment = deployment_api.get_deployment_by_release_trace_id(
                cluster_id=cluster_id, release_trace_id=release_trace_id
            )

            if not wait or deployment.status not in IN_PROGRESS_STATES:
                # Return immediately if not waiting or if already complete
                return json.dumps(
                    {
                        "success": True,
                        "message": f"Deployment {deployment.status}",
                        "data": {
                            "status": deployment.status,
                            "release_trace_id": release_trace_id,
                            "cluster_id": cluster_id,
                            "started_at": deployment.created_at.isoformat()
                            if hasattr(deployment, "created_at")
                            and deployment.created_at
                            else None,
                            "completed_at": deployment.completed_at.isoformat()
                            if hasattr(deployment, "completed_at")
                            and deployment.completed_at
                            else None,
                            "triggered_by": deployment.triggered_by
                            if hasattr(deployment, "triggered_by")
                            else None,
                            "elapsed_seconds": elapsed_time,
                        },
                    },
                    indent=2,
                )

            # If we're waiting, poll until completion or timeout
            while (
                deployment.status in IN_PROGRESS_STATES
                and elapsed_time < timeout_seconds
            ):
                # Sleep for poll interval
                time.sleep(poll_interval_seconds)

                # Update elapsed time
                elapsed_time = time.time() - start_time

                try:
                    # Check status again
                    deployment = deployment_api.get_deployment_by_release_trace_id(
                        cluster_id=cluster_id, release_trace_id=release_trace_id
                    )
                except ApiException as e:
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Error checking deployment status: {e!s}",
                            "data": {
                                "release_trace_id": release_trace_id,
                                "cluster_id": cluster_id,
                                "elapsed_seconds": elapsed_time,
                            },
                        },
                        indent=2,
                    )

            # Check if we timed out
            if (
                elapsed_time >= timeout_seconds
                and deployment.status in IN_PROGRESS_STATES
            ):
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Timed out after {timeout_seconds} seconds. Deployment still in progress.",
                        "data": {
                            "status": deployment.status,
                            "release_trace_id": release_trace_id,
                            "cluster_id": cluster_id,
                            "elapsed_seconds": elapsed_time,
                        },
                    },
                    indent=2,
                )

            # Deployment completed (either successfully or with failure)
            return json.dumps(
                {
                    "success": deployment.status == "SUCCEEDED",
                    "message": f"Deployment {deployment.status}",
                    "errors": None
                    if deployment.status == "SUCCEEDED"
                    else f"Deployment ended with status: {deployment.status}",
                    "data": {
                        "status": deployment.status,
                        "release_trace_id": release_trace_id,
                        "cluster_id": cluster_id,
                        "started_at": deployment.created_at.isoformat()
                        if hasattr(deployment, "created_at") and deployment.created_at
                        else None,
                        "completed_at": deployment.completed_at.isoformat()
                        if hasattr(deployment, "completed_at")
                        and deployment.completed_at
                        else None,
                        "triggered_by": deployment.triggered_by
                        if hasattr(deployment, "triggered_by")
                        else None,
                        "elapsed_seconds": elapsed_time,
                    },
                },
                indent=2,
            )

        except ApiException as e:
            if e.status == 404:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Deployment not found: {release_trace_id}",
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Error checking deployment status: {e!s}",
                    },
                    indent=2,
                )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Error in check_deployment_status tool: {e!s}",
            },
            indent=2,
        )


@mcp.tool()
def get_deployment_logs(cluster_id: str, release_trace_id: str) -> str:
    """
    Get logs for a specific deployment.

    Args:
        cluster_id (str): The ID of the environment where the deployment is running
        release_trace_id (str): The release trace ID of the deployment to get logs for

    Returns:
        str: JSON with deployment logs
    """
    try:
        # Initialize API client
        api_client = ClientUtils.get_client()
        deployment_api = UiDeploymentControllerApi(api_client)

        try:
            # First get the deployment to find the deployment ID
            deployment = deployment_api.get_deployment_by_release_trace_id(
                cluster_id=cluster_id, release_trace_id=release_trace_id
            )

            deployment_id = deployment.id if hasattr(deployment, "id") else None

            if not deployment_id:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Deployment ID not found for release trace ID: {release_trace_id}",
                    },
                    indent=2,
                )

            # Get deployment logs using the deployment ID
            logs_response = deployment_api.get_deployment_logs(
                cluster_id=cluster_id, deployment_id=deployment_id
            )

            # Extract log entries
            log_entries = []
            if hasattr(logs_response, "log_event_list"):
                log_entries = logs_response.log_event_list

            # Format logs for easier reading
            formatted_logs = []
            for log in log_entries:
                formatted_logs.append(log.get("message"))

            # Get current deployment status
            status = deployment.status if hasattr(deployment, "status") else "UNKNOWN"

            return json.dumps(
                {
                    "success": True,
                    "message": f"Successfully retrieved logs for deployment {release_trace_id}.",
                    "data": {
                        "release_trace_id": release_trace_id,
                        "cluster_id": cluster_id,
                        "status": status,
                        "log_count": len(formatted_logs),
                        "logs": formatted_logs,
                    },
                },
                indent=2,
            )

        except ApiException as e:
            if e.status == 404:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Deployment not found: {release_trace_id}",
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Error getting deployment logs: {e!s}",
                    },
                    indent=2,
                )

    except Exception as e:
        return json.dumps(
            {
                "success": False,
                "error": f"Error in get_deployment_logs tool: {e!s}",
            },
            indent=2,
        )
