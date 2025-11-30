Here is the link to our Edge Impulse Public project, where we imported the dataset, started labeling, and ran several model tests to detect hornets and bees. 
We currently use three classes: hornets, bees (group) when multiple bees appear together, and bee (single) when only one bee is visible. 
So far, we have labeled around 200 images, and we tested different model architectures. The most promising results come from a YOLO-based model, which reaches a precision score of 70 % on the training set and 37,32 % accuracy on the test set. 

https://studio.edgeimpulse.com/public/798417/live

Throughout the project, we explored a wide range of tools provided by Edge Impulse to build our hornet-detection pipeline. 
We started with the Data Acquisition module, manually labeling hundreds of images, then experimented with AI-assisted annotation using both Bounding Box Labelling with OWL-ViT and Bounding Box Relabelling powered by a GPT-4 API key. These approaches produced promising results, but still required significant refinement, and we are currently working on improving the prompting strategy to achieve more reliable labels across the full dataset. 

We then used the EON Tuner to identify the best model architecture before training detection models with YOLO Pro. 
After validation and testing, we attempted deployment on embedded hardware. However, because yellow-legged hornets disappear naturally around mid-November when temperatures drop, we were unable to perform real-world field tests on active hives this season. 

Despite this limitation, the combination of data tools, AI-assisted labeling, model tuning, YOLO-based training, and hardware deployment provided a strong foundation for the next development cycle of BeeGuardAI.
