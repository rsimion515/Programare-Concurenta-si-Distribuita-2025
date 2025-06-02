import os.path

from torchvision import datasets, transforms
from torch.utils.data import DataLoader

def get_loaders(data_dir, batch_size=16):
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    train_ds = datasets.ImageFolder(os.path.join(data_dir, "train"), transform=transform)
    test_ds = datasets.ImageFolder(os.path.join(data_dir, "test"), transform=transform)
    return (
        DataLoader(train_ds, batch_size=batch_size, shuffle=True),
        DataLoader(test_ds, batch_size=batch_size)
    )
