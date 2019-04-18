"""
Initial DCGAN implementation

Based on https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html

Repurposed to use Aurora Borealis images instead

"""

import argparse
import os
import numpy as np
import random
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.optim as optim
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import sagemaker_containers

# from IPython.display import HTML


# custom weights initialization called on netG and netD
def weights_init(m):
    classname = m.__class__.__name__
    if classname.find('Conv') != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif classname.find('BatchNorm') != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


# Generator Code
class Generator(nn.Module):
    def __init__(self, ngpu):
        super(Generator, self).__init__()
        self.ngpu = ngpu
        self.main = nn.Sequential(
            # L1: input is Z, going into a convolution
            nn.ConvTranspose2d(nz, ngf * 16, 4, 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 16),
            nn.ReLU(True),

            # L2: state size. (ngf*8) x 4 x 4
            nn.ConvTranspose2d(ngf * 16, ngf * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 8),
            nn.ReLU(True),

            # L3: state size. (ngf*8) x 4 x 4
            nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 4),
            nn.ReLU(True),

            # L4: state size. (ngf*4) x 8 x 8
            nn.ConvTranspose2d( ngf * 4, ngf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 2),
            nn.ReLU(True),

            # L5: state size. (ngf*2) x 16 x 16
            nn.ConvTranspose2d( ngf * 2, ngf, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf),
            nn.ReLU(True),

            # L6: state size. (ngf) x 32 x 32
            nn.ConvTranspose2d(image_size, nc, 4, 2, 1, bias=False),
            nn.Tanh()
            # state size. (nc) x 64 x 64
        )

        # self.main = nn.Sequential(
        #     # L1: input is Z, going into a convolution
        #     # nn.ConvTranspose2d(nz, ngf * 64, 4, 1, 0, bias=False),
        #     # nn.BatchNorm2d(ngf * 64),
        #     # nn.ReLU(True),
        #
        #     # L1: input is Z, going into a convolution
        #     nn.ConvTranspose2d(nz, ngf * 32, 4, 1, 0, bias=False),
        #     nn.BatchNorm2d(ngf * 32),
        #     nn.ReLU(True),
        #
        #     # # L2: state size. (ngf*64) x 4 x 4
        #     # nn.ConvTranspose2d(ngf * 64, ngf * 32, 4, 2, 1, bias=False),
        #     # nn.BatchNorm2d(ngf * 32),
        #     # nn.ReLU(True),
        #
        #     # l2: state size. (ngf*32) x 8 x 8
        #     nn.ConvTranspose2d(ngf * 32, ngf * 16, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ngf * 16),
        #     nn.ReLU(True),
        #
        #     # L3: state size. (ngf*16) x 16 x 16
        #     nn.ConvTranspose2d(ngf * 16, ngf * 8, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ngf * 8),
        #     nn.ReLU(True),
        #
        #     # L4: state size. (ngf*8) x 32 x 32
        #     nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ngf * 4),
        #     nn.ReLU(True),
        #
        #     # L5: state size. (ngf*4) x 64 x 64
        #     nn.ConvTranspose2d(ngf * 4, ngf * 2, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ngf * 2),
        #
        #     # L6: state size. (ngf*4) x 64 x 64
        #     nn.ConvTranspose2d(ngf * 2, ngf, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ngf),
        #
        #     # L7: state size. (ngf) x 128 x 128
        #     nn.ConvTranspose2d(ngf, nc, 4, 2, 1, bias=False),
        #     nn.Tanh()
        #     # state size. (nc) x 256 x 256
        # )

    def forward(self, input):
        return self.main(input)


