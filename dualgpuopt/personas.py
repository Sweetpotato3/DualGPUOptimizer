"""
Personas module for DualGPUOptimizer
Provides functionality for managing different AI personas in chat
"""
import json
from pathlib import Path
import logging
from typing import Dict, Optional

logger = logging.getLogger("DualGPUOpt.Personas")

# Default personas
DEFAULT_PERSONAS = {
    "Assistant": {
        "description": "A helpful, harmless, and honest assistant",
        "system_prompt": "You are a helpful, harmless, and honest assistant.",
        "greeting": "Hello! I'm your AI assistant. How can I help you today?",
        "temperature": 0.7,
        "top_p": 0.9,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
    },
    "Programmer": {
        "description": "A coding expert specializing in AI and GPU optimization",
        "system_prompt": "You are an expert programmer specializing in AI systems, GPU optimization, and high-performance computing. Provide detailed, accurate coding advice with a focus on optimizing performance for GPU-accelerated workloads.",
        "greeting": "Hello! I'm your programming assistant specializing in AI and GPU optimization. What coding challenge are you working on?",
        "temperature": 0.3,
        "top_p": 0.9,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
    },
    "Tutor": {
        "description": "An educational assistant focused on explaining AI concepts",
        "system_prompt": "You are a patient and knowledgeable tutor specializing in explaining artificial intelligence, machine learning, and deep learning concepts in simple terms. Break down complex ideas into understandable explanations.",
        "greeting": "Hi there! I'm your AI tutor. What concept would you like me to explain today?",
        "temperature": 0.5,
        "top_p": 0.9,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0
    }
}

def get_personas_path():
    """Get the path to the personas file

    Returns:
        Path: Path to the personas file
    """
    # Try to use home directory for configuration
    home_dir = Path.home() / ".dualgpuopt"

    # Create directory if it doesn't exist
    try:
        home_dir.mkdir(exist_ok=True)
        return home_dir / "personas.json"
    except Exception as e:
        logger.warning(f"Failed to create config directory in home: {e}")

    # Fallback to current directory if home directory is not accessible
    return Path("personas.json")

def list_personas() -> Dict:
    """Get all available personas

    Returns:
        dict: Dictionary of persona configurations
    """
    personas_path = get_personas_path()
    personas = DEFAULT_PERSONAS.copy()

    try:
        if personas_path.exists():
            with open(personas_path, "r") as f:
                user_personas = json.load(f)
                personas.update(user_personas)
                logger.info(f"Loaded {len(user_personas)} custom personas from {personas_path}")
    except Exception as e:
        logger.error(f"Error loading personas: {e}")

    return personas

def get_persona(name: str) -> Optional[Dict]:
    """Get a specific persona by name

    Args:
        name: Name of the persona to get

    Returns:
        dict: Persona configuration or None if not found
    """
    personas = list_personas()
    return personas.get(name)

def add_persona(name: str, config: Dict) -> bool:
    """Add or update a persona

    Args:
        name: Name of the persona
        config: Persona configuration

    Returns:
        bool: True if successful, False otherwise
    """
    personas_path = get_personas_path()

    try:
        # Load existing personas first
        if personas_path.exists():
            with open(personas_path, "r") as f:
                try:
                    personas = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid personas file, creating new one")
                    personas = {}
        else:
            personas = {}

        # Add or update the persona
        personas[name] = config

        # Save back to file
        with open(personas_path, "w") as f:
            json.dump(personas, f, indent=2)

        logger.info(f"Added/updated persona: {name}")
        return True
    except Exception as e:
        logger.error(f"Error saving persona {name}: {e}")
        return False

def delete_persona(name: str) -> bool:
    """Delete a persona

    Args:
        name: Name of the persona to delete

    Returns:
        bool: True if successful, False otherwise
    """
    personas_path = get_personas_path()

    try:
        # Load existing personas
        if not personas_path.exists():
            logger.warning(f"Personas file does not exist")
            return False

        with open(personas_path, "r") as f:
            try:
                personas = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Invalid personas file")
                return False

        # Check if persona exists
        if name not in personas:
            logger.warning(f"Persona {name} not found")
            return False

        # Delete the persona
        del personas[name]

        # Save back to file
        with open(personas_path, "w") as f:
            json.dump(personas, f, indent=2)

        logger.info(f"Deleted persona: {name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting persona {name}: {e}")
        return False

def reset_to_defaults() -> bool:
    """Reset personas to defaults

    Returns:
        bool: True if successful, False otherwise
    """
    personas_path = get_personas_path()

    try:
        # Save default personas to file
        with open(personas_path, "w") as f:
            json.dump(DEFAULT_PERSONAS, f, indent=2)

        logger.info(f"Reset personas to defaults")
        return True
    except Exception as e:
        logger.error(f"Error resetting personas: {e}")
        return False