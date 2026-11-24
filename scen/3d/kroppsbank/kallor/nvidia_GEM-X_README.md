---
license: other
license_name: nvidia-open-model-license
license_link: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/
tags:
  - pose-estimation
  - human-motion
  - soma-body-model
  - video
  - monocular-video
  - 3d-pose
  - transformer
library_name: gem
---

# GEM Overview

## Description:

Generalist Model for Human Motion (GEM) is a monocular video 3D human body pose estimation model developed by NVIDIA. GEM reconstructs full-body motion — including body and hands — from unconstrained video sequences with dynamic cameras, producing accurate per-frame 3D body pose and world-space global motion trajectories in SOMA (Unifying Parametric Human Body Models) format. The model outputs 77-joint poses using the SOMA parametric body model, recovering both local body kinematics and global motion trajectories from monocular video.
All training data and the SOMA parametric body model are owned by NVIDIA or released under permissive licenses, making GEM ready for commercial use.  
GEM was developed by NVIDIA.  
*This model is ready for commercial or non-commercial use.*

This card describes temporal Body Motion. This repository also distributes
Body Pose weights for image inputs. Hand Pose uses the official
[EgoHand-v1 checkpoint](https://huggingface.co/nvidia/EgoHand-v1),
distributed separately by the EgoHand project. The table below identifies
the model configurations and their roles.

### License/Terms of Use:

Use of the source code is governed by the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). Use of the associated model is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).

### Deployment Geography:

Global

### Use Case:

GEM is intended for use by individuals and professionals in fields such as machine learning and computer vision research, gaming, animation, 3D content creation, and biomechanics. Specific use cases include:

- Motion capture from video — reconstruct accurate 3D body pose and global motion trajectories from monocular video with dynamic cameras, useful for recovering full-body motion in unconstrained environments.
- Character animation — create realistic full-body character animations derived from real video footage for gaming and film applications.
- Digital humans — drive SOMA-compatible avatar rigs directly from video input.
- Biomechanical analysis — study human movement for applications in sports, rehabilitation, and medicine.



### Release Date:

