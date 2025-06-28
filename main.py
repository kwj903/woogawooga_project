import torch, torchvision, cv2
print(torch.__version__)  # 2.7.1  출력
print(torchvision.__version__)  # 0.22.1 출력
print(cv2.__version__)  # 4.11.0  출력
print("CUDA?", torch.cuda.is_available())
