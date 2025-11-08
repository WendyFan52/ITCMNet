1- md3_original-convnext is the ITCMNet code.
(1)  Environment Configuration: md3_original-convnext_environment.yml
(2)  The code is based on a customized modification of MMDetection 3.0 (https://github.com/open-mmlab/mmdetection). For some general problems, please refer to the official MMDetection documentation. 
(3) Train-set, test-set and val-set are put in data folder. 
(4) annotations_s contains segmentation annotations only.
annotations_c includes species classification annotations, used for both segmentation and classification tasks.
annotations_v includes vitality classification annotations, used for both segmentation and classification tasks.
annotations_cv contains both species and vitality annotations, enabling joint segmentation and classification.

Train-set, test-set and val-set images could be downloaded from Bamberg_coco2048.zip (30 GB) in BAMFORESTS (https://www.dlr.de/en/eoc/about-us/remote-sensing-technology-institute/photogrammetry-and-image-analysis/public-datasets/bamforests). Please download and put Train-set, test-set and val-set images in the train2017, test2017, val2017 folder.

Please select the corresponding annotations folder when performing training, validation, or inference. The folder name should remain as 'annotations'.
(5) If you need to retrain and retest:
Train：
python .\tools\train.py .\projects\ConvNeXt-V2\configs\mask-rcnn_convnext-v2-b_fpn_lsj-3x-fcmae_coco.py
Test：
python .\tools\test.py .\work_dirs\mask-rcnn_convnext-v2-b_fpn_lsj-3x-fcmae_coco\mask-rcnn_convnext-v2-b_fpn_lsj-3x-fcmae_coco.py .\work_dirs\mask-rcnn_convnext-v2-b_fpn_lsj-3x-fcmae_coco\epoch.pth --show-dir out

(6) Use the trained model and checkpoint file: 
python ./predict.py