**GitHub:** 10/30/2026 via [https://github.com/NVlabs/GEM-X](https://github.com/NVlabs/GEM-X)  
**HuggingFace:** 10/30/2026 via [https://huggingface.co/nvidia/GEM-X](https://huggingface.co/nvidia/GEM-X)  

## Reference(s):

[https://arxiv.org/abs/2505.01425](https://arxiv.org/abs/2505.01425)  

## Model Architecture:

**Architecture Type:** Transformer  
**Network Architecture:** 12-layer temporal Transformer, hidden size 512, 8 attention heads<br>
**This model was developed based on Not Applicable (N/A).**  
**Number of model parameters:** 46.8M total temporal Motion parameters (46,762,136), including 44.2M trainable parameters (44,202,136). This excludes the separate Body Pose feature extractor, Hand Pose model, and detectors.

## Computational Load

**Cumulative Compute:** 1.9x10^19 FLOP  
**Estimated Energy and Emissions for Model Training:** 58 kWh  

## Input:

**Input Type(s):** Video, Other: person bounding box, camera intrinsics

**Input Format(s):**

- Video: RGB tensor `(T, H, W, 3)`, any resolution, internally processed via the frozen Body Pose image encoder
- Other — person bounding box: `(T, 4)` float array in `xyxy` pixel coordinates
- Other — camera intrinsics: `(T, 3, 3)` float array of per-frame camera intrinsic matrices containing focal lengths and principal-point coordinates

**Input Parameters:**

- Video: Three-Dimensional (3D)
- Other — person bounding box: One-Dimensional (1D) four-value vector per frame, batched as `(T, 4)`
- Other — camera intrinsics: Two-Dimensional (2D) 3 × 3 matrix per frame, batched as `(T, 3, 3)`

**Other Properties Related to Input:** The RGB video pipeline detects and tracks one person, extracts 77-joint 2D observations and frozen Body Pose query features, and prepares camera-motion and frame-time conditions. The temporal Motion network consumes these prepared conditions rather than RGB pixels directly. The bounding box and camera intrinsics determine the three-value CLIFF conditioning for each frame. Cached inputs can carry per-frame intrinsics; the RGB video command accepts a constant calibration matrix for the clip or estimates one when it is not supplied.

## Output:

**Output Type(s):** Other: Human body motion in SOMA format (world-space)  
**Output Format:** Tensor  
**Output Parameters:** Three-Dimensional (3D)  
**Other Properties Related to Output:** Three-Dimensional (3D) per-frame body parameters  

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.

## Software Integration:

**Runtime Engine(s):** PyTorch for Body Pose feature extraction and temporal Motion inference; ONNX Runtime for optional person detection  
**Supported Hardware Microarchitecture Compatibility:** NVIDIA Ampere  
**Supported Operating System(s):**

- Linux
- Windows
- macOS

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.  

## Model Version(s):

GEM v1.1  

An installable Python package provides the `gem-infer`, `gem-render`, `gem-train`, and `gem-eval` entry points. Body Motion inference uses `gem-infer motion-video --task body` for RGB video or `gem-infer motion-cache --task body` for prepared conditions. The package requires Python 3.10 or newer. The validated CUDA runtime uses PyTorch 2.10 and SOMA 0.3.3 with separately supplied model weights and geometry assets. Mesh/video rendering uses the documented x86/Open3D 0.19 environment.  
 

## Pretrained Checkpoint Bundle

The unified code supports Body Pose, Hand Pose and Body Motion. This repository
provides the Body Pose and Body Motion weights; obtain Hand Pose weights from
the official EgoHand-v1 repository. The Body Pose export contains model
weights for inference and fine-tuning initialization, without optimizer or
training-loop state. It is not a full training-resume checkpoint.

| Component | Weights | Configuration / companion files |
| --- | --- | --- |
| Body Pose | [body_s240000.ckpt](https://huggingface.co/nvidia/GEM-X/resolve/main/body_s240000.ckpt) | [body_config.json](https://huggingface.co/nvidia/GEM-X/blob/main/body_config.json); preset `body` |
| Hand Pose | [egohand_s060000.ckpt — official EgoHand-v1](https://huggingface.co/nvidia/EgoHand-v1/blob/main/egohand_s060000.ckpt) | Built-in preset `hand`; includes the learned RLE density used for fine-tuning |
| Body Motion native77 | [motion_native77_e774_s292175.ckpt](https://huggingface.co/nvidia/GEM-X/resolve/main/motion_native77_e774_s292175.ckpt) | [motion_stats_raw.npz](https://huggingface.co/nvidia/GEM-X/resolve/main/motion_stats_raw.npz) and [motion_native77.yaml](https://huggingface.co/nvidia/GEM-X/blob/main/motion_native77.yaml) |
| Original native77 ViTPose | [vitpose.pth](https://huggingface.co/nvidia/GEM-X/resolve/main/vitpose.pth) | Used by [body_video_native77.yaml](https://huggingface.co/nvidia/GEM-X/blob/main/body_video_native77.yaml) |

The video recipe pairs the original final775 Motion weights with Body Pose
s240000 features and the existing original ViTPose detector. The experimental
random-blur epoch10 detector is not included in this release bundle.

Download the Body Pose and Body Motion files together, preserving their relative placement:

```bash
hf download nvidia/GEM-X \
  body_s240000.ckpt body_config.json \
  motion_native77_e774_s292175.ckpt motion_stats_raw.npz \
  motion_native77.yaml body_video_native77.yaml vitpose.pth \
  --local-dir weights
```

Download Hand Pose separately from its official repository using a Hugging Face
account with access to that repository:

```bash
hf auth login
hf download nvidia/EgoHand-v1 egohand_s060000.ckpt --local-dir weights
```

Use `--task hand --release hand` for image inference and the public
`docs/configs/hand_finetune.yaml` recipe for fine-tuning initialization.
Access and the checkpoint license are managed by the
[EgoHand-v1 model card](https://huggingface.co/nvidia/EgoHand-v1).
These Hand weights are not redistributed in GEM-X.

The video YAML resolves checkpoint paths relative to its own directory. Obtain
the YOLOX HumanArt person detector separately as `weights/yolox_humanart.onnx`,
or change that path in the YAML. SOMA 0.3.3 geometry assets and an optional
[RT-DETR Hand detector](https://huggingface.co/nvidia/RT-DETR-Hand-Detector-v1) are also supplied separately. Follow the
[GEM-X installation and inference guides](https://github.com/NVlabs/GEM-X)
for these prerequisites and the unified command-line interface.

## Training, Testing, and Evaluation Datasets:



## Training Dataset:

**Data Modality:**

- Video  
- Image

**Image Training Data Size:** 1 Million to 1 Billion Images  
**Video Training Data Size:** Less than 10,000 Hours  
**Data Collection Method by dataset:** Hybrid: Automated/Synthetic  
**Labeling Method by dataset:** Hybrid: Automated/Synthetic  
**Properties:** Quantity: The training dataset contains 1 million images and 300 hours of video. Modalities: Image and video. Content nature: The dataset combines synthetic human-motion video rendered from NVIDIA in-house motion-capture data with real-world visual data released under licenses compatible with commercial use; annotations are generated automatically by models released under licenses compatible with commercial use. Linguistic characteristics: Not applicable because the dataset contains no text, speech, or other natural-language modality. Sensor(s): Not specified for the real-world subset and not applicable to the synthetically rendered subset.

### Testing Dataset:

**Data Collection Method by dataset:** Synthetic  
**Labeling Method by dataset:** Synthetic  
**Properties:** Quantity: The testing dataset contains 5,000 held-out synthetically rendered RGB video clips from the same rendering pipeline used for training. Modality: Video. Content nature: The dataset consists of machine-generated human-motion scenes with automatically generated synthetic ground-truth labels and does not overlap with the training split. Linguistic characteristics: Not applicable because the dataset contains no text, speech, or other natural-language content. Sensor(s): Not applicable because the videos are synthetically rendered.

### Evaluation Dataset:

**Benchmark Score:** W-MPJPE: 100.2 mm


| Benchmark | Metric       | Score |
| --------- | ------------ | ----- |
| Internal  | W-MPJPE (mm) | 100.2 |


**Data Collection Method by dataset:** Synthetic  
**Labeling Method by dataset:** Synthetic  
**Properties:** This is the same held-out split described under Testing Dataset. Quantity: The evaluation dataset contains 5,000 held-out synthetically rendered RGB video clips from the same rendering pipeline used for training. Modality: Video. Content nature: The dataset consists of machine-generated human-motion scenes with automatically generated synthetic ground-truth labels and does not overlap with the training split. Linguistic characteristics: Not applicable because the dataset contains no text, speech, or other natural-language content. Sensor(s): Not applicable because the videos are synthetically rendered.

## Inference:

**Acceleration Engine:** PyTorch with CUDA
**Hardware Requirements (GPU Architecture, Model):**  NVIDIA Ampere A100 80GB

## Ethical Considerations:

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.  
Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.  
For more detailed information on ethical considerations for this model, please see the Model Card++ Explainability, Bias, Safety & Security, and Privacy Subcards.  
Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

For more detailed information on ethical considerations for this model, please see the Model Card++ [Bias](./gem-subcards/bias.md), [Explainability](./gem-subcards/explainability.md), [Safety & Security](./gem-subcards/safety_security.md), and [Privacy Subcards](./gem-subcards/privacy.md).   
 
