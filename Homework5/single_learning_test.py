import torch
import os

from FederatedLearning.utils.cnn_model import get_model
from FederatedLearning.utils.dataset import get_loaders

from FederatedLearning.utils.train import train
from FederatedLearning.utils.eval import test

def main():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {DEVICE}")

    # Set clinic path
    clinic_id = 'all'
    data_path = os.path.join('FederatedLearning/datasets', clinic_id)

    print("Using cuda:", torch.cuda.is_available())
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = get_model().to(DEVICE)
    trainloader, testloader = get_loaders(data_path)

    # Train for 5 epochs
    epochs = 5
    print(f"[INFO] Starting local training for {epochs} epochs...")
    for epoch in range(1, epochs + 1):
        optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
        train(model, trainloader, optimizer, DEVICE)

        # Evaluate after epoch
        accuracy = test(model, testloader, DEVICE)
        print(f"[INFO] Epoch {epoch} - Accuracy: {accuracy:.4f}")

    print("[INFO] Training finished.")

if __name__ == "__main__":
    main()