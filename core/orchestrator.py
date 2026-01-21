"""Orchestrator for running multiple agents."""

import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents import SpellCheckerAgent, VisualQAAgent
from core.exceptions import AgentValidatorError
from utils.validation_utils import validate_url
from utils.progress_utils import ProgressTracker

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrate multiple validation agents."""

    AGENT_REGISTRY = {
        "spell_checker": SpellCheckerAgent,
        "visual_qa": VisualQAAgent,
    }

    def __init__(
        self, config: Optional[Dict[str, Any]] = None, show_progress: bool = True
    ):
        """
        Initialize orchestrator.

        Args:
            config: Configuration dictionary
            show_progress: Whether to show progress bars (default: True)
        """
        self.config = config or {}
        self._agents: Dict[str, Any] = {}
        self.show_progress = show_progress
        self.progress_tracker: Optional[ProgressTracker] = None

    def register_agent(self, name: str, agent_instance: Any) -> None:
        """
        Register a custom agent instance.

        Args:
            name: Agent name
            agent_instance: Agent instance
        """
        self._agents[name] = agent_instance
        logger.info(f"Registered agent: {name}")

    def create_agent(self, agent_name: str, agent_config: Dict[str, Any]) -> Any:
        """
        Create an agent instance from configuration.

        Args:
            agent_name: Name of the agent type
            agent_config: Agent configuration

        Returns:
            Agent instance

        Raises:
            AgentValidatorError: If agent type is unknown
        """
        if agent_name in self._agents:
            return self._agents[agent_name]

        agent_class = self.AGENT_REGISTRY.get(agent_name)
        if not agent_class:
            raise AgentValidatorError(f"Unknown agent type: {agent_name}")

        # Extract agent-specific config
        agent_instance = agent_class(**agent_config)
        self._agents[agent_name] = agent_instance

        logger.info(f"Created agent: {agent_name}")
        return agent_instance

    def run_agent(
        self,
        agent_name: str,
        url: str,
        agent_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run a single agent on a URL.

        Args:
            agent_name: Name of the agent to run
            url: URL to validate
            agent_config: Optional agent configuration
            **kwargs: Additional parameters for the agent

        Returns:
            Result dictionary with agent output
        """
        url = validate_url(url)
        agent_config = agent_config or {}

        try:
            agent = self.create_agent(agent_name, agent_config)

            # Set up progress tracking
            if self.progress_tracker:
                # Extract domain from URL for cleaner display
                from urllib.parse import urlparse
                from rich.markup import escape

                parsed_url = urlparse(url)
                display_url = parsed_url.netloc or url

                # Escape the agent name and URL to prevent markup interpretation
                escaped_agent = escape(f"[{agent.name}]")
                escaped_url = escape(f"[{display_url}]")

                task_key = self.progress_tracker.start_task(
                    agent_name=agent.name,
                    description=f"[bold cyan]{escaped_agent}[/bold cyan][yellow]{escaped_url}[/yellow] [dim]Starting...[/dim]",
                    total=3,  # Most agents have 3 steps
                )

                def progress_callback(step_name: str, advance: int = 1):
                    """Progress callback for agent."""
                    if self.progress_tracker:
                        # Format: [AgentName][domain] step description with colors
                        full_description = f"[bold cyan]{escaped_agent}[/bold cyan][yellow]{escaped_url}[/yellow] [green]{step_name}[/green]"
                        self.progress_tracker.update_task(
                            task_key,
                            advance=advance,
                            description=full_description,
                        )

                agent.set_progress_callback(progress_callback)

            logger.info(f"Running {agent_name} on {url}")
            result = agent.run(url, **kwargs)

            # Complete the progress task
            if self.progress_tracker:
                self.progress_tracker.complete_task(agent.name)

            return {
                "agent": agent.name,
                "url": url,
                "success": True,
                "report": result.get("report", ""),
                "errors": result.get("errors", []),
                "issues": result.get("issues", []),
                "raw_result": result,
            }

        except Exception as e:
            logger.error(f"Agent {agent_name} failed on {url}: {e}")
            return {
                "agent": agent_name,
                "url": url,
                "success": False,
                "error": str(e),
                "report": f"Error: {str(e)}",
            }

    def run_multiple_agents(
        self, url: str, agent_names: List[str], parallel: bool = False, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Run multiple agents on a single URL.

        Args:
            url: URL to validate
            agent_names: List of agent names to run
            parallel: Run agents in parallel (default: sequential)
            **kwargs: Additional parameters for agents

        Returns:
            List of result dictionaries
        """
        url = validate_url(url)
        results = []

        # Create progress tracker if enabled
        with ProgressTracker(show_progress=self.show_progress) as progress:
            self.progress_tracker = progress

            if parallel:
                logger.info(f"Running {len(agent_names)} agents in parallel on {url}")
                with ThreadPoolExecutor(max_workers=len(agent_names)) as executor:
                    futures = {}
                    for agent_name in agent_names:
                        agent_config = self.config.get("agents", {}).get(agent_name, {})
                        future = executor.submit(
                            self.run_agent, agent_name, url, agent_config, **kwargs
                        )
                        futures[future] = agent_name

                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            agent_name = futures[future]
                            logger.error(
                                f"Parallel execution failed for {agent_name}: {e}"
                            )
                            results.append(
                                {
                                    "agent": agent_name,
                                    "url": url,
                                    "success": False,
                                    "error": str(e),
                                }
                            )
            else:
                logger.info(f"Running {len(agent_names)} agents sequentially on {url}")
                for agent_name in agent_names:
                    agent_config = self.config.get("agents", {}).get(agent_name, {})
                    result = self.run_agent(agent_name, url, agent_config, **kwargs)
                    results.append(result)

            self.progress_tracker = None

        return results

    def run_targets(
        self, targets: List[Dict[str, Any]], parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Run agents on multiple targets from configuration.

        Args:
            targets: List of target configurations
            parallel: Run agents in parallel for each target

        Returns:
            List of all results
        """
        all_results = []

        for target in targets:
            url = target.get("url")
            if not url:
                logger.warning("Target missing URL, skipping")
                continue

            agent_names = target.get("agents", [])
            if not agent_names:
                # Use all enabled agents
                agent_names = [
                    name
                    for name, config in self.config.get("agents", {}).items()
                    if config.get("enabled", True)
                ]

            logger.info(f"Processing target: {url}")
            results = self.run_multiple_agents(url, agent_names, parallel=parallel)
            all_results.extend(results)

        return all_results

    def get_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from results.

        Args:
            results: List of result dictionaries

        Returns:
            Summary dictionary
        """
        total = len(results)
        passed = sum(1 for r in results if r.get("success", False))
        failed = total - passed

        total_errors = sum(len(r.get("errors", [])) for r in results)
        total_issues = sum(len(r.get("issues", [])) for r in results)

        return {
            "total_validations": total,
            "passed": passed,
            "failed": failed,
            "total_spelling_errors": total_errors,
            "total_visual_issues": total_issues,
            "total_problems": total_errors + total_issues,
        }
