# Quick Start Guide: DualGPUOptimizer

This guide will help you quickly set up and start using the DualGPUOptimizer for efficient ML model deployment across multiple GPUs.

## Prerequisites

- **Hardware**: Two NVIDIA GPUs (ideally with at least 8GB VRAM each)
- **Software**:
  - Windows 10/11 or Linux (Ubuntu 20.04+)
  - Python 3.12+ or Python 3.11 with compatible PyTorch
  - NVIDIA drivers 535.xx or newer

## Installation

### Method 1: Using Pre-built Binary (Windows)

1. Download the latest release from the GitHub releases page
2. Extract the zip file to a folder of your choice
3. Run `DualGPUOptimizer.exe`

### Method 2: From Source

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/DualGPUOptimizer.git
   cd DualGPUOptimizer
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Linux/Mac
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -e .

   # Install PyTorch with CUDA support
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

   # For Python 3.12 compatibility, install pre-release qdarktheme
   pip install --pre qdarktheme
   ```

4. Launch the application:
   ```bash
   python run_optimizer.py
   ```

## First Run: GPU Configuration

When you first launch the application:

1. The app will automatically detect your GPUs
2. The dashboard will show basic information about each GPU
3. If your NVIDIA drivers are not compatible, you'll see a warning message

## Optimizing Your First Model

### Step 1: Navigate to the Optimizer Tab

Click on the "Optimizer" tab to access GPU split optimization features.

### Step 2: Select a Model

1. Choose a model from the dropdown list (e.g., "Llama-2 7B")
2. Adjust the context length if needed (default values are appropriate for most cases)
3. For custom models, select "Custom" and enter the specific parameters

### Step 3: Calculate Optimal Split

1. Click the "Calculate Optimal Split" button
2. Review the results, which include:
   - Tensor parallel size
   - GPU split ratio
   - Maximum context length
   - Memory usage per GPU

### Step 4: Use Generated Commands

The optimizer generates two sets of commands:

1. **llama.cpp Tab**: Copy these parameters to use with llama.cpp
2. **vLLM Tab**: Copy these parameters to use with vLLM

## Running a Model with Optimization

### Step 1: Navigate to the Launcher Tab

Click on the "Launcher" tab to configure and run models.

### Step 2: Configure Launch Options

1. Select your framework (llama.cpp or vLLM)
2. Click "Browse" to select your model file
3. The optimizer will suggest optimal settings for:
   - GPU split ratio
   - Context size
   - Batch size

### Step 3: Launch the Model

1. Click "Launch Model" to start the inference engine
2. Monitor the output in the log window
3. Use the dashboard to track GPU utilization in real-time

## Memory Management

### VRAM Reset

If you encounter memory issues or want to clear GPU memory:

1. Click the "Reset VRAM" button in the Launcher tab
2. This forces CUDA to release cached memory

### Memory Monitoring

1. Enable the "Memory Monitor" checkbox for active monitoring
2. The system will notify you of high memory pressure
3. It will attempt to recover from out-of-memory conditions automatically

## Tips for Best Performance

- **Optimal GPU Pairing**: Pair your strongest GPU with the secondary one
- **Context Length**: Lower context lengths require less VRAM
- **Quantization**: Use quantized models (4-bit, 5-bit) for larger models
- **Batch Size**: Start with the recommended batch size; adjust based on your needs
- **Layer Balance**: Keep the "Optimize Layer Balance" option enabled for best performance

## Troubleshooting

- **CUDA errors**: Ensure your PyTorch version matches your CUDA version
- **Out of memory**: Try using a quantized model or reducing context length
- **Import errors**: Make sure all dependencies are properly installed
- **Black screen on startup**: Update your NVIDIA drivers

For more detailed guidance, refer to the full documentation in the `docs` folder.
