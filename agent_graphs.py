import os
import yaml
import logging
from agents.spell_checker_agent import SpellCheckerAgent
from agents.visual_qa_agent import VisualQAAgent

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml if it exists."""
    config_path = "config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config.yaml: {e}")
    return {}


# Load configuration
config = load_config()
agents_config = config.get("agents", {})

# Spell Checker Configuration
spell_config = agents_config.get("spell_checker", {})
spell_checker = SpellCheckerAgent(
    model=spell_config.get("model", "gemini-2.5-flash"),
    provider=spell_config.get("provider", "gemini"),
    temperature=spell_config.get("temperature", 0),
    max_text_length=spell_config.get("max_text_length", 10000),
    wait_time=spell_config.get("wait_time", 2000),
)

# Visual QA Configuration
visual_config = agents_config.get("visual_qa", {})
visual_qa = VisualQAAgent(
    model=visual_config.get("model", "gemini-2.5-flash"),
    provider=visual_config.get("provider", "gemini"),
    temperature=visual_config.get("temperature", 0),
    wait_time=visual_config.get("wait_time", 5000),
)

# Compile graphs
spell_checker_graph = spell_checker.compile()
visual_qa_graph = visual_qa.compile()
