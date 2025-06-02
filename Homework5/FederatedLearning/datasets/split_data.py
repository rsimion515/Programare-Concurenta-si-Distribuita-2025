import os
import shutil

folders = [
    'a',
    'b',
    'c'
]

count = 0
for test_type in ["train", "test"]:
    for result in ["NORMAL", "PNEUMONIA"]:
        folder = f"all\\{test_type}\\{result}"

        for image in os.listdir(folder):
            file = os.path.join(folder, image)
            dest_file = f"{folders[count]}\\{test_type}\\{result}\\{image}"

            shutil.copy(file, dest_file)

            count = (count + 1) % 3