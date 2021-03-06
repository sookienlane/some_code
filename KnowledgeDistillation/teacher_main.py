from tqdm import tqdm
from KnowledgeDistillation.dataset import ImageTrainDataset, ImageValDataset
from KnowledgeDistillation.model import get_model
from KnowledgeDistillation.utils import val_transform
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


seed = 2020
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.manual_seed(seed)
np.random.seed(seed)

############# model ##################
model_name = "densenet"
model = get_model(model_name)
model.to(device)

#### data loader #######
train_path = "raw_data/tiny-imagenet-200/train/"
val_path = "raw_data/tiny-imagenet-200/val/"
train_dataset = ImageTrainDataset(train_path, val_transform)
val_dataset = ImageValDataset(val_path, val_transform, train_dataset.label2index_dict)
train_dataloader = torch.utils.data.DataLoader(train_dataset,batch_size=128,shuffle=True,num_workers=4)
val_dataloader = torch.utils.data.DataLoader(val_dataset,batch_size=128,shuffle=False,num_workers=4)
##################
learning_rate = 0.01
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

#####################
best_acc = 0.0

for epoch in range(50):

    model.train()
    running_loss = 0.0
    right_total = 0.0
    total_total = 0.0
    t = tqdm(enumerate(train_dataloader), total=train_dataloader.__len__(), leave=True)
    for i, data in t:
        feature, label = data.get("feature").to(device), data.get("label").to(device)
        optimizer.zero_grad()
        output = model(feature)
        loss = criterion(output, label)
        loss.backward()
        optimizer.step()

        _, predicted = torch.max(output, 1)
        right = (predicted == label).sum().item()
        total = label.size(0)
        running_loss += loss.item()
        right_total += right
        total_total += total
        t.set_description("Epoch is {}, Loss is {}. Acc is {}".format(epoch, np.round(running_loss / (i + 1), 5),
                                                         np.round(right_total / total_total * 100, 5)))
        t.refresh()  # to show immediately the update

    model.eval()
    with torch.no_grad():
        correct = 0
        total = 0
        for data_one in val_dataloader:
            images, labels = data_one.get("feature").to(device), data_one.get("label").to(device)
            outputs = model(images)
            # import pdb; pdb.set_trace()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    print('Epoch is {}, and accuracy is {}'.format(epoch, 100 * correct / total))

    # scheduler.step()
    if correct / total > best_acc:
        best_acc = correct / total

        PATH = 'models/model_{}_new.pth'.format(model_name)
        print("#######Save best is {}########".format(np.round(best_acc, 4)))
        torch.save(model.state_dict(), PATH)