class Discriminator(nn.Module):
    def __init__(self, ngpu):
        super(Discriminator, self).__init__()
        self.ngpu = ngpu
        self.main = nn.Sequential(
            # L1: input is (nc) x 64 x 64
            nn.Conv2d(nc, ndf, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),

            # L2: state size. (ndf) x 32 x 32
            nn.Conv2d(ndf, ndf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),

            # L3: state size. (ndf*2) x 16 x 16
            nn.Conv2d(ndf * 2, ndf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),

            # L4: state size. (ndf*4) x 8 x 8
            nn.Conv2d(ndf * 4, ndf * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),

            # L5: state size. (ndf*8) x 8 x 8
            nn.Conv2d(ndf * 8, ndf * 16, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 16),
            nn.LeakyReLU(0.2, inplace=True),

            # L6: state size. (ndf*8) x 4 x 4
            nn.Conv2d(ndf * 16, 1, 4, 1, 0, bias=False),
            nn.Sigmoid()
        )
        # self.main = nn.Sequential(
        #     # L1: input is (nc) x 256 x 256
        #     nn.Conv2d(nc, ndf, 4, 2, 1, bias=False),
        #     nn.LeakyReLU(0.2, inplace=True),
        #
        #     # L2: state size. (ndf) x 128 x 128
        #     nn.Conv2d(ndf, ndf * 2 , 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ndf * 2),
        #     nn.LeakyReLU(0.2, inplace=True),
        #
        #     # L3: state size. (ndf * 2) x 64 x 64
        #     nn.Conv2d(ndf * 2, ndf * 4, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ndf * 4),
        #     nn.LeakyReLU(0.2, inplace=True),
        #
        #     # L4: state size. (ndf * 4) x 32 x 32
        #     nn.Conv2d(ndf * 4, ndf * 8, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ndf * 8),
        #     nn.LeakyReLU(0.2, inplace=True),
        #
        #     # L5: state size. (ndf * 8) x 16 x 16
        #     nn.Conv2d(ndf * 8, ndf * 16, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ndf * 16),
        #     nn.LeakyReLU(0.2, inplace=True),
        #
        #     # L6: state size. (ndf * 16) x 8 x 8
        #     nn.Conv2d(ndf * 16, ndf * 32, 4, 2, 1, bias=False),
        #     nn.BatchNorm2d(ndf * 32),
        #     nn.LeakyReLU(0.2, inplace=True),
        #
        #     # L7: state size. (ndf*32) x 4 x 4
        #     nn.Conv2d(ndf * 32, 1, 4, 1, 0, bias=False),
        #     nn.Sigmoid()

            # L7: state size. (ndf * 32) x 8 x 8
            # nn.Conv2d(ndf * 32, ndf * 64, 4, 2, 1, bias=False),
            # nn.BatchNorm2d(ndf * 64),
            # nn.LeakyReLU(0.2, inplace=True),

            # L8: state size. (ndf*64) x 4 x 4
            # nn.Conv2d(ndf * 64, 1, 4, 1, 0, bias=False),
            # nn.Sigmoid()
        # )

    def forward(self, input):
        return self.main(input)


