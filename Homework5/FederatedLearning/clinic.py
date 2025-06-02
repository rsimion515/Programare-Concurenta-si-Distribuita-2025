import argparse
import os.path

import flwr as fl
import torch

from utils.cnn_model import get_model
from utils.train import train
from utils.eval import test

from utils.dataset import get_loaders


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Federated client for pneumonia detection")
parser.add_argument("--clinic", type=str, required=True, help="Clinic ID: a, b, or c")
args = parser.parse_args()

# Set clinic path
clinic_id = args.clinic.lower()
data_path = os.path.join('datasets', clinic_id)

print("Using cuda:", torch.cuda.is_available())
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = get_model().to(DEVICE)
trainloader, testloader = get_loaders(data_path)

def set_parameters(parameters):
    state_dict = model.state_dict()
    for k, v in zip(state_dict.keys(), parameters):
        state_dict[k] = torch.tensor(v)
    model.load_state_dict(state_dict)


class FlowerClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        return [val.cpu().numpy() for val in model.state_dict().values()]

    def fit(self, parameters, config):
        set_parameters(parameters)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
        train(model, trainloader, optimizer, DEVICE)
        return self.get_parameters(config={}), len(trainloader.dataset), {}

    def evaluate(self, parameters, config):
        set_parameters(parameters)
        accuracy = test(model, testloader, DEVICE)
        print(f"[Client] Evaluation -> Accuracy: {accuracy:.4f}")

        return 0.0, len(testloader.dataset), {"accuracy": float(accuracy)}

if __name__ == "__main__":
    fl.client.start_numpy_client(server_address="localhost:8080", client=FlowerClient())
