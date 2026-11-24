---
license: openmdw-1.1
library_name: rt-detr-hand-detector-v1
---

# RT-DETR Hand Detection v1.0 Overview

## Description:  
RT-DETR Hand Detection v1.0 adapts the Real-Time Detection Transformer (RT-DETR) architecture to detect and localize hands directly in RGB images. The model combines a convolutional backbone with an efficient hybrid encoder and a TransformerDecoder head to predict 2D hand bounding boxes and class confidence scores in a single end-to-end pass. It is pre-trained on a diverse combination of synthetic and real-world egocentric hand datasets for 2D hand predictions that serve as regions-of-interest (ROIs) for downstream 3D hand pose estimation models. 

RT-DETR Hand Detection v1.0 was developed by NVIDIA based on RT-DETRv2-S.  
_This model is ready for commercial or non-commercial use._  



### License/Terms of Use:
Use of the associated model is governed by the [OpenMDW License Agreement, version 1.1](https://github.com/OpenMDW/OpenMDW/blob/main/1.1/LICENSE.OpenMDW-1.1).  

ADDITIONAL INFORMATION: [Apache License, Version 2.0.](https://www.apache.org/licenses/LICENSE-2.0)

### Deployment Geography:  
Global

### Use Case:  
RT-DETR Hand Detection v1.0 could be used by researchers and engineers working on egocentric perception to detect and localize hands directly from egocentric RGB images or video frames. The resulting 2D hand bounding boxes serve as a ROI crop that downstream models (e.g., EgoHand) use to predict 3D hand keypoints/mesh for the egocentric hand in the image. 

## Reference(s):
[RT-DETRv2: Improved Baseline with Bag-of-Freebies for Real-Time Detection Transformer](https://github.com/lyuwenyu/RT-DETR/tree/main/rtdetrv2_pytorch)  
[ONNX (Open Neural Network Exchange)](https://onnx.ai/) 
[EgoHand: Monocular 3D Hand Reconstruction from Egocentric Video](https://huggingface.co/nvidia/EgoHand-v1)

## Model Architecture:   
**Architecture Type:** Transformer   
**Network Architecture:** RT-DETR with HGNetv2-S Backbone + Efficient Hybrid Encoder + TransformerDecoder Head (with Discrete Sampling in deformable cross-attention)   
**This model was built upon Real-Time Detection Transformer v2 (RT-DETRv2) architecture.**  
**Number of model parameters:** \~20M  
  
 
## Input:  
**Input Type(s):** Image  
**Input Format(s):** Red, Green, Blue (RGB)  
**Input Parameters:** Two-Dimensional (2D)  
**Other Properties Related to Input:** Input images are resized to the model's fixed training resolution (640×640) prior to inference; no strict minimum source resolution is enforced, though very low-resolution inputs may reduce detection accuracy.  
  

## Output:  
**Output Type(s):** Other: Array  
**Output Format:** Other: Floating Point  
**Output Parameters:** One-Dimensional (1D): Per-detection [bounding box coordinates (x1, y1, x2, y2), class confidence score]  
**Other Properties Related to Output:** Reports bounding boxes for left hand and right hand (wearer-anatomical) as two separate classes, each with its own confidence score, directly from the detector's class head.  


Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.  

## Software Integration:
**Runtime Engine(s):** Not Applicable (N/A)  
**Supported Hardware Microarchitecture Compatibility:** NVIDIA Lovelace  
**Supported Operating System(s):** Linux  

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.  


## Model Version(s): 
RT-DETR-v2-S  

The model is exported to ONNX (Open Neural Network Exchange) format for deployment and integrated as the first stage of an egocentric hand-perception pipeline: it runs inference on each input RGB frame to produce left/right hand bounding boxes with confidence scores, which are consumed directly by a downstream tracking module (temporal/identity association across frames) and by 3D hand pose/mesh estimation models that use the bounding boxes as their region-of-interest input.  

 
## Training, Testing, and Evaluation Datasets:  

## Dataset Overview:  
**Total Size:** Less than a Million Images  
**Total Number of Datasets:** 3  
**Modality:** RGB image files  

## Training Dataset:

**Data Modality:** Image  

**Image Training Data Size:** Less than a Million Images  
**Data Collection Method by dataset:** Hybrid: Manually-Collected/Synthetic  
**Labeling Method by dataset:** Hybrid: Manually-Labeled, Synthetic  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):** The model is trained on a mix of egocentric synthetic and real-world hand motion image/video data, annotated with 2D bounding boxes for the left and right hands.  
* In-house real-world egocentric hand data: 43K RGB images of hand motion captured with head-mounted egocentric cameras, sourced from 3rd-party data vendors.  
* Synthetic data generated via a proprietary in-house rendering pipeline built on NVIDIA Omniverse: 26K photorealistic renders of hand motion with exact ground-truth 2D bounding boxes for the left and right hands.  

### Testing Dataset:  

**Data Collection Method by dataset:** Manually-Collected  
**Labeling Method by dataset:** Hybrid: Manually-Collected/Synthetic  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):** The testing dataset is a held-out 10% split (80% training / 10% testing / 10% evaluation) of the same mix of synthetic and real-world hand motion image/video data used for training, annotated with 2D bounding boxes for the left and right hands.  
* Number of items: 4.8K frames of real-world and 2.6K frames of synthetic egocentric hand data.  


### Evaluation Dataset:  

**Data Collection Method by dataset:** Manually-Collected  
**Labeling Method by dataset:** Hybrid: Manually-Collected/Synthetic  
**Benchmark Score:** Undisclosed  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):** The evaluation dataset is a held-out 10% split  (80% training / 10% testing / 10% evaluation) of the same mix of synthetic and real-world hand motion image/video data used for training, annotated with 2D bounding boxes for the left and right hands.  
* Number of items: 4.8K frames of real-world and 2.6K frames of synthetic egocentric hand data.  



## Inference:  
**Engine:** PyTorch  
**Acceleration Engine:** Other: None  
**Test Hardware:**  
* NVIDIA Lovelace L40  
* NVIDIA Lovelace L40s  


## Ethical Considerations:  
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.  
Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.  

For more detailed information on ethical considerations for this model, please see the Model Card++ [Bias](rtdetr-subcards/bias.md), [Explainability](rtdetr-subcards/explainability.md), [Safety & Security](rtdetr-subcards/safety_security.md), and [Privacy](rtdetr-subcards/privacy.md) Subcards.  

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).  