if __name__ =='__main__':

    parser = argparse.ArgumentParser()

    # hyperparameters sent by the client are passed as command-line arguments to the script.
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--lr', type=float, default=0.0002)
    parser.add_argument('--beta1', type=float, default=0.5)
    parser.add_argument('--use_cuda', type=bool, default=True)
    # TODO: manualSeed = random.randint(1, 10000) # use if you want new results
    parser.add_argument('--manual_seed', type=int, default=999)
    parser.add_argument('--batch_size', type=int, default=64)


    # Data, model, and output directories
    parser.add_argument('--output_data_dir', type=str, default=os.environ['SM_OUTPUT_DATA_DIR'])
    parser.add_argument('--model_dir', type=str, default=os.environ['SM_MODEL_DIR'])
    # parser.add_argument('--train', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    # parser.add_argument('--test', type=str, default=os.environ['SM_CHANNEL_TESTING'])
    # From https://github.com/awslabs/amazon-sagemaker-examples/blob/master/sagemaker-python-sdk/pytorch_cnn_cifar10/pytorch_local_mode_cifar10.ipynb
    # env = sagemaker_containers.training_env()
    # parser.add_argument('--data_dir', type=str, default=env.channel_input_dirs.get('training'))
    parser.add_argument('--data-dir', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    
    args, _ = parser.parse_known_args()
    print('args: {}'.format(args))

    # Set random seem for reproducibility
    random.seed(args.manual_seed)
    torch.manual_seed(args.manual_seed)

    # Root directory for dataset
    # dataroot = 'images/base'
    dataroot = args.data_dir  # args['train']

    model_netG_path = os.path.join(args.model_dir, 'model_netG.pth')
    model_netD_path = os.path.join(args.model_dir, 'model_netD.pth')
    checkpoint_state_path = os.path.join(args.output_data_dir, 'model_info.pth')

    # Number of workers for dataloader
    workers = 2

    # Batch size during training
    batch_size = args.batch_size # ['batch-size']

    # Spatial size of training images. All images will be resized to this
    #   size using a transformer.
    image_size = 128 # 64

    # Number of channels in the training images. For color images this is 3
    nc = 3

    # Size of z latent vector (i.e. size of generator input)
    nz = 100

    # Size of feature maps in generator
    ngf = 128  # 128

    # Size of feature maps in discriminator
    ndf = 128  # 128

    # Number of training epochs
    num_epochs = args.epochs

    # Learning rate
    lr = args.lr

    # Beta1 hyperparam for Adam optimizers
    beta1 = args.beta1

    # Number of GPUs available. Use 0 for CPU mode.
    ngpu = 1

    # Create the dataset
    print('dataroot={}'.format(dataroot))
    dataset = dset.ImageFolder(root=dataroot,
                               transform=transforms.Compose([
                                   transforms.Resize(image_size),
                                   # transforms.CenterCrop(image_size),
                                   transforms.ToTensor(),
                                   transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                               ]))
    # Create the dataloader
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                                             shuffle=True, num_workers=workers)

    # Decide which device we want to run on
    device = torch.device("cuda:0" if (torch.cuda.is_available() and ngpu > 0) else "cpu")

    # Create the generator
    netG = Generator(ngpu).to(device)

    # Handle multi-gpu if desired
    if (device.type == 'cuda') and (ngpu > 1):
        netG = nn.DataParallel(netG, list(range(ngpu)))

    # Apply the weights_init function to randomly initialize all weights
    #  to mean=0, stdev=0.2.
    netG.apply(weights_init)

    # Print the model
    # TODO - Write this out to S3 so we can view it later
    print(netG)

    # Create the Discriminator
    netD = Discriminator(ngpu).to(device)

    # Handle multi-gpu if desired
    if (device.type == 'cuda') and (ngpu > 1):
        netD = nn.DataParallel(netD, list(range(ngpu)))

    # Apply the weights_init function to randomly initialize all weights
    #  to mean=0, stdev=0.2.
    netD.apply(weights_init)

    # Print the model
    # TODO - Write this out to S3 so we can view it later
    print(netD)

    # Initialize BCELoss function
    criterion = nn.BCELoss()

    # Create batch of latent vectors that we will use to visualize
    #  the progression of the generator
    fixed_noise = torch.randn(64, nz, 1, 1, device=device)

    # Establish convention for real and fake labels during training
    real_label = 1
    fake_label = 0

    # Setup Adam optimizers for both G and D
    optimizerD = optim.Adam(netD.parameters(), lr=lr, betas=(beta1, 0.999))
    optimizerG = optim.Adam(netG.parameters(), lr=lr, betas=(beta1, 0.999))

    # Training Loop

    # Lists to keep track of progress
    img_list = []
    G_losses = []
    D_losses = []
    iters = 0
    best_state = None

    print("Starting Training Loop...")
    # For each epoch
    for epoch in range(num_epochs):
        # For each batch in the dataloader
        for i, data in enumerate(dataloader, 0):

            ############################
            # (1) Update D network: maximize log(D(x)) + log(1 - D(G(z)))
            ###########################
            ## Train with all-real batch
            netD.zero_grad()
            # Format batch
            real_cpu = data[0].to(device)
            b_size = real_cpu.size(0)
            label = torch.full((b_size,), real_label, device=device)
            # Forward pass real batch through D
            output = netD(real_cpu).view(-1)
            # Calculate loss on all-real batch
            errD_real = criterion(output, label)
            # Calculate gradients for D in backward pass
            errD_real.backward()
            D_x = output.mean().item()

            ## Train with all-fake batch
            # Generate batch of latent vectors
            noise = torch.randn(b_size, nz, 1, 1, device=device)
            # Generate fake image batch with G
            fake = netG(noise)
            label.fill_(fake_label)
            # Classify all fake batch with D
            output = netD(fake.detach()).view(-1)
            # Calculate D's loss on the all-fake batch
            errD_fake = criterion(output, label)
            # Calculate the gradients for this batch
            errD_fake.backward()
            D_G_z1 = output.mean().item()
            # Add the gradients from the all-real and all-fake batches
            errD = errD_real + errD_fake
            # Update D
            optimizerD.step()

            ############################
            # (2) Update G network: maximize log(D(G(z)))
            ###########################
            netG.zero_grad()
            label.fill_(real_label)  # fake labels are real for generator cost
            # Since we just updated D, perform another forward pass of all-fake batch through D
            output = netD(fake).view(-1)
            # Calculate G's loss based on this output
            errG = criterion(output, label)
            # Calculate gradients for G
            errG.backward()
            D_G_z2 = output.mean().item()
            # Update G
            optimizerG.step()

            # Output training stats
            if i % 500 == 0:
                # TODO - Save to S3!
                print('[%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f\tD(x): %.4f\tD(G(z)): %.4f / %.4f'
                      % (epoch, num_epochs, i, len(dataloader),
                         errD.item(), errG.item(), D_x, D_G_z1, D_G_z2))
            if not best_state or errG < best_state['errG']:
                best_state = {
                    'epoch': epoch,
                    'lr': lr,
                    'errD': errD.item(),
                    'errG': errG.item(),
                    'D_x': D_x,
                    'D_G_z1': D_G_z1,
                    'D_G_z2': D_G_z2
                    # 'val_loss': val_loss,
                    # 'val_ppl': math.exp(val_loss),
                }
                with open(checkpoint_state_path, 'w') as f:
                    f.write('epoch {:3d} | lr: {:5.2f} | [%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f\tD(x): %.4f\tD(G(z)): %.4f / %.4f'
                      % (epoch, num_epochs, i, len(dataloader),
                         errD.item(), errG.item(), D_x, D_G_z1, D_G_z2))
            # else:
            #     # Anneal the learning rate if no improvement has been seen in the validation dataset.
            #     lr /= 4.0

            # Save Losses for plotting later
            G_losses.append(errG.item())
            D_losses.append(errD.item())

            # Check how the generator is doing by saving G's output on fixed_noise
            if (iters % 50 == 0) or ((epoch == num_epochs - 1) and (i == len(dataloader) - 1)):
                with torch.no_grad():
                    fake = netG(fixed_noise).detach().cpu()
                    print('Generated fake images of shape {}'.format(fake.shape))
                img_list.append([fake])
                # img_list.append(vutils.make_grid(fake, padding=2, normalize=True))

            iters += 1

    print('Saving final model: {}'.format(best_state))
    with open(model_netG_path, 'wb') as f:
        torch.save(netG.state_dict(), f)
    with open(model_netD_path, 'wb') as f:
        torch.save(netD.state_dict(), f)

    # Plot Loss vs training iteration
    # TODO - Save to S3
    # plt.figure(figsize=(10,5))
    # plt.title("Generator and Discriminator Loss During Training")
    # plt.plot(G_losses,label="G")
    # plt.plot(D_losses,label="D")
    # plt.xlabel("iterations")
    # plt.ylabel("Loss")
    # plt.legend()
    # plt.show()

    # Visualisation of G's progression
    # TODO - Save to S3
    # fig = plt.figure(figsize=(8, 8))
    # plt.axis("off")
    # ims = [[plt.imshow(np.transpose(i, (1, 2, 0)), animated=True)] for i in img_list]
    # ani = animation.ArtistAnimation(fig, ims, interval=1000, repeat_delay=1000, blit=True)
    #
    # HTML(ani.to_jshtml())

    # Grab a batch of real images from the dataloader
    real_batch = next(iter(dataloader))

    # Plot the real images
    # TODO - Save to S3
    # plt.figure(figsize=(15,15))
    # plt.subplot(1,2,1)
    # plt.axis("off")
    # plt.title("Real Images")
    # plt.imshow(np.transpose(vutils.make_grid(real_batch[0].to(device)[:64], padding=5, normalize=True).cpu(),(1,2,0)))
    #
    # # Plot the fake images from the last epoch
    # plt.subplot(1,2,2)
    # plt.axis("off")
    # plt.title("Fake Images")
    # plt.imshow(np.transpose(img_list[-1],(1,2,0)))
    # plt.show()

    np.save(os.path.join(args.model_dir, 'training_loss_g'), G_losses)
    np.save(os.path.join(args.model_dir, 'training_loss_d'), D_losses)
    np.save(os.path.join(args.model_dir, 'generated_images'), np.transpose(img_list[-1], (1, 2, 0)))



