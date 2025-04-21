"""
Test script for the model_profiles module, specifically the apply_profile function.
"""
import json
import logging
from dualgpuopt.model_profiles import apply_profile, get_model_profile

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ModelProfilesTest")

def test_apply_profile():
    """Test the apply_profile function with different GPU configurations"""
    models_to_test = [
        "llama2-7b",
        "llama2-13b",
        "mixtral-8x7b",
        "mistral-7b"
    ]

    gpu_configs = [
        {"0": 24.0, "1": 24.0},  # Equal GPUs
        {"0": 24.0, "1": 12.0},  # Primary larger
        {"0": 8.0},             # Single GPU
        {"0": 8.0, "1": 8.0, "2": 8.0}  # Three GPUs
    ]

    quantization_types = [None, "int8", "q4_k_m"]

    results = {}

    logger.info("Testing apply_profile function...")

    for model in models_to_test:
        model_results = {}

        for gpu_config in gpu_configs:
            config_name = "+".join([f"{v}GB" for v in gpu_config.values()])
            config_results = {}

            for quant in quantization_types:
                try:
                    # Get the profile first for reference
                    get_model_profile(model, quant)
                    logger.info(f"Testing {model} with {quant or 'no'} quantization on {conf" +
                    "ig_name}")

                    # Apply the profile
                    result = apply_profile(model, gpu_config, quant)

                    # Log key information
                    logger.info(f"  Memory required: {result['memory_required']:.2f} GB")
                    logger.info(f"  Max batch size: {result['max_batch_size']}")

                    if len(gpu_config) == 2:
                        logger.info(f"  Split ratio: {result['split_ratio'][0]:.2f}/{result[" +
                        "'split_ratio'][1]:.2f}")

                        # Verify some layer distribution
                        primary_layers = sum(
                                             1 for layer,
                                             gpu in result['device_map'].items()
                        )                                          if int(gpu) == int(list(gpu_config.keys())[0]))
                        total_layers = len(result['device_map'])
                        primary_pct = primary_layers / total_layers
                        logger.info(f"  Primary GPU layers: {primary_layers}/{total_layers} " +
                        "({primary_pct:.2f})")

                        # Verify the split ratio matches the layer distribution (approximately)
                        assert abs(primary_pct - result['split_ratio'][0]) < 0.1, \
                            f"Split ratio {result['split_ratio'][0]:.2f} doesn't" +
                            " match layer distribution {primary_pct:.2f}"

                    # Save results
                    quant_key = quant or "none"
                    config_results[quant_key] = {
                        "memory_required": result["memory_required"],
                        "max_batch_size": result["max_batch_size"],
                        "split_ratio": result["split_ratio"] if "split_ratio" in result else None,
                        "layer_count": len(result["device_map"]) if "device_map" in result else 0
                    }

                except Exception as e:
                    logger.error(f"Error testing {model} with {quant} on {config_name}: {e}")
                    config_results[quant or "none"] = {"error": str(e)}

            model_results[config_name] = config_results

        results[model] = model_results

    # Save results to JSON file
    with open("profile_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("Tests completed. Results saved to profile_test_results.json")
    return results

if __name__ == "__main__":
    test_apply_profile()