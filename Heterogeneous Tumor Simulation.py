import numpy as np
import matplotlib.pyplot as plt
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import generate_uid
from scipy.ndimage import gaussian_filter

# Set the size of the 3D image (volume dimensions)
image_size = 256

# Define the tumor properties: radius and center within the image
tumor_radius = int(image_size / 6)
tumor_center = (int(image_size / 2), int(image_size / 2), int(image_size / 2))

# Define properties for tiny heterogeneous circles within the tumor
num_circles = 10000  # Number of tiny circles. 
circle_radius_range = (2, 5)  # Radius range of the circles
circle_uptake_range = (50, 255)  # Intensity range (gray levels)

# Define Gaussian blurring parameters (PSF: Point Spread Function)
psf_sigma = 3.0  # Standard deviation for Gaussian filter

# Initialize a blank 3D volume (all zeros)
volume = np.zeros((image_size, image_size, image_size), dtype=np.float32)

# Generate a spherical tumor mask within the volume
y, x, z = np.ogrid[:image_size, :image_size, :image_size]
tumor_mask = (x - tumor_center[0]) ** 2 + (y - tumor_center[1]) ** 2 + (z - tumor_center[2]) ** 2 <= tumor_radius ** 2

# Populate the tumor with tiny circles of varying intensities
for _ in range(num_circles):
    # Randomly generate circle properties (radius and intensity)
    circle_radius = np.random.uniform(*circle_radius_range)
    circle_uptake = int(np.random.uniform(*circle_uptake_range))  # Convert to integer intensity

    # Ensure the circle's position is within the tumor boundaries
    while True:
        circle_x = np.random.randint(tumor_center[0] - tumor_radius + circle_radius,
                                     tumor_center[0] + tumor_radius - circle_radius + 1)
        circle_y = np.random.randint(tumor_center[1] - tumor_radius + circle_radius,
                                     tumor_center[1] + tumor_radius - circle_radius + 1)
        circle_z = np.random.randint(tumor_center[2] - tumor_radius + circle_radius,
                                     tumor_center[2] + tumor_radius - circle_radius + 1)

        # Check if the circle is inside the tumor mask
        if tumor_mask[circle_x, circle_y, circle_z]:
            break

    # Create a mask for the tiny circle and update its intensity in the volume
    circle_mask = (x - circle_x) ** 2 + (y - circle_y) ** 2 + (z - circle_z) ** 2 <= circle_radius ** 2
    volume[circle_mask] = circle_uptake

# Apply Gaussian blurring to simulate the PET imaging PSF
volume_blurred = gaussian_filter(volume, sigma=psf_sigma)

# Get the intensity range of the blurred image for normalization
min_original = np.min(volume_blurred)
max_original = np.max(volume_blurred)

# Scaling factors for different noise levels (low, medium, high)
scaling_factors = [10, 4, 1]

# Generate noisy images using Poisson noise
noisy_images = []
for scale_factor in scaling_factors:
    # Scale the image for noise addition
    scaled_image = volume_blurred * scale_factor

    # Add Poisson noise to the image
    noisy_image = np.random.poisson(scaled_image).astype(np.float32)

    # Normalize the noisy image to 0-1 range
    min_noisy = np.min(noisy_image)
    max_noisy = np.max(noisy_image)
    noisy_image_normalized = (noisy_image - min_noisy) / (max_noisy - min_noisy)

    # Scale to the DICOM range (0-65535)
    noisy_image_dicom = np.clip(noisy_image_normalized * 65535, 0, 65535)
    noisy_images.append(noisy_image_dicom)

# Display the images (original and noisy)
fig, axes = plt.subplots(1, 4, figsize=(20, 5))

# Original blurred tumor image
axes[0].imshow(volume_blurred[:, :, int(image_size / 2)], cmap="plasma")
axes[0].set_title("Original Tumor Image")
axes[0].axis("off")

# Low-noise tumor image
axes[1].imshow(noisy_images[0][:, :, int(image_size / 2)], cmap="plasma")
axes[1].set_title("Low Noise Image")
axes[1].axis("off")

# Medium-noise tumor image
axes[2].imshow(noisy_images[1][:, :, int(image_size / 2)], cmap="plasma")
axes[2].set_title("Medium Noise Image")
axes[2].axis("off")

# High-noise tumor image
axes[3].imshow(noisy_images[2][:, :, int(image_size / 2)], cmap="plasma")
axes[3].set_title("High Noise Image")
axes[3].axis("off")

plt.tight_layout()
plt.show()

# Save 3D volume as a DICOM file
def save_dicom_image(volume, filename):
    # Define DICOM-specific metadata and voxel properties
    voxel_size = 1.5  # Voxel size in mm
    pixel_spacing = [voxel_size, voxel_size, voxel_size]
    patient_position = "HFS"  # Hypothetical orientation: Head First Supine

    # Create a FileDataset object for DICOM file metadata
    ds_pet = FileDataset("", {}, file_meta=Dataset(), preamble=b"\0" * 128)

    # Populate required DICOM attributes
    ds_pet.file_meta.MediaStorageSOPClassUID = generate_uid()
    ds_pet.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    ds_pet.SOPInstanceUID = generate_uid()
    ds_pet.SOPClassUID = pydicom.uid.PositronEmissionTomographyImageStorage
    ds_pet.StudyInstanceUID = "1.2.3.4"
    ds_pet.SeriesInstanceUID = generate_uid()
    ds_pet.SeriesNumber = 1
    ds_pet.Modality = "PT"
    ds_pet.PatientName = "Simulation"
    ds_pet.PatientID = "123456"
    ds_pet.PixelSpacing = pixel_spacing
    ds_pet.PatientPosition = patient_position
    ds_pet.ImagePositionPatient = [0, 0, 0]
    ds_pet.SliceThickness = voxel_size
    ds_pet.Rows, ds_pet.Columns, ds_pet.NumberOfFrames = volume.shape
    ds_pet.PixelData = volume.astype(np.uint16).tobytes()
    ds_pet.SamplesPerPixel = 1
    ds_pet.PhotometricInterpretation = "MONOCHROME2"
    ds_pet.BitsAllocated = 16
    ds_pet.BitsStored = 16
    ds_pet.HighBit = 15
    ds_pet.PixelRepresentation = 0  # Unsigned integer

    # Save the volume as a DICOM file
    ds_pet.save_as(filename, write_like_original=False)

# Save the original tumor image as a DICOM file
save_dicom_image(volume_blurred, "HOM_RES0_F.dcm")
print("Saved original tumor image as DICOM file: HOM_RES0_F.dcm")

# Save the noisy images as separate DICOM files
filenames = ['HOM_RES0_F_Low_Noise_Tumor.dcm', 'HOM_RES0_F_Medium_Noise_Tumor.dcm', 'HOM_RES0_F_High_Noise_Tumor.dcm']
for i, noisy_image in enumerate(noisy_images):
    save_dicom_image(noisy_image, filenames[i])
    print(f"Saved noisy image as DICOM file: {filenames[i]}")